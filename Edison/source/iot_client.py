from tornado import escape
from tornado import gen
from tornado import httpclient
from tornado import httputil
from tornado import ioloop
from tornado import websocket

from Queue import Queue, Empty
from config_handler import config, prefs
from multiprocessing.pool import ThreadPool

import client as client_module

import functools
import json
import time
import logging
import re
import pprint
import datetime

DEFAULT_CONNECT_TIMEOUT = 60
DEFAULT_REQUEST_TIMEOUT = 60

regex_split_json_packets = re.compile('}\s*{')
message_queue = Queue()
iot_connected = False


class WebSocketClient():
    """
    Base for web socket clients.
    """

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                 request_timeout=DEFAULT_REQUEST_TIMEOUT):
        logging.info('Initializing WebSocketClient instance')
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout

    def connect(self, io_loop=None, url=None):
        """
        Connect to the server.

        :param str url: server URL.
        """
        if url is None:
            url = 'ws://localhost:8878/API-ws/'
        if io_loop is None:
            io_loop = ioloop.IOLoop.current()

        logging.info('Opening websocket to IoT-Backend: %s' % str(url))
        headers = httputil.HTTPHeaders({'Content-Type': 'application/json'})
        request = httpclient.HTTPRequest(url=url,
                                         connect_timeout=self.connect_timeout,
                                         request_timeout=self.request_timeout,
                                         headers=headers)
        ws_conn = websocket.WebSocketClientConnection(io_loop, request)
        ws_conn.connect_future.add_done_callback(self.connect_callback)

    def send(self, data):
        """
        Send message to the server

        :param str data: message.
        """
        if not self.ws_connection:
            raise RuntimeError('Web socket connection is closed.')

        self.ws_connection.write_message(escape.utf8(json.dumps(data)))

    def close(self):
        """
        Close connection.
        """
        if not self.ws_connection:
            raise RuntimeError('Web socket connection is already closed.')

        self.ws_connection.close()

    def connect_callback(self, future):
        '''
        Callback function called after connection attempt is done.

        :param future: Asynchronous result from connection attempt
        :return: None
        '''
        if future.exception() is None:
            self.ws_connection = future.result()
            self.on_connection_success()
            self.read_messages()
        else:
            self.on_connection_error(future.exception())

    @gen.coroutine
    def read_messages(self):
        '''
        Asynchronous generator that reads all messages coming from server

        :return: None
        '''
        while True:
            msg = yield self.ws_connection.read_message()
            if msg is None:
                self.on_connection_close()
                break

            self.on_message(msg)

    def on_message(self, msg):
        """
        This is called when new message is available from the server.

        :param str msg: server message.
        """

        pass

    def on_connection_success(self):
        """
        This is called on successful connection to the server.
        """

        pass

    def on_connection_close(self):
        """
        This is called when server closed the connection.
        """
        pass

    def on_connection_error(self, exception):
        """
        This is called in case if connection to the server could
        not established.
        """
        pass


class IoTWebSocketClient(WebSocketClient):
    '''
    Create a communication channel to the IoT Backend
    and handle all incoming/outgoing communication to it.
    '''
    prev_id = 1000

    def on_connection_success(self):
        """
        This is called on successful connection to the server. It first sends
        an initial message to the server to initialize the channel by setting
        its mode and also by providing its client name with which to be
        identified.
        """
        from random import randint
        global iot_connected
        iot_connected = True
        logging.info('IoT Connected! Conn:%s' % str(iot_connected))
        self.send_message('channel', 'setchannelmode',
                          {'channelmode': 'control',
                           'clientname': 'SM' + str(randint(0,100))})
        pool_tx = ThreadPool(processes=1)
        async_tx = pool_tx.apply_async(self.inspect_queue_for_messages, ())

    def on_connection_close(self):
        """
        This is called when server closed the connection. After server closes
        connection, This will try to reconnect immediately to reestablish
        communication.
        """
        global iot_connected
        iot_connected = False
        self.ws_connection = None
        logging.info('IoT Connection closed! Conn:%s' % str(iot_connected))
        time.sleep(prefs.getint('timeouts', 'timeout_iot_retry', fallback=2))
        self.connect()

    def on_connection_error(self, exception):
        """
        This is called in case if connection to the server could
        not be established. This will try to reconnect immediately to
        establish communication. Connection error might occur when clients
        try to connect when server is down.
        """
        global iot_connected
        iot_connected = False
        self.ws_connection = None
        logging.warning('IoT Connection error: Conn %s | %s' %
                        (str(iot_connected), str(exception)))
        time.sleep(prefs.getint('timeouts', 'timeout_nms_retry', fallback=2))
        self.connect()

    def inspect_queue_for_messages(self):
        '''
        Asynchronously run to constantly inspect if there is any existing
        message in the queue to be sent to the IoT. Any other
        module wanting to send a notification should place it first in the
        queue.

        :return: None
        '''
        import random
        while True:
            try:
                if iot_connected:
                    tx_message = message_queue.get(block=True, timeout=5)
                    if tx_message:
                        self.send_message('control', 'send_notification',
                                          tx_message)
                    else:
                        raise Empty
            except Empty:
                # TODO remove autogenerating notifications. Just for testing
                continue
        return

    def send_message(self, handler, msgtype, msg, respond_id=None):
        '''
        Send a message to IoT.

        :param handler: API handler from where reply comes from
        :param msgtype: Type of message sent. Example: 'notification', 'ack'
        :param msg: Payload of message
        :param respond_id: Message ID
        :return: None
        '''
        if respond_id is None:
            respond_id = self.generate_id()

        message = {
            'msgid': respond_id,
            'handler': handler,
            'command': msgtype,
            'data': msg
        }

        logging.info(
            '%s | Sending to %s - msgid: %s, handler: %s, command: %s' %
            (str(datetime.datetime.now()),
             'IoT', respond_id, handler, msgtype))
        pp_message = pprint.pformat(message)
        logging.info(
            '>>>Sending to IoT Backend<<<\n' +
            '\treceiver:\t\t%s\n' % 'IoT Backend' +
            '\thandler:\t%s\n\tmessage id:\t%d\n' % (handler, respond_id) +
            '\tmessagetype:\t%s\n' % (msgtype) +
            '\t=============================================\n'
            '\t%s\n' % str(pp_message) +
            '\t=============================================')

        if not self.ws_connection:
            logging.warning('Web socket connection is closed.')
            return
        self.ws_connection.write_message(escape.utf8(json.dumps(message)))

    def on_message(self, message):
        '''
        Handle an incoming message on the websocket.

        :param message: JSON Message as received from websocket
        :return: None
        '''
        try:
            message = self.unpack_json(message)
            if message is None:
                # Either malformed JSON or stacked and handled separately
                return

            unpacked = self.unpack_message(message)
            if unpacked is None:
                # Invalid data in message, already handled
                return

            msgid, handler, msgtype, data = unpacked
            self.process_message(handler, msgid, msgtype, data, message)
        except OSError as e:
            if e.errno == 9:
                pass
            else:
                logging.exception("Uncaught and unhandled internal error: " +
                                  str(type(e)) + ': ' + str(e))
        except Exception as e:
            logging.exception("Uncaught and unhandled internal error: " +
                              str(type(e)) + ': ' + str(e))

    def unpack_json(self, message):
        '''
        Try to unpack the message into a Python dict. If it fails, first check
        whether this is because several packets are stacked together.

        :param message: JSON Message as received from websocket
        :return: Unpacked JSON in a Python dictionary
        '''
        try:
            message = json.loads(message)
            return message
        except ValueError:
            # Try if stacked request
            messages = regex_split_json_packets.split(message)
            if len(messages) > 1:
                # Remove trailing '{' and '}' from resp. first and last elem
                messages[0] = messages[0].strip()[1:]
                messages[-1] = messages[-1].strip()[:-1]

                compiled_message = ''
                for msg in messages:
                    # Reconstruct message after previous split

                    compiled_message += '{' + msg + '}'

                    # Check if count of " characters is equal. If not, it is
                    # part of a data field and the message should not be split
                    # here.
                    if compiled_message.count('"') % 2 == 0:
                        # Split message complete, call with separate
                        self.on_message(compiled_message)
                        compiled_message = ''
                return

            logging.warning('Malformed JSON packet received from IoT')
            return

    def unpack_message(self, message):
        '''
        Try to unpack the message into variables.

        :param message: Unpacked JSON in a Python dictionary
        :return: Unpacked dict into individual expected fields
        '''
        try:
            msgid = int(message['msgid'])
            handler = message['handler']
            msgtype = message['command']
            data = message['data']
            return msgid, handler, msgtype, data
        except KeyError as e:
            try:
                handler = message['handler']
            except KeyError:
                handler = 'handler_unidentifiable'

            try:
                respond_id = int(message['msgid'])
            except KeyError:
                respond_id = -1
            except ValueError:
                respond_id = -1

            logging.warning('Malformed packet received from IoT' +
                            ' - Missing parameter')
            return

    def process_message(self, handler, msgid, msgtype, data, message):
        '''
        Receives unpacked message and decides how to process it depending on
        its content.

        :param handler: API handler to process message. Example: 'control'
        :param msgid: Message ID
        :param msgtype:  Command received. Example: 'notification'
        :param data: Payload of message
        :param message: Full message in Python dictionary
        :return: None
        '''
        logging.info(
            '%s | Receiving from IoT - msgid: %d, handler: %s, command: %s' %
            (str(datetime.datetime.now()), msgid, handler, msgtype))
        pp_data = pprint.pformat(data)
        logging.info(
            '>>>Receiving from IoT<<<\n' +
            '\tsender:\t\t%s\n' % 'IoT' +
            '\thandler:\t%s\n\tmessage id:\t%d\n' % (handler, msgid) +
            '\tmessagetype:\t%s\n' % (msgtype) +
            '\t=============================================\n'
            '\t%s\n' % str(pp_data) +
            '\t=============================================')

        response = None
        try:
            if handler == 'control' and msgtype == 'notification':
                response = self.send_notification_to_final_user(data)
        except Exception:
            logging.error('Unknown exception while handling notification ' +
                          'from IoT')
        if response is not None:
            r_channel, r_receivers, r_msgtype, \
                r_message, r_respondID = response

            if r_respondID is None:
                r_respondID = self.generate_id()

            if r_msgtype == 'error':
                logging.error('Error while handling IoT message: '
                              + r_message['msg'])
            elif r_msgtype == 'notification':
                # Send notification to all receivers
                for r in r_receivers:
                    channel = r.get_channel(r_channel)
                    channel.send(r_channel, r_msgtype, r_message, r_respondID)

    def send_notification_to_final_user(self, message):
        '''
        Handle the reception of a send_notification message from IoT.

        :param message: Notification to be sent. Dictionary with corresponding
         fields.
        :return: Tuple with response to be sent to final user.
        '''
        # Forward notification to final users.
        receivers = []
        if 'target' in message:
            if message['target'] == 'broadcast':
                sender_uid = message.get('sender_uid', None)
                is_admin_user = True
                if not is_admin_user:
                    return ('control', None, 'error',
                            {'msg': 'User must be admin to broadcast a' +
                                    ' message'},
                            None)
                all_clients = client_module.find_clients_all()
                if all_clients is None:
                    return ('control', None, 'error',
                            {'msg': 'No clients in the system.'},
                            None)
                receivers.extend(all_clients)
            else:
                target = client_module.find_client(message['target'])
                if target is None:
                    return ('control', None, 'error',
                            {'msg': 'no such client'}, None)
                receivers.append(target)
        sender = None
        # Check if the the original sender_uid comes in message
        if 'sender_uid' in message:
            sender_clients = client_module\
                .find_clients_by_user(message['sender_uid'])
            if len(sender_clients) > 0:
                # Take the first one
                sender = sender_clients[0]

        data = dict()
        if sender is not None:
            data['sender'] = sender.ip
        if 'msg' in message:
            data['msg'] = message['msg']
        if 'display_time' in message:
            data['display_time'] = message['display_time']
        if 'title' in message:
            data['title'] = message['title']
        if 'source' in message:
            data['source'] = message['source']
        if 'type' in message:
            data['type'] = message['type']
        if 'extras' in message:
            data['extras'] = message['extras']
        if 'confirm_is_seen' in message:
            if message['confirm_is_seen'] in ['True', 'true', True]:
                data['confirm_is_seen'] = True
        return ('control', receivers, 'notification', data, None)

    def generate_id(self):
        '''Generate a message ID to use. Yield sequence from 1000-9999'''
        self.prev_id = ((self.prev_id - 999) % 9000) + 1000
        return self.prev_id


def enqueue_message(message, check_connected=False):
    '''
    Add a new notification to the outgoing messages queue to be sent to IoT.

    :param message: Message to be sent. It is a dictionary with the
     corresponding key, value pairs.
    :return: None
    '''
    global iot_connected
    if check_connected and not iot_connected:
        # Generally used for timely notifications that do not make sense if not
        # sent immediately
        logging.warning('IoT not connected. Discarding notification: ' +
                        str(message))
        return

    try:
        logging.info('Conn: %s | Enqueuing notification:' % str(iot_connected)
                     + str(message))
    except Exception:
        pass
    message_queue.put(message)
    return

# def main():
#     client = IoTWebSocketClient()
#     client.connect()
#
#     try:
#         ioloop.IOLoop.instance().start()
#     except KeyboardInterrupt:
#         client.close()
#
#
# if __name__ == '__main__':
#     main()
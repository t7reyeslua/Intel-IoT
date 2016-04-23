import logging
import json
import client
import re
import tornado
import tornado.ioloop
import pprint
import datetime
from config_handler import config, prefs
from APIs.control.controlHandler import ControlAPIHandler
handlers = {'control': ControlAPIHandler()}

regex_split_json_packets = re.compile('}\s*{')


class BaseConnectionHandler:
    prev_id = 1000

    def setup(self):
        self.ip = None
        self.client = None
        self.id = None
        self.channeltype = None
        self.remote_host = None
        self.ioloop = tornado.ioloop.IOLoop.instance()

    def on_message(self, message):
        '''
        Handle an incoming message on the websocket. Extract message ID and
        message class, and then call the appropriate message handler. If a
        response is given,  this to the caller or to the specified
        receiver(s).

        :param message: Message received
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
        except tornado.websocket.WebSocketClosedError:
            # Channel already closed if websocket
            pass
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
        whether this is because several packets are stacked together. If not,
        reply with an error message to the client.

        :param message: Message to unpack in JSON format
        :return: Message unpacked
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

            logging.warning('Client %s, channel %d: ' % (self.ip, self.id) +
                            'Malformed JSON packet received')
            self.send('handler_unidentifyable', 'error',
                      {'msg': 'Malformed JSON packet received'},
                      -1)
            return

    def unpack_message(self, message):
        '''
        Try to unpack the message into variables. If it fails, respond to the
        client that there is a missing parameter.

        :param message: Message
        :return: msgid, handler, msgtype, data
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

            logging.warning('Client %s, channel %d: ' % (self.ip, self.id) +
                            'Malformed packet received - Missing parameter')
            self.send(handler, 'error',
                      {'msg': 'Missing parameter "' + e.args[0] + '"'},
                      respond_id)
            return

    def process_message(self, handler, msgid, msgtype, data, message):
        '''
        Process the message with corresponding handler.

        :param handler: API handler. e.g. 'control'
        :param msgid: Id of message
        :param msgtype: Type of message request. e.g. 'send_notification'
        :param data: Data of message
        :param message: message
        :return: None
        '''
        logging.info(
            '%s | Receiving from %s - msgid: %d, handler: %s, command: %s | %s'
            % (str(datetime.datetime.now()), self.ip, msgid, handler, msgtype,
               str(self)))
        ppdata = pprint.pformat(data)
        logging.debug(
            '>>>Receiving<<<\n' +
            '\tsender:\t\t%s\n' % self.ip +
            '\tchannelid:\t%d\n' % self.id +
            '\thandler:\t%s\n\tmessage id:\t%d\n' % (handler, msgid) +
            '\tmessagetype:\t%s\n' % (msgtype) +
            '\t=============================================\n'
            '\t%s\n' % str(ppdata) +
            '\t=============================================')
        # Determine what to do with this message
        if handler == 'channel':
            self.handle_channel_command(msgtype, msgid, data)
        else:
            # 'Normal' message, find correct handler and handle responses
            # Check if optional user parameter provided in message
            user = None

            # Execute message handler, if any. Otherwise request is malformed
            try:
                response = handlers[handler].handle(msgid, msgtype, data,
                                                    self.client, user)
            except KeyError as e:
                logging.error('Unknown handler %s' % handler)
                self.send(handler, 'error',
                          {'msg': 'Unknown handler "' + e.args[0] + '"'},
                          msgid)
                return
            if response is not None:
                r_channel, r_receivers, r_msgtype, r_message, \
                    r_respondID = response

                if r_receivers is None:
                    # Response just goes current client
                    self.send_self(r_channel, r_msgtype, r_message,
                                   r_respondID)
                elif len(r_receivers) > 0:
                    # Find the appropriate channel for all receivers
                    for r in r_receivers:
                        if r.ws == self:
                            logging.info("Sending through self channel: " +
                                         str(self))
                            self.send_self(r_channel, r_msgtype, r_message,
                                           r_respondID)
                        else:
                            channel = r.get_channel(r_channel)
                            logging.info("Sending through channel: " +
                                         str(channel))
                            if channel is not None:
                                # Add to waiting for acknowledgements list
                                if r_respondID is None:
                                    r_respondID = channel.generate_id()

                                channel.send(r_channel, r_msgtype, r_message,
                                             r_respondID)
                else:
                    # Empty list of receivers equals no responses
                    self.send_ack(msgid, handler)
            else:
                # No explicit response and no effect for other clients, send
                # acknowledgement right away
                self.send_ack(msgid, handler)

    def send_ack(self, respond_id, handler=None):
        '''
        Send an acknowledgement message on this channel.

        :param respond_id: Message Id
        :param handler: Handler
        :return: None
        '''
        if handler is None:
            handler = self.channeltype
        self.send(handler, 'ack', None, respond_id)

    def send_self(self, handler, msgtype, message, respond_id=None):
        '''
        Send a message to this client, by checking whether this is the
        appropriate channel or finding another one.

        :param handler: Hanlder
        :param msgtype: Message type
        :param message: Message
        :param respond_id: Message Id
        :return: None
        '''
        if self.channeltype is None or self.channeltype == handler:
            self.send(handler, msgtype, message, respond_id)
        else:
            channel = self.client.get_channel(handler)
            if channel is not None:
                channel.send(handler, msgtype, message, respond_id)
            else:
                self.send(self.channeltype, 'error',
                          {'msg': 'No channel available for response'},
                          respond_id)

    def send(self, handler, msgtype, message, respond_id=None):
        '''
        Send a message on this channel.

        :param handler: Handler
        :param msgtype: Message type
        :param message: Message
        :param respond_id: Message Id
        :return: None
        '''
        if respond_id is None:
            respond_id = self.generate_id()

        message = {
            'msgid': respond_id,
            'handler': handler,
            'command': msgtype,
            'data': message
        }

        logging.info(
            '%s | Sending to %s - msgid: %s, handler: %s, command: %s' %
            (str(datetime.datetime.now()),
             self.ip, respond_id, handler, msgtype))
        ppmessage = pprint.pformat(message)
        logging.debug(
            '>>>Sending<<<\n' +
            '\treceiver:\t\t%s\n' % self.ip +
            '\tchannelid:\t%d\n' % self.id +
            '\thandler:\t%s\n\tmessage id:\t%d\n' % (handler, respond_id) +
            '\tmessagetype:\t%s\n' % (msgtype) +
            '\t=============================================\n'
            '\t%s\n' % str(ppmessage) +
            '\t=============================================')

        self.write_message(json.dumps(message))

    def handle_channel_command(self, msgtype, msgid, data):
        '''
        Handle channel commands

        :param msgtype: Message type
        :param msgid: Message Id
        :param data: Data of message
        :return: None
        '''
        if msgtype not in ['setchannelmode']:
            self.send('channel', 'error',
                      {'msg': 'Unsupported messagetype "' + msgtype + '"'},
                      msgid)
            return

        if msgtype == 'setchannelmode':
            if self.client.set_channeltype(self.id, data['channelmode']):
                self.channeltype = data['channelmode']
            else:
                self.send('channel', 'error',
                          {'msg': 'Failed to set channel mode'},
                          msgid)
                return
            if 'clientname' in data:
                self.client.set_name(data['clientname'])
        self.send_ack(msgid, 'channel')

    def on_close(self):
        '''
        Handle closing of a connection

        :return: None
        '''
        if self.id is None:
            self.id = -1
        logging.info('Connection to %s, channel %d closed' %
                     (self.ip, self.id))
        if self.id > -1:
            self.client.remove_channel(self.id)
            logging.info('Connection to %s on %s closed' %
                         (self.client.name, self.ip))
        ppdata = pprint.pformat([{c.ws: (c.ip, c.host)}
                                 for c in client.clients.values()])
        logging.info("Current clients after deletion==================")
        logging.info(ppdata)

    def generate_id(self):
        '''
        Generate a message ID to use. Yield sequence from 1000-9999

        :return: Id
        '''
        self.prev_id = ((self.prev_id - 999) % 9000) + 1000
        return self.prev_id

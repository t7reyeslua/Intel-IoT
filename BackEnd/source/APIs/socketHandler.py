import socket
import logging
import tornado
import tornado.tcpserver
import tornado.gen
import tornado.iostream
import client
import APIs.baseConnectionHandler as baseConnectionHandler
from config_handler import config


class SocketAPIHandler(baseConnectionHandler.BaseConnectionHandler):

    def __init__(self, stream, address):
        '''
        Init SocketAPI for a connecting client

        :param stream: Stream
        :param address: Address
        :return: None
        '''
        self.setup()
        self.stream = stream
        self.ip = address[0]
        remote_host = None
        self.client = client.get_client(self.ip, remote_host, self)
        num_channels = len(self.client.channels)
        if num_channels >= config.getint('server',
                                         'max_connections_per_client'):
            logging.warning("Connection limit for client %s reached" % self.ip)
            # Notify and close connection again
            self.id = -1
            self.send('handler_unidentifiable', 'error',
                      {'msg': 'Maximum number of connections for this client' +
                              ' reached'})
            self.on_close()
            self.stream.socket.close()
            return

        self.id = self.client.add_channel(self)

        self.stream.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,
                                      1)
        self.stream.socket.setsockopt(socket.IPPROTO_TCP, socket.SO_KEEPALIVE,
                                      1)
        self.stream.set_close_callback(self.on_disconnect)

        client_name = self.client.name
        if client_name is None:
            client_name = 'Unknown client'
        logging.info('%s from %s is now connected as TCP socket, channel %d' %
                     (client_name, self.ip, self.id))

    @tornado.gen.coroutine
    def on_connect(self):
        yield self.handle_message()

    @tornado.gen.coroutine
    def handle_message(self):
        try:
            length_exists = False
            while True:
                lengthstring = yield self.stream.read_until(b'\n')
                lengthstring = lengthstring.decode('utf-8').rstrip('\n')\
                    .rstrip('\r')
                logging.info("[Header] " + str(lengthstring))
                if 'length' not in lengthstring or ':' not in lengthstring:
                    pass
                else:
                    length_exists = True
                    length = int(lengthstring.split(':')[1])
                    self.get_message(length)
                yield []
            if not length_exists:
                self.send('handler_unidentifiable', 'error',
                          {'msg': 'No length:<length> header provided'},
                          -1)
        except tornado.iostream.StreamClosedError:
            pass
        except OSError as e:
            if e.errno == 9:
                pass
            else:
                raise

    @tornado.gen.coroutine
    def get_message(self, length):
        line = yield self.stream.read_bytes(length)
        self.on_message(line.decode('utf-8'))

    # TODO return false if write message failed
    @tornado.gen.coroutine
    def write_message(self, message):
        length = len(message)
        logging.info(length)
        logging.info(message)
        try:
            yield self.stream.write(
                str.encode('length:%d\n' % length + message))
        except tornado.iostream.StreamClosedError:
            pass

    @tornado.gen.coroutine
    def on_disconnect(self):
        self.on_close()
        yield []


class TCPServer(tornado.tcpserver.TCPServer):
    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        connection = SocketAPIHandler(stream, address)
        yield connection.on_connect()

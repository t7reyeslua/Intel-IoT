import logging

import APIs.baseConnectionHandler as baseConnectionHandler
import tornado.websocket

import client
from config_handler import config


class WebsocketAPIHandler(baseConnectionHandler.BaseConnectionHandler,
                          tornado.websocket.WebSocketHandler):
    def open(self, identifier):
        '''
        Handle an incoming connection. Opens up a new channel with the client
        that has this IP.
        '''
        self.setup()
        self.ip = self.request.remote_ip
        self.client = client.get_client(self.ip)
        num_channels = len(self.client.channels)
        if num_channels >= config.getint('server',
                                         'max_connections_per_client'):
            logging.warning("Connection limit for client %s reached" % self.ip)
            # Notify and close connection again
            self.id = -1
            self.send('handler_unidentifyable', 'error',
                      {'msg': 'Maximum number of connections for this client' +
                              ' reached'})
            self.on_close()
            self.close()
            return
        self.id = self.client.add_channel(self)

        logging.info('%s is now connected as websocket, channel %d' %
                     (self.ip, self.id))

    def check_origin(self, origin):
        return True

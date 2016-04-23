import tornado.websocket
import logging
import APIs.baseConnectionHandler as baseConnectionHandler
import client
from config_handler import config
import pprint


class WebsocketAPIHandler(baseConnectionHandler.BaseConnectionHandler,
                          tornado.websocket.WebSocketHandler):
    def open(self, identifier):
        '''
        Handle an incoming connection. Opens up a new channel with the client
        that has this IP.

        :param identifier: Identifier
        :return: None
        '''
        self.setup()
        self.ip = self.request.remote_ip
        logging.info('Creating client for %s from %s' % (self.remote_host,
                                                         self.ip) +
                     ' |' + str(self))
        self.client = client.get_client(self.ip, self.remote_host, self)
        ppdata = pprint.pformat([{c.ws: (c.ip, c.host)}
                                 for c in client.clients.values()])
        logging.info("Current clients on connection==================")
        logging.info(ppdata)
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
            self.close()
            return
        self.id = self.client.add_channel(self)
        client_name = self.client.name
        if client_name is None:
            client_name = 'Unknown client'
        logging.info('%s from %s is now connected as websocket, channel %d' %
                     (client_name, self.ip, self.id))

    def check_origin(self, origin):
        '''
        Check origin of message

        :param origin: origin
        :return: Result boolean
        '''
        return True

    def select_subprotocol(self, subprotocols):
        '''
        Select subprotocol. Used by NMS to receive client's name. May also be
        sent embedded within the 'setchannelmode' command in the 'clientname'
        field.

        :param subprotocols:
        :return:
        '''
        self.remote_host = None
        if len(subprotocols) > 0:
            self.remote_host = subprotocols[0]
            try:
                if self.client is not None:
                    self.client.host = self.remote_host
                    self.client.client_load_info()
            except Exception:
                logging.info("Client not yet created.")
            logging.info('Subprotocol arg: ' + self.remote_host + ' |' +
                         str(self))
        return self.remote_host

import tornado
import tornado.web
import logging
import APIs.baseConnectionHandler as baseConnectionHandler
import client


class HttpAPIHandler(baseConnectionHandler.BaseConnectionHandler,
                     tornado.web.RequestHandler):
    def post(self, something):
        '''
        Handle an incoming request.

        :param something: Something
        :return: None
        '''
        self.setup()

        # Temporarily create channel
        self.ip = self.request.remote_ip
        self.client = client.get_client(self.ip, self.remote_host, self)
        self.id = self.client.add_channel(self)
        client_name = self.client.name
        if client_name is None:
            client_name = 'Unknown client'
        logging.info('%s from %s made HTTP request, temporary channel %d' %
                     (client_name, self.ip, self.id))

        self.on_message(self.request.body.decode('utf-8'))

        # HTTP channel is stateless, so close again
        self.client.remove_channel(self.id)

    def write_message(self, message):
        '''
        Write a message

        :param message: Message to be written
        :return: None
        '''
        self.write(message)

    def select_subprotocol(self, subprotocols):
        '''
        Select subprotocol. Used by NMS to receive client's name. May also be
        sent embedded within the 'setchannelmode' command in the 'clientname'
        field.

        :param subprotocols: Client name. Example: ['Name']
        :return: None
        '''
        self.remote_host = None
        if len(subprotocols) > 0:
            self.remote_host = subprotocols[0]
        return self.remote_host

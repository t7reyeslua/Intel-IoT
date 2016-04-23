import logging
from config_handler import config
import pprint

clients = {}


class Client:
    def __init__(self, ip, remote_host, wsHandler):
        '''
        Create a new client

        :param ip: IP of client
        :return: None
        '''
        self.ip = ip
        self.host = remote_host
        self.ws = wsHandler
        self.channels = {}
        self.name = None
        self.id = None
        self.from_trusted_ip = False
        self.client_load_info()

    def set_name(self, name):
        '''
        Set a friendly name for the client.

        :param name: Client name
        :return: None
        '''
        self.host = name
        self.client_load_info()
        ppdata = pprint.pformat([{c.ws: (c.ip, c.host)}
                                 for c in clients.values()])
        logging.info("Current clients after update==================")
        logging.info(ppdata)
        return

    def client_load_info(self):
        '''
        Load the basic client information.

        :return: None
        '''
        self.name = self.host
        self.id = -1
        self.from_trusted_ip = True

        logging.info("Client info loaded: %s, %s, %s, %s" %
                     (self.ip, self.host, self.id, self.from_trusted_ip))
        return

    def add_channel(self, channel, channel_type=None):
        '''
        Add a new channel to a client (usually on connection).

        A channel gets a generated ID. By taking the current number of elements
        + 1 and then counting down if already exists, we guarantee an ID larger
        than 0 is always found in at most O(n) and it will not be enormously
        large.

        :param channel: Channel to be added
        :param channel_type: Type of channel
        :return: Id of channel
        '''
        try_id = len(self.channels) + 1
        while try_id in self.channels:
            try_id -= 1

        channel_id = try_id
        self.channels[channel_id] = (channel, channel_type)
        return channel_id

    def get_channel(self, channel_type):
        '''
        Get a channel based on the channel type.

        :param channel_type: Type of channel
        :return: Channel
        '''
        for channel_id, channel in self.channels.items():
            if channel[1] == channel_type:
                return channel[0]

        # No specific channel found. Return the first channel with type None.
        # TODO: More intelligence, select a random channel for load balancing
        for channel_id, channel in self.channels.items():
            if channel[1] is None:
                return channel[0]

        # No channel found
        logging.error('Client %s %s:' % (self.name, self.ip) +
                      'No valid channel found for channeltype: %s' %
                      (channel_type))
        return None

    def remove_channel(self, channel_id):
        '''
        Remove a channel from the client

        :param channel_id: Id of channel
        :return: None
        '''
        try:
            del self.channels[channel_id]
        except KeyError:
            logging.warning('Client %s %s: Can\'t remove channel %d ' %
                            (self.name, self.ip, channel_id)
                            + ' - does not exist')

        if len(self.channels) == 0:
            # Stop existing
            del clients[(self.ip, None, self.ws)]

    def set_channeltype(self, channel_id, channel_type):
        '''
        Set a channeltype

        :param channel_id: Id of channel
        :param channel_type: Type of channel. e.g. 'control'
        :return: None
        '''
        try:
            self.channels[channel_id] = (self.channels[channel_id][0],
                                         channel_type)
            return True
        except KeyError:
            logging.error('Client %s %s: Can\'t set channeltype for channel %d'
                          % (self.name, self.ip, channel_id)
                          + ' - does not exist')
            return False

    def remove(self):
        '''
        Remove client

        :return: None
        '''
        # Close all connections
        channels_temp = dict(self.channels)
        for channel_id in channels_temp:
            self.remove_channel(channel_id)

        # Manually remove client if there were no channels
        try:
            del clients[(self.ip, self.host, self.ws)]
        except KeyError:
            # Already gone
            pass


def find_client(ip):
    '''
    Find a client by IP.

    :param ip: IP of client
    :return:  If there is no client with that IP, return None.
    '''
    for key, client in clients.items():
        if client.ip == ip:
            return client
    return None


def find_client_by_id(client_id):
    '''
    Find a client by id

    :param client_id: Id of client
    :return: If there is no client with that id, return None.
    '''
    for key, client in clients.items():
        if client.id == client_id:
            return client
    return None


def find_client_by_name(client_name):
    '''
    Find a client by name

    :param client_name: Name of client
    :return:  If there is no client with that IP, return None.
    '''
    for key, client in clients.items():
        if client.name == client_name:
            return client
    return None


def find_clients_all():
    '''
    Find all existing clients

    :return: List containing all existing clients
    '''
    all_clients = []
    for key, client in clients.items():
        all_clients.append(client)
    if len(all_clients) > 0:
        return all_clients
    return None


def get_client(ip, remote_host=None, wsHandler=None):
    '''
    Find a client by IP. If there is no client with that IP, create a new one.

    :param ip: IP of client
    :return: Client
    '''
    # If client exists return it, otherwise create new client, add to list and
    # return it (handled by dict.setdefault)
    return clients.setdefault((ip, remote_host, wsHandler),
                              Client(ip, remote_host, wsHandler))

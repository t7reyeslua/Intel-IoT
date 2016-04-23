import logging


class BaseAPIHandler:
    '''
    Base class for an API Handler. To be used by the content, control
    and management API's. The handle function shown here will remain to be
    used, but the message_handlers variable will be overwritten with a dict
    specifying the handler to call for a certain message type.
    '''
    name = ''
    message_handlers = {}

    def authenticate(self, client, msgid, data, user, msgtype):
        '''
        Authenticate client to be able to use API

        :param client: Client
        :param msgid: Message ID
        :param data: Data
        :param user: User
        :param msgtype: Message Type
        :return: True/False
        '''
        pass

    def handle(self, msgid, msgtype, data, client, user=None):
        '''
        Find the right handler and distribute the incoming message to there.

        :param msgid: Message ID
        :param msgtype: Message Type
        :param data: Data
        :param client: Client
        :param user: User
        :return: None
        '''
        try:
            func = self.message_handlers[msgtype]
            try:
                return func(client, msgid, data, user)
            except KeyError as e:
                logging.exception('Keyerror inside function:', e.args[0])
                return (self.name, None, 'error',
                        {'msg': 'Missing parameter "' + str(e.args[0]) + '"'},
                        msgid)
            except TypeError as e:
                logging.exception('TypeError inside function: ' + str(e))
                return (self.name, None, 'error',
                        {'msg': 'Invalid command syntax'},
                        msgid)
            except AttributeError as e:
                logging.exception('AttributeError inside function: ' + str(e))
                return (self.name, None, 'error',
                        {'msg': 'Invalid command syntax'},
                        msgid)
        except KeyError:
            logging.error('Unknown messagetype %s' % msgtype)
            return (self.name, None, 'error', {'msg': 'Unknown messagetype'},
                    msgid)

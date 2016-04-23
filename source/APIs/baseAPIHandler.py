import logging
# import psycopg2
# from user import get_user


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
        pass

    def handle(self, msgid, msgtype, data, client, user=None):
        '''
        Find the right handler and distribute the incoming message to there.
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

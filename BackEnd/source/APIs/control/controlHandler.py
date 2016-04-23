import APIs.control.systemAPI as systemAPI
from APIs.baseAPIHandler import BaseAPIHandler


class ControlAPIHandler(BaseAPIHandler):
    name = 'control'
    message_handlers = {'list_available_clients':
                            systemAPI.handle_list_available_clients
                        }

    def authenticate(self, client, msgid, data, user, msgtype):
        return True

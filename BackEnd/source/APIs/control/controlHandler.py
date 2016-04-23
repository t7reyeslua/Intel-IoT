import APIs.control.systemAPI as systemAPI
from APIs.baseAPIHandler import BaseAPIHandler


class ControlAPIHandler(BaseAPIHandler):
    name = 'control'
    message_handlers = {'list_available_clients':
                            systemAPI.handle_list_available_clients,
                        'list_available_bags':
                            systemAPI.handle_list_available_bags,
                        'report_missing_item':
                            systemAPI.handle_report_missing_item,
                        'set_tracking_place':
                            systemAPI.handle_set_tracking_place,
                        'create_beacon_configuration':
                            systemAPI.handle_create_beacon_configuration
                        }

    def authenticate(self, client, msgid, data, user, msgtype):
        return True

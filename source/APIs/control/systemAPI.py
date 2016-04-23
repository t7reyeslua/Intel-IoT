import logging
import client as client_module

def handle_list_available_clients(client, msgid, msg, user):
    '''
    Send a list of currently available clients in the system. A client is
    considered active if it has one or more active channels associated with it.
    '''
    data = {'clients': []}
    for target in client_module.clients.values():
        if len(target.channels) != 0:
            elem = {'ip': target.ip,
                    'name': target.name,
                    'host': target.host,
                    'id': target.id}

            data['clients'].append(elem)
    return ('control', None, 'available_clients', data, msgid)

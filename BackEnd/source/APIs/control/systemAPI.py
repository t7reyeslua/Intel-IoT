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
                    'trusted_ip': target.from_trusted_ip,
                    'id': target.id}

            data['clients'].append(elem)
    return ('control', None, 'available_clients', data, msgid)

def handle_list_available_bags(client, msgid, msg, user):
    '''
    Send a list of currently available bags in the system. A bag is
    considered active if it has one or more active channels associated with it.
    '''
    data = {'clients': []}
    for target in client_module.clients.values():
        if len(target.channels) != 0 and 'SB' in target.name:
            elem = {'ip': target.ip,
                    'name': target.name,
                    'host': target.host,
                    'trusted_ip': target.from_trusted_ip,
                    'id': target.id}

            data['clients'].append(elem)
    return ('control', None, 'available_clients', data, msgid)

def handle_report_missing_item(client, msgid, message, user):
    receivers = []
    if 'target' in message:
        target = client_module.find_client(message['target'])
        if target is None:
            return ('control', None, 'error',
                    {'msg': 'no such client'}, msgid)
        receivers.append(target)

    data = dict()
    if client is not None:
        data['sender'] = client.ip
    if 'line1' in message:
        data['line1'] = message['line1']
    if 'line2' in message:
        data['line2'] = message['line2']
    if 'is_error' in message:
        data['is_error'] = message['is_error']

    return ('control', receivers, 'print_message', data, None)


def handle_set_tracking_place(client, msgid, message, user):
    receivers = []
    if 'target' in message:
        target = client_module.find_client(message['target'])
        if target is None:
            return ('control', None, 'error',
                    {'msg': 'no such client'}, msgid)
        receivers.append(target)

    data = dict()
    data['tags'] = message['tags']

    return ('control', receivers, 'track_articles', data, None)

def handle_create_beacon_configuration(client, msgid, msg, user):

    return
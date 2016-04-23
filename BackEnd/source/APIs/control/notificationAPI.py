import client as client_module
import copy
import logging
from datetime import datetime, timedelta
from collections import namedtuple
from config_handler import config, prefs


def handle_send_notification(client, msgid, message, user):
    '''
    Handle the reception of a send_notification message from a client.

    :param client: Client
    :param msgid: Message Id
    :param message: Message
    :param user: User
    :return: Reply
    '''
    # Select to whom to send the notification
    receivers = []
    if 'destination' in message:
        destination = client_module.find_client_by_name(message['destination'])
        if destination is None:
            return ('control', None, 'error',
                    {'msg': 'no such client'}, msgid)
        receivers.append(destination)
    else:
        # Broadcast
        all_clients = client_module.find_clients_all()
        if all_clients is None:
            return ('control', None, 'error',
                    {'msg': 'No clients in the system.'},
                    msgid)
        receivers.extend(all_clients)
        logging.info("Current clients: " + str(receivers))

    # Build notification
    data = {'sender_ip': client.ip,
            'msg': message['msg'],
            'sender': client.name}

    if 'target' in message:
        data['target'] = message['target']
    if 'display_time' in message:
        data['display_time'] = message['display_time']
    if 'title' in message:
        data['title'] = message['title']
    if 'source' in message:
        data['source'] = message['source']
    if 'type' in message:
        data['type'] = message['type']
    if 'extras' in message:
        data['extras'] = message['extras']
    if 'user_id' in message:
        data['user_id'] = message['user_id']
    if 'sender_uid' in message:
        data['sender_uid'] = message['sender_uid']
    if 'confirm_is_seen' in message:
        if message['confirm_is_seen'] in ['True', 'true', True]:
            data['confirm_is_seen'] = True

    # Select how to send notification: Now or later
    if not 'delay' in message and not 'scheduled_at' in message:
        # Send right away, but do not send back to original sender
        receivers = [x for x in receivers if x != client]
        client.get_channel('control').send_ack(msgid, handler='control')
        return ('control', receivers, 'notification', data, None)
    else:
        return schedule_notification(client, msgid, message, data, receivers)


scheduled_notifications = {}
ScheduledNotification = namedtuple("ScheduledNotification",
                                   ["data",
                                    "receivers",
                                    "scheduled_at"])


def schedule_notification(client, msgid, message, data, receivers):
    '''
    Schedule a notification to be sent later in time as defined by the value
    of 'delay' or 'scheduled_at'.

    :param client: client sending the notification
    :param msgid: msg id of send_notification request
    :param message: message to be sent
    :param data: data to be sent
    :param receivers: targets of notification
    :return: None or error message
    '''
    scheduled_at = None
    if 'scheduled_at' in message:
        # Validate date string
        try:
            scheduled_at = datetime.strptime(message['scheduled_at'],
                                             '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            return ('control', None, 'error',
                    {'msg': 'Wrong date format. ' +
                            'Expected: %Y-%m-%d %H:%M:%S.%f'},
                    msgid)
    elif 'delay' in message:
        # Translate minute delay into absolute time
        delay = None
        try:
            delay = int(message['delay'])
        except Exception:
            pass
        if not isinstance(delay, int):
            return ('control', None, 'error',
                    {'msg': 'Delay should be an integer'}, msgid)
        # TODO change seconds to minutes before production
        scheduled_at = datetime.utcnow() + timedelta(seconds=delay)

    # Add it to the scheduled notifications
    scheduled_notifications[(client, msgid)] = \
        ScheduledNotification(data=data, receivers=receivers,
                              scheduled_at=scheduled_at)
    return


def send_scheduled_notification(notification):
    '''
    Send a scheduled notification through the targets control channel.

    :param notification: ScheduledNotification instance
    :return: None
    '''
    for target in notification.receivers:
        logging.info(str(datetime.now()) +
                     ' | Sending notification '
                     + ' to ' + str(target.ip)
                     + ' scheduled at ' + str(notification.scheduled_at))
        target.get_channel('control').send('control', 'notification',
                                           notification.data)
    return


def check_scheduled_notifications_to_send(now):
    '''
    Handle scheduled notifications queue.

    :param now: current time
    :return: None
    '''
    notifications_to_send = []

    # Mark notifications to be sent
    for key in scheduled_notifications.keys():
        notification = scheduled_notifications[key]
        if now >= notification.scheduled_at:
            notifications_to_send.append(key)

    # Send notifications
    for key in notifications_to_send:
        send_scheduled_notification(scheduled_notifications[key])
        scheduled_notifications.pop(key, None)
    return


def scheduled_notifications_watchdog(ioloop):
    '''
    Periodical checkup of pending notifications to be sent. These come
    from notifications that were sent with a 'delay' or 'scheduled_at' field.

    :param ioloop:  Tornado ioloop instance
    :return: None
    '''
    #logging.info(str(datetime.now()) + '| Notifications watchdog')

    now = datetime.utcnow()
    check_scheduled_notifications_to_send(now)

    # Schedule next 1 minute from now
    # TODO change value before production
    callback_time = prefs.getint('timeouts', 'watchdog_notifications')
    ioloop.call_at(ioloop.time() + callback_time,
                   scheduled_notifications_watchdog, ioloop)
    return

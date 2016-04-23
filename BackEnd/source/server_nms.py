#!/usr/bin/env python3
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import logging
from logging.handlers import RotatingFileHandler
from APIs.control.notificationAPI import scheduled_notifications_watchdog
import sys
import signal
import os
from config_handler import config
from daemon import Daemon


def setup_logging():
    '''
    Create logging based on settings in server.config. At least log to a
    logfile that has a maximum size.

    :return: None
    '''
    log_location = config.get('locations', 'log')
    if not os.path.exists(log_location):
        os.makedirs(log_location)

    # Determine logging level
    ll = config.get('server', 'logging_level')
    logging_level = logging.DEBUG
    if ll == 'debug':
        logging_level = logging.DEBUG
    elif ll == 'info':
        logging_level = logging.INFO

    # Create logger
    root = logging.getLogger()
    root.setLevel(logging_level)

    # Create logging file handler. Filesize limited, after that the start will
    # be overwritten
    log_formatter = logging.Formatter('%(asctime)s %(message)s',
                                      '%d-%m-%Y %H:%M:%S')

    # Add separate handler for errors
    my_handler_error = RotatingFileHandler(
        log_location + '/error.log', mode='a',
        maxBytes=config.getint('server', 'max_logsize'), backupCount=2,
        encoding=None, delay=0)
    my_handler_error.setLevel(logging.ERROR)
    my_handler_error.setFormatter(log_formatter)
    root.addHandler(my_handler_error)

    my_handler = RotatingFileHandler(
        log_location + '/server.log', mode='a',
        maxBytes=config.getint('server', 'max_logsize'), backupCount=2,
        encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    root.addHandler(my_handler)

    # Create logging to stdout handler
    if config.getboolean('server', 'log_to_stdout'):
        ch = logging.StreamHandler(sys.stdout)
        root.addHandler(ch)


def signal_handler(signal, frame):
    '''
    Handle server shutdown.

    :param signal: signal
    :param frame: frame
    :return: None
    '''
    logging.info("Server shutting down")
    sys.exit(0)


def setup_signal_handling():
    '''
    Setup OS signal handlers for the server.

    :return: None
    '''
    # Close or terminate server
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def setup_database():
    '''
    Do preparation work on the database.

    :return: None
    '''
    pass


def setup_server():
    '''
    Setup the necessary handlers for the server.

    :return: None
    '''
    from APIs.websocketHandler import WebsocketAPIHandler
    from APIs.httpHandler import HttpAPIHandler
    from APIs.socketHandler import TCPServer

    socket_server = TCPServer()
    http_server = tornado.httpserver.HTTPServer(
        tornado.web.Application([
            ('/API-ws/(.*)', WebsocketAPIHandler),
            ('/API-http/(.*)', HttpAPIHandler),
            # Below are features useful during development
            ('/APItestSuite/(.*)', tornado.web.StaticFileHandler,
             {'path': 'test_tools/webinterface',
              'default_filename': 'index.html'}),
            ('/coverage/(.*)', tornado.web.StaticFileHandler,
                {'path': 'htmlcov', 'default_filename': 'index.html'})]))
    return socket_server, http_server


class NMS:
    '''
    Single server instance.
    '''
    def run(self):
        '''
        Run the server.
        :return: None
        '''
        # Run setup
        setup_logging()
        setup_signal_handling()
        setup_database()
        socket_server, http_server = setup_server()

        # Start servers
        # Start Socket server
        logging.info("Launching socket listener")
        socket_server.listen(config.get('server', 'tcpport'),
                             config.get('server', 'listen'))

        # Prepare HTTP server
        ioloop = tornado.ioloop.IOLoop.instance()
        scheduled_notifications_watchdog(ioloop)

        http_server.listen(config.get('server',  'webport'))
        logging.info("Launching Websocket and HTTP POST listeners")
        ioloop.start()


class NMS_Daemon(Daemon):
    '''
    Daemon wrapper around MCS server. Using this allows us to also launch the
    server in non-daemon mode, which is useful during development.
    '''
    def run(self):
        server = NMS()
        server.run()


def main():
    if __file__ != 'source/server_nms.py':
        print("The server needs to be run from the NMS root directory " +
              "(e.g. NMS/). It is\nadvisable to use the nms.sh script " +
              "that is provided there.")
        sys.exit(2)

    if len(sys.argv) == 2:
        daemon = NMS_Daemon('/tmp/nms.pid')
        if 'start' == sys.argv[1]:
            print("Starting server")
            daemon.start()
        elif 'stop' == sys.argv[1]:
            print("Stopping server")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print("Restarting server")
            daemon.restart()
        else:
            print("Unknown command %s" % sys.argv[1])
            print("Usage: %s start|stop|restart" % sys.argv[0])
            sys.exit(2)
        sys.exit(0)
    else:
        server = NMS()
        server.run()


if __name__ == "__main__":
    main()

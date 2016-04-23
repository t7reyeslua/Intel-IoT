#!/usr/bin/env python
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import logging
from logging.handlers import RotatingFileHandler
import sys
import signal
import os
from config_handler import config
from daemon import Daemon
from iot_client import IoTWebSocketClient

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


def setup_server():
    '''
    Setup the necessary handlers for the server.

    :return: None
    '''
    from APIs.websocketHandler import WebsocketAPIHandler

    http_server = tornado.httpserver.HTTPServer(
        tornado.web.Application([
            ('/API-ws/(.*)', WebsocketAPIHandler),
            # ('/API-http/(.*)', HttpAPIHandler),
            # # Below are features useful during development
            # ('/APItestSuite/(.*)', tornado.web.StaticFileHandler,
            #  {'path': 'test_tools/webinterface',
            #   'default_filename': 'index.html'}),
            # ('/coverage/(.*)', tornado.web.StaticFileHandler,
            #     {'path': 'htmlcov', 'default_filename': 'index.html'})
        ]))
    return http_server

def setup_iot_client():
    '''
    Setup the client for the NMS
    '''
    backend_url = 'ws://%s:%s/API-ws/' % (config.get('backend',
                                                 'localhost'),
                                      config.getint('backend',
                                                    'webport'))
    backend_client = IoTWebSocketClient()
    backend_client.connect(url=backend_url)
    return

class SmartBag:
    '''
    Single instance.
    '''
    def run(self):
        '''
        Run the client.
        :return: None
        '''
        # Run setup
        setup_logging()
        setup_signal_handling()

        ioloop = tornado.ioloop.IOLoop.instance()
        setup_iot_client()
        ioloop.start()


class SmartBag_Daemon(Daemon):
    def run(self):
        server = SmartBag()
        server.run()


def main():
    if __file__ != 'source/main.py':
        print("The server needs to be run from the root directory. " +
              "It is\nadvisable to use the iot.sh script " +
              "that is provided there.")
        sys.exit(2)

    if len(sys.argv) == 2:
        daemon = SmartBag_Daemon('/tmp/iot.pid')
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
        server = SmartBag()
        server.run()


if __name__ == "__main__":
    main()

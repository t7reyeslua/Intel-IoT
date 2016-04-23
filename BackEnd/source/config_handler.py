import ConfigParser as configparser

config = configparser.ConfigParser()
config.read('server.config')

prefs = configparser.ConfigParser()
prefs.read('preferences.config')

from configparser import ConfigParser


path = 'config.ini'
parser = ConfigParser()
parser.read(path)


def get_host() -> str:
    return parser.get('server', 'host', fallback='')


def get_port_communication() -> int:
    return parser.getint('server', 'port_communication', fallback=9191)


def get_port_streaming() -> int:
    return parser.getint('server', 'port_streaming', fallback=9090)


def get_db_relative_path() -> str:
    return parser.get('database', 'db_relative_path', fallback='')


def get_songs_relative_path() -> str:
    return parser.get('database', 'songs_relative_path', fallback='')


def get_images_relative_path() -> str:
    return parser.get('database', 'images_relative_path', fallback='')

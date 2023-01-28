from configparser import ConfigParser

path = "config.ini"
parser = ConfigParser()
parser.read(path)


def get_host() -> str:
    return parser.get('server', 'host', fallback='')


def get_port_communication() -> int:
    return parser.getint('server', 'port_communication', fallback=9191)


def get_port_streaming() -> int:
    return parser.getint('server', 'port_streaming', fallback=9090)


def get_client_id() -> str:
    return parser.get('client', 'id', fallback='111111')


def get_history_relative_path() -> str:
    return parser.get('paths', 'history_relative_path', fallback='')


def get_playlists_relative_path() -> str:
    return parser.get('paths', 'playlists_relative_path', fallback='')

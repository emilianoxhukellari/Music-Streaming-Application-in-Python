import socket
import threading
import sqlite3

import configuration
from eventsystem import Listener
from clienthandler import ClientHandler


class Server(Listener):
    """
    Summary:
    This class represents a server that can connect to multiple clients. It uses a main socket to
    connect to clients, and for each client it creates two dedicated sockets for streaming music
    and for communication.

    Usage:
    Create a single Server object and call its run method.
    """

    def __init__(self):
        Listener.__init__(self)

        # ATTRIBUTES
        self._client_streaming_sockets = {}
        self._client_communication_sockets = {}
        self._clients = []
        # ATTRIBUTES

        # SOCKET
        self.HOST = configuration.get_host()
        self.PORT_COMMUNICATION = configuration.get_port_communication()
        self.PORT_STREAMING = configuration.get_port_streaming()
        self._communication_socket = self._create_communication_socket()
        self._streaming_socket = self._create_streaming_socket()
        self._awake_socket(self._communication_socket, self.HOST, self.PORT_COMMUNICATION)
        self._awake_socket(self._streaming_socket, self.HOST, self.PORT_STREAMING)
        # SOCKET

        # DATA
        self._database_path = configuration.get_db_relative_path()
        self._server_db_connection = sqlite3.connect(
            self._database_path, check_same_thread=False
        )
        # DATA

        # THREADS
        self._listener_streaming_thread = threading.Thread(
            target=self._communication_listening_loop, args=()
        )
        self._listener_communication_thread = threading.Thread(
            target=self._streaming_listening_loop, args=()
        )
        self._create_client_handler_thread = threading.Thread(
            target=self._create_client_handler_loop, args=()
        )
        # THREADS

        # THREADING EVENTS
        self._new_client = threading.Event()
        # THREADING EVENTS

        # EVENT LISTENERS
        self.listen("remove_client_handler", self._remove_client_handler)
        # EVENT LISTENERS

    def __del__(self):
        self._streaming_socket.close()
        self._communication_socket.close()

    def _remove_client_handler(self, client_handler: ClientHandler) -> None:
        """
        Call this method by passing a client handler from a client handler object (self). This method
        will remove that client handler from the _clients list.
        """

        for element in self._clients:
            if element is client_handler:
                self._clients.remove(client_handler)

    def _create_client_handler_loop(self) -> None:
        """
        This method should be run in a separate thread. It waits for a new client to be created, and once
        the thread is awakened it creates a client handler passing a streaming socket, a communication
        socket, and a database connection.
        """

        while True:
            self._new_client.wait()
            self._new_client.clear()
            for client_full_id in list(self._client_streaming_sockets):
                if client_full_id in self._client_communication_sockets:
                    self._clients.append(
                        ClientHandler(
                            client_full_id,
                            self._client_streaming_sockets[client_full_id],
                            self._client_communication_sockets[client_full_id],
                            sqlite3.connect(
                                self._database_path, check_same_thread=False
                            ),
                        )
                    )
                    del self._client_streaming_sockets[client_full_id]
                    del self._client_communication_sockets[client_full_id]

    def _streaming_listening_loop(self) -> None:
        """
        This method should be run in a separate thread. It accepts streaming request connections.
        """

        while True:
            client_socket, client_address = self._streaming_socket.accept()
            client_id = client_socket.recv(6).decode("utf-8")
            client_full_id = self._get_client_full_id(client_id, client_address)
            self._client_streaming_sockets[client_full_id] = client_socket
            self._new_client.set()

    def _communication_listening_loop(self) -> None:
        """
        This method should be run in a separate thread. It accepts communication request connections.
        """

        while True:
            client_socket, client_address = self._communication_socket.accept()
            client_id = client_socket.recv(6).decode("utf-8")
            client_full_id = self._get_client_full_id(client_id, client_address)
            self._client_communication_sockets[client_full_id] = client_socket
            self._new_client.set()

    def run(self) -> None:
        """
        Call this method to run the server.
        """

        self._listener_streaming_thread.start()
        self._listener_communication_thread.start()
        self._create_client_handler_thread.start()

    @staticmethod
    def _get_client_full_id(client_id: str, address: tuple[str, str]) -> str:
        """
        Call this method to get the full id of the client. It includes
        the client ID and client IP.
        """
        ip_address = address[0]
        full_address = client_id + "@" + ip_address
        return full_address

    @staticmethod
    def _create_communication_socket() -> socket:
        """
        This method creates an AF_INET SOCKET_STREAM socket and returns it.
        """

        communication_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return communication_socket

    @staticmethod
    def _create_streaming_socket() -> socket:
        """
        This method creates an AF_INET SOCKET_STREAM socket and returns it.
        """

        streaming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return streaming_socket

    @staticmethod
    def _awake_socket(server_socket: socket, host: str, port: int) -> None:
        """
        Call this method to bind an existing socket to the host and port.
        """

        server_socket.bind((host, port))
        server_socket.listen()

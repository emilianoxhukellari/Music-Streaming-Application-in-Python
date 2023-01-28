import wave
import pickle
import threading
from socket import socket
from sqlite3 import Connection
from typing import Optional, List

import configuration
from math import ceil
from eventsystem import Event
from song import Song


class ClientHandler:
    """
    Summary:
    This class represents a handler for a single client. It contains the necessary logic and
    attributes to communicate with a client.

    Usage:
    Create a handler by passing client full id, a dedicated streaming socket, a dedicated communicated socket,
    and a dedicated db_connection. The handler will self-run.
    """

    def __init__(
        self,
        client_full_id: str,
        streaming_socket: socket,
        communication_socket: socket,
        db_connection: Connection,
    ):

        # ATTRIBUTES
        self.client_full_id = client_full_id
        self._communication_socket = communication_socket
        self._streaming_socket = streaming_socket
        self._chunk = 1024
        self._streaming_loop_ended = False
        self._communication_loop_ended = False
        # ATTRIBUTES

        # DATABASE
        self._db_connection = db_connection
        self._cursor = self._db_connection.cursor()
        self._songs_path = configuration.get_songs_relative_path()
        self._images_path = configuration.get_images_relative_path()
        # DATABASE

        # THREADING EVENTS
        self._communication_flag = threading.Event()
        self._streaming_flag = threading.Event()
        # THREADING EVENTS

        # Threading Events
        self._stop_send = False

        # THREADS
        self._streaming_thread = threading.Thread(
            target=self._streaming_loop, args=(), daemon=True
        )
        self._communication_thread = threading.Thread(
            target=self._communication_loop, args=(), daemon=True
        )
        # THREADS

        print(f"[{self.client_full_id}] CONNECTED")
        self.run()

    def __del__(self):
        print(f"[{self.client_full_id}] TERMINATED")

    def _terminate_song_data_send(self) -> None:
        self._stop_send = True

    def _communication_loop(self) -> None:
        """
        This method must be run in a separate thread. It waits for a request from a client, and it
        executes it.
        """

        try:
            while True:
                length_bytes = self.communication_tcp_recv(4)
                length_int = int.from_bytes(length_bytes, "little")
                request = self.communication_tcp_recv(length_int)
                request = request.decode("utf-8")
                self._execute_request(request)
        except ConnectionResetError:
            self._communication_loop_ended = True
            self._terminate_self()

    def _execute_request(self, request: str) -> None:
        """
        Call this method to execute a request.
        """

        translate = request.split("@")

        if translate[0] == "TERMINATE_SONG_DATA_RECV":
            self._terminate_song_data_send()

        elif translate[0] == "SEARCH":
            self._search_for_song(translate[1])

    def _search_for_song(self, search_string: str) -> None:
        """
        This method handles a search song request. Pass a song to this method, and it will
        send all necessary information to the client.
        This method will send the number of songs, and each individual found song.
        """

        if search_string != "":
            command = f"""SELECT song_id, song_name, artist_name, song_name_serialized, artist_name_serialized,
            duration, image_file_name FROM songs WHERE song_name_serialized LIKE '%{search_string}%' OR 
            artist_name_serialized LIKE '%{search_string}%' """

            self._cursor.execute(command)
            results = self._cursor.fetchall()
            number_of_songs_found = len(results)
            number_of_songs_found_bytes = number_of_songs_found.to_bytes(4, "little")
            self.communication_tcp_send(number_of_songs_found_bytes, 4)

            for row in results:
                image_file_location = self._images_path + row[6]
                image_bytes = open(
                    image_file_location, "rb"
                ).read()  # Change this so it handles exceptions with 'with'
                current_song = Song(row[0], row[1], row[2], row[5], image_bytes)
                serialized_song = pickle.dumps(current_song)
                data, data_length = self.slice_song_bytes(serialized_song)
                data_length_bytes = data_length.to_bytes(4, "little")
                self.communication_tcp_send(data_length_bytes, 4)
                for i in range(data_length - 1):
                    self.communication_tcp_send(data[i], 1024)
                last_packet_length = len(data[-1])
                last_packet_length_bytes = last_packet_length.to_bytes(4, "little")
                self.communication_tcp_send(last_packet_length_bytes, 4)
                self.communication_tcp_send(data[-1], last_packet_length)

    def _streaming_loop(self) -> None:
        """
        This method must be run in a separate thread. It waits for a song_id from the client,
        and it calls _send_song_data() to send the requested song.
        """

        try:
            while True:
                song_id_bytes = self.streaming_tcp_recv(4)
                song_id = int.from_bytes(song_id_bytes, "little")
                self._send_song_data(song_id)
        except ConnectionResetError:
            self._streaming_loop_ended = True
            self._terminate_self()

    def _terminate_self(self) -> None:
        """
        Call this method to remove this client handler.
        """

        if self._communication_loop_ended and self._streaming_loop_ended:
            del self._communication_thread
            del self._streaming_thread
            Event("remove_client_handler", self, self_fire=True)

    def _get_song_and_length(self, song_id: int) -> Optional[tuple[any, int]]:
        """
        Call this method to get a song (bytes) and its length (int).
        """

        command = f"""SELECT song_file_name 
                      FROM songs
                      WHERE song_id = {song_id}"""

        self._cursor.execute(command)
        results = self._cursor.fetchone()

        if results:
            song_file_name = results[0]
            song_file_location = self._songs_path + song_file_name
            song_bytes = wave.open(song_file_location)
            song_data_length = int(song_bytes.getnframes() / self._chunk)
            return song_bytes, song_data_length
        return None

    def _send_song_data(self, song_id: int) -> None:
        """
        Call this method to send song data to a client. This client can send a terminate-stream flag
        to the client, and the sending of song data will be canceled.
        """

        song_and_length = self._get_song_and_length(song_id)

        if song_and_length:
            song_bytes = song_and_length[0]
            song_data_length = song_and_length[1]
            song_data_length_bytes = song_data_length.to_bytes(4, "little")
            self.streaming_tcp_send(song_data_length_bytes, 4)

            type_data = "data".encode("utf-8")
            type_exit = "exit".encode("utf-8")

            current_packet = song_bytes.readframes(self._chunk)
            # Do not send an incomplete packet
            while len(current_packet) == self._chunk * 4:
                if self._stop_send:
                    self._stop_send = False
                    self.streaming_tcp_send(type_exit, 4)
                    break

                self.streaming_tcp_send(type_data, 4)
                self.streaming_tcp_send(current_packet, 4096)
                current_packet = song_bytes.readframes(self._chunk)
        else:
            song_data_length = 0
            song_data_length_bytes = song_data_length.to_bytes(4, "little")
            self.streaming_tcp_send(song_data_length_bytes, 4)

    def streaming_tcp_send(self, data: bytes, buf_size: int) -> None:
        """
        This method sends the specified data (bytes) of length bufsize(int) using socket.send().
        If not all data was successfully sent, the method will try again to send the remaining data.
        """

        total_sent = 0
        while total_sent < buf_size:
            sent = self._streaming_socket.send(data[total_sent:])
            if sent == 0:
                raise ConnectionResetError("socket connection broken")
            total_sent = total_sent + sent

    def streaming_tcp_recv(self, buf_size: int) -> bytes:
        """
        This method received data (bytes) of size bufsize (int) from the client. If not all data was received,
        the method will try again to receive the remaining data.
        """

        chunks = []
        bytes_received = 0
        while bytes_received < buf_size:
            chunk = self._streaming_socket.recv(buf_size - bytes_received)
            if chunk == b"":
                raise ConnectionResetError("socket connection broken")
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)
        return b"".join(chunks)

    def communication_tcp_send(self, data: bytes, buf_size: int) -> None:
        """
        This method sends the specified data (bytes) of length bufsize(int) using socket.send().
        If not all data was successfully sent, the method will try again to send the remaining data.
        """

        total_sent = 0
        while total_sent < buf_size:
            sent = self._communication_socket.send(data[total_sent:])
            if sent == 0:
                raise ConnectionResetError("socket connection broken")
            total_sent = total_sent + sent

    def communication_tcp_recv(self, buf_size: int) -> bytes:
        """
        This method received data (bytes) of size bufsize (int) from the client. If not all data was received,
        the method will try again to receive the remaining data.
        """

        chunks = []
        bytes_received = 0
        while bytes_received < buf_size:
            chunk = self._communication_socket.recv(buf_size - bytes_received)
            if chunk == b"":
                raise ConnectionResetError("socket connection broken")
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)
        return b"".join(chunks)

    def run(self):
        self._communication_flag.clear()
        self._streaming_flag.clear()
        self._streaming_thread.start()
        self._communication_thread.start()

        # Wait for threads
        # Close streams
        # notify server to remove you

    @staticmethod
    def slice_song_bytes(serialized_song: bytes) -> tuple[List[bytes], int]:
        """
        Call this method to slice a serialized_song into chunks of size _chunk.
        This method returns a list of chunks and the length of the list.
        """

        chunk = 1024
        serialized_song_length = len(serialized_song)
        data_length = ceil(serialized_song_length / chunk)
        data = [serialized_song[i: i + chunk] for i in range(0, serialized_song_length, chunk)]
        return data, data_length

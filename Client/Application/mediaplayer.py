import socket
import threading
import random
import configuration
from typing import List
from song import Song
from player import Player


class MediaPlayer:
    """
    Summary:
    This class represents a media player which uses a player to play songs.
    It has a custom queue which contains the songs and the ordered indexes for shuffling and unshuffling.

    Usage:
    Create a Mediaplayer object and call its run() method. Once you run the mediaplayer, you can call its
    methods such as play_this(song), next_song(), previous_song(), add_to_queue(), etc.
    """

    def __init__(
        self,
        send_progress_info_callback,
        terminate_song_data_recv_request_callback,
        send_current_song_update_callback,
        display_queue_callback,
        update_repeat_state_callback,
    ):

        # CONFIGURATION
        self._host = configuration.get_host()
        self._port_streaming = configuration.get_port_streaming()
        self._client_id = configuration.get_client_id().encode("utf-8")
        # CONFIGURATION

        # ATTRIBUTES
        self._player = Player(progress_callback=self._send_progress)
        self._queue = SongQueue()  # Stores Song objects
        self._create_stream_client()
        self._current_song_index = 0
        self._repeat_state = 0
        self._shuffle_state = 0
        self._connected = None
        # ATTRIBUTES

        # THREADING EVENTS
        self._start_read_flag = threading.Event()
        self._currently_reading = threading.Event()
        self._next_index = threading.Event()
        self._player.on_stream_end(self._next_index)  # Set by the player
        self._currently_streaming = threading.Event()
        self._player.on_stream_terminate(self._currently_streaming)  # Set by the player
        self._reconnect = threading.Event()
        # THREADING EVENTS

        # THREADS
        self.song_thread = threading.Thread(target=self._player.stream_loop, args=())
        self.read_thread = threading.Thread(
            target=self._read_from_server, args=(), daemon=True
        )
        self.auto_next_thread = threading.Thread(
            target=self._auto_next_song, args=(), daemon=True
        )
        self.connection_thread = threading.Thread(
            target=self._connect_to_server, args=(), daemon=True
        )
        # THREADS

        # CALLBACKS
        self.send_progress_info = send_progress_info_callback
        self.terminate_song_data_recv_request = terminate_song_data_recv_request_callback
        self.send_current_song_update = send_current_song_update_callback
        self.send_queue_info = display_queue_callback
        self.update_repeat_state = update_repeat_state_callback
        # CALLBACKS

    def set_shuffle_state(self, state: int) -> None:
        """
        This method takes 0 (unshuffle) or 1 (shuffle).
        Based on the parameter state, it will change the internal shuffle state,
        shuffle/ unshuffle the queue and display the queue.
        """

        if state == 1:
            self._shuffle_state = 1
            self._queue.shuffle(self._current_song_index)
            self.display_queue()
        elif state == 0:
            self._shuffle_state = 0
            self._queue.unshuffle(self._current_song_index)
            self.display_queue()

    def set_repeat_state(self, state: int) -> None:
        """
        This method sets the repeat state 0 (repeat_off), 1 (repeat_on), 2 (repeat_one).
        """

        self._repeat_state = state

    @staticmethod
    def _seconds_to_string(seconds: int) -> str:
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes:0>2d}:{seconds:0>2d}"

    def _send_progress(self, progress: int) -> None:  # Send progress and minutes
        """
        This is a callback method. It is usually called by the player, and it sends progress
        info: time_passed (string). Progress must be between 0 - 1000.
        """

        duration_sec = self._queue[self._current_song_index].duration
        current_time_sec = duration_sec * (progress / 1000)
        time_passed_string = MediaPlayer._seconds_to_string(current_time_sec)
        self.send_progress_info(progress, time_passed_string)

    def set_progress(self, value: int) -> None:
        """
        This method sets the song progress based on the input from the progress bar.
        Value must be between 0 - 1000.
        """

        self._player.set_progress(value)

    def run(self) -> None:
        """
        Call this method to run the mediaplayer.
        """

        # Events
        self._currently_streaming.set()
        self._currently_reading.set()
        self._start_read_flag.clear()
        self._next_index.clear()
        self._reconnect.set()
        # Threads
        self.auto_next_thread.start()
        self.song_thread.start()
        self.read_thread.start()
        self.connection_thread.start()

    def exit(self) -> None:
        """
        Call this method to exit mediaplayer.
        """

        self._player.exit_stream_loop()
        self._player.terminate_stream()
        self._currently_streaming.wait()
        self._stream_client.close()

    def _create_stream_client(self) -> None:
        self._stream_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _connect_to_server(self) -> None:
        while True:
            self._reconnect.wait()
            self._reconnect.clear()
            self._create_stream_client()
            while True:
                try:
                    self._connected = False
                    self._stream_client.connect((self._host, self._port_streaming))
                    self.streaming_tcp_send(self._client_id, 6)
                    self._connected = True
                    print("[STREAMING CONNECTED]")
                    break
                except ConnectionRefusedError:
                    print("[WAITING FOR SERVER] - [STREAM]")
                except OSError:
                    break

    def _auto_next_song(self) -> None:
        while True:
            self._next_index.wait()
            if self._repeat_state == 2:  # On Repeat
                self.next_song(repeat_one=True)
            else:
                self.next_song(repeat_one=False)
            self._next_index.clear()

    def _current_song_update(self) -> None:
        song_name = self._queue[self._current_song_index].song_name
        artist_name = self._queue[self._current_song_index].artist_name
        duration_string = self._queue[self._current_song_index].duration_string
        image_binary = self._queue[self._current_song_index].image_binary
        song = self._queue[self._current_song_index]
        self.send_current_song_update(song_name, artist_name, duration_string, image_binary, song)

    def display_queue(self, self_display=False) -> None:
        """
        Call this method to display current queue to window. self_display=True must be used when display_queue
        is called from an automated function - fixes race condition problems.
        """

        results = []  # Store songs to be displayed
        if (
            not self._currently_streaming.is_set() or self_display
        ):  # If streaming or calling from 'start_song'
            start = self._current_song_index + 1
        else:
            start = self._current_song_index
        for song_index in range(start, len(self._queue)):
            results.append((self._queue[song_index], song_index))
        self.send_queue_info(results)  # Send the results to window

    def remove_from_queue(self, song_index: int) -> None:
        """
        Removes a song from queue at specified index.
        """

        try:
            self._queue.pop_from_queue(song_index)
        except IndexError:
            print(f"Index Error while trying to remove song at index {song_index} from queue.")
        self.display_queue()

    def play_playlist_songs(self, playlist_songs: List[Song]) -> None:
        """
        This method- Takes a list of songs; Clears the current queue; Adds the list of playlist songs to queue;
        Shuffles/ Unshuffles/ the queue based on the shuffle state; Plays the first song in queue.
        """

        self._terminate_read()
        self._currently_reading.wait()
        self._player.terminate_stream()
        self._currently_streaming.wait()
        self._queue.clear_queue()
        self._current_song_index = 0
        for song in playlist_songs:
            self._queue.append_to_queue(song)
        if self._shuffle_state == 1:
            self._queue.shuffle(self._current_song_index)
        if self._repeat_state == 2:
            self.update_repeat_state(1)
        self.start_song()

    def delete_queue(self) -> None:
        """
        Call this method to delete the entire queue except the song that is currently playing.
        """

        if not self._currently_streaming.is_set() and self._queue:  # Streaming
            current_song = self._queue[self._current_song_index]
            self._queue.clear_queue()
            self._queue.append_to_queue(current_song)
            self._current_song_index = 0

        elif self._currently_streaming.is_set() and self._queue:  # Not streaming
            self._queue.clear_queue()

        self.display_queue()

    def add_playlist_songs_to_queue(self, playlist_songs: List[Song]) -> None:
        """
        Adds a list of songs to the queue.
        """

        for song in playlist_songs:
            self._queue.append_to_queue(song)
        self.display_queue()

    def move_up(self, song_index: int) -> None:
        """
        Moves a song at specified index up in queue and displays the new queue.
        """

        if not self._currently_streaming.is_set():  # If streaming
            start = self._current_song_index + 1
        else:
            start = self._current_song_index

        if song_index > start:
            self._queue[song_index], self._queue[song_index - 1] = (
                self._queue[song_index - 1],
                self._queue[song_index],
            )
            self.display_queue()

    def move_down(self, song_index: int) -> None:
        """
        Moves a song at specified index down in queue and displays the new queue.
        """

        if song_index < len(self._queue) - 1:
            self._queue[song_index], self._queue[song_index + 1] = (
                self._queue[song_index + 1],
                self._queue[song_index],
            )
            self.display_queue()

    def start_song(self) -> None:
        """
        This is the main method of MediaPlayer class. Call this method to play the song at current index.
        The method will start a music stream and reading stream. At the end it will display the new queue.
        """

        if self._queue and self._connected:
            # Everytime you start a new song, update some variables AND SEND TO APPLICATION
            self._terminate_read()  # Request read termination
            self._currently_reading.wait()  # Wait for any current reading to end
            self._player.terminate_stream()  # Request stream termination
            self._currently_streaming.wait()  # Wait for the stream to fully terminate
            try:  # If streaming is disconnected -> Reconnect
                request_song_id = self._queue[self._current_song_index].song_id
                request_song_id_bytes = request_song_id.to_bytes(4, "little")
                self.streaming_tcp_send(request_song_id_bytes, 4)
                self._start_read()  # Start reading from server
                self._player.start_stream()  # Start streaming song
                self._current_song_update()  # Update the current song in window
                self.display_queue(self_display=True)  # New queue
            except ConnectionResetError:
                self._reconnect.set()  # Try to reconnect to server

    def play_this(self, song: Song) -> None:
        """
        This method will play the song passed as parameter.
        """

        if self._repeat_state == 2:  # If repeat_one, reset state to repeat_on
            self.update_repeat_state(1)

        if not self._currently_streaming.is_set():  # Streaming
            self._queue.insert_to_queue(self._current_song_index + 1, song)
            self._current_song_index += 1
        else:
            self._queue.insert_to_queue(self._current_song_index, song)

        self.start_song()

    def add_to_queue(self, song: Song) -> None:
        """
        Adds the passed song to queue.
        """

        self._queue.append_to_queue(song)
        self.display_queue()

    def next_song(self, repeat_one=False) -> None:
        """
        Call this method to play next song from queue.
        """

        if self._queue:
            if self._repeat_state == 2 and not repeat_one:  # Update button state, user clicked next
                self.update_repeat_state(1)

            if repeat_one:  # Play the song at current index again
                self.start_song()

            elif self._repeat_state == 0:  # If repeat state is repeat_off and at the end of queue, play the last song
                if self._current_song_index != len(self._queue) - 1:
                    self._current_song_index += 1
                self.start_song()

            elif self._repeat_state == 1:  # If repeat state is repeat_on, play the queue again, starting at index 0
                if self._current_song_index == len(self._queue) - 1:
                    self._current_song_index = 0
                else:
                    self._current_song_index += 1
                self.start_song()

    def previous_song(self) -> None:
        """
        Call this method to play next song from queue.
        """

        if self._repeat_state == 2:  # Update button state from repeat_one to repeat_on, user clicked next
            self.update_repeat_state(1)

        if self._queue and self._current_song_index != 0:  # If index is 0, do not change it
            self._current_song_index -= 1
        self.start_song()

    def play(self) -> None:
        """
        Call this method to play the current song if paused.
        """

        self._player.play()

    def pause(self) -> None:
        """
        Call this method to pause the current song if playing.
        """

        self._player.pause()

    def get_play_state(self) -> bool:
        """
        Returns play/pause state. True for play, False for pause.
        """

        return self._player.get_play_state()

    def change_play_state(self) -> bool:
        """
        Call this method to change the play/pause state. It will return the state after the change.
        True for play, False for pause.
        """

        return self._player.change_play_state()

    def _start_read(self) -> None:
        self._start_read_flag.set()
        self._currently_reading.clear()

    def _terminate_read(self) -> None:
        if not self._currently_reading.is_set():  # If not is_set -> already terminated
            self.terminate_song_data_recv_request()

    def _read_from_server(self) -> None:
        while True:
            self._start_read_flag.wait()
            self._currently_reading.clear()
            self._start_read_flag.clear()
            type_data = "data".encode("utf-8")
            type_exit = "exit".encode("utf-8")

            try:
                song_data_length_bytes = self.streaming_tcp_recv(4)
                song_data_length = int.from_bytes(song_data_length_bytes, "little")
                self._player.set_song_data_length(song_data_length)
                for i in range(song_data_length):
                    current_type = self.streaming_tcp_recv(4)
                    if current_type == type_data:
                        current_packet = self.streaming_tcp_recv(4096)
                        self._player.receive_packet(current_packet)
                    elif current_type == type_exit:
                        break

            except ConnectionResetError:
                self._reconnect.set()
            finally:
                self._player.receive_packet("END_OF_FILE".encode("utf-8"))
                self._currently_reading.set()

    def streaming_tcp_send(self, data: bytes, bufsize: int) -> None:
        """
        This method sends the specified data (bytes) of length bufsize(int) using socket.send().
        If not all data was successfully sent, the method will try again to send the remaining data.
        """

        total_sent = 0
        while total_sent < bufsize:
            sent = self._stream_client.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent

    def streaming_tcp_recv(self, bufsize: int) -> bytes:
        """
        This method received data (bytes) of size bufsize (int) from the server. If not all data was received,
        the method will try again to receive the remaining data.
        """

        chunks = []
        bytes_received = 0
        while bytes_received < bufsize:
            chunk = self._stream_client.recv(bufsize - bytes_received)
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)
        return b"".join(chunks)


class SongQueue:
    def __init__(self):
        """
        Summary:
        This Class is a List-like class which internally has two lists which store song objects.
        The first list is the queue, which is used by the media player to play songs.
        The second list is the ordered queue. Regardless of how the program shuffles songs, the second list
        will keep track of the order.

        Usage:
        Create an object and use it like a list.
        Call shuffle() to shuffle the queue.
        Call unshuffle() to unshuffle() the queue.
        """

        self._queue = []  # Store songs
        self._ordered_queue = []  # Store ordered song_ids

    def __getitem__(self, key: int):
        return self._queue[key]

    def __setitem__(self, key: int, new_value) -> None:
        self._queue[key] = new_value

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)

    def __contains__(self, item):
        return item in self._queue

    def clear_queue(self) -> None:
        """
        Clears the current song queue, and the ordered queue.
        """

        self._queue.clear()
        self._ordered_queue.clear()

    def insert_to_queue(self, index: int, song: Song) -> None:
        """
        Insert a song to the specified index in the queue and ordered queue.
        """

        self._queue.insert(index, song)
        self._ordered_queue.insert(index, song)

    def pop_from_queue(self, index=-1) -> None:
        """
        This method acts similar to list.pop(). Additionally, it pops an element from the ordered queue.
        """

        self._ordered_queue.remove(self._queue[index].song_id)  # Remove song_id
        self._queue.pop(index)  # Remove song

    def append_to_queue(self, song: Song) -> None:
        """
        Append a song object to queue and ordered queue.
        """

        self._queue.append(song)
        self._ordered_queue.append(song.song_id)

    def shuffle(self, current_song_index: int) -> None:
        """
        Call this method to shuffle the queue. The current song element is not changed.
        """

        if self._queue:
            # Generate a random number excluding current song index.
            r = list(range(0, current_song_index)) + list(range(current_song_index + 1, len(self)))
            for i in range(len(self)):
                if i != current_song_index:
                    random_number = random.choice(r)
                    # Shuffle queue
                    self._queue[i], self._queue[random_number] = self._queue[random_number], self._queue[i]

    def unshuffle(self, current_song_index: int) -> None:
        """
        Call this method to unshuffle the queue. Information from ordered queue is used to do this operation.
        Current song and the respective ordered index of the current songs are exceptions.
        Thus, two songs might not be changed.
        """

        if self._queue:
            for i in range(0, len(self)):
                ordered_index = next(
                    index
                    for index, value in enumerate(self._queue)
                    if value.song_id == self._ordered_queue[i]
                )
                if i != current_song_index and ordered_index != current_song_index:
                    # Unshuffle queue
                    self._queue[i], self._queue[ordered_index] = self._queue[ordered_index], self._queue[i],

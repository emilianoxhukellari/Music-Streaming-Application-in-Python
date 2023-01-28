import pyaudio
import threading
import time


class Player:
    """
    Summary:
    Class Player represents a player that can transform binary wav data into music.
    It uses pyaudio to establish the connection to hardware speakers.

    Usage:
    To use this class you must create an object and call its stream_loop() method in a separate thread.
    Use receive_packet(packet) to feed data into the internal buffer. Data must be binary wav.
    """

    def __init__(self, progress_callback=lambda progress: None):
        # ATTRIBUTES
        self._pa = pyaudio.PyAudio()
        self._stream = self._create_stream()
        self._song_data = []
        self._song_data_length = 0
        self._current_index = 0
        self._last_index = 0
        self._stop = False
        self._stream_has_started = False
        self._stream_loop_continue = True
        self._end_of_stream_event = None
        self._terminate_stream_event = None
        self._STOP_CONDITION = "END_OF_FILE".encode("utf-8")
        # ATTRIBUTES

        # THREADING EVENTS
        self._play_pause = threading.Event()
        self._start_stream_flag = threading.Event()
        self._start_stream_flag.clear()
        # THREADING EVENTS

        # CALLBACKS
        self.send_progress = progress_callback
        # CALLBACKS

    def __del__(self) -> None:
        self._stream.close()
        self._pa.terminate()

    def _create_stream(self) -> pyaudio.Stream:
        """
        This method creates a stream using pyaudio.open(). It has 2 channels, rate of 48000,
        output is True.
        """

        _stream = self._pa.open(
            format=self._pa.get_format_from_width(2),
            channels=2,
            rate=48000,
            output=True,
        )
        return _stream

    def exit_stream_loop(self) -> None:
        """
        Calling this method causes the stream_loop() to exit.
        """

        self._stream_loop_continue = False
        self._start_stream_flag.set()

    def set_song_data_length(self, length: int) -> None:
        """
        This method takes length and assigns it to the song buffer.
        """

        self._song_data_length = length
        self._last_index = self._song_data_length - 1

    def pause(self) -> None:
        """
        Call this method to pause the music.
        """

        self._play_pause.clear()

    def play(self) -> None:
        """
        Call this method to unpause the music.
        """

        self._play_pause.set()

    def get_play_state(self) -> bool:
        """
        This method will return the play/ pause state. True for play and False for pause.
        """

        return self._play_pause.is_set()

    def change_play_state(self) -> bool:
        """
        Call this method to change the state play-pause.
        If the player is playing, change state to pause.
        If the player is paused, change state to play.
        Returns the state after the change. True for play and False for pause.
        """

        if self._play_pause.is_set():
            self._play_pause.clear()
        else:
            self._play_pause.set()
        return self._play_pause.is_set()

    def set_progress(self, value: int) -> None:
        """
        Takes value between 0 - 1000 and sets the progress of the song. 0 for beginning, 500 for the middle,
        1000 for the end.
        """

        if value < 0:
            value = 0
        elif value > 1000:
            value = 1000

        index_from_percent = round(((value / 1000) * (self._song_data_length - 1)))
        if index_from_percent < 0:
            index_from_percent = 0
        self._current_index = index_from_percent

    def receive_packet(self, packet: bytes) -> None:
        """
        Call this method to feed the player's buffer with data. Packet must be binary wav.
        """

        self._song_data.append(packet)

    def _set_start_conditions(self) -> None:
        self._stream_has_started = True
        self._stop = False
        self._play_pause.set()
        self._current_index = 0

    def _set_end_conditions(self) -> None:
        self._song_data.clear()
        self._stream_has_started = False
        self._current_index = 0
        self._terminate_stream_event.set()

    def on_stream_end(self, e: threading.Event) -> None:
        """
        Set the reference of a threading Event to be used when the stream_loop() ends.
        """

        self._end_of_stream_event = e

    def on_stream_terminate(self, e: threading.Event) -> None:
        """
        Set the reference of a threading.Event() to be used when stream_loop() terminates.
        """

        self._terminate_stream_event = e

    def start_stream(self) -> None:
        """
        Call this method to start a stream which will play a single song.
        You must start feeding data to the player buffer shortly before/ after this method is called.
        """

        self._terminate_stream_event.clear()
        self._start_stream_flag.set()
        self._play_pause.set()

    def terminate_stream(self) -> None:
        """
        Call this method to terminate a stream which is playing a single song.
        The current stream is not guaranteed to be terminated immediately.
        Use on_stream_terminate() to create a threading.Event() to check if the current stream has terminated.
        """

        self._stop = True
        self._play_pause.set()  # Let start_stream end execution; solve Pause -> Terminate problem

    def stream_loop(self) -> None:
        """
        This method should be run in a separate thread. It is recommended that the thread is non-daemon
        and that you use exit_stream_loop() to exit the loop.
        Use start_stream() to start a stream.
        Use terminate_stream() to terminate a stream.
        Use receive_packet() to feed data to the buffer.
        If the data is not feed until the stream has reached the last packet, the stream will wait for 0.01 sec
        until it tries to read data again.
        Changing hardware output in your computer will create a new pyaudio stream.
        """

        while self._stream_loop_continue:
            self._start_stream_flag.wait()
            self._start_stream_flag.clear()
            self._set_start_conditions()
            end = False
            _previous_progress = -1
            if not self._stream_loop_continue:
                break
            while True:
                try:
                    while (
                        not self._stop
                        and self._song_data[self._current_index] != self._STOP_CONDITION
                    ):
                        # Play music
                        self._stream.write(self._song_data[self._current_index])
                        # Calculate progress
                        progress_from_index = round(((self._current_index * 1000) / self._last_index))
                        if progress_from_index != _previous_progress:
                            self.send_progress(progress_from_index)
                            _previous_progress = progress_from_index
                        # Play-Pause
                        self._play_pause.wait()
                        self._current_index += 1
                        if self._song_data[self._current_index] == self._STOP_CONDITION:
                            self._end_of_stream_event.set()
                    end = True
                except IndexError:  # receive_packet() is not receiving data enough quickly. Wait.
                    time.sleep(0.01)
                except OSError:  # Different Audio Hardware
                    self._stream = self._create_stream()
                finally:
                    if end:
                        self._set_end_conditions()
                        break

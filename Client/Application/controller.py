import socket
import threading
import pickle
import os
import base64
import csv
import re
from typing import List, Dict

import configuration
from mediaplayer import MediaPlayer
from window import Window
from eventsystem import Listener
from song import Song


class Controller(Listener):
    """
    Summary:
    This class represents a controller which controls the application. It contains a mediaplayer and window.
    It also contains the communication methods to communicate with the server.

    Usage:
    Create a Controller object and call its run() method. Call exit() to end the execution.
    """

    def __init__(self, window=True):
        Listener.__init__(self)
        csv.field_size_limit(2000000000)  # Increase csv size limit to store images

        # CONFIGURATION
        self._host = configuration.get_host()
        self._port_communication = configuration.get_port_communication()
        self._playlists_relative_path = configuration.get_playlists_relative_path()
        self._history_relative_path = configuration.get_history_relative_path()
        self._client_id = configuration.get_client_id().encode("utf-8")
        # CONFIGURATION

        # ATTRIBUTES
        self._song_queue = []
        self._network_request_queue = []
        self._internal_request_queue = []
        self._internal_search_results = []
        self._create_controller_client()
        if window:
            self._window = Window()
        else:
            self._window = None
        self.current_playlist = None
        self._slider_busy = False
        self._mediaplayer = MediaPlayer(
            send_progress_info_callback=self._get_progress,
            terminate_song_data_recv_request_callback=self._terminate_song_data_recv_request,
            send_current_song_update_callback=self._current_song_update,
            display_queue_callback=self.display_queue,
            update_repeat_state_callback=self.update_repeat_state,
        )
        # ATTRIBUTES

        # EVENT LISTENERS
        self.listen("exit", self.exit)
        self.listen("play_pause", self._set_play_pause)
        self.listen("set_progress", self._set_progress)
        self.listen("slider_pressed", self._set_slider_busy)
        self.listen("slider_released", self._set_slider_free)
        self.listen("send_progress_info", self._get_progress)
        self.listen("add_to_queue", self._add_to_queue)
        self.listen("move_up", self._mediaplayer.move_up)
        self.listen("move_down", self._mediaplayer.move_down)
        self.listen("remove_from_queue", self._mediaplayer.remove_from_queue)
        self.listen("update_playlist", self._update_playlist)
        self.listen("add_to_playlist", self._add_to_playlist)
        self.listen("remove_from_playlist", self._remove_from_playlist)
        self.listen("create_new_playlist", self._create_new_playlist)
        self.listen("delete_queue", self._delete_queue)
        self.listen("add_playlist_to_queue", self._add_playlist_to_queue)
        self.listen("delete_current_playlist", self._delete_current_playlist)
        self.listen("rename_current_playlist", self._rename_current_playlist)
        self.listen("current_playlist_search", self._search_playlist)
        self.listen("repeat_state", self._set_repeat_state)
        self.listen("shuffle_state", self._set_shuffle_state)
        self.listen("network_request", self._add_network_request)
        self.listen("internal_request", self._add_internal_request)
        # EVENT LISTENERS

        # THREADING EVENTS
        self._reconnect = threading.Event()
        self._new_network_request_flag = threading.Event()
        self._new_internal_request_flag = threading.Event()
        self._internal_search = threading.Event()
        self._activity_file_flag = threading.Event()
        # THREADING EVENTS

        # THREADS
        self.connection_thread = threading.Thread(
            target=self._connect_to_server, args=(), daemon=True
        )
        self.communication_thread = threading.Thread(
            target=self._communication_loop, args=(), daemon=True
        )
        self.internal_request_thread = threading.Thread(
            target=self._internal_request_loop, args=(), daemon=True
        )
        # THREADS

    def __del__(self):
        self._controller_client.close()

    def _set_internal_search_results(self, results: List[Song]) -> None:
        """
        Call this method to update the internal search results attribute with new results.
        """

        self._internal_search_results.clear()
        self._internal_search_results.extend(results)
        self._internal_search.set()

    @staticmethod
    def _priority_first(song_data: List[List[str]], artist_data: List[Dict[str, int]]):
        """
        This method takes a list of rows from csv file that has information about a song object and a list
        of dictionaries that has information for artists.
        This method finds the most listened songs from different artists and returns song_data, and artist_data,
        and one song object if the algorithm was successful. If a song is returned, song_data, and artist_data will
        exclude information of this song.
        """

        try:
            if artist_data and song_data:
                index, data = next(
                    (index, data)
                    for index, data in enumerate(song_data)
                    if artist_data[0]["artist"] == data[2]
                )
                image_bytes = Controller._string_to_bytes(data[4])
                song = Song(int(data[0]), data[1], data[2], int(data[3]), image_bytes)
                song_data.pop(index)
                artist_data.pop(0)
                return song_data, artist_data, song  # If a song was found
            else:
                return (
                    song_data,
                    artist_data,
                    None,
                )  # If no more artist_data or song_data
        except StopIteration:
            return song_data, artist_data, None  # Next Exception

    @staticmethod
    def _priority_second(song_data: List[List[str]], artist: Dict[str, int]):
        """
        This method takes a list of rows from csv file that has information about a song object and a dictionary
        that has information about an artist.
        This method finds the most listened songs from the most listened artist and returns song_data,
        and one song object if the algorithm was successful. If a song is returned, song_data will
        exclude information of this song.
        """

        try:
            if song_data and artist:
                index, data = next(
                    (index, data)
                    for index, data in enumerate(song_data)
                    if artist["artist"] == data[2]
                )
                image_bytes = Controller._string_to_bytes(data[4])
                song = Song(int(data[0]), data[1], data[2], int(data[3]), image_bytes)
                song_data.pop(index)
                return song_data, song
            else:
                return song_data, None
        except StopIteration:
            return song_data, None

    def _priority_third(self, artist: Dict[str, int], recommendations: List[Song]):
        """
        This method takes an arist (dict) and recommendations (list).
        It searches for songs in the server from known artists. Already recommended songs are excluded.
        """

        if artist and recommendations:
            artist_name = artist["artist"]
            self._internal_search.clear()
            self._add_network_request("search", "internal", artist_name)
            self._internal_search.wait()
            results = self._internal_search_results
            recommendation_ids = [
                recommendation.song_id for recommendation in recommendations
            ]
            for song in results:
                if song.song_id not in recommendation_ids:
                    return song
            return None
        return None

    def _find_recommendations(self, song_data: List[List[str]], artist_data: List[Dict[str, int]]):
        """
        This method takes song_data and artist_data, and it finds four recommendations based on user's history.
        It uses three algorithms with different priorities.
        First priority finds the most listened songs from different artists. Second priority finds songs from the most
        listened artist. Third priority finds songs from known artists.
        This method returns a list with at most four Song objects.
        """

        recommendations = []  # Store all recommendations
        song_data.sort(
            key=lambda x: int(x[5]), reverse=True
        )  # At 5 is count (how many times a song was played)

        artist_data.sort(
            key=lambda k: k["count"], reverse=True
        )  # How many times an artist was played

        temp_song_data = song_data.copy()
        temp_artist_data = artist_data.copy()
        flag = False
        while len(recommendations) < 4 and not flag:
            temp_song_data, temp_artist_data, song = Controller._priority_first(
                temp_song_data, temp_artist_data
            )
            if song:
                recommendations.append(song)  # Song found, first priority
                continue
            else:
                count_second = 0
                while len(recommendations) < 4 and not flag:
                    if count_second < len(artist_data):
                        temp_song_data, song = Controller._priority_second(
                            temp_song_data, artist_data[0]
                        )
                        if song:
                            recommendations.append(song)  # Song found, second priority
                            continue
                        else:
                            count_second += 1
                    else:
                        count_third = 0
                        while len(recommendations) < 4 and not flag:
                            if count_third < len(artist_data):
                                song = self._priority_third(
                                    artist_data[count_third], recommendations
                                )
                                if song:
                                    recommendations.append(
                                        song
                                    )  # Song found, third priority
                                    continue
                                else:
                                    count_third += 1
                            else:  # Could not find four songs
                                flag = True
        return recommendations

    def _home_handler(self) -> None:
        """
        This method handles the home menu recommendations. It checks current user history and provides
        the home menu with at most four recommendations.
        """

        self._activity_file_flag.wait()  # If history file is opened, wait
        self._activity_file_flag.clear()
        path = self._history_relative_path
        try:
            with open(path, mode="r", newline="") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                rows = [row for row in csv_reader]  # Store all songs
            self._activity_file_flag.set()
            artists = []  # Store all artists
            for row in rows:
                try:
                    # Append artist to artists.
                    # An artist is a Dict[str, int] {'artist': artist_name, 'count': times_played}
                    # Check if artist name is the same as the artist in row; if it is the same, increase times_played
                    result = next(
                        (index, data)
                        for index, data in enumerate(artists)
                        if row[2] == data["artist"]
                    )
                    current_count = result[1]["count"]
                    additional_count = int(row[5])
                    new_count = current_count + additional_count
                    artists[result[0]]["count"] = new_count
                except StopIteration:  # No artist was found for current row, add a new artist
                    artists.append({"artist": row[2], "count": int(row[5])})
            recommendations = self._find_recommendations(rows, artists)
            self._window.display_recommendations(recommendations)

        except FileNotFoundError:
            self._activity_file_flag.set()
            self._window.show_internal_error()

    def _update_history(self, song: Song) -> None:
        """
        This method should be called every time a song is played. It will update the history
        for the current with the new song.
        """

        self._activity_file_flag.wait()
        self._activity_file_flag.clear()
        path = self._history_relative_path
        try:
            # Get existing songs
            csv_file = open(path, mode="r", newline="")
            csv_reader = csv.reader(csv_file, delimiter=",")
            existing_songs = [row for row in csv_reader]
            csv_file.close()
            song_exists = False

            for i in range(len(existing_songs)):
                # If song already exists, increase count by 1
                if song.song_id == int(existing_songs[i][0]):
                    song_count = int(existing_songs[i][5])
                    song_count += 1
                    existing_songs[i][5] = str(song_count)
                    song_exists = True
                    break
            if song_exists:
                # Write the new list of songs
                csv_file = open(path, mode="w", newline="")
                csv_writer = csv.writer(csv_file, delimiter=",")
                all_songs = tuple(existing_songs)
                csv_writer.writerows(all_songs)
                csv_file.close()
            else:
                # If this song does not exist in history, add it with count set to 1
                csv_file = open(path, mode="a", newline="")
                csv_writer = csv.writer(csv_file, delimiter=",")
                image_string = Controller._bytes_to_string(song.image_binary)
                data = [
                    song.song_id,
                    song.song_name,
                    song.artist_name,
                    song.duration,
                    image_string,
                    1,
                ]
                csv_writer.writerow(data)
                csv_file.close()

        except FileNotFoundError:  # If not history file was found, create it and call this method again
            f = open(path, mode="x")
            f.close()
            self._activity_file_flag.set()
            self._update_history(song)
        finally:
            self._activity_file_flag.set()

    def _set_shuffle_state(self, state: int) -> None:
        self._mediaplayer.set_shuffle_state(state)

    def update_repeat_state(self, state: int) -> None:
        self._window.update_repeat_state(state)

    def _set_repeat_state(self, state: int) -> None:
        self._mediaplayer.set_repeat_state(state)

    def _delete_queue(self) -> None:
        """
        Delete queue of mediaplayer
        """

        self._mediaplayer.delete_queue()

    def _search_playlist(self, search_string: str) -> None:
        """
        Call this method to search for songs in the current playlist.
        Pass a string as parameter, and the method will update the window with the found song if any,
        """

        search_string_serialized = "".join(search_string.split())
        if search_string_serialized == "":
            self._window.display_playlist_songs(
                self._get_playlist_songs(self.current_playlist), self.current_playlist
            )
            return
        results = []
        playlist_songs = self._get_playlist_songs(self.current_playlist)
        for playlist_song in playlist_songs:
            song_name_serialized = "".join(playlist_song.song_name.split())
            artist_name_serialized = "".join(playlist_song.artist_name.split())
            # Find songs that match with the pattern
            if re.search(
                search_string_serialized, song_name_serialized, re.IGNORECASE
            ) or re.search(
                search_string_serialized, artist_name_serialized, re.IGNORECASE
            ):
                results.append(playlist_song)
        self._window.display_playlist_songs(
            results, self.current_playlist
        )  # Update window

    def _play_current_playlist(self) -> None:
        """
        Call this method to play the entire current playlist. The queue will be cleared, and the first
        song of the playlist will start playing.
        """

        playlist_songs = self._get_playlist_songs(self.current_playlist)
        self._mediaplayer.play_playlist_songs(playlist_songs)
        self.send_play_pause(True)

    def _add_playlist_to_queue(self) -> None:
        """
        Call this method to add the entire current playlist to queue.
        """

        playlist_songs = self._get_playlist_songs(self.current_playlist)
        self._mediaplayer.add_playlist_songs_to_queue(playlist_songs)

    def _rename_current_playlist(self, name: str) -> None:
        """
        Call this method to rename the current playlist with the given name.
        If the name is taken, the user will be notified.
        If the name is invalid, the user will be notified.
        """

        path = self._playlists_relative_path
        try:
            os.rename(f"{path}{self.current_playlist}.csv", f"{path}{name}.csv")
            self._window.display_playlist_links(
                self._get_playlist_links(), mode="rename", active=name
            )
            self._window.update_playlist_name(name)
            self.current_playlist = name
            self._window.update_inner_more_menus(self._get_playlist_links())
        except FileNotFoundError:  # Display internal error
            self._window.show_internal_error()
        except OSError:  # Display name already taken
            self._window.show_error()

    def _create_new_playlist(self, name: str) -> None:
        """
        This method will create a new playlist with the specified name.
        """

        path = self._playlists_relative_path
        try:
            f = open(f"{path}{name}.csv", mode="x")
            f.close()
            self._window.display_playlist_links(
                self._get_playlist_links(), mode="new", active=name
            )  # REDISPLAY SEARCH
            self._window.update_inner_more_menus(self._get_playlist_links())
        except FileExistsError:
            self._window.show_playlist_warning()  # Display name already taken
        except OSError:  # Display invalid name error
            self._window.show_error()

    def _delete_current_playlist(self):
        """
        This method will delete the current playlist.
        """

        path = self._playlists_relative_path
        try:
            os.remove(f"{path}{self.current_playlist}.csv")
            self._window.display_playlist_links(
                self._get_playlist_links(), mode="delete"
            )
            self._window.show_home_widget()
            self._window.update_inner_more_menus(self._get_playlist_links())
        except FileNotFoundError:
            self._window.show_internal_error()  # Display internal error

    def _add_to_playlist(self, song: Song, playlist_link: str) -> None:
        """
        Add a song to the specified playlist.
        """

        path = self._playlists_relative_path
        try:
            with open(f"{path}{playlist_link}.csv", mode="r") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    if int(row[0]) == song.song_id:
                        self._window.show_song_exists(
                            song.song_name, playlist_link
                        )  # Song already exists
                        return
        except FileNotFoundError:  # Display internal error
            self._window.show_internal_error()

        try:
            with open(f"{path}{playlist_link}.csv", mode="a", newline="") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=",")
                image_string = Controller._bytes_to_string(song.image_binary)
                song_data = [
                    song.song_id,
                    song.song_name,
                    song.artist_name,
                    song.duration,
                    image_string,
                ]
                csv_writer.writerow(song_data)  # Add the song to the playlist
        except FileNotFoundError:
            self._window.show_internal_error()

    def _get_playlist_links(self) -> List[str]:
        """
        This method returns all playlists as a list of strings.
        """

        links = []
        path = self._playlists_relative_path
        for filename in os.listdir(path):
            playlist_link = filename.split(".")[0]
            links.append(playlist_link)
        return links

    def _get_playlist_songs(self, playlist_link: str) -> List[Song]:
        """
        Call this method to get a list of all songs in the current playlist.
        """

        path = self._playlists_relative_path
        playlist_songs = []
        playlist_path = f"{path}{playlist_link}.csv"
        try:
            with open(playlist_path, mode="r", newline="") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    image_bytes = Controller._string_to_bytes(row[4])
                    # Create song objects
                    playlist_songs.append(
                        Song(int(row[0]), row[1], row[2], int(row[3]), image_bytes)
                    )
        except FileNotFoundError:
            self._window.show_internal_error()
        return playlist_songs

    def _update_playlist(self, playlist_link: str) -> None:
        """
        This method updates the current playlist in the controller, and sends all playlist songs to window.
        """

        self.current_playlist = playlist_link
        self._window.display_playlist_songs(
            self._get_playlist_songs(playlist_link), self.current_playlist
        )

    def _remove_from_playlist(self, song_id: int) -> None:
        """
        Remove a song from playlist using its song_id attribute.
        """

        path = self._playlists_relative_path
        playlist_path = f"{path}{self.current_playlist}.csv"  # Current Playlist
        updated_playlist = []
        try:
            # Get all songs excluding the one with song_id == song_id
            with open(playlist_path, "r") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for row in csv_reader:
                    if int(row[0]) != song_id:
                        updated_playlist.append(row)
        except FileNotFoundError:
            self._window.show_internal_error()

        try:
            # Write the updated playlist to the file
            with open(playlist_path, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=",")
                csv_writer.writerows(updated_playlist)
        except FileNotFoundError:
            self._window.show_internal_error()
        # Update the playlist
        self._update_playlist(self.current_playlist)

    @staticmethod
    def _string_to_bytes(string: str) -> bytes:
        image = string.encode("utf-8")
        image = base64.b64decode(image)
        return image

    @staticmethod
    def _bytes_to_string(image_bytes: bytes) -> str:
        image = base64.b64encode(image_bytes)
        string = image.decode("utf-8")
        return string

    def display_queue(self, results):
        """
        Display the entire queue in window.
        """

        self._window.display_queue(results)

    def _current_song_update(
        self,
        song_name: str,
        artist_name: str,
        duration_string: str,
        image_binary: bytes,
        song: Song,
    ) -> None:
        """
        This will display the song name, artist name, duration, and image in window.
        Furthermore, it will update the history file with this song.
        """

        self._update_history(song)
        self._window.update_song_info(
            song_name, artist_name, duration_string, image_binary
        )  # Update current song

    def _terminate_song_data_recv_request(self) -> None:
        """
        Call this method to contact the server to terminate streaming a song.
        The method should be called by the mediaplayer.
        """

        self._add_network_request("terminate_song_data_recv")

    def _communication_loop(self) -> None:
        """
        This method should be run in a separate thread. It waits for network request from the client
        and contacts the server based on the request type. It then waits for a response and sends the
        response to the appropriate method.
        """

        while True:
            self._new_network_request_flag.wait()  # Wait for new network request
            network_request = self._network_request_queue[0]
            self._execute_network_request(network_request)
            del self._network_request_queue[
                0
            ]  # Delete the request from queue after completion
            if len(self._network_request_queue) == 0:
                self._new_network_request_flag.clear()

    def _internal_request_loop(self):
        """
        This method should be run in a separate thread. It waits for internal request from the client
        and contacts the server based on the request type. The requests are usually time-consuming requests
        that would block the UI if executed in the PYQT thread.
        """

        while True:
            self._new_internal_request_flag.wait()  # Wait for a new internal request
            internal_request = self._internal_request_queue[0]
            self._execute_internal_request(internal_request)
            del self._internal_request_queue[
                0
            ]  # Delete the request from queue after completion
            if len(self._internal_request_queue) == 0:
                self._new_internal_request_flag.clear()

    def _execute_network_request(self, network_request) -> None:
        """
        Call this method to execute a network request. The method will check its type,
        and then execute it.
        """

        if network_request[0] == "terminate_song_data_recv":
            self._terminate_song_data_recv_request_handler()

        elif network_request[0] == "search":
            self._search_request_handler(network_request[1], network_request[2])

    def _execute_internal_request(self, internal_request) -> None:
        """
        Call this method to execute an internal request. The method will check its type,
        and then execute it.
        """

        if internal_request[0] == "next":
            self.next_song()

        elif internal_request[0] == "previous":
            self.previous_song()

        elif internal_request[0] == "play_this":
            self.play_this(internal_request[1])

        elif internal_request[0] == "play_current_playlist":
            self._play_current_playlist()

        elif internal_request[0] == "home_handler":
            self._home_handler()

    def _add_internal_request(
        self, internal_request_type: str, *args, **kwargs
    ) -> None:
        """
        Call this method to add an internal request to the queue.
        """

        internal_request = (internal_request_type, *args, *kwargs)
        self._internal_request_queue.append(internal_request)
        self._new_internal_request_flag.set()  # If the internal request loop is waiting for request, inform it

    def _add_network_request(self, network_request_type: str, *args, **kwargs) -> None:
        """
        Call this method to add a network request to the queue.
        """

        network_request = (network_request_type, *args, *kwargs)
        self._network_request_queue.append(network_request)
        self._new_network_request_flag.set()  # In case the communication loop is waiting for a new request, inform it

    def _search_request_handler(
        self, search_type: str, search_string: str
    ) -> None:  # handle if search_string is empty
        """
        Call this method to search for a song in the server. The method takes a search_type ('user' or 'internal')
        and updates the window, or sets the internal search results respectively.
        """

        search_string_serialized = "".join(search_string.split())
        results = []
        if search_string_serialized == "":  # If empty search string, return
            if search_type == "user":
                self._window.display_songs(results)
            elif search_type == "internal":
                self._set_internal_search_results(results)
            return
        request = f"SEARCH@{search_string_serialized}"  # Prepare the request
        request_bytes = request.encode("utf-8")

        length = len(request_bytes)
        length_bytes = length.to_bytes(4, "little")
        self.communication_tcp_send(length_bytes, 4)
        self.communication_tcp_send(request_bytes, length)
        number_of_songs_bytes = self.communication_tcp_recv(4)
        number_of_songs = int.from_bytes(number_of_songs_bytes, "little")

        if number_of_songs > 0:  # If the server gives number_of_songs > 0
            for i in range(number_of_songs):
                data_length_bytes = self.communication_tcp_recv(4)
                data_length = int.from_bytes(data_length_bytes, "little")
                serialized_song = b""

                for j in range(data_length - 1):
                    serialized_song += self.communication_tcp_recv(1024)  # Receive song

                last_packet_length_bytes = self.communication_tcp_recv(4)
                last_packet_length = int.from_bytes(
                    last_packet_length_bytes, "little"
                )  # Receive last packet
                serialized_song += self.communication_tcp_recv(last_packet_length)
                try:
                    current_song = pickle.loads(serialized_song)  # Unpickle song
                    results.append(current_song)  # Add song to results
                except pickle.PickleError:
                    self._window.show_internal_error()

        if search_type == "user":
            self._window.display_songs(results)
        elif search_type == "internal":
            self._set_internal_search_results(results)

    def _terminate_song_data_recv_request_handler(self) -> None:
        """
        Call this method to send a stream terminate request to the server.
        """

        network_request = "TERMINATE_SONG_DATA_RECV@"
        network_request_bytes = network_request.encode("utf-8")
        length = len(network_request_bytes)
        length_bytes = length.to_bytes(4, "little")
        self.communication_tcp_send(length_bytes, 4)
        self.communication_tcp_send(network_request_bytes, length)

    def _set_slider_free(self):
        self._slider_busy = False

    def _set_slider_busy(self):
        self._slider_busy = True

    def _set_progress(self, value):
        self._mediaplayer.set_progress(value)

    def _get_progress(self, progress, time_passed_string):
        if not self._slider_busy:
            self._window.send_progress_info(progress, time_passed_string)

    def run(self):
        """
        Call this method to run the controller. Run() will set all the required threading.Events and
        start all the threads.
        """

        # Threading Events
        self._reconnect.set()
        self._new_network_request_flag.clear()
        self._new_internal_request_flag.clear()
        self._internal_search.clear()
        self._activity_file_flag.set()
        # Threads
        self.connection_thread.start()
        self.communication_thread.start()
        self.internal_request_thread.start()
        # Other
        self._mediaplayer.run()
        self._window.display_playlist_links(self._get_playlist_links())
        self._window.show_search_widget()

    def _create_controller_client(self):
        self._controller_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _connect_to_server(self):
        while True:
            self._reconnect.wait()
            self._reconnect.clear()
            self._create_controller_client()
            while True:
                try:
                    self._controller_client.connect(
                        (self._host, self._port_communication)
                    )
                    self.communication_tcp_send(self._client_id, 6)
                    print("[COMMUNICATION CONNECTED]")
                    break
                except ConnectionRefusedError:
                    print("[WAITING FOR SERVER] - [CONTROLLER]")
                except OSError:
                    print("[OS ERROR]")
                    break

    def send_play_pause(self, value: bool):
        """
        This method will send the state of play (True) / pause (False) to the window.
        """

        self._window.receive_play_pause(value)

    def _set_play_pause(self) -> None:
        """
        This method updates the state of play (True) / pause (False). If the state is True, it will set it to False;
        if the state is False it will set it to True. The state changes for the mediaplayer and for the window.
        """

        state = self._mediaplayer.change_play_state()
        self.send_play_pause(state)

    def _add_to_queue(self, song: Song) -> None:
        """
        Add song to queue.
        """

        self._mediaplayer.add_to_queue(song)

    def play_this(self, song: Song) -> None:
        """
        Plays the given song and sends the current play/ pause to window as play (True).
        """

        self.send_play_pause(True)
        self._mediaplayer.play_this(song)

    def next_song(self):
        """
        Calls next_song() from mediaplayer and sends play/ pause state (True) to window.
        """

        self._mediaplayer.next_song()
        self.send_play_pause(True)

    def previous_song(self):
        """
        Calls previous_song() from mediaplayer and sends play/ pause state (False) to window.
        """

        self._mediaplayer.previous_song()
        self.send_play_pause(True)

    def exit(self):
        """
        Call this method to exit controller.
        """

        self._mediaplayer.exit()

    def communication_tcp_send(self, data: bytes, bufsize: int) -> None:
        """
        This method sends the specified data (bytes) of length bufsize(int) using socket.send().
        If not all data was successfully sent, the method will try again to send the remaining data.
        """

        total_sent = 0
        while total_sent < bufsize:
            sent = self._controller_client.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent

    def communication_tcp_recv(self, bufsize: int) -> bytes:
        """
        This method received data (bytes) of size bufsize (int) from the server. If not all data was received,
        the method will try again to receive the remaining data.
        """

        chunks = []
        bytes_received = 0
        while bytes_received < bufsize:
            chunk = self._controller_client.recv(bufsize - bytes_received)
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)
        return b"".join(chunks)

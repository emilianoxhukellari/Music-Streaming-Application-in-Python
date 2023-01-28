import unittest
import pyaudio
import player
import mediaplayer
import controller
import eventsystem
import song


class TestPLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.player = player.Player()

    def test_create_stream(self):
        self.assertIsInstance(self.player._create_stream(), pyaudio.Stream)

    def test_set_progress_valid_value_0(self):
        self.player.set_song_data_length(50)
        self.player.set_progress(0)
        self.assertEqual(0, self.player._current_index)

    def test_set_progress_valid_value_500(self):
        self.player.set_song_data_length(50)
        self.player.set_progress(500)
        self.assertEqual(24, self.player._current_index)

    def test_set_progress_valid_value_1000(self):
        self.player.set_song_data_length(50)
        self.player.set_progress(1000)
        self.assertEqual(49, self.player._current_index)

    def test_set_progress_invalid_value_less_than_0(self):
        self.player.set_song_data_length(50)
        self.player.set_progress(-1)
        self.assertEqual(0, self.player._current_index)

    def test_set_progress_invalid_value_greater_than_1000(self):
        self.player.set_song_data_length(50)
        self.player.set_progress(1001)
        self.assertEqual(49, self.player._current_index)


class TestMediaplayer(unittest.TestCase):
    def setUp(self) -> None:
        self.mediaplayer = mediaplayer.MediaPlayer(None, None, None, lambda results: None, None)
        self.mediaplayer.run()
        self.test_song_1 = song.Song(1, 'On & On', 'Cartoon', 207, b'test')
        self.test_song_2 = song.Song(2, 'Whatever', 'Cartoon', 205, b'test')
        self.test_song_3 = song.Song(3, 'Xenogenesis', 'TheFatRat', 233, b'test')

    def tearDown(self) -> None:
        self.mediaplayer.exit()

    def test_seconds_to_string(self):
        self.assertEqual(self.mediaplayer._seconds_to_string(60), "01:00")

    def test_add_to_queue(self):
        self.mediaplayer.add_to_queue(self.test_song_1)
        self.assertIn(self.test_song_1, self.mediaplayer._queue)

    def test_remove_from_queue(self):
        self.mediaplayer.add_to_queue(self.test_song_1)
        self.mediaplayer.remove_from_queue(0)
        self.assertNotIn(self.test_song_1, self.mediaplayer._queue)

    def test_delete_queue(self):
        self.mediaplayer.add_to_queue(self.test_song_1)
        self.mediaplayer.add_to_queue(self.test_song_2)
        self.mediaplayer.add_to_queue(self.test_song_3)
        self.mediaplayer.delete_queue()
        self.assertFalse(self.mediaplayer._queue)

    def test_move_up(self):
        self.mediaplayer.add_to_queue(self.test_song_1)
        self.mediaplayer.add_to_queue(self.test_song_2)
        self.mediaplayer.add_to_queue(self.test_song_3)

        self.mediaplayer.move_up(1)
        self.assertEqual(self.mediaplayer._queue[0], self.test_song_2)
        self.assertEqual(self.mediaplayer._queue[1], self.test_song_1)

    def test_move_down(self):
        self.mediaplayer.add_to_queue(self.test_song_1)
        self.mediaplayer.add_to_queue(self.test_song_2)
        self.mediaplayer.add_to_queue(self.test_song_3)

        self.mediaplayer.move_down(1)
        self.assertEqual(self.mediaplayer._queue[2], self.test_song_2)
        self.assertEqual(self.mediaplayer._queue[1], self.test_song_3)

    def test_change_play_state(self):
        self.assertTrue(self.mediaplayer.change_play_state())
        self.assertFalse(self.mediaplayer.change_play_state())


class TestSongQueue(unittest.TestCase):
    def setUp(self) -> None:
        self.song_queue = mediaplayer.SongQueue()
        self.test_song_1 = song.Song(1, 'On & On', 'Cartoon', 207, b'test')
        self.test_song_2 = song.Song(2, 'Whatever', 'Cartoon', 205, b'test')
        self.test_song_3 = song.Song(3, 'Xenogenesis', 'TheFatRat', 233, b'test')
        self.song_queue.append_to_queue(self.test_song_1)
        self.song_queue.append_to_queue(self.test_song_2)
        self.song_queue.append_to_queue(self.test_song_3)

    def test_shuffle_current_index_unchanged(self):
        self.song_queue.shuffle(0)
        self.assertEqual(self.song_queue[0], self.test_song_1)

    def test_unshuffle(self):
        self.song_queue.shuffle(0)
        self.song_queue.unshuffle(0)
        self.assertEqual(self.song_queue[1], self.test_song_2)
        self.assertEqual(self.song_queue[2], self.test_song_3)


class TestController(unittest.TestCase):

    def setUp(self) -> None:
        self.controller = controller.Controller(window=None)

    def test_priority_first_valid(self):
        song_data = [['1', 'On & On', 'Cartoon', '207', ''],
                     ['2', 'Xenogenesis', 'TheFatRat', '233', ''],
                     ['3', 'Collide', 'Elektronomia', '222', ''],
                     ['4', 'Whatever', 'Cartoon', '205', '']]

        artist_data = [{'artist': 'Cartoon', 'count': 10},
                       {'artist': 'TheFatRat', 'count': 9},
                       {'artist': 'Elektronomia', 'count': 8},
                       {'artist': 'Cartoon', 'count': 7}]
        for i in range(1, 5):
            result_song_data, result_artist_data, song = self.controller._priority_first(song_data, artist_data)
            self.assertEqual(i, song.song_id)

    def test_priority_first_no_result(self):
        song_data = [['1', 'On & On', 'Cartoon', '207', ''],
                     ['2', 'Xenogenesis', 'TheFatRat', '233', ''],
                     ['3', 'Collide', 'Elektronomia', '222', ''],
                     ['4', 'Whatever', 'Cartoon', '205', '']]

        artist_data = [{'artist': 'X', 'count': 10},
                       {'artist': 'X', 'count': 9},
                       {'artist': 'X', 'count': 8},
                       {'artist': 'X', 'count': 7}]
        result_song_data_after, result_artist_data_after, song = self.controller._priority_first(song_data, artist_data)
        self.assertListEqual(result_song_data_after, song_data)
        self.assertListEqual(result_artist_data_after, artist_data)
        self.assertIsNone(song)

    def test_priority_first_no_input_data(self):
        song_data = []
        artist_data = []
        result_song_data_after, result_artist_data_after, song = self.controller._priority_first(song_data, artist_data)
        self.assertEqual(result_song_data_after, song_data)
        self.assertEqual(result_artist_data_after, artist_data)
        self.assertIsNone(song)

    def test_priority_second(self):
        song_data = [['1', 'On & On', 'Cartoon', '207', ''],
                     ['2', 'Xenogenesis', 'Cartoon', '233', ''],
                     ['3', 'Collide', 'Cartoon', '222', ''],
                     ['4', 'Whatever', 'Cartoon', '205', '']]

        artist = {'artist': 'Cartoon', 'count': 10}

        for i in range(1, 5):
            song_data, song = self.controller._priority_second(song_data, artist)
            self.assertEqual(i, song.song_id)


class ListenerClass(eventsystem.Listener):
    def __init__(self):
        eventsystem.Listener.__init__(self)


class TestEventSystem(unittest.TestCase):

    def setUp(self) -> None:
        self.listener_object = ListenerClass()

    def test_listener_assert_true(self):
        self.listener_object.listen('assert_true', self.assertTrue)
        eventsystem.Event('assert_true', True, self_fire=True)

    def test_listener_assert_equal(self):
        self.listener_object.listen('assert_equal', self.assertEqual)
        eventsystem.Event('assert_equal', 1, 1, self_fire=True)


if __name__ == '__main__':
    unittest.main()

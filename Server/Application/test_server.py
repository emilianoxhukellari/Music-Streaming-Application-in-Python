import unittest
import unittest.mock
import server
import socket
import clienthandler
import eventsystem
import song


class TestServer(unittest.TestCase):
    def setUp(self) -> None:
        self.server = server.Server()
        self.streaming_socket = unittest.mock.Mock()
        self.communication_socket = unittest.mock.Mock()
        self.db_connection = unittest.mock.Mock()

    def tearDown(self) -> None:
        self.server.__del__()

    def test_get_client_full_id(self):
        client_id = '123456'
        address = ('1.1.1.1', 'test')
        self.assertEqual('123456@1.1.1.1', self.server._get_client_full_id(client_id, address))

    def test_create_communication_socket(self):
        temp_socket = self.server._create_communication_socket()
        self.assertIsInstance(temp_socket, socket.socket)
        temp_socket.close()

    def test_create_streaming_socket(self):
        temp_socket = self.server._create_streaming_socket()
        self.assertIsInstance(temp_socket, socket.socket)
        temp_socket.close()


class TestClientHandler(unittest.TestCase):

    def test_slice_song_bytes_one(self):
        temp = 'AAA'.encode('utf-8')
        data, data_length = clienthandler.ClientHandler.slice_song_bytes(temp)
        self.assertEqual(temp, data[0])
        self.assertEqual(data_length, 1)

    def test_slice_song_bytes_two(self):
        temp = ''.encode('utf-8')
        temp_1024 = ''.encode('utf-8')
        for i in range(1025):
            temp += 'A'.encode('utf-8')
            if i != 1024:
                temp_1024 += 'A'.encode('utf-8')

        data, data_length = clienthandler.ClientHandler.slice_song_bytes(temp)
        self.assertEqual(temp_1024, data[0])
        self.assertEqual('A'.encode('utf-8'), data[1])
        self.assertEqual(data_length, 2)


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


class TestSong(unittest.TestCase):
    def test_seconds_to_string(self):
        self.assertEqual(song.Song._seconds_to_string(60), "01:00")


if __name__ == '__main__':
    unittest.main()

class Song:
    """
    This class represents a song. It contains the data of a song.
    """

    def __init__(self, song_id: int, song_name: str, artist_name: str, duration: int, image_binary: bytes):
        self.song_id = song_id
        self.song_name = song_name
        self.artist_name = artist_name
        self.duration = duration
        self.duration_string = self._seconds_to_string(duration)
        self.image_binary = image_binary

    @staticmethod
    def _seconds_to_string(seconds):
        """Converts seconds to minute and seconds (00:00)"""
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes:0>2d}:{seconds:0>2d}"

    def __str__(self):
        return (
            str(self.song_id)
            + ", "
            + self.song_name
            + ", "
            + self.artist_name
            + ", "
            + str(self.duration)
        )

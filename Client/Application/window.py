from typing import List
from PyQt5 import QtGui
from PyQt5.QtCore import (
    QCoreApplication,
    QObject,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtWidgets import (
    QToolButton,
    QFrame,
    QLabel,
    QWidget,
    QLayout,
    QVBoxLayout,
    QScrollArea,
    QAbstractScrollArea,
    QGridLayout,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QMenu,
    QPushButton,
    QSlider,
    QStackedWidget,
)
from PyQt5 import QtCore, sip
from PyQt5.QtGui import QCursor, QFont, QIcon
from eventsystem import Listener, Event
from song import Song


class ToolButton(QToolButton):
    """
    Summary:
    This class represents a tool button which can change icon on enter event.

    Usage:
    Create a ToolButton object, and use it similarly to a QToolButton. You must pass a default
    icon, and a hover icon. On mouse enter the icon changes to hover icon, and on
    mouse leave the icon changes to default icon.
    """

    def __init__(self, parent: QObject, default_icon: QIcon, hover_icon: QIcon) -> None:
        QToolButton.__init__(self, parent)
        self.default_icon = default_icon
        self.hover_icon = hover_icon

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.setIcon(self.hover_icon)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.setIcon(self.default_icon)


class ShuffleButton(QToolButton):
    """
    Summary:
    This class represents the shuffle button. It remembers state, and it can change state
    on click.

    Usage:
    Create a Shuffle Button object, and pass two icons - when shuffle is off and on.
    On click the state changes from off to on or from on to on. The button will fire a
    'shuffle_state' event on click.
    """

    def __init__(self, parent, shuffle_off_icon: QIcon, shuffle_on_icon: QIcon) -> None:
        QToolButton.__init__(self, parent)
        self.shuffle_off_icon = shuffle_off_icon
        self.shuffle_on_icon = shuffle_on_icon
        self._state = 0
        self.clicked.connect(self.set_state)

    def change_state(self) -> int:
        """
        Call this method to change the state of the shuffle button: from 0 to 1 or from 1 to 0.
        Returns the changed state.
        """
        if self._state == 0:
            self._state = 1
        elif self._state == 1:
            self._state = 0

        return self._state

    def set_state(self) -> None:
        """
        Call this method to set the state of the button. It calls change_state(), and then
        it sets the state.
        """

        state = self.change_state()
        if state == 0:
            self.set_shuffle_off()
        elif state == 1:
            self.set_shuffle_on()

    def set_shuffle_off(self) -> None:
        """
        This method will fire a shuffle off state event and update the icon of the button.
        """

        Event("shuffle_state", self._state, self_fire=True)
        self.setIcon(self.shuffle_off_icon)

    def set_shuffle_on(self) -> None:
        """
        This method will fire a shuffle oon state event and update the icon of the button.
        """

        Event("shuffle_state", self._state, self_fire=True)
        self.setIcon(self.shuffle_on_icon)


class RepeatButton(QToolButton):
    """
    Summary:
    This class represents the repeat button. It can change state and it remembers state.

    Usage:
    Create a RepeatButton object by passing repeat many off icon, repeat many on icon, and repeat one icon.
    On click this button will change state from many off, to many on, and finally to repeat one.
    """

    def __init__(
        self,
        parent: QObject,
        repeat_many_off_icon: QIcon,
        repeat_many_on_icon: QIcon,
        repeat_one_icon: QIcon,
    ):
        QToolButton.__init__(self, parent)
        self.repeat_many_off_icon = repeat_many_off_icon
        self.repeat_many_on_icon = repeat_many_on_icon
        self.repeat_one_icon = repeat_one_icon
        self._state = 0
        self.clicked.connect(self.set_state)

    def change_state(self) -> int:
        """
        This method will change the state from 0 to 1, 1 to 2, or 2 to 0.
        0 represents repeat many off, 1 represents repeat many on, and 2 represents repeat one.
        """

        if self._state == 2:
            self._state = 0
        else:
            self._state += 1
        return self._state

    def set_state(self, state=None) -> None:
        """
        Call this method to set the state of the button. If no state is passed in the method,
        it will change it by calling change_state(), and then set the state.
        If state is passed, it will use that state and not change it.
        """

        if state:
            current_state = state
        else:
            current_state = self.change_state()

        if current_state == 0:
            self.set_repeat_many_off()
        elif current_state == 1:
            self.set_repeat_many_on()
        else:
            self.set_repeat_one()

    def set_repeat_many_off(self) -> None:
        """
        this method will fire a repeat_state 0 event, and set the icon to repeat many off.
        """

        self._state = 0
        Event("repeat_state", self._state, self_fire=True)
        self.setIcon(self.repeat_many_off_icon)

    def set_repeat_many_on(self) -> None:
        """
        This method will fire a repeat_state 1 event, and set the icon to repeat many on.
        """

        self._state = 1
        Event("repeat_state", self._state, self_fire=True)
        self.setIcon(self.repeat_many_on_icon)

    def set_repeat_one(self) -> None:
        """
        This method will fire a repeat_state 2 event, and set the icon to repeat one.
        """

        self._state = 2
        Event("repeat_state", self._state, self_fire=True)
        self.setIcon(self.repeat_one_icon)


class PlaylistLinkContainer(QToolButton):
    """
    Summary:
    This class represents a link to a playlist.

    Usage:
    Create an object of this class and pass the playlist name (str).
    """

    def __init__(self, parent: QObject, playlist_link: str):
        QToolButton.__init__(self, parent)
        self._playlist_link = playlist_link
        self._set_self_params()
        self._is_active = False

    def _set_self_params(self) -> None:
        self.setFixedHeight(25)
        self.setFixedWidth(290)
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.setFont(font)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 5px; border: 0px solid rgb(0, 170, 127);"
        )
        self.setText(self._playlist_link)

    def connect(self, method) -> None:
        self.clicked.connect(method)

    def get_playlist_link(self) -> str:
        return self._playlist_link

    def set_active_style(self) -> None:
        """
        Call this method to set active style to the playlist link container. It has a green rgb(0, 170, 127) border.
        """

        self.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 5px; border: 1px solid rgb(0, 170, 127);"
        )
        self._is_active = True

    def set_inactive_style(self):
        """
        Call this method to set inactive style to the playlist container. It does not have a border.
        """

        self.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 5px; border: 0px solid rgb(0, 170, 127);"
        )
        self._is_active = False

    def is_active(self) -> bool:
        return self._is_active


class RecommendationContainer(QFrame):
    """
    Summary:
    This class represents a recommended song. It has rectangular shape, and it holds the song image, song name,
    artist name, play button, and a menu which can be accessed by right-clicking on the container.

    Usage:
    Create an instance if this class and add it to its container.
    """

    def __init__(
        self,
        parent: QObject,
        song: Song,
        image: QtGui.QPixmap,
        playlist_links: List[str],
        icon_play=QIcon(),
    ):
        QFrame.__init__(self, parent)
        self.menu = None
        self._playlist_links = None
        self._icon_play = icon_play
        self.set_playlist_links(playlist_links)
        self._song = song
        self._image = image
        self._set_self_params()
        self._set_image_container()
        self._set_song_name_inner()
        self._set_artist_name_inner()
        self._set_play_this_button()
        self.set_menu()

    def set_playlist_links(self, playlist_links: List[str]) -> None:
        self._playlist_links = playlist_links

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.RightButton:
            self.menu.exec_(self.mapToGlobal(event.pos()))

    def _set_self_params(self) -> None:
        self.setFixedSize(150, 185)
        self.setStyleSheet("background-color: transparent;")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

    def set_menu(self) -> None:
        self.menu = QMenu(self)
        self.menu.setGeometry(QRect(420, 130, 36, 36))
        self.menu.addAction("Add to queue", lambda: Event("add_to_queue", self._song, self_fire=True))
        for playlist_link in self._playlist_links:
            self._add_playlist_to_menu(self._song, playlist_link)
        self.menu.setStyleSheet("""QMenu {background-color: rgb(60, 60, 60); color: white;} 
            QMenu::item:selected {background-color: rgb(100, 100, 100);}""")

    def _set_image_container(self) -> None:
        self._image_container = QLabel(self)
        self._image_container.setGeometry(QRect(1, 1, 148, 148))
        self._image_container.setStyleSheet("background-color: transparent; border-radius: 0px;")
        self._image_container.setScaledContents(True)
        self._image_container.setPixmap(self._image)

    def _set_song_name_inner(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self._song_name_inner = QLabel(self)
        self._song_name_inner.setGeometry(QRect(2, 151, 146, 16))
        self._song_name_inner.setFont(font)
        self._song_name_inner.setStyleSheet("background-color: transparent;")
        self._song_name_inner.setText(self._song.song_name)

    def _set_artist_name_inner(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self._artist_name_inner = QLabel(self)
        self._artist_name_inner.setGeometry(QRect(2, 168, 146, 16))
        self._artist_name_inner.setFont(font)
        self._artist_name_inner.setStyleSheet("background-color: transparent; color: rgb(85, 255, 255);")
        self._artist_name_inner.setText(self._song.artist_name)

    def _set_play_this_button(self) -> None:
        self._play_this_button = QToolButton(self)
        self._play_this_button.setGeometry(QRect(6, 110, 34, 34))
        self._play_this_button.setStyleSheet(
            "background-color: black; border-radius: 17px; border: 1px solid rgb(100, 100, 100);"
        )
        self._play_this_button.setIcon(self._icon_play)
        self._play_this_button.setIconSize(QSize(15, 15))
        self._play_this_button.clicked.connect(
            lambda: Event("internal_request", "play_this", self._song, self_fire=True)
        )

    def _add_playlist_to_menu(self, song: Song, playlist_link: str) -> None:
        self.menu.addAction(
            f"Add to Playlist: {playlist_link}",
            lambda: Event("add_to_playlist", song, playlist_link, self_fire=True),
        )


class SongSearchContainer(QFrame):
    """
    Summary:
    This class represents a song container from search menu. It contains an image, song name, artist name, play button,
    and more button.

    Usage:
    Create an instance if this class and add it to its container.
    """

    def __init__(
        self,
        parent: QObject,
        song: Song,
        image: QtGui.QPixmap,
        playlist_links: List[str],
        icon_play=QIcon(),
        icon_more=QIcon(),
    ):
        QFrame.__init__(self, parent)
        self._menu = None
        self._playlist_links = None
        self.icon_play = icon_play
        self.icon_more = icon_more
        self.set_playlist_links(playlist_links)
        self.song = song
        self.image = image
        self._set_self_params()
        self._set_play_this_button()
        self._set_img_container()
        self._set_song_name_inner()
        self._set_artist_name_inner()
        self._set_more_button()
        self.set_menu()

    def set_playlist_links(self, playlist_links: List[str]) -> None:
        self._playlist_links = playlist_links

    def _set_self_params(self) -> None:
        self.setFixedSize(470, 62)
        self.setStyleSheet("background-color: rgb(35, 35, 35); border-radius: 8px;")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

    def _set_play_this_button(self) -> None:
        self._play_this_button = QToolButton(self)
        self._play_this_button.setGeometry(QRect(380, 13, 36, 36))
        self._play_this_button.setStyleSheet("background-color: transparent; border-radius: 18px;")
        self._play_this_button.setIcon(self.icon_play)
        self._play_this_button.setIconSize(QSize(20, 20))
        self._play_this_button.clicked.connect(
            lambda: Event("internal_request", "play_this", self.song, self_fire=True)
        )

    def _set_img_container(self) -> None:
        self._small_img_container = QLabel(self)
        self._small_img_container.setGeometry(QRect(1, 1, 60, 60))
        self._small_img_container.setStyleSheet("background-color: rgb(85, 85, 127); border-radius: 0px;")
        self._small_img_container.setScaledContents(True)
        self._small_img_container.setPixmap(self.image)

    def _set_song_name_inner(self) -> None:
        self._song_name_inner = QLabel(self)
        self._song_name_inner.setGeometry(QRect(70, 5, 300, 24))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self._song_name_inner.setFont(font)
        self._song_name_inner.setStyleSheet("background-color: transparent; color: white;")
        self._song_name_inner.setText(self.song.song_name)

    def _set_artist_name_inner(self) -> None:
        self._artist_name_inner = QLabel(self)
        self._artist_name_inner.setGeometry(QRect(70, 33, 300, 24))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self._artist_name_inner.setFont(font)
        self._artist_name_inner.setStyleSheet("background-color: transparent; color: white;")
        self._artist_name_inner.setText(self.song.artist_name)

    def _set_more_button(self) -> None:
        self._more_button = QPushButton(self)
        self._more_button.setObjectName("more_button")
        self._more_button.setGeometry(QRect(420, 13, 36, 36))
        font = QFont()
        font.setPointSize(10)
        self._more_button.setFont(font)
        self._more_button.setStyleSheet("""QPushButton::menu-indicator { image: none; } 
            QPushButton {background-color: transparent; border-radius: 18px;}""")
        self._more_button.setIcon(self.icon_more)
        self._more_button.setIconSize(QSize(20, 20))

    def set_menu(self) -> None:
        self._menu = QMenu(self)
        self._menu.setGeometry(QRect(420, 13, 36, 36))
        self._menu.addAction("Add to queue", lambda: Event("add_to_queue", self.song, self_fire=True))
        for playlist_link in self._playlist_links:
            self._add_playlist_to_menu(self.song, playlist_link)
        self._menu.setStyleSheet("""QMenu {
                                    background-color: rgb(60, 60, 60); 
                                    color: white;
                                    } 
                                    QMenu::item:selected {
                                    background-color: rgb(100, 100, 100);
                                    }""")
        self._more_button.setMenu(self._menu)

    def _add_playlist_to_menu(self, song: Song, playlist_link: str) -> None:
        self._menu.addAction(
            f"Add to Playlist: {playlist_link}",
            lambda: Event("add_to_playlist", song, playlist_link, self_fire=True),
        )


class SongPlaylistContainer(QFrame):
    """
    Summary:
    This class represents a song container inside the playlist widget. It contains an image, song name, artist name,
    duration, more button, and index.
    On mouse enter the color changes, and the play button appears. The user can play the song by either clicking the
    play button, or double-clicking the container.

    Usage:
    Create an instance if this class and add it to its container.
    """

    def __init__(
        self,
        parent: QObject,
        song: Song,
        image: QtGui.QPixmap,
        playlist_links: List[str],
        current_playlist: str,
        index: int,
        icon_play=QIcon(),
        icon_more=QIcon(),
        icon_empty=QIcon(),
    ):
        QFrame.__init__(self, parent)
        self._menu = None
        self._playlist_links = None
        self._icon_play = icon_play
        self._icon_more = icon_more
        self._icon_empty = icon_empty
        self._current_playlist = current_playlist
        self.set_playlist_links(playlist_links)
        self._song = song
        self._image = image
        self._set_self_params()
        self._set_play_this_button_params(index)
        self._set_small_img_container()
        self._set_song_name_inner()
        self._set_artist_name_inner()
        self._set_more_button()
        self.set_menu()
        self._set_playlist_time_label()

    def set_playlist_links(self, playlist_links: List[str]) -> None:
        self._playlist_links = playlist_links

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.setStyleSheet("background-color: rgb(60, 10, 60); border-radius: 6px;")
        self._play_this_button.setIcon(self._icon_play)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.setStyleSheet("background-color: transparent; border-radius: 6px;")
        self._play_this_button.setIcon(self._icon_empty)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        Event("internal_request", "play_this", self._song, self_fire=True)

    def _set_self_params(self) -> None:
        self.setFixedSize(470, 46)
        self.setStyleSheet("background-color: transparent; border-radius: 6px;")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

    def _set_play_this_button_params(self, index: int) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self._play_this_button = QToolButton(self)
        self._play_this_button.setGeometry(QRect(11, 11, 24, 24))
        self._play_this_button.setStyleSheet("background-color: transparent; ")
        self._play_this_button.setFont(font)
        self._play_this_button.clicked.connect(
            lambda: Event("internal_request", "play_this", self._song, self_fire=True)
        )
        self._play_this_button.setText(str(index))

    def _set_small_img_container(self) -> None:
        self._small_img_container = QLabel(self)
        self._small_img_container.setGeometry(QRect(44, 1, 44, 44))
        self._small_img_container.setStyleSheet("background-color: rgb(85, 85, 127); border-radius: 0px;")
        self._small_img_container.setScaledContents(True)
        self._small_img_container.setPixmap(self._image)

    def _set_song_name_inner(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self._song_name_inner = QLabel(self)
        self._song_name_inner.setGeometry(QRect(94, 2, 281, 20))
        self._song_name_inner.setFont(font)
        self._song_name_inner.setStyleSheet("background-color: transparent; color: white;")
        self._song_name_inner.setText(self._song.song_name)

    def _set_artist_name_inner(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self._artist_name_inner = QLabel(self)
        self._artist_name_inner.setGeometry(QRect(94, 24, 281, 20))
        self._artist_name_inner.setFont(font)
        self._artist_name_inner.setStyleSheet("background-color: transparent; color: rgb(85, 255, 255);")
        self._artist_name_inner.setText(self._song.artist_name)

    def _set_more_button(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self._more_button = QPushButton(self)
        self._more_button.setObjectName("more_button")
        self._more_button.setGeometry(QRect(430, 8, 30, 30))
        self._more_button.setFont(font)
        self._more_button.setStyleSheet(
            "QPushButton::menu-indicator { image: none; } QPushButton {background-color: transparent;}"
        )
        self._more_button.setIcon(self._icon_more)

    def set_menu(self) -> None:
        self._menu = QMenu(self)
        self._menu.setGeometry(QRect(420, 13, 36, 36))
        self._menu.addAction("Add to queue", lambda: Event("add_to_queue", self._song, self_fire=True))
        self._menu.addAction(
            "Remove from playlist",
            lambda: Event("remove_from_playlist", self._song.song_id, self_fire=True),
        )
        for playlist_link in self._playlist_links:
            if playlist_link != self._current_playlist:
                SongPlaylistContainer._add_playlist_to_menu(self._menu, self._song, playlist_link)
        self._menu.setStyleSheet("""QMenu {background-color: rgb(60, 60, 60); color: white;} 
            QMenu::item:selected {background-color: rgb(100, 100, 100);}""")
        self._more_button.setMenu(self._menu)

    def _set_playlist_time_label(self) -> None:
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self._playlist_time_label = QLabel(self)
        self._playlist_time_label.setGeometry(QRect(375, 13, 34, 20))
        self._playlist_time_label.setFont(font)
        self._playlist_time_label.setStyleSheet("color: white; background-color: transparent;")
        self._playlist_time_label.setText(self._song.duration_string)

    @staticmethod
    def _add_playlist_to_menu(menu, song: Song, playlist_link: str) -> None:
        menu.addAction(
            f"Add to Playlist: {playlist_link}",
            lambda: Event("add_to_playlist", song, playlist_link, self_fire=True),
        )


class RecommendationReceiver(QObject):
    """
    Summary:
    This class represents a recommendation receiver. Use its receive_recommendation() method to receive
    a recommendation from another thread. Once this method is called, the object will fire a pyqtSignal to
    dynamically create QObjects.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with receive_recommendation().
    """

    recommendation_received = pyqtSignal(Song)

    def __init__(self):
        QObject.__init__(self)
        self._recommendation = None

    def fire(self) -> None:
        self.recommendation_received.emit(self._recommendation)

    def receive_recommendation(self, recommendation: Song) -> None:
        self._recommendation = recommendation
        self.fire()


class RecommendationRemover(QObject):
    """
    Summary:
    This class represents a pyqt remover for recommendations.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with fire().
    """

    command_received = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def fire(self) -> None:
        self.command_received.emit()


class SongReceiver(QObject):
    """
    Summary:
    This class represents a song receiver. It uses pyqtSignal() to get songs from separate thread
    and create QObjects.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with receive_song().
    """

    song_received = pyqtSignal(Song)

    def __init__(self):
        QObject.__init__(self)
        self._song = None

    def fire(self) -> None:
        self.song_received.emit(self._song)

    def receive_song(self, song: Song) -> None:
        self._song = song
        self.fire()


class SongRemover(QObject):
    """
    Summary:
    This class represents a remover for searched songs. It uses pyqtSignal().

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with fire().
    """

    command_received = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def fire(self) -> None:
        self.command_received.emit()


class PlaylistSongReceiver(QObject):
    """
    Summary:
    This class represents a playlist song receiver that receives songs from a separate thread and
    dynamically creates QObjects.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with receive_song().
    """

    playlist_song_received = pyqtSignal(Song, str, int)

    def __init__(self):
        QObject.__init__(self)
        self._playlist_song = None
        self._current_playlist = None
        self._index = None

    def fire(self) -> None:
        self.playlist_song_received.emit(self._playlist_song, self._current_playlist, self._index)

    def receive_song(self, playlist_song: Song, current_playlist: str, index: int) -> None:
        self._playlist_song = playlist_song
        self._current_playlist = current_playlist
        self._index = index
        self.fire()


class PlaylistSongRemover(QObject):
    """
    Summary:
    This class represents a remover for playlist songs. It is used to delete objects.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with fire().
    """

    command_received = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def fire(self) -> None:
        self.command_received.emit()


class PlaylistLinkReceiver(QObject):
    """
    Summary:
    This class represents a receiver for playlist links that are received from
    a different thread, and it helps dynamically create QObjects.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with receive_playlist_link().
    """

    playlist_link_received = pyqtSignal(str, bool)

    def __init__(self):
        QObject.__init__(self)
        self._playlist_link = None
        self._active = False

    def fire(self) -> None:
        self.playlist_link_received.emit(self._playlist_link, self._active)

    def receive_playlist_link(self, playlist_link: str, active=False) -> None:
        self._playlist_link = playlist_link
        self._active = active
        self.fire()


class PlaylistLinkRemover(QObject):
    """
    Summary:
    This class represents a remover for playlist links. It helps delete playlist links from
    a separate thread.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with fire().
    """

    command_received = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def fire(self) -> None:
        self.command_received.emit()


class QueueReceiver(QObject):
    """
    Summary:
    This class represents a receiver for queue songs. It allows receiving songs from another thread,
    and dynamically creating QObjects on the main thread.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with receive_song().
    """

    queue_song_received = pyqtSignal(Song, int)

    def __init__(self):
        QObject.__init__(self)
        self._song = None
        self._current_index = None

    def fire(self) -> None:
        self.queue_song_received.emit(self._song, self._current_index)

    def receive_song(self, song: Song, current_index: int) -> None:
        self._song = song
        self._current_index = current_index
        self.fire()


class QueueRemover(QObject):
    """
    Summary:
    This class represents a remover for queue songs. It deletes QObjects from
    a separate thread.

    Usage:
    Create an object of this class and connect it to a method you want to call when
    a signal occurs. You can emit the signal with fire().
    """

    command_received = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def fire(self) -> None:
        self.command_received.emit()


class Window(QWidget, Listener):
    """
    Summary:
    This is the main class of UI. This class represents the window. It inherits QWidget.
    It contains static and dynamic entities. Dynamic entities are created using Receivers that
    use pyqtSignal().

    Usage:
    Create an instance of this class and use its public methods to interact.

    display_recommendations() - to dynamically create recommendation in home widget.

    display_playlist_songs() - to dynamically create playlist songs in playlist widget.

    display_playlist_link() - to dynamically create playlists containers in playlist links widget.

    display_queue() - to dynamically create queue songs in queue widget.

    display_songs() - to dynamically create songs in search widget.

    update_song_info() - to change song info.
    """

    def __init__(self):
        QWidget.__init__(self)
        Listener.__init__(self)
        self._set_self_params()
        self._create_icons()
        # CREATE AREAS
        self._create_stacked_widget()
        self._create_home_widget()
        self._create_playlist_widget()
        self._create_search_widget()
        self._create_playlist_links_area()
        self._create_queue_area()
        self._stackedWidget.setCurrentWidget(self._home_widget)
        # CREATE AREAS

        # CREATE STATIC ENTITIES
        self._create_progress_bar()
        self._create_previous_button()
        self._create_next_button()
        self._create_play_pause_button()
        self._create_create_playlist_button()
        self._create_delete_queue_button()
        self._create_repeat_button()
        self._create_shuffle_button()
        self._create_home_button()
        self._create_search_button()
        self._create_current_song_data_area()
        self._set_playlist_input()
        # CREATE STATIC ENTITIES

        # PYQT SIGNALS
        self.song_receiver = SongReceiver()
        self.song_remover = SongRemover()
        self.song_receiver.song_received.connect(self.display_one_song_search)
        self.song_remover.command_received.connect(self.delete_search)

        self.queue_receiver = QueueReceiver()
        self.queue_remover = QueueRemover()
        self.queue_receiver.queue_song_received.connect(
            self.display_one_song_queue
        )  # Add
        self.queue_remover.command_received.connect(self.delete_queue)

        self.playlist_link_receiver = PlaylistLinkReceiver()
        self.playlist_link_remover = PlaylistLinkRemover()
        self.playlist_link_receiver.playlist_link_received.connect(
            self.display_one_playlist_link
        )
        self.playlist_link_remover.command_received.connect(self.delete_playlist_links)

        self.playlist_song_receiver = PlaylistSongReceiver()
        self.playlist_song_remover = PlaylistSongRemover()
        self.playlist_song_receiver.playlist_song_received.connect(
            self.display_one_song_playlist
        )
        self.playlist_song_remover.command_received.connect(self.delete_playlist_songs)

        self.recommendation_receiver = RecommendationReceiver()
        self.recommendation_remover = RecommendationRemover()
        self.recommendation_receiver.recommendation_received.connect(
            self.display_one_recommendation
        )
        self.recommendation_remover.command_received.connect(
            self.delete_recommendations
        )
        # PYQT SIGNALS

        self.playlist_links = []

    def _set_self_params(self) -> None:
        self.setWindowTitle("Application")
        self.setFixedHeight(800)
        self.setFixedWidth(1300)
        self.show()
        self.x = QVBoxLayout(self)
        self.y = QFrame(self)
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.setWindowOpacity(1)
        self.setStyleSheet("""QWidget{
                            background-color: rgb(22, 22, 22);
                            color: white;
                            font-family: Arial;
                            }
                            QScrollArea{
                            background-color: transparent;
                            border: 0px;
                            }
                            QScrollBar:vertical{
                            background-color: transparent;
                            border: 0px;
                            }
                            QScrollBar::handle:vertical{
                            background-color: rgb(0, 170, 127);
                            border-radius: 6px;
                            }
                            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical{
                            background: none;
                            }
                            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical{
                            border: none;
                            background: none;
                            }
                            QScrollBar::add-line:vertical{
                            border: none;
                            background: none;
                            }
                            QScrollBar::sub-line:vertical {
                            border: none;
                            background: none;
                            }
                            """)

    def _create_progress_bar(self) -> None:
        self._progress_bar = QSlider(self)
        self._progress_bar.setGeometry(QRect(385, 770, 530, 22))
        self._progress_bar.setStyleSheet("""QSlider::groove:horizontal {
                                        background-color: rgb(130, 130, 130);
                                        height: 5px; 
                                        border-radius: 2px;
                                        }
                                        QSlider::handle:horizontal {
                                        background-color: white;
                                        width: 14px; 
                                        line-height: 8px; 
                                        margin-top: -5px; 
                                        margin-bottom: -5px; 
                                        border-radius: 7px; 
                                        }
                                        QSlider::handle:horizontal:hover { 
                                        border-radius: 7px;
                                        background-color: rgb(0, 230, 127); 
                                        }
                                        QSlider {
                                        background-color: transparent;
                                        }
                                        QSlider::sub-page:horizontal {
                                        border-radius: 2px;
                                        background-color:rgb(0, 170, 127);
                                        }
                                        """)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(999)
        self._progress_bar.setValue(1)
        self._progress_bar.setSliderPosition(1)
        self._progress_bar.setTracking(False)
        self._progress_bar.setOrientation(Qt.Horizontal)
        self._progress_bar.valueChanged.connect(
            lambda: Event("set_progress", self._progress_bar.value(), self_fire=True)
        )
        self._progress_bar.sliderPressed.connect(lambda: Event("slider_pressed", self_fire=True))
        self._progress_bar.sliderReleased.connect(lambda: Event("slider_released", self_fire=True))
        self._label_time_passed = QLabel(self)
        self._label_time_passed.setGeometry(QRect(348, 772, 30, 16))
        self._label_time_passed.setStyleSheet("color: white; background-color: transparent;")
        self._label_time_passed.setScaledContents(False)
        self._label_time_passed.setText("00:00")
        self._label_length = QLabel(self)
        self._label_length.setGeometry(QRect(930, 772, 30, 16))
        self._label_length.setStyleSheet("color: white; background-color: transparent;")
        self._label_length.setScaledContents(False)
        self._label_length.setText("00:00")
        self._label_time_passed.show()
        self._label_length.show()
        self._progress_bar.show()

    def _create_home_button(self) -> None:
        self._home_button = QToolButton(self)
        self._home_button.setGeometry(QRect(490, 45, 130, 50))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self._home_button.setFont(font)
        self._home_button.setCursor(QCursor(Qt.PointingHandCursor))
        self._home_button.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 16px; border: 0px solid  rgb(0, 170, 127);"
        )
        self._home_button.setIconSize(QSize(100, 80))
        self._home_button.setText("Home")
        self._home_button.clicked.connect(self.show_home_widget)
        self._home_button.show()

    def _create_search_button(self) -> None:
        self._search_button = QToolButton(self)
        self._search_button.setGeometry(QRect(680, 45, 130, 50))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self._search_button.setFont(font)
        self._search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self._search_button.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 16px; border: 0px solid  rgb(0, 170, 127);"
        )
        self._search_button.setIconSize(QSize(60, 60))
        self._search_button.setText("Search")
        self._search_button.clicked.connect(self.show_search_widget)
        self._search_button.show()

    def _create_create_playlist_button(self) -> None:
        self._create_playlist_button = ToolButton(
            self, self._icon_add_default, self._icon_add_hover
        )
        self._create_playlist_button.setGeometry(QRect(114, 120, 30, 30))
        self._create_playlist_button.setStyleSheet("background-color: transparent; border-radius: 14px;")
        self._create_playlist_button.setIcon(self._icon_add_default)
        self._create_playlist_button.setIconSize(QSize(24, 24))
        self._create_playlist_button.clicked.connect(
            self.show_create_new_playlist_dialog
        )
        self._create_playlist_button.show()

    def _create_delete_queue_button(self) -> None:
        self._delete_queue_button = ToolButton(
            self, self._icon_delete_default, self._icon_delete_hover
        )
        self._delete_queue_button.setGeometry(QRect(1114, 120, 30, 30))
        self._delete_queue_button.setStyleSheet("background-color: transparent; border-radius: 14px;")
        self._delete_queue_button.setIcon(self._icon_delete_default)
        self._delete_queue_button.setIconSize(QSize(24, 24))
        self._delete_queue_button.clicked.connect(lambda: Event("delete_queue", self_fire=True))
        self._delete_queue_button.show()

    def _create_previous_button(self) -> None:
        self._button_previous = ToolButton(self, self._icon_previous_default, self._icon_previous_hover)
        self._button_previous.setGeometry(QRect(576, 710, 36, 36))
        self._button_previous.setStyleSheet("background-color: transparent; border-radius: 18px;")
        self._button_previous.setIcon(self._icon_previous_default)
        self._button_previous.setIconSize(QSize(25, 25))
        self._button_previous.clicked.connect(lambda: Event("internal_request", "previous", self_fire=True))
        self._button_previous.show()

    def _create_play_pause_button(self) -> None:
        self._button_play_pause = QToolButton(self)
        self._button_play_pause.setGeometry(QRect(632, 710, 36, 36))
        self._button_play_pause.setStyleSheet("background-color: transparent;")
        self._button_play_pause.setIcon(self._icon_play)
        self._button_play_pause.setIconSize(QSize(25, 25))
        self._button_play_pause.clicked.connect(lambda: Event("play_pause", self_fire=True))
        self._button_play_pause.setShortcut(QCoreApplication.translate("Application", "Space", None))
        self._button_play_pause.show()

    def _create_next_button(self) -> None:
        self._button_next = ToolButton(self, self._icon_next_default, self._icon_next_hover)
        self._button_next.setGeometry(QRect(688, 710, 36, 36))
        self._button_next.setStyleSheet("background-color: transparent; border-radius: 18px;")
        self._button_next.setIcon(self._icon_next_default)
        self._button_next.setIconSize(QSize(25, 25))
        self._button_next.clicked.connect(lambda: Event("internal_request", "next", self_fire=True))
        self._button_next.show()

    def _create_repeat_button(self) -> None:
        self._button_repeat = RepeatButton(
            self,
            self._icon_repeat_many_off,
            self._icon_repeat_many_on,
            self._icon_repeat_one,
        )
        self._button_repeat.setGeometry(QRect(740, 710, 36, 36))
        self._button_repeat.setStyleSheet("background-color: transparent; border-radius: 18px;")
        self._button_repeat.setIcon(self._icon_repeat_many_off)
        self._button_repeat.setIconSize(QSize(20, 20))
        self._button_repeat.show()

    def _create_shuffle_button(self) -> None:
        self._button_shuffle = ShuffleButton(self, self._icon_shuffle_off, self._icon_shuffle_on)
        self._button_shuffle.setGeometry(QRect(520, 710, 36, 36))
        self._button_shuffle.setStyleSheet("background-color: transparent; border-radius: 18px;")
        self._button_shuffle.setIcon(self._icon_shuffle_off)
        self._button_shuffle.setIconSize(QSize(20, 20))
        self._button_shuffle.show()

    def _create_playlist_links_area(self) -> None:
        self._verticalFramePlaylistLinks = QFrame(self)
        self._verticalFramePlaylistLinks.setGeometry(QRect(1250, 40, 16, 16))
        self._verticalFramePlaylistLinks.setStyleSheet("background-color: transparent;")
        self._verticalLayoutPlaylistLinks = QVBoxLayout(self._verticalFramePlaylistLinks)
        self._verticalLayoutPlaylistLinks.setSpacing(4)
        self._verticalLayoutPlaylistLinks.setSizeConstraint(QLayout.SetMinimumSize)
        self._verticalLayoutPlaylistLinks.setContentsMargins(0, 10, 0, 0)
        self._verticalLayoutPlaylistLinks.setAlignment(QtCore.Qt.AlignTop)

        self._scrollAreaPlaylistLinks = QScrollArea(self)
        self._scrollAreaPlaylistLinks.setGeometry(QRect(30, 160, 320, 340))
        self._scrollAreaPlaylistLinks.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scrollAreaPlaylistLinks.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollAreaPlaylistLinks.setWidgetResizable(True)
        self._scrollAreaPlaylistLinks.setWidget(self._verticalFramePlaylistLinks)

        self._playlists_label = QLabel(self)
        self._playlists_label.setObjectName("label_2")
        self._playlists_label.setGeometry(QRect(30, 120, 8_1, 30))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self._playlists_label.setFont(font)
        self._playlists_label.setStyleSheet("color: white; background-color: transparent;")
        self._playlists_label.setText("Playlists")
        self._playlists_label.show()
        self._scrollAreaPlaylistLinks.show()

    def _create_queue_area(self) -> None:
        self._verticalFrameQueue = QFrame(self)
        self._verticalFrameQueue.setGeometry(QRect(1230, 40, 16, 16))
        self._verticalFrameQueue.setStyleSheet("background-color:transparent;")
        self._verticalLayoutQueue = QVBoxLayout(self._verticalFrameQueue)
        self._verticalLayoutQueue.setSpacing(10)
        self._verticalLayoutQueue.setSizeConstraint(QLayout.SetMinimumSize)
        self._verticalLayoutQueue.setContentsMargins(0, 10, 0, 0)
        self._verticalLayoutQueue.setAlignment(QtCore.Qt.AlignTop)

        self._scrollAreaQueue = QScrollArea(self)
        self._scrollAreaQueue.setGeometry(QRect(950, 160, 320, 550))
        self._scrollAreaQueue.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scrollAreaQueue.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollAreaQueue.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self._scrollAreaQueue.setWidgetResizable(True)
        self._scrollAreaQueue.setWidget(self._verticalFrameQueue)

        self._next_from_queue_label = QLabel(self)
        self._next_from_queue_label.setGeometry(QRect(952, 120, 161, 31))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self._next_from_queue_label.setFont(font)
        self._next_from_queue_label.setStyleSheet("color: white; background-color: transparent;")
        self._next_from_queue_label.setText("Next from queue")
        self._next_from_queue_label.show()
        self._scrollAreaQueue.show()

    def _create_stacked_widget(self) -> None:
        self._stackedWidget = QStackedWidget(self)
        self._stackedWidget.setGeometry(QRect(380, 120, 540, 541))
        self._stackedWidget.show()

    def _create_home_widget(self) -> None:
        self._home_widget = QWidget(self)
        self._gridFrameRecommendations = QFrame(self._home_widget)
        self._gridFrameRecommendations.setGeometry(QRect(80, 80, 380, 440))
        self._gridFrameRecommendations.setStyleSheet("background-color: transparent;")
        self._gridLayoutRecommendations = QGridLayout(self._gridFrameRecommendations)
        self._gridLayoutRecommendations.setSizeConstraint(QLayout.SetFixedSize)
        self._gridLayoutRecommendations.setHorizontalSpacing(62)
        self._gridLayoutRecommendations.setVerticalSpacing(50)
        self._label_recommended = QLabel(self._home_widget)
        self._label_recommended.setGeometry(QRect(200, 30, 140, 20))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self._label_recommended.setFont(font)
        self._label_recommended.setStyleSheet("color: rgb(0, 255, 255);")
        self._label_recommended.setText("Recommended")
        self._stackedWidget.addWidget(self._home_widget)

    def _create_playlist_widget(self) -> None:
        self._verticalFramePlaylist = QFrame(self)
        self._verticalFramePlaylist.setGeometry(QRect(1270, 40, 16, 16))
        self._verticalFramePlaylist.setStyleSheet("background-color: transparent;")
        self._verticalLayoutPlaylist = QVBoxLayout(self._verticalFramePlaylist)
        self._verticalLayoutPlaylist.setSpacing(10)
        self._verticalLayoutPlaylist.setSizeConstraint(QLayout.SetMinimumSize)
        self._verticalLayoutPlaylist.setContentsMargins(0, 10, 0, 0)
        self._verticalLayoutPlaylist.setAlignment(QtCore.Qt.AlignTop)

        self._playlist_widget = QWidget(self)
        self._playlist_name_label = QLabel(self._playlist_widget)
        self._playlist_name_label.setGeometry(QRect(60, 10, 321, 34))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        self._playlist_name_label.setFont(font)
        self._playlist_name_label.setStyleSheet("color: rgb(0, 255, 255); background-color: transparent;")
        self._playlist_name_label.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)
        self._playlist_name_label.setText("Playlist Name")
        self._scrollAreaPlaylist = QScrollArea(self._playlist_widget)
        self._scrollAreaPlaylist.setObjectName("scrollAreaPlaylist")
        self._scrollAreaPlaylist.setGeometry(QRect(20, 90, 500, 440))
        self._scrollAreaPlaylist.setStyleSheet("")
        self._scrollAreaPlaylist.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scrollAreaPlaylist.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollAreaPlaylist.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self._scrollAreaPlaylist.setWidgetResizable(True)
        self._scrollAreaPlaylist.setWidget(self._verticalFramePlaylist)

        self._more_playlist_button = QPushButton(self._playlist_widget)
        self._more_playlist_button.setObjectName("more_playlist_button")
        self._more_playlist_button.setGeometry(QRect(450, 50, 34, 34))
        self._more_playlist_button.setStyleSheet("QPushButton {background-color: transparent; color: black;}")
        self._more_playlist_button.setIcon(self._icon_more)
        self._more_playlist_button.setIconSize(QSize(30, 30))
        self._search_entry_playlist = QLineEdit(self._playlist_widget)
        self._search_entry_playlist.setObjectName("search_entry_playlist")
        self._search_entry_playlist.setGeometry(QRect(29, 50, 401, 30))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        self._search_entry_playlist.setFont(font)
        self._search_entry_playlist.setStyleSheet("background-color: white; color: black; border-radius: 4px;")
        self._search_entry_playlist.setPlaceholderText("Search in playlist")
        self._search_entry_playlist.textChanged.connect(
            lambda: Event("current_playlist_search", self._search_entry_playlist.text(), self_fire=True)
        )
        self._start_playlist_button = QToolButton(self._playlist_widget)
        self._start_playlist_button.setGeometry(QRect(22, 10, 34, 34))
        self._start_playlist_button.setStyleSheet("background-color: transparent;")
        self._start_playlist_button.setIcon(self._icon_play)
        self._start_playlist_button.setIconSize(QSize(22, 22))
        self._stackedWidget.addWidget(self._playlist_widget)

    def _create_search_widget(self) -> None:
        self._verticalFrameSearch = QFrame(self)
        self._verticalFrameSearch.setGeometry(QRect(1210, 40, 16, 16))
        self._verticalFrameSearch.setStyleSheet("background-color:transparent;")
        self._verticalLayoutSearch = QVBoxLayout(self._verticalFrameSearch)
        self._verticalLayoutSearch.setSpacing(10)
        self._verticalLayoutSearch.setSizeConstraint(QLayout.SetMinimumSize)
        self._verticalLayoutSearch.setContentsMargins(0, 10, 0, 0)
        self._verticalLayoutSearch.setAlignment(QtCore.Qt.AlignTop)
        self._search_widget = QWidget(self)
        self._scrollAreaSearch = QScrollArea(self._search_widget)
        self._scrollAreaSearch.setGeometry(QRect(20, 90, 500, 440))
        self._scrollAreaSearch.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scrollAreaSearch.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollAreaSearch.setWidgetResizable(True)
        self._scrollAreaSearch.setWidget(self._verticalFrameSearch)
        self._search_entry = QLineEdit(self._search_widget)
        self._search_entry.setGeometry(QRect(22, 40, 468, 40))
        self._search_entry.setPlaceholderText("Search song, artist")
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        self._search_entry.setFont(font)
        self._search_entry.setStyleSheet(
            "background-color: white; color: black; border-radius: 6px;"
        )
        self._search_entry.textChanged.connect(
            lambda: Event("network_request", "search", "user", self._search_entry.text(), self_fire=True)
        )
        self._stackedWidget.addWidget(self._search_widget)

    def _create_current_song_data_area(self) -> None:
        self._image_container = QLabel(self)
        self._image_container.setGeometry(QRect(30, 520, 200, 200))
        self._image_container.setStyleSheet("background-color: transparent;")
        self._image_container.show()
        self._song_name = QLabel(self)
        self._song_name.setGeometry(QRect(40, 730, 300, 24))
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self._song_name.setFont(font)
        self._song_name.setStyleSheet("background-color: transparent; color: white;")
        self._song_name.show()
        self._artist_name = QLabel(self)
        self._artist_name.setGeometry(QRect(40, 755, 300, 24))
        font1 = QFont()
        font1.setFamily("Arial")
        font1.setPointSize(11)
        self._artist_name.setFont(font1)
        self._artist_name.setStyleSheet("background-color: transparent; color: rgb(85, 255, 255);")
        self._artist_name.show()

    def update_repeat_state(self, state: int) -> None:
        """
        Call this method to manually change the state of repeat.
        """

        self._button_repeat.set_state(state)

    def _set_playlist_input(self) -> None:
        self._start_playlist_button.clicked.connect(
            lambda: Event("internal_request", "play_current_playlist", self_fire=True)
        )
        self._more_menu = QMenu()
        self._more_menu.setGeometry(QRect(420, 13, 36, 36))
        self._more_menu.setStyleSheet("""QMenu {
                                        background-color: rgb(60, 60, 60); 
                                        color: white;
                                        } 
                                        QMenu::item:selected {
                                        background-color: rgb(100, 100, 100);
                                        }""")
        self._more_menu.addAction("Add song", self.show_search_widget)
        self._more_menu.addAction("Add to queue", lambda: Event("add_playlist_to_queue", self_fire=True))
        self._more_menu.addAction("Rename playlist", self.show_rename_current_playlist_dialog)
        self._more_menu.addAction("Delete playlist", lambda: Event("delete_current_playlist", self_fire=True))
        self._more_playlist_button.setMenu(self._more_menu)
        self._more_playlist_button.setStyleSheet("QPushButton::menu-indicator { image: none; } "
                                                 "QPushButton {background-color: transparent; color: black;}")

    def show_rename_current_playlist_dialog(self) -> None:
        """
        Call this method to display an input box asking for a name for renaming the playlist.
        """

        dialog = QInputDialog(self)
        dialog.setStyleSheet("background-color: white; color: black")
        name, ok = dialog.getText(self, "Rename", "Enter New Name:")
        if ok:
            if name:
                Event("rename_current_playlist", name, self_fire=True)

    def show_playlist_warning(self) -> None:
        """
        Call this method to display a waning box stating that playlist already exists.
        """

        playlist_warning = QMessageBox(self)
        playlist_warning.setIcon(QMessageBox.Warning)
        playlist_warning.setText("Playlist already exists. You must choose another name.")
        playlist_warning.setWindowTitle("Invalid Name")
        playlist_warning.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        playlist_warning.show()

    def show_error(self) -> None:
        """
        Call this method to display an error box stating that the name is invalid.
        """

        error = QMessageBox(self)
        error.setIcon(QMessageBox.Critical)
        error.setText("Invalid Name.")
        error.setWindowTitle("Error")
        error.setStandardButtons(QMessageBox.Ok)
        error.show()

    def show_internal_error(self) -> None:
        """
        Call this method to display an error box stating that an internal error occurred.
        """

        internal_error = QMessageBox(self)
        internal_error.setIcon(QMessageBox.Critical)
        internal_error.setText("Internal Error.")
        internal_error.setWindowTitle("Error")
        internal_error.setStandardButtons(QMessageBox.Ok)

    def show_create_new_playlist_dialog(self) -> None:
        """
        Call this method to display an input dialog box to ask for a name for the new playlist.
        """

        dialog = QInputDialog(self)
        dialog.setStyleSheet("background-color: white; color: black")
        name, ok = dialog.getText(self, "New Playlist", "Enter Name:")
        if ok:
            if name:
                Event("create_new_playlist", name, self_fire=True)

    def show_song_exists(self, song_name: str, playlist_name: str) -> None:
        """
        Call this method to display a warning box stating that the song already exists in playlist.
        """

        song_exists = QMessageBox(self)
        song_exists.setIcon(QMessageBox.Warning)
        song_exists.setText(f"{song_name} already is in {playlist_name}.")
        song_exists.setWindowTitle("Song Exists")
        song_exists.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        song_exists.show()

    def show_search_widget(self) -> None:
        """
        Call this method to show search widget.
        """

        self._stackedWidget.setCurrentWidget(self._search_widget)
        self._search_button.setStyleSheet("""background-color: rgb(35, 35, 35); 
                                            color: white; border-radius: 16px; 
                                            border: 2px solid  rgb(0, 170, 127);""")
        self._home_button.setStyleSheet("""background-color: rgb(35, 35, 35); 
                                            color: white; border-radius: 16px; 
                                            border: 0px solid  rgb(0, 170, 127);""")
        for i in range(1, len(self._verticalFramePlaylistLinks.children())):
            self._verticalFramePlaylistLinks.children()[i].set_inactive_style()

    def show_home_widget(self) -> None:
        """
        Call this method to show home widget.
        """

        self._stackedWidget.setCurrentWidget(self._home_widget)

        self._home_button.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 16px; border: 2px solid  rgb(0, 170, 127);"
        )
        self._search_button.setStyleSheet("""background-color: rgb(35, 35, 35); 
                                            color: white; border-radius: 16px; 
                                            border: 0px solid  rgb(0, 170, 127);""")

        for i in range(1, len(self._verticalFramePlaylistLinks.children())):
            self._verticalFramePlaylistLinks.children()[i].set_inactive_style()
        Event("internal_request", "home_handler", self_fire=True)

    def show_playlist_widget(self, playlist_link: str) -> None:
        """
        Call this method to show playlist widget.
        """

        self._stackedWidget.setCurrentWidget(self._playlist_widget)
        self._search_button.setStyleSheet(
            "background-color: rgb(35, 35, 35); color: white; border-radius: 16px; border: 0px solid  rgb(0, 170, 127);"
        )
        self._home_button.setStyleSheet("""background-color: rgb(35, 35, 35); 
                color: white; border-radius: 16px; 
                border: 0px solid  rgb(0, 170, 127);""")
        for i in range(1, len(self._verticalFramePlaylistLinks.children())):
            if (
                self._verticalFramePlaylistLinks.children()[i].get_playlist_link()
                == playlist_link
            ):
                self._verticalFramePlaylistLinks.children()[i].set_active_style()
            else:
                self._verticalFramePlaylistLinks.children()[i].set_inactive_style()

    def send_progress_info(self, progress: int, time_passed_string: str) -> None:
        """
        Call this method to update the slider and time passed label with the new parameters.
        """

        self._progress_bar.setSliderPosition(progress)
        self._label_time_passed.setText(time_passed_string)

    @staticmethod
    def from_bytes_to_pixmap(pixmap_bytes: bytes) -> QtGui.QPixmap:
        """
        Converts bytes to pixmap using loadFromData().
        """

        byte_array = QtCore.QByteArray(pixmap_bytes)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(byte_array, "PNG")
        return pixmap

    def update_song_info(self, song_name: str, artist_name: str, duration_string: str, image_binary: bytes) -> None:
        """
        Update current song info with the specified parameters.
        """

        image = Window.from_bytes_to_pixmap(image_binary)
        self._song_name.setText(song_name)
        self._artist_name.setText(artist_name)
        self._label_length.setText(duration_string)
        self._image_container.setPixmap(image)

    def display_recommendations(self, recommendations: List[Song]) -> None:
        """
        This method takes a list of recommendations (Song) and dynamically creates recommendation
        containers on the screen.
        """

        if recommendations:
            self.recommendation_remover.fire()
            for recommendation in recommendations:
                self.recommendation_receiver.receive_recommendation(recommendation)
        else:
            self.recommendation_remover.fire()

    def display_songs(self, songs: List[Song]) -> None:
        """
        This method takes a list of songs (Song) and dynamically creates song containers on the screen.
        """

        if songs:
            self.song_remover.fire()
            for song in songs:
                self.song_receiver.receive_song(song)  # Signal for PyQt custom event
        else:
            self.song_remover.fire()  # Signal for PyQt custom event

    def display_queue(self, queue) -> None:
        """
        This method takes a list of queue songs (Song) and dynamically creates queue containers on the screen.
        """

        if queue:
            self.queue_remover.fire()
            for queue_song in queue:
                self.queue_receiver.receive_song(queue_song[0], queue_song[1])  # Song and index
        else:
            self.queue_remover.fire()

    def get_active_playlist_link(self) -> str:
        """
        This method will find the current active playlist link and return it.
        """

        active_link = ""
        if self._stackedWidget.currentWidget().objectName() == "playlist_widget":
            for i in range(1, len(self._verticalFramePlaylistLinks.children())):
                if self._verticalFramePlaylistLinks.children()[i].is_active():
                    active_link = self._verticalFramePlaylistLinks.children()[i].get_playlist_link()
        return active_link

    def display_playlist_links(self, playlist_links: List[str], mode="", **kwargs) -> None:
        """
        This method will display playlist links. If the user renames the playlist, that playlist will
        still be active. If the user creates a new playlist, that playlist will be active.
        """

        if playlist_links:
            active_link = self.get_active_playlist_link()
            if mode == "rename":
                active_link = kwargs["active"]

            elif mode == "new":
                active_link = kwargs["active"]
                self.update_playlist_widget(active_link)
                self.show_playlist_widget(active_link)

            self.playlist_link_remover.fire()
            self.playlist_links.clear()
            for playlist_link in playlist_links:
                if playlist_link == active_link:
                    # If current widget and this playlist link, set it to active again
                    self.playlist_link_receiver.receive_playlist_link(playlist_link, active=True)
                else:
                    self.playlist_link_receiver.receive_playlist_link(playlist_link, active=False)
                self.playlist_links.append(playlist_link)
        else:
            self.playlist_link_remover.fire()
            self.playlist_links.clear()

    def display_playlist_songs(self, playlist_songs: List[Song], current_playlist: str) -> None:
        """
        This method takes a list of playlist songs (Song) and the current_playlist. It then dynamically
        creates playlist songs objects on the screen.
        """

        if playlist_songs:
            self.playlist_song_remover.fire()
            index = 1
            for playlist_song in playlist_songs:
                self.playlist_song_receiver.receive_song(
                    playlist_song, current_playlist, index
                )
                index += 1
        else:
            self.playlist_song_remover.fire()

    @pyqtSlot(Song, int)
    def display_one_song_queue(self, song: Song, current_index: int) -> None:
        """
        This method will add a single song container to the queue area.
        """

        queue_container = QFrame(self._verticalFrameQueue)
        queue_container.setFixedHeight(44)
        queue_container.setFixedWidth(290)
        queue_container.setStyleSheet("background-color: rgb(35, 35, 35); color: black; border-radius: 6px;")
        queue_container.setFrameShape(QFrame.StyledPanel)
        queue_container.setFrameShadow(QFrame.Raised)

        song_name_queue = QLabel(queue_container)
        song_name_queue.setObjectName("song_name_queue")
        song_name_queue.setGeometry(QRect(10, 1, 161, 20))
        font1 = QFont()
        font1.setFamily("Arial")
        font1.setPointSize(11)
        song_name_queue.setFont(font1)
        song_name_queue.setStyleSheet("background-color: transparent; color: white; border: 0px;")
        song_name_queue.setText(song.song_name)

        artist_name_queue = QLabel(queue_container)
        artist_name_queue.setObjectName("artist_name_queue")
        artist_name_queue.setGeometry(QRect(10, 23, 161, 20))
        font3 = QFont()
        font3.setFamily("Arial")
        font3.setPointSize(10)
        artist_name_queue.setFont(font3)
        artist_name_queue.setStyleSheet("background-color: transparent; color: rgb(85, 255, 255); border: 0px")
        artist_name_queue.setText(song.artist_name)

        queue_up_button = ToolButton(queue_container, self._icon_arrow_up_default, self._icon_arrow_up_hover)
        queue_up_button.setObjectName("queue_up_button")
        queue_up_button.setGeometry(QRect(185, 7, 30, 30))
        queue_up_button.setStyleSheet("background-color: transparent;")
        queue_up_button.clicked.connect(lambda: Event("move_up", current_index, self_fire=True))
        queue_up_button.setIcon(self._icon_arrow_up_default)

        queue_down_button = ToolButton(queue_container, self._icon_arrow_down_default, self._icon_arrow_down_hover)
        queue_down_button.setObjectName("queue_down_button")
        queue_down_button.setGeometry(QRect(220, 7, 30, 30))
        queue_down_button.setStyleSheet("background-color: transparent;")
        queue_down_button.clicked.connect(lambda: Event("move_down", current_index, self_fire=True))
        queue_down_button.setIcon(self._icon_arrow_down_default)

        remove_from_queue_button = ToolButton(queue_container, self._icon_remove_default, self._icon_remove_hover)
        remove_from_queue_button.setObjectName("remove_from_queue_button")
        remove_from_queue_button.setGeometry(QRect(255, 7, 30, 30))
        remove_from_queue_button.setStyleSheet("background-color: transparent;")
        remove_from_queue_button.clicked.connect(lambda: Event("remove_from_queue", current_index, self_fire=True))
        remove_from_queue_button.setIcon(self._icon_remove_default)

        self._verticalLayoutQueue.addWidget(queue_container)

    def _create_icons(self):
        self._icon_empty = QIcon()
        self._icon_play = QIcon()
        self._icon_play.addFile("../UI/play_green.png")
        self._icon_play_black = QIcon()
        self._icon_play_black.addFile("../UI/play_black.png")
        self._icon_pause = QIcon()
        self._icon_pause.addFile("../UI/pause.png")
        self._icon_more = QIcon()
        self._icon_more.addFile("../UI/more_white.png")
        self._icon_remove_default = QIcon()
        self._icon_remove_default.addFile("../UI/remove_default.png")
        self._icon_remove_hover = QIcon()
        self._icon_remove_hover.addFile("../UI/remove_hover.png")
        self._icon_arrow_down_default = QIcon()
        self._icon_arrow_down_default.addFile("../UI/arrow_down_default.png")
        self._icon_arrow_down_hover = QIcon()
        self._icon_arrow_down_hover.addFile("../UI/arrow_down_hover.png")
        self._icon_arrow_up_default = QIcon()
        self._icon_arrow_up_default.addFile("../UI/arrow_up_default.png")
        self._icon_arrow_up_hover = QIcon()
        self._icon_arrow_up_hover.addFile("../UI/arrow_up_hover.png")
        self._icon_add_default = QIcon()
        self._icon_add_default.addFile("../UI/add_default.png")
        self._icon_add_hover = QIcon()
        self._icon_add_hover.addFile("../UI/add_hover.png")
        self._icon_delete_default = QIcon()
        self._icon_delete_default.addFile("../UI/delete_default.png")
        self._icon_delete_hover = QIcon()
        self._icon_delete_hover.addFile("../UI/delete_hover.png")
        self._icon_previous_default = QIcon()
        self._icon_previous_default.addFile("../UI/previous_default.png")
        self._icon_previous_hover = QIcon()
        self._icon_previous_hover.addFile("../UI/previous_hover.png")
        self._icon_next_default = QIcon()
        self._icon_next_default.addFile("../UI/next_default.png")
        self._icon_next_hover = QIcon()
        self._icon_next_hover.addFile("../UI/next_hover.png")
        self._icon_repeat_many_on = QIcon()
        self._icon_repeat_many_on.addFile("../UI/repeat_many_on.png")
        self._icon_repeat_many_off = QIcon()
        self._icon_repeat_many_off.addFile("../UI/repeat_many_off.png")
        self._icon_repeat_one = QIcon()
        self._icon_repeat_one.addFile("../UI/repeat_one.png")
        self._icon_shuffle_on = QIcon()
        self._icon_shuffle_on.addFile("../UI/shuffle_on.png")
        self._icon_shuffle_off = QIcon()
        self._icon_shuffle_off.addFile("../UI/shuffle_off.png")

    @pyqtSlot(Song)
    def display_one_recommendation(self, song: Song) -> None:
        """
        This method will add one recommendation song to the recommendation area.
        """

        image = Window.from_bytes_to_pixmap(song.image_binary)
        container = RecommendationContainer(
            self._gridFrameRecommendations,
            song,
            image,
            self.playlist_links,
            self._icon_play,
        )

        current_length = len(self._gridFrameRecommendations.children())

        if current_length == 2:
            self._gridLayoutRecommendations.addWidget(container, 0, 0)
        elif current_length == 3:
            self._gridLayoutRecommendations.addWidget(container, 0, 1)
        elif current_length == 4:
            self._gridLayoutRecommendations.addWidget(container, 1, 0)
        elif current_length == 5:
            self._gridLayoutRecommendations.addWidget(container, 1, 1)

    @pyqtSlot(Song)
    def display_one_song_search(self, song: Song) -> None:
        """
        This song will add one song from search to the search area.
        """

        image = Window.from_bytes_to_pixmap(song.image_binary)
        container = SongSearchContainer(
            self._verticalFrameSearch,
            song,
            image,
            self.playlist_links,
            self._icon_play,
            self._icon_more,
        )
        self._verticalLayoutSearch.addWidget(container)

    @pyqtSlot(str, bool)
    def display_one_playlist_link(self, playlist_link: str, active: bool) -> None:
        """
        This method will add one playlist link to playlist links area.
        """

        container = PlaylistLinkContainer(self._verticalFramePlaylistLinks, playlist_link)

        if active:
            container.set_active_style()

        container.connect(lambda: self.update_playlist_widget(playlist_link))
        container.connect(lambda: self.show_playlist_widget(playlist_link))
        self._verticalLayoutPlaylistLinks.addWidget(container)

    def update_playlist_widget(self, playlist_link: str) -> None:
        """
        This method will update the playlist widget with the giver playlist_link. It will ask the controller
        to send songs for the playlist_link.
        """

        Event("update_playlist", playlist_link, self_fire=True)
        self._playlist_name_label.setText(playlist_link)

    def update_playlist_name(self, playlist_name: str) -> None:
        """
        Call this method to update only the name of the playlist on the screen.
        """

        self._playlist_name_label.setText(playlist_name)

    @pyqtSlot(Song, str, int)
    def display_one_song_playlist(self, song, current_playlist, index):
        """
        This method will add one playlist song (Song) to the playlist area.
        """

        image = Window.from_bytes_to_pixmap(song.image_binary)
        container = SongPlaylistContainer(
            self._verticalFramePlaylist,
            song,
            image,
            self.playlist_links,
            current_playlist,
            index,
            icon_play=self._icon_play,
            icon_more=self._icon_more,
            icon_empty=self._icon_empty,
        )
        self._verticalLayoutPlaylist.addWidget(container)

    @pyqtSlot()
    def delete_search(self) -> None:
        """
        Call this method to delete all song containers from search area.
        """

        for i in range(1, len(self._verticalFrameSearch.children())):
            sip.delete(self._verticalFrameSearch.children()[1])

    @pyqtSlot()
    def delete_queue(self) -> None:
        """
        Call this method to delete all queue song containers from queue area.
        """

        for i in range(1, len(self._verticalFrameQueue.children())):
            sip.delete(self._verticalFrameQueue.children()[1])

    @pyqtSlot()
    def delete_playlist_links(self) -> None:
        """
        Call this method to delete all playlist link containers from playlist links area.
        """

        for i in range(1, len(self._verticalFramePlaylistLinks.children())):
            sip.delete(self._verticalFramePlaylistLinks.children()[1])

    @pyqtSlot()
    def delete_playlist_songs(self):
        """
        Call this method to delete all playlist song containers from playlist area.
        """

        for i in range(1, len(self._verticalFramePlaylist.children())):
            sip.delete(self._verticalFramePlaylist.children()[1])

    @pyqtSlot()
    def delete_recommendations(self):
        """
        Call this method to delete all recommendations from recommendation area.
        """

        for i in range(1, len(self._gridFrameRecommendations.children())):
            sip.delete(self._gridFrameRecommendations.children()[1])

    def receive_play_pause(self, value: bool) -> None:
        """
        This method receives the state of the play/ pause state.
        """

        if not value:
            self._button_play_pause.setIcon(self._icon_play)
        else:
            self._button_play_pause.setIcon(self._icon_pause)

    def update_inner_more_menus(self, playlist_links):
        """
        This method will dynamically change inner more menus for the songs in search area.
        """

        for i in range(1, len(self._verticalFrameSearch.children())):
            self._verticalFrameSearch.children()[i].set_playlist_links(playlist_links)
            self._verticalFrameSearch.children()[i].set_menu()

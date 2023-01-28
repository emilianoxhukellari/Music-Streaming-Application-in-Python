import sys
from controller import Controller
from PyQt5.QtWidgets import QApplication


class Application(QApplication):
    """
    Summary:
    This Class represents an application containing the UI and Logic.
    It uses QApplication from pyqt5 to create a running application.

    Usage:
    To use this class you must create an object and call its run() method.
    """

    def __init__(self):
        QApplication.__init__(self, sys.argv)
        self._controller = Controller()

    def run(self):
        """
        Starts the controller and the main QApplication loop.
        """

        self._controller.run()
        try:
            sys.exit(self.exec())
        except SystemExit:
            self._controller.exit()

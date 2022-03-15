import logging
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.gui.gui import Gui

logger = logging.getLogger('logsmith')


def start_gui():
    try:
        app = QApplication(sys.argv)
        Gui(app)

        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        sys.exit(app.exec())
    except Exception:
        logging.error('unexpected error', exc_info=True)

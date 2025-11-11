import logging

from PyQt6.QtCore import QTimer

logger = logging.getLogger('logsmith')


class Repeater:
    def __init__(self):
        self._current_task = None

    def start(self, task, delay_seconds):
        delay_millies = delay_seconds * 1000
        self.stop()

        logger.info(f'start timer for {delay_seconds}s')
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(task)
        timer.start(delay_millies)
        self._current_task = timer

    def stop(self):
        if self._current_task:
            self._current_task.stop()

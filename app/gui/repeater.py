import logging
import time

from PyQt6.QtCore import QObject, QTimer

logger = logging.getLogger("logsmith")


class Repeater(QObject):
    def __init__(self):
        super().__init__()
        self._current_task = None
        self._target_epoch = None

    def start(self, task, delay_seconds):
        delay_millies = delay_seconds * 1000
        time_text = self.millis_human_readable(delay_millies)
        self.stop()

        logger.info(f"start timer for {time_text}")
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(task)
        timer.start(delay_millies)
        self._current_task = timer
        self._target_epoch = self.get_target_epoch(delay_millies)

    def stop(self):
        if self._current_task:
            self._current_task.stop()
            self._current_task.deleteLater()
            self._current_task = None
        self._target_epoch = None

    def pause_for_sleep(self):
        if self._current_task and self._current_task.isActive():
            logger.info("pause timer beause of system sleep")
            self._current_task.stop()

    def resume_after_sleep(self):
        if self._current_task and self._target_epoch is not None:
            remaining_ms = self.get_remaining_ms()
            time_text = self.millis_human_readable(remaining_ms)
            logger.info(f"resume timer after sleep with {time_text} remaining")
            self._current_task.start(remaining_ms)

    def current_time_in_ms(self):
        return round(time.time() * 1000)

    def get_target_epoch(self, delay_millies) -> int:
        return self.current_time_in_ms() + delay_millies

    def get_remaining_ms(self) -> int:
        # Do not return 0 immediatly because sometimes the machine needs to fully boot up before the times can savely trigger
        return max(5000, self._target_epoch - self.current_time_in_ms())

    def millis_human_readable(self, millis: int) -> str:
        total_minutes = millis // 60000
        hours, minutes = divmod(total_minutes, 60)
        if hours > 0:
            return f"{hours:d}h {minutes:02d}m"
        return f"{minutes}m"


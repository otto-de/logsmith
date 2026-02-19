import logging
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('logsmith')


class Task:
    def __init__(self, func: Callable, **kwargs):
        self.func = func
        self.kwargs = kwargs


class BackgroundTask(QThread):
    success_channel = pyqtSignal(object)
    failure_channel = pyqtSignal(object)
    error_channel = pyqtSignal(str)

    def __init__(
            self,
            task: Task | list[Task],
            on_success,
            on_failure,
            on_error):
        super().__init__()
        self.setObjectName("Worker")
        if task is None:
            raise ValueError('BackgroundTask requires `task`')

        self.task_list = [task] if isinstance(task, Task) else task
        if not self.task_list:
            raise ValueError('`task` must not be empty')

        self.success_channel.connect(on_success)
        self.failure_channel.connect(on_failure)
        self.error_channel.connect(on_error)

    def run(self):
        last_payload = None
        try:

            for index, task in enumerate(self.task_list):
                func: Callable = task.func
                kwargs = dict(task.kwargs or {})
                if index > 0 and 'payload' in kwargs:
                    kwargs['payload'] = last_payload

                result = func(**kwargs)
                last_payload = result.payload

                if result.was_error:
                    self.error_channel.emit(result.error_message)
                    return
                elif not result.was_success:
                    self.failure_channel.emit(result.payload)
                    return

        except Exception as e:
            logging.error('unexpected error while executing background task', exc_info=True)
            self.error_channel.emit(str(e))
        
        self.success_channel.emit(last_payload)

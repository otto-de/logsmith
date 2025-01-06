from PyQt6.QtCore import QThread, pyqtSignal


class BackgroundTask(QThread):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, on_success, on_error, kwargs):
        super().__init__()
        self.func = func
        self.on_success = on_success
        self.on_error = on_error
        self.kwargs = kwargs

        self.result.connect(self.on_success)
        self.error.connect(self.on_error)

    def run(self):
        try:
            result = self.func(**self.kwargs)
            if result.was_error:
                self.error.emit(result.error_message)
            else:
                self.result.emit(result.payload)
        except Exception as e:
            self.error.emit(str(e))

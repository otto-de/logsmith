from PyQt6.QtCore import QThread, pyqtSignal


class BackgroundTask(QThread):
    success_channel = pyqtSignal(object)
    failure_channel = pyqtSignal(object)
    error_channel = pyqtSignal(str)

    def __init__(self, func, func_kwargs, on_success, on_failure, on_error):
        super().__init__()
        self.func = func
        self.func_kwargs = func_kwargs
        self.on_success = on_success
        self.on_failure = on_failure
        self.on_error = on_error

        self.success_channel.connect(self.on_success)
        self.failure_channel.connect(self.on_failure)
        self.error_channel.connect(self.on_error)

    def run(self):
        try:
            result = self.func(**self.func_kwargs)
            if result.was_error:
                print('task error')
                self.error_channel.emit(result.error_message)
            elif not result.was_success:
                print('task failure')
                print(self.on_failure)
                print(result.payload)
                print(result.error_message)
                self.failure_channel.emit(result.payload)
            else:
                print('task success')
                self.success_channel.emit(result.payload)
        except Exception as e:
            self.error_channel.emit(str(e))

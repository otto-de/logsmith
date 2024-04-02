import logging

logger = logging.getLogger('logsmith')


class Result:
    def __init__(self):
        self.was_success = False
        self.was_error = False
        self.error_message = 'unknown'
        self.payload = {}

    def set_success(self):
        self.was_success = True

    def add_payload(self, content):
        self.payload = content

    def error(self, message):
        logger.error(message)
        self.was_error = True
        self.error_message = message

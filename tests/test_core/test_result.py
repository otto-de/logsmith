from unittest import TestCase

from app.core.result import Result


class TestResult(TestCase):
    def test___unsuccessful_by_default(self):
        result = Result()
        self.assertEqual(False, result.was_success)
        self.assertEqual(False, result.was_error)

    def test_set_success(self):
        result = Result()
        result.set_success()
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    def test_add_payload(self):
        result = Result()
        result.add_payload('test')
        self.assertEqual(False, result.was_success)
        self.assertEqual(False, result.was_error)
        self.assertEqual('test', result.payload)

    def test_error(self):
        result = Result()
        error_message = 'there was an error'
        result.error(error_message)
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual(error_message, result.error_message)

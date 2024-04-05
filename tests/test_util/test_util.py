from unittest import TestCase

from app.util.util import generate_session_name


class TestUtil(TestCase):

    def test_generate_session_name(self):
        result = generate_session_name('key-name')
        expected = 'session-token-key-name'
        self.assertEqual(expected, result)

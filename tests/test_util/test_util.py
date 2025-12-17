from unittest import TestCase

from app.util.util import generate_session_name, is_positive_int


class TestUtil(TestCase):

    def test_generate_session_name(self):
        result = generate_session_name('key-name')
        expected = 'session-token-key-name'
        self.assertEqual(expected, result)

    def test_is_positive_int__accepts_int_like_values(self):
        self.assertTrue(is_positive_int(5))
        self.assertTrue(is_positive_int('7'))
        self.assertTrue(is_positive_int(' 8 '))
        self.assertTrue(is_positive_int(0))
        self.assertTrue(is_positive_int('0'))

    def test_is_positive_int__rejects_non_digits_or_negative(self):
        self.assertFalse(is_positive_int(-1))
        self.assertFalse(is_positive_int('-2'))
        self.assertFalse(is_positive_int('abc'))
        self.assertFalse(is_positive_int('1.2'))
        self.assertFalse(is_positive_int(None))

from unittest import TestCase, mock
from unittest.mock import call

from app.core.repeater import Repeater


class TestRepeater(TestCase):
    @mock.patch('app.core.repeater.QTimer')
    def test_repeater(self, mock_timer):
        mock_timer.return_value = mock_timer

        repeater = Repeater()
        repeater.start('test', 2)

        expected = [call(),
                    call.setSingleShot(True),
                    call.timeout.connect('test'),
                    call.start(2000)]
        self.assertEqual(expected, mock_timer.mock_calls)

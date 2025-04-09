from unittest import TestCase, mock
from unittest.mock import call

from app.core.toggles import Toggles


class TestToggles(TestCase):
    def setUp(self):
        self.toggles = Toggles()

    @mock.patch('app.core.config.files.load_toggles')
    def test_initialize__empty_files(self, mock_load_toggles):
        mock_load_toggles.return_value = {}
        self.toggles.initialize()

        self.assertEqual(True, self.toggles.run_script)
        self.assertEqual(1, mock_load_toggles.call_count)

    @mock.patch('app.core.config.files.load_toggles')
    def test_initialize(self, mock_load_toggles):
        mock_load_toggles.return_value = {
            'run_script': False,
        }
        self.toggles.initialize()

        self.assertEqual(False, self.toggles.run_script)
        self.assertEqual(1, mock_load_toggles.call_count)

    @mock.patch('app.core.config.files.save_toggles_file')
    def test_save_toggles(self, mock_save_toggles_file):
        self.toggles.run_script = "SOME VALUE"
        self.toggles.save_toggles()
        expected = [call({'run_script': 'SOME VALUE'})]
        self.assertEqual(expected, mock_save_toggles_file.mock_calls)

    def test_toggle_run_script(self):
        self.toggles.run_script = True
        self.toggles.toggle_run_script()
        self.assertEqual(False, self.toggles.run_script)

        self.toggles.toggle_run_script()
        self.assertEqual(True, self.toggles.run_script)

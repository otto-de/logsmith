import os
from unittest import TestCase, mock
from unittest.mock import call

from app.core import files

script_dir = os.path.dirname(os.path.realpath(__file__))


class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file = f'{script_dir}/../test_resources/test_file'
        cls.test_home = f'{script_dir}/../test_resources'

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_app_path(self, _):
        self.assertEqual('home/.logsmith', files.get_app_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_aws_path(self, _):
        self.assertEqual('home/.aws', files.get_aws_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_config_path(self, _):
        self.assertEqual('home/.logsmith/config.yaml', files.get_config_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_accounts_path(self, _):
        self.assertEqual('home/.logsmith/accounts.yaml', files.get_accounts_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_log_path(self, _):
        self.assertEqual('home/.logsmith/app.log', files.get_log_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_active_group_file_path(self, _):
        self.assertEqual('home/.aws/active_group', files.get_active_group_file_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_team_file_path(self, _):
        self.assertEqual('home/.aws/active_team', files.get_team_file_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_account_file_path(self, _):
        self.assertEqual('home/.aws/active_account', files.get_account_file_path())

    def test__parse_yaml(self):
        yaml = files._parse_yaml('test: true')
        expected = {'test': True}
        self.assertEqual(expected, yaml)

    def test__parse_yaml__invalid_yaml(self):
        yaml = files._parse_yaml('test: true test: true')
        self.assertEqual({}, yaml)

    def test__dump_yaml(self):
        text = files._dump_yaml({'test': True})
        expected = 'test: true\n'
        self.assertEqual(expected, text)

    def test__load_file(self):
        text = files._load_file(self.test_file)
        expected = 'this is a test'
        self.assertEqual(expected, text)

    def test__load_file__file_not_found(self):
        text = files._load_file('no_file')
        expected = ''
        self.assertEqual(expected, text)

    @mock.patch('app.core.files.Path.home')
    def test_load_config(self, mock_home):
        mock_home.return_value = self.test_home
        file = files.load_config()
        expected = {'test': True}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_config__files_does_not_exist(self, mock_home):
        mock_home.return_value = 'wrong_home'
        file = files.load_config()
        expected = {}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_accounts(self, mock_home):
        mock_home.return_value = self.test_home
        file = files.load_accounts()
        expected = {'test': True}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_accounts__files_does_not_exist(self, mock_home):
        mock_home.return_value = 'wrong_home'
        file = files.load_accounts()
        expected = {}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files._write_file')
    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_save_config_file(self, mock_home, mock_write):
        files.save_config_file({'test': True})
        expected = [
            call('home/.logsmith/config.yaml', 'test: true\n')
        ]
        self.assertEqual(expected, mock_write.mock_calls)

    @mock.patch('app.core.files._write_file')
    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_save_accounts_file(self, mock_home, mock_write):
        files.save_accounts_file({'test': True})
        expected = [
            call('home/.logsmith/accounts.yaml', 'test: true\n')
        ]
        self.assertEqual(expected, mock_write.mock_calls)

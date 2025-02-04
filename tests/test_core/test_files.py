import os
from unittest import TestCase, mock
from unittest.mock import call

from app.core import files

script_dir = os.path.dirname(os.path.realpath(__file__))


class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file = f'{script_dir}/../test_resources/test_file'
        cls.non_existing_test_file = f'{script_dir}/../test_resources/test_file_does_not_exist'
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
    def test_get_service_roles_path(self, _):
        self.assertEqual('home/.logsmith/service_roles.yaml', files.get_service_roles_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_log_path(self, _):
        self.assertEqual('home/.logsmith/app.log', files.get_log_path())

    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_get_active_group_file_path(self, _):
        self.assertEqual('home/.logsmith/active_group', files.get_active_group_file_path())

    def test_parse_yaml(self):
        yaml = files.parse_yaml('test: true')
        expected = {'test': True}
        self.assertEqual(expected, yaml)

    def test_parse_yaml__invalid_yaml(self):
        yaml = files.parse_yaml('test: true test: true')
        self.assertEqual({}, yaml)

    def test_dump_yaml(self):
        text = files.dump_yaml({'test': True})
        expected = 'test: true\n'
        self.assertEqual(expected, text)

    def test_dump_yaml__leading_zero(self):
        text = files.dump_yaml({'test': '043156558'})
        expected = 'test: \'043156558\'\n'
        self.assertEqual(expected, text)

    def test_dump_yaml__do_not_sort_keys(self):
        text = files.dump_yaml({'z': 'dog', 'a': 'cat'})
        expected = 'z: dog\na: cat\n'
        self.assertEqual(expected, text)

    def test_dump_yaml__indentation(self):
        text = files.dump_yaml({'a': 'cat', 'b': {'c': 'dog'}})
        expected = 'a: cat\nb:\n  c: dog\n'
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
        expected = {'test': 'config'}
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
        expected = {'test': 'accounts'}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_accounts__files_does_not_exist(self, mock_home):
        mock_home.return_value = 'wrong_home'
        file = files.load_accounts()
        expected = {}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_service_roles(self, mock_home):
        mock_home.return_value = self.test_home
        file = files.load_service_roles()
        expected = {'test': 'service_roles'}
        self.assertEqual(expected, file)

    @mock.patch('app.core.files.Path.home')
    def test_load_service_roles__files_does_not_exist(self, mock_home):
        mock_home.return_value = 'wrong_home'
        file = files.load_service_roles()
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

    @mock.patch('app.core.files._write_file')
    @mock.patch('app.core.files.Path.home', return_value='home')
    def test_save_service_roles_file(self, mock_home, mock_write):
        files.save_service_roles_file({'test': True})
        expected = [
            call('home/.logsmith/service_roles.yaml', 'test: true\n')
        ]
        self.assertEqual(expected, mock_write.mock_calls)

    def test_file_exists(self):
        self.assertTrue(files.file_exists(self.test_file))

    def test_file_exists__files_does_not_exist(self):
        self.assertFalse(files.file_exists(self.non_existing_test_file))

    @mock.patch('app.core.files.os.path.exists', return_value=True)
    def test_file_exists__script_path_without_arguments(self, mock_os_path_exists):
        files.file_exists(self.test_file)
        expected = [call(self.test_file)]
        self.assertEqual(expected, mock_os_path_exists.mock_calls)

    @mock.patch('app.core.files.os.path.exists', return_value=True)
    def test_file_exists__script_path_with_arguments(self, mock_os_path_exists):
        files.file_exists(f'{self.test_file} argument1 argument2')
        expected = [call(self.test_file)]
        self.assertEqual(expected, mock_os_path_exists.mock_calls)

    @mock.patch('app.core.core.files.get_home_dir', return_value='/home/user')
    def test__replace_home_variable(self, mock_get_home_dir):
        self.assertEqual('/home/user/some/path', files.replace_home_variable('\"${HOME}\"/some/path'))
        self.assertEqual('/home/user/some/path', files.replace_home_variable('\"$HOME\"/some/path'))
        self.assertEqual('/home/user/some/path', files.replace_home_variable('${HOME}/some/path'))
        self.assertEqual('/home/user/some/path', files.replace_home_variable('$HOME/some/path'))
        self.assertEqual('/home/user/some/path', files.replace_home_variable('~/some/path'))

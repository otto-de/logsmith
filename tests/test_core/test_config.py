from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from tests.test_data.test_accounts import get_test_accounts


class TestConfig(TestCase):
    def setUp(self):
        self.config = Config()

    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def test_load_from_disk__empty_config(self, mock_accounts, mock_config):
        mock_accounts.return_value = {}
        mock_config.return_value = {}
        self.config.load_from_disk()
        self.assertEqual(None, self.config.mfa_shell_command)

    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def test_load_from_disk(self, mock_load_accounts, mock_load_config):
        mock_load_accounts.return_value = get_test_accounts()
        mock_load_config.return_value = {
            'mfa_shell_command': 'some command',
        }
        self.config.load_from_disk()
        self.assertEqual('some command', self.config.mfa_shell_command)

    @mock.patch('app.core.config.files.save_config_file')
    @mock.patch('app.core.config.files.save_accounts_file')
    def test_save_to_disk(self, mock_save_accounts_file, mock_save_config_file):
        self.config.set_accounts(get_test_accounts())
        self.config.save_to_disk()
        expected_accounts = [call(
            {'development': {
                'color': '#388E3C',
                'team': 'awesome-team',
                'region': 'us-east-1',
                'profiles': [
                    {
                        'profile': 'developer',
                        'account': '123495678901',
                        'role': 'developer',
                        'default': True
                    },
                    {
                        'profile': 'readonly',
                        'account': '123495678901',
                        'role': 'readonly'
                    }
                ]
            },
                'live': {
                    'color': '#388E3C',
                    'team': 'awesome-team',
                    'region': 'us-east-1',
                    'profiles': [
                        {
                            'profile': 'developer',
                            'account': '123456789012',
                            'role': 'developer',
                            'default': True},
                        {
                            'profile': 'readonly',
                            'account': '123456789012',
                            'role': 'readonly'
                        }
                    ]
                }
            }
        )]

        expected_config = [call({
            'mfa_shell_command': None
        })]

        self.assertEqual(expected_accounts, mock_save_accounts_file.mock_calls)
        self.assertEqual(expected_config, mock_save_config_file.mock_calls)

    def test_set_accounts(self):
        self.config.set_accounts(get_test_accounts())

        groups = ['development', 'live']
        self.assertEqual(groups, list(self.config.profile_groups.keys()))

        development_group = self.config.get_group('development')
        self.assertEqual('development', development_group.name)
        self.assertEqual('awesome-team', development_group.team)
        self.assertEqual('us-east-1', development_group.region)
        self.assertEqual('#388E3C', development_group.color)

        profile = development_group.profiles[0]
        self.assertEqual(development_group, profile.group)
        self.assertEqual('developer', profile.profile)
        self.assertEqual('123495678901', profile.account)
        self.assertEqual('developer', profile.role)
        self.assertEqual(True, profile.default)

        profile = development_group.profiles[1]
        self.assertEqual(development_group, profile.group)
        self.assertEqual('readonly', profile.profile)
        self.assertEqual('123495678901', profile.account)
        self.assertEqual('readonly', profile.role)
        self.assertEqual(False, profile.default)

    def test_validate(self):
        self.config.set_accounts(get_test_accounts())
        self.config.validate()
        self.assertEqual(True, self.config.valid)
        self.assertEqual('', self.config.error)

    def test_validate_empty_config(self):
        self.config.validate()
        self.assertEqual(False, self.config.valid)
        self.assertEqual('config is empty', self.config.error)

    def test_validate_calls_validate_and_use_return_value(self):
        mock_group1 = Mock()
        mock_group1.validate.return_value = True, 'no error'
        mock_group2 = Mock()
        mock_group2.validate.return_value = False, 'some error'
        mock_group3 = Mock()
        mock_group3.validate.return_value = True, 'everything is okay'

        self.config.profile_groups['1'] = mock_group1
        self.config.profile_groups['2'] = mock_group2
        self.config.profile_groups['3'] = mock_group3
        self.config.validate()
        self.assertEqual(1, mock_group1.validate.call_count)
        self.assertEqual(1, mock_group2.validate.call_count)
        self.assertEqual(0, mock_group3.validate.call_count)

        self.assertEqual(False, self.config.valid)
        self.assertEqual('some error', self.config.error)

    def test_list_groups(self):
        self.config.profile_groups = {
            '1': 'group 1',
            '2': 'group 2'
        }
        expected = ['group 1', 'group 2']
        self.assertEqual(expected, self.config.list_groups())

    def test_get_group(self):
        self.config.profile_groups = {
            '1': 'group 1',
            '2': 'group 2'
        }
        expected = 'group 1'
        self.assertEqual(expected, self.config.get_group('1'))

    def test_to_dict(self):
        mock_group1 = Mock()
        mock_group1.to_dict.return_value = 'group 1'
        mock_group2 = Mock()
        mock_group2.to_dict.return_value = 'group 2'
        mock_group3 = Mock()
        mock_group3.to_dict.return_value = 'group 3'

        self.config.profile_groups['1'] = mock_group1
        self.config.profile_groups['2'] = mock_group2
        self.config.profile_groups['3'] = mock_group3

        result = self.config.to_dict()
        self.assertEqual(1, mock_group1.to_dict.call_count)
        self.assertEqual(1, mock_group2.to_dict.call_count)
        self.assertEqual(1, mock_group3.to_dict.call_count)

        expected = {'1': 'group 1', '2': 'group 2', '3': 'group 3'}

        self.assertEqual(expected, result)

from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from tests.test_data.test_accounts import get_test_accounts
from tests.test_data.test_service_roles import get_test_service_roles


class TestConfig(TestCase):
    def setUp(self):
        self.config = Config()

    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def test_initialize__empty_config(self, mock_accounts, mock_config):
        mock_accounts.return_value = {}
        mock_config.return_value = {}
        self.config.initialize()
        self.assertEqual(None, self.config.mfa_shell_command)

    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def test_initialize(self, mock_load_accounts, mock_load_config):
        mock_load_accounts.return_value = get_test_accounts()
        mock_load_config.return_value = {
            'mfa_shell_command': 'some command',
        }
        self.config.initialize()
        self.assertEqual('some command', self.config.mfa_shell_command)

    @mock.patch('app.core.config.files.save_accounts_file')
    def test_save_accounts(self, mock_save_accounts_file):
        self.config.initialize_profile_groups(get_test_accounts(), get_test_service_roles(), 'default-access-key')
        self.config.save_accounts()
        expected = [call(
            {
                'development': {
                    'color': '#388E3C',
                    'team': 'awesome-team',
                    'region': 'us-east-1',
                    'profiles': [
                        {
                            'profile': 'developer',
                            'account': '123495678901',
                            'role': 'developer',
                            'default': True,
                        },
                        {
                            'profile': 'readonly',
                            'account': '012349567890',
                            'role': 'readonly'
                        }
                    ]
                },
                'live': {
                    'color': '#388E3C',
                    'team': 'awesome-team',
                    'region': 'us-east-1',
                    'access_key': 'access-key-123',
                    'profiles': [
                        {
                            'profile': 'developer',
                            'account': '123456789012',
                            'role': 'developer',
                            'default': True
                        },
                        {
                            'profile': 'readonly',
                            'account': '012345678901',
                            'role': 'readonly'
                        }
                    ]
                },
                'gcp-project-dev': {
                    'color': '#FF0000',
                    'team': 'another-team',
                    'region': 'europe-west1',
                    'type': 'gcp',
                    'profiles': [],  # this will be automatically added
                }
            }
        )]

        self.assertEqual(expected, mock_save_accounts_file.mock_calls)

    @mock.patch('app.core.config.files.save_config_file')
    def test_save_config(self, mock_save_config_file):
        self.config.initialize_profile_groups(get_test_accounts(), get_test_service_roles(), 'default-access-key')
        self.config.save_config()

        expected = [call({
            'mfa_shell_command': None,
            'default_access_key': 'default-access-key'
        })]

        self.assertEqual(expected, mock_save_config_file.mock_calls)

    def test_initialize_profile_groups(self):
        self.config.initialize_profile_groups(get_test_accounts(), get_test_service_roles(), 'default-access-key')

        groups = ['development', 'live', 'gcp-project-dev']
        self.assertEqual(groups, list(self.config.profile_groups.keys()))

        development_group = self.config.get_group('development')
        self.assertEqual('development', development_group.name)
        self.assertEqual('awesome-team', development_group.team)
        self.assertEqual('us-east-1', development_group.region)
        self.assertEqual('#388E3C', development_group.color)
        self.assertEqual('aws', development_group.type)
        self.assertEqual('default-access-key', development_group.get_access_key())

        profile = development_group.profiles[0]
        self.assertEqual(development_group, profile.group)
        self.assertEqual('developer', profile.profile)
        self.assertEqual('123495678901', profile.account)
        self.assertEqual('developer', profile.role)
        self.assertEqual(True, profile.default)

        profile = development_group.profiles[1]
        self.assertEqual(development_group, profile.group)
        self.assertEqual('readonly', profile.profile)
        self.assertEqual('012349567890', profile.account)
        self.assertEqual('readonly', profile.role)
        self.assertEqual(False, profile.default)

        live_group = self.config.get_group('live')
        self.assertEqual('access-key-123', live_group.get_access_key())

    def test_validate(self):
        self.config.initialize_profile_groups(get_test_accounts(), get_test_service_roles(), 'default-access-key')
        self.config.validate()
        self.assertEqual('', self.config.error)
        self.assertEqual(True, self.config.valid)

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

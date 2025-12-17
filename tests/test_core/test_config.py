from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config, _default_access_key, _default_sso_sesson, _default_sso_interval
from tests.test_data.test_accounts import get_default_test_accounts, get_test_accounts__minimal, get_test_accounts__mixed_auth_modes
from tests.test_data.test_config import get_test_config
from tests.test_data.test_service_roles import get_test_service_roles


class TestConfig(TestCase):
    def setUp(self):
        self.config = Config()

    @mock.patch('app.core.config.files.load_service_roles')
    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    @mock.patch('app.core.config.Config.initialize_profile_groups')
    def test_initialize__empty_files(self, mock_initialize_profile_groups, mock_accounts, mock_config,
                                     mock_service_roles):
        mock_accounts.return_value = {}
        mock_config.return_value = {}
        mock_service_roles.return_value = {}
        self.config.initialize()

        expected_calls = [call(accounts={}, service_roles={}, default_access_key=_default_access_key, default_sso_session=_default_sso_sesson, default_sso_interval=_default_sso_interval)]

        self.assertEqual(None, self.config.mfa_shell_command)
        self.assertEqual(_default_access_key, self.config.default_access_key)
        self.assertEqual(_default_sso_sesson, self.config.default_sso_session)
        self.assertEqual({}, self.config.profile_groups)
        self.assertEqual({}, self.config.service_roles)
        self.assertEqual(expected_calls, mock_initialize_profile_groups.mock_calls)

    @mock.patch('app.core.config.files.load_service_roles')
    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    @mock.patch('app.core.config.Config.initialize_profile_groups')
    def test_initialize__with_config(self, mock_initialize_profile_groups, mock_load_accounts, mock_load_config, mock_service_roles):
        mock_load_accounts.return_value = {}
        mock_load_config.return_value = {
            'mfa_shell_command': 'some-command',
            'default_access_key': 'some-key',
            'default_sso_session': 'some-session',
            'default_sso_interval': 'some-sso-interval',
        }
        mock_service_roles.return_value = {}
        self.config.initialize()

        expected_calls = [call(accounts={}, service_roles={}, default_access_key='some-key', default_sso_session='some-session', default_sso_interval='some-sso-interval')]

        self.assertEqual('some-key', self.config.default_access_key)
        self.assertEqual('some-session', self.config.default_sso_session)
        self.assertEqual('some-command', self.config.mfa_shell_command)
        self.assertEqual(expected_calls, mock_initialize_profile_groups.mock_calls)

    @mock.patch('app.core.config.files.load_service_roles')
    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    @mock.patch('app.core.config.Config.initialize_profile_groups')
    def test_initialize(self, mock_initialize_profile_groups, mock_load_accounts, mock_load_config, mock_service_roles):
        mock_load_accounts.return_value = get_default_test_accounts()
        mock_load_config.return_value = get_test_config()
        mock_service_roles.return_value = get_test_service_roles()
        self.config.initialize()

        expected_calls = [
            call(accounts=get_default_test_accounts(), 
                 service_roles=get_test_service_roles(),
                 default_access_key='some-access-key', 
                 default_sso_session='some-sso-session', 
                 default_sso_interval='some-sso-interval')]

        self.assertEqual('some-access-key', self.config.default_access_key)
        self.assertEqual('some-sso-session', self.config.default_sso_session)
        self.assertEqual('some-command', self.config.mfa_shell_command)
        self.assertEqual('/some/dir/', self.config.shell_path_extension)
        self.assertEqual(expected_calls, mock_initialize_profile_groups.mock_calls)

    @mock.patch('app.core.config.files.save_accounts_file')
    def test_save_accounts__default(self, mock_save_accounts_file):
        self.config.initialize_profile_groups(get_default_test_accounts(), get_test_service_roles(), 'some-access-key', 'some-sso-session', 'default-sso-interval')
        self.config.save_accounts()
        expected = [call(
            {
                'development': {
                    'color': '#388E3C',
                    'team': 'awesome-team',
                    'region': 'us-east-1',
                    'auth_mode': 'key',
                    'script': None,
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
                    'auth_mode': 'key',
                    'access_key': 'access-key-123',
                    'script': './some-script.sh',
                    'profiles': [
                        {
                            'profile': 'admin',
                            'account': '9876543210',
                            'role': 'admin',
                            'default': True
                        },
                        {
                            'profile': 'readonly',
                            'account': '0000000000',
                            'role': 'readonly'
                        }
                    ]
                },
                'gcp-project-dev': {
                    'color': '#FF0000',
                    'team': 'another-team',
                    'region': 'europe-west1',
                    'type': 'gcp',
                    'auth_mode': 'key',
                    'script': None,
                    'profiles': [],  # this will be automatically added
                }
            }
        )]

        self.assertEqual(expected, mock_save_accounts_file.mock_calls)
        
    @mock.patch('app.core.config.files.save_accounts_file')
    def test_save_accounts__auth_mode_mixed(self, mock_save_accounts_file):
        self.config.initialize_profile_groups(get_test_accounts__mixed_auth_modes(), get_test_service_roles(), 'some-access-key', 'some-sso-session', 'default-sso-interval')
        self.config.save_accounts()
        expected = [call(
            {
                'development': {
                    'color': '#388E3C',
                    'team': 'awesome-team',
                    'region': 'us-east-1',
                    'auth_mode': 'key',
                    'access_key': 'access-key-123',
                    'script': None,
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
                    'auth_mode': 'sso',
                    'sso_session': 'sso-123',
                    'script': './some-script.sh',
                    'profiles': [
                        {
                            'profile': 'admin',
                            'account': '9876543210',
                            'role': 'admin',
                            'default': True
                        },
                        {
                            'profile': 'readonly',
                            'account': '0000000000',
                            'role': 'readonly'
                        }
                    ]
                },
                'gcp-project-dev': {
                    'color': '#FF0000',
                    'team': 'another-team',
                    'region': 'europe-west1',
                    'type': 'gcp',
                    'auth_mode': 'key',
                    'script': None,
                    'profiles': [],  # this will be automatically added
                }
            }
        )]

        self.assertEqual(expected, mock_save_accounts_file.mock_calls)

    @mock.patch('app.core.config.files.save_config_file')
    def test_save_config__defaults(self, mock_save_config_file):
        self.config.save_config()

        expected = [call({'mfa_shell_command': None, 
                          'shell_path_extension': None,
                          'default_access_key': None,
                          'default_sso_session': None,
                          'default_sso_interval': None})]

        self.assertEqual(expected, mock_save_config_file.mock_calls)
        
    @mock.patch('app.core.config.files.save_config_file')
    def test_save_config(self, mock_save_config_file):
        self.config.mfa_shell_command = 'some command'
        self.config.shell_path_extension = 'some path'
        self.config.default_access_key = 'some access key'
        self.config.default_sso_session = 'some sso session'
        self.config.default_sso_interval = 'some interval'
        self.config.save_config()

        expected = [call({'mfa_shell_command': 'some command', 
                          'shell_path_extension': 'some path',
                          'default_access_key': 'some access key',
                          'default_sso_session': 'some sso session',
                          'default_sso_interval': 'some interval'})]

        self.assertEqual(expected, mock_save_config_file.mock_calls)

    @mock.patch('app.core.config.files.save_service_roles_file')
    def test_save_selected_service_role__empty_data(self, mock_save_service_roles_file):
        self.config.save_selected_service_role(group_name='development', profile_name='developer', role_name='pipeline')
        expected = [call({
            'development': {
                'selected_profile': 'developer',
                'selected_role': 'pipeline',
                'available': {},
                'history': ['developer : pipeline']},
        })]
        self.assertEqual(expected, mock_save_service_roles_file.mock_calls)

    @mock.patch('app.core.config.files.save_service_roles_file')
    def test_save_selected_service_role__update_loaded_data(self, mock_save_service_roles_file):
        self.config.service_roles = get_test_service_roles()
        self.config.save_selected_service_role(group_name='development', profile_name='developer', role_name='pipeline')
        expected = [call({
            'development': {
                'selected_profile': 'developer',
                'selected_role': 'pipeline',
                'available': {'profile-1': ['role-1-1', 'role-1-2'],
                              'profile-2': ['role-2-1']},
                'history': ['developer : pipeline', 'profile-2 : role-2', 'profile-1 : role-3']},
            'live': {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []}})]
        self.assertEqual(expected, mock_save_service_roles_file.mock_calls)

    @mock.patch('app.core.config.files.save_service_roles_file')
    def test_save_available_service_roles__empty_data(self, mock_save_service_roles_file):
        self.config.save_available_service_roles(group_name='development', profile_name='developer',
                                                 role_list=['pipeline'])
        expected = [call({
            'development': {
                'selected_profile': None,
                'selected_role': None,
                'available': {'developer': ['pipeline']},
                'history': []},
        })]
        self.assertEqual(expected, mock_save_service_roles_file.mock_calls)

    @mock.patch('app.core.config.files.save_service_roles_file')
    def test_save_available_service_roles__update_loaded_data(self, mock_save_service_roles_file):
        self.config.service_roles = get_test_service_roles()
        self.config.save_available_service_roles(group_name='development', profile_name='developer',
                                                 role_list=['pipeline'])
        expected = [call({
            'development': {
                'selected_profile': 'developer',
                'selected_role': 'pipeline',
                'available': {'profile-1': ['role-1-1', 'role-1-2'],
                              'profile-2': ['role-2-1'],
                              'developer': ['pipeline']},
                'history': ['profile-2 : role-2', 'profile-1 : role-3']},
            'live': {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []}})]
        self.assertEqual(expected, mock_save_service_roles_file.mock_calls)

    def test_initialize_profile_groups(self):
        self.config.initialize_profile_groups(get_default_test_accounts(), get_test_service_roles(), 'default-access-key', 'default-sso-session', 'default-sso-interval')

        self.assertEqual(['development', 'live', 'gcp-project-dev'], list(self.config.profile_groups.keys()))

        development_group = self.config.get_group('development')
        self.assertEqual('development', development_group.name)
        self.assertEqual('awesome-team', development_group.team)
        self.assertEqual('us-east-1', development_group.region)
        self.assertEqual('#388E3C', development_group.color)
        self.assertEqual('aws', development_group.type)
        self.assertEqual('default-access-key', development_group.get_access_key())

        development_profile1 = development_group.profiles[0]
        self.assertEqual(development_group, development_profile1.group)
        self.assertEqual('developer', development_profile1.profile)
        self.assertEqual('123495678901', development_profile1.account)
        self.assertEqual('developer', development_profile1.role)
        self.assertEqual(True, development_profile1.default)
        self.assertEqual(None, development_profile1.source)

        development_profile2 = development_group.profiles[1]
        self.assertEqual(development_group, development_profile2.group)
        self.assertEqual('readonly', development_profile2.profile)
        self.assertEqual('012349567890', development_profile2.account)
        self.assertEqual('readonly', development_profile2.role)
        self.assertEqual(False, development_profile2.default)
        self.assertEqual(None, development_profile2.source)

        development_service_role = development_group.service_profile
        self.assertEqual(development_group, development_service_role.group)
        self.assertEqual('service', development_service_role.profile)
        self.assertEqual('123495678901', development_service_role.account)
        self.assertEqual('pipeline', development_service_role.role)
        self.assertEqual(False, development_service_role.default)
        self.assertEqual('developer', development_service_role.source)

        live_group = self.config.get_group('live')
        self.assertEqual('access-key-123', live_group.get_access_key())
        self.assertEqual(None, live_group.service_profile)

        live_profile1 = live_group.profiles[0]
        self.assertEqual(live_group, live_profile1.group)
        self.assertEqual('admin', live_profile1.profile)
        self.assertEqual('9876543210', live_profile1.account)
        self.assertEqual('admin', live_profile1.role)
        self.assertEqual(True, live_profile1.default)
        self.assertEqual(None, live_profile1.source)

        live_profile2 = live_group.profiles[1]
        self.assertEqual(live_group, live_profile2.group)
        self.assertEqual('readonly', live_profile2.profile)
        self.assertEqual('0000000000', live_profile2.account)
        self.assertEqual('readonly', live_profile2.role)
        self.assertEqual(False, live_profile2.default)
        self.assertEqual(None, live_profile2.source)

    def test_initialize_profile_groups__replace_old_values_on_config_reload(self):
        self.config.initialize_profile_groups(get_default_test_accounts(), get_test_service_roles(),
                                              'default-access-key', 'defauls-sso-session', 'default-sso-interval')
        self.config.initialize_profile_groups(get_test_accounts__minimal(), get_test_service_roles(),
                                              'default-access-key', 'defauls-sso-session', 'default-sso-interval')

        self.assertEqual(['development'], list(self.config.profile_groups.keys()))

        development_group = self.config.get_group('development')
        self.assertEqual('development', development_group.name)
        self.assertEqual('awesome-team', development_group.team)
        self.assertEqual('us-east-1', development_group.region)
        self.assertEqual('#388E3C', development_group.color)
        self.assertEqual('aws', development_group.type)
        self.assertEqual('default-access-key', development_group.get_access_key())

        development_profile1 = development_group.profiles[0]
        self.assertEqual(development_group, development_profile1.group)
        self.assertEqual('developer', development_profile1.profile)
        self.assertEqual('123495678901', development_profile1.account)
        self.assertEqual('developer', development_profile1.role)
        self.assertEqual(True, development_profile1.default)
        self.assertEqual(None, development_profile1.source)

        self.assertEqual(1, len(development_group.profiles))

    def test_set_default_sso_interval__string_none_sets_none(self):
        self.config.set_default_sso_interval('None')
        self.assertIsNone(self.config.default_sso_interval)

    def test_set_default_sso_interval__stores_value(self):
        self.config.set_default_sso_interval('15')
        self.assertEqual('15', self.config.default_sso_interval)

    def test_add_to_history(self):
        history = ['profile-1 : role-1', 'profile-2 : role-2']
        result = self.config._add_to_history('profile-3', 'role-3', history)
        expected = ['profile-3 : role-3', 'profile-1 : role-1', 'profile-2 : role-2']
        self.assertEqual(expected, result)

    def test_add_to_history__deduplicates_and_limits(self):
        history = [f'profile-{i} : role-{i}' for i in range(1, 11)]
        history.append('profile-3 : role-3')

        result = self.config._add_to_history('profile-99', 'role-99', history)

        expected = [
            'profile-99 : role-99',
            'profile-1 : role-1',
            'profile-2 : role-2',
            'profile-3 : role-3',
            'profile-4 : role-4',
            'profile-5 : role-5',
            'profile-6 : role-6',
            'profile-7 : role-7',
            'profile-8 : role-8',
            'profile-9 : role-9',
        ]
        self.assertEqual(expected, result)

    def test_add_to_history__ignores_missing_profile_or_role(self):
        history = ['profile-1 : role-1']
        result = self.config._add_to_history(profile=None, role='role-2', history=list(history))
        self.assertEqual(history, result)

    def test_get_service_role_helpers(self):
        self.config.service_roles = {
            'dev': {
                'selected_profile': 'developer',
                'selected_role': 'pipeline',
                'available': {'developer': ['pipeline']},
                'history': ['developer : pipeline']
            }
        }

        self.assertEqual('developer', self.config.get_selected_service_role_source_profile('dev'))
        self.assertEqual('pipeline', self.config.get_selected_service_role('dev'))
        self.assertEqual(['pipeline'], self.config.get_available_service_roles('dev', 'developer'))
        self.assertEqual(['developer : pipeline'], self.config.get_history('dev'))

    def test_get_service_role_helpers__defaults(self):
        self.assertIsNone(self.config.get_selected_service_role_source_profile('unknown'))
        self.assertIsNone(self.config.get_selected_service_role('unknown'))
        self.assertEqual([], self.config.get_available_service_roles('unknown', 'developer'))
        self.assertEqual([], self.config.get_history('unknown'))

    def test_validate(self):
        self.config.initialize_profile_groups(get_default_test_accounts(), get_test_service_roles(), 
                                              'default-access-key', 'defauls-sso-session', 'default-sso-interval')
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

from unittest.mock import call

import pytest

from app.core import files
from app.core.config import Config, _default_access_key, _default_sso_sesson, _default_sso_interval
from tests.test_data.test_accounts import get_default_test_accounts, get_test_accounts__minimal, get_test_accounts__mixed_auth_modes
from tests.test_data.test_config import get_test_config
from tests.test_data.test_service_roles import get_test_service_roles

#######################
# Fixures


@pytest.fixture(scope="function")
def config():
    return Config()

#######################
# Tests


def test_initialize__empty_files(config, mocker):
    mock_service_roles = mocker.patch.object(files, "load_service_roles")
    mock_load_config = mocker.patch.object(files, "load_config")
    mock_load_accounts = mocker.patch.object(files, "load_accounts")
    mock_initialize_profile_groups = mocker.patch.object(Config, "initialize_profile_groups")

    mock_load_accounts.return_value = {}
    mock_load_config.return_value = {}
    mock_service_roles.return_value = {}
    config.initialize()

    mock_initialize_profile_groups.assert_called_once_with(accounts={},
                                                           service_roles={},
                                                           default_access_key=_default_access_key,
                                                           default_sso_session=_default_sso_sesson,
                                                           default_sso_interval=_default_sso_interval)

    assert None == config.mfa_shell_command
    assert _default_access_key == config.default_access_key
    assert _default_sso_sesson == config.default_sso_session
    assert {} == config.profile_groups
    assert {} == config.service_roles


def test_initialize__with_config(config, mocker):
    mock_service_roles = mocker.patch.object(files, "load_service_roles")
    mock_load_config = mocker.patch.object(files, "load_config")
    mock_load_accounts = mocker.patch.object(files, "load_accounts")
    mock_initialize_profile_groups = mocker.patch.object(config, "initialize_profile_groups")

    mock_load_accounts.return_value = {}
    mock_load_config.return_value = {
        'mfa_shell_command': 'some-command',
        'default_access_key': 'some-key',
        'default_sso_session': 'some-session',
        'default_sso_interval': 'some-sso-interval',
    }
    mock_service_roles.return_value = {}
    config.initialize()

    mock_initialize_profile_groups.assert_called_once_with(accounts={},
                                                           service_roles={},
                                                           default_access_key='some-key',
                                                           default_sso_session='some-session',
                                                           default_sso_interval='some-sso-interval')

    assert 'some-key' == config.default_access_key
    assert 'some-session' == config.default_sso_session
    assert 'some-command' == config.mfa_shell_command


def test_initialize(config, mocker):
    mock_service_roles = mocker.patch.object(files, "load_service_roles")
    mock_load_config = mocker.patch.object(files, "load_config")
    mock_load_accounts = mocker.patch.object(files, "load_accounts")
    mock_initialize_profile_groups = mocker.patch.object(config, "initialize_profile_groups")

    mock_load_accounts.return_value = get_default_test_accounts()
    mock_load_config.return_value = get_test_config()
    mock_service_roles.return_value = get_test_service_roles()
    config.initialize()

    mock_initialize_profile_groups.assert_called_once_with(accounts=get_default_test_accounts(),
                                                           service_roles=get_test_service_roles(),
                                                           default_access_key='some-access-key',
                                                           default_sso_session='some-sso-session',
                                                           default_sso_interval='some-sso-interval')

    assert 'some-access-key' == config.default_access_key
    assert 'some-sso-session' == config.default_sso_session
    assert 'some-command' == config.mfa_shell_command
    assert '/some/dir/' == config.shell_path_extension


def test_save_accounts__default(config, mocker):
    mock_save_accounts_file = mocker.patch.object(files, "save_accounts_file")

    config.initialize_profile_groups(
        get_default_test_accounts(),
        get_test_service_roles(),
        'some-access-key',
        'some-sso-session',
        'default-sso-interval')
    config.save_accounts()
    expected = {
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

    mock_save_accounts_file.assert_called_once_with(expected)


def test_save_accounts__auth_mode_mixed(config, mocker):
    mock_save_accounts_file = mocker.patch.object(files, "save_accounts_file")

    config.initialize_profile_groups(
        get_test_accounts__mixed_auth_modes(),
        get_test_service_roles(),
        'some-access-key',
        'some-sso-session',
        'default-sso-interval')
    config.save_accounts()
    expected = {
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
    mock_save_accounts_file.assert_called_once_with(expected)


def test_save_config__defaults(config, mocker):
    mock_save_config_file = mocker.patch.object(files, "save_config_file")

    config.save_config()

    expected = {
        'mfa_shell_command': None,
        'shell_path_extension': None,
        'default_access_key': None,
        'default_sso_session': None,
        'default_sso_interval': None}
    mock_save_config_file.assert_called_once_with(expected)


def test_save_config(config, mocker):
    mock_save_config_file = mocker.patch.object(files, "save_config_file")

    config.mfa_shell_command = 'some command'
    config.shell_path_extension = 'some path'
    config.default_access_key = 'some access key'
    config.default_sso_session = 'some sso session'
    config.default_sso_interval = 'some interval'
    config.save_config()

    expected = {
        'mfa_shell_command': 'some command',
        'shell_path_extension': 'some path',
        'default_access_key': 'some access key',
        'default_sso_session': 'some sso session',
        'default_sso_interval': 'some interval'}
    mock_save_config_file.assert_called_once_with(expected)


def test_save_selected_service_role__empty_data(config, mocker):
    mock_save_service_roles_file = mocker.patch.object(files, "save_service_roles_file")

    config.save_selected_service_role(group_name='development', profile_name='developer', role_name='pipeline')
    expected = {
        'development': {
            'selected_profile': 'developer',
            'selected_role': 'pipeline',
            'available': {},
            'history': ['developer : pipeline']}}
    mock_save_service_roles_file.assert_called_once_with(expected)


def test_save_selected_service_role__update_loaded_data(config, mocker):
    mock_save_service_roles_file = mocker.patch.object(files, "save_service_roles_file")

    config.service_roles = get_test_service_roles()
    config.save_selected_service_role(group_name='development', profile_name='developer', role_name='pipeline')
    expected = {
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
            'history': []}}
    mock_save_service_roles_file.assert_called_once_with(expected)


def test_save_available_service_roles__empty_data(config, mocker):
    mock_save_service_roles_file = mocker.patch.object(files, "save_service_roles_file")

    config.save_available_service_roles(group_name='development', profile_name='developer',
                                        role_list=['pipeline'])
    expected = {
        'development': {
            'selected_profile': None,
            'selected_role': None,
            'available': {'developer': ['pipeline']},
            'history': []}}
    mock_save_service_roles_file.assert_called_once_with(expected)


def test_save_available_service_roles__update_loaded_data(config, mocker):
    mock_save_service_roles_file = mocker.patch.object(files, "save_service_roles_file")

    config.service_roles = get_test_service_roles()
    config.save_available_service_roles(group_name='development',
                                        profile_name='developer',
                                        role_list=['pipeline'])
    expected = {
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
            'history': []}}
    mock_save_service_roles_file.assert_called_once_with(expected)


def test_initialize_profile_groups(config):
    config.initialize_profile_groups(get_default_test_accounts(),
                                     get_test_service_roles(),
                                     'default-access-key',
                                     'default-sso-session',
                                     'default-sso-interval')

    assert ['development', 'live', 'gcp-project-dev'] == list(config.profile_groups.keys())

    development_group = config.get_group('development')
    assert 'development' == development_group.name
    assert 'awesome-team' == development_group.team
    assert 'us-east-1' == development_group.region
    assert '#388E3C' == development_group.color
    assert 'aws' == development_group.type
    assert 'default-access-key' == development_group.get_access_key()

    development_profile1 = development_group.profiles[0]
    assert development_group == development_profile1.group
    assert 'developer' == development_profile1.profile
    assert '123495678901' == development_profile1.account
    assert 'developer' == development_profile1.role
    assert True == development_profile1.default
    assert None == development_profile1.source

    development_profile2 = development_group.profiles[1]
    assert development_group == development_profile2.group
    assert 'readonly' == development_profile2.profile
    assert '012349567890' == development_profile2.account
    assert 'readonly' == development_profile2.role
    assert False == development_profile2.default
    assert None == development_profile2.source

    development_service_role = development_group.service_profile
    assert development_group == development_service_role.group
    assert 'service' == development_service_role.profile
    assert '123495678901' == development_service_role.account
    assert 'pipeline' == development_service_role.role
    assert False == development_service_role.default
    assert 'developer' == development_service_role.source

    live_group = config.get_group('live')
    assert 'access-key-123' == live_group.get_access_key()
    assert None == live_group.service_profile

    live_profile1 = live_group.profiles[0]
    assert live_group == live_profile1.group
    assert 'admin' == live_profile1.profile
    assert '9876543210' == live_profile1.account
    assert 'admin' == live_profile1.role
    assert True == live_profile1.default
    assert None == live_profile1.source

    live_profile2 = live_group.profiles[1]
    assert live_group == live_profile2.group
    assert 'readonly' == live_profile2.profile
    assert '0000000000' == live_profile2.account
    assert 'readonly' == live_profile2.role
    assert False == live_profile2.default
    assert None == live_profile2.source


def test_initialize_profile_groups__replace_old_values_on_config_reload(config):
    config.initialize_profile_groups(get_default_test_accounts(),
                                     get_test_service_roles(),
                                     'default-access-key',
                                     'defauls-sso-session',
                                     'default-sso-interval')
    config.initialize_profile_groups(get_test_accounts__minimal(),
                                     get_test_service_roles(),
                                     'default-access-key',
                                     'defauls-sso-session',
                                     'default-sso-interval')

    assert ['development'] == list(config.profile_groups.keys())

    development_group = config.get_group('development')
    assert 'development' == development_group.name
    assert 'awesome-team' == development_group.team
    assert 'us-east-1' == development_group.region
    assert '#388E3C' == development_group.color
    assert 'aws' == development_group.type
    assert 'default-access-key' == development_group.get_access_key()

    development_profile1 = development_group.profiles[0]
    assert development_group == development_profile1.group
    assert 'developer' == development_profile1.profile
    assert '123495678901' == development_profile1.account
    assert 'developer' == development_profile1.role
    assert True == development_profile1.default
    assert None == development_profile1.source

    assert 1 == len(development_group.profiles)


def test_set_default_sso_interval__string_none_sets_none(config):
    config.set_default_sso_interval('None')
    assert None == config.default_sso_interval


def test_set_default_sso_interval__stores_value(config):
    config.set_default_sso_interval('15')
    assert '15' == config.default_sso_interval


def test_add_to_history(config):
    history = ['profile-1 : role-1', 'profile-2 : role-2']
    result = config._add_to_history('profile-3', 'role-3', history)
    expected = ['profile-3 : role-3', 'profile-1 : role-1', 'profile-2 : role-2']
    assert expected == result


def test_add_to_history__deduplicates_and_limits(config):
    history = [f'profile-{i} : role-{i}' for i in range(1, 11)]
    history.append('profile-3 : role-3')

    result = config._add_to_history('profile-99', 'role-99', history)

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
    assert expected == result


def test_add_to_history__ignores_missing_profile_or_role(config):
    history = ['profile-1 : role-1']
    result = config._add_to_history(profile=None, role='role-2', history=list(history))
    assert history == result


def test_get_service_role_helpers(config):
    config.service_roles = {
        'dev': {
            'selected_profile': 'developer',
            'selected_role': 'pipeline',
            'available': {'developer': ['pipeline']},
            'history': ['developer : pipeline']
        }
    }

    assert 'developer' == config.get_selected_service_role_source_profile('dev')
    assert 'pipeline' == config.get_selected_service_role('dev')
    assert ['pipeline'] == config.get_available_service_roles('dev', 'developer')
    assert ['developer : pipeline'] == config.get_history('dev')


def test_get_service_role_helpers__defaults(config):
    assert None == config.get_selected_service_role_source_profile('unknown')
    assert None == config.get_selected_service_role('unknown')
    assert [] == config.get_available_service_roles('unknown', 'developer')
    assert [] == config.get_history('unknown')


def test_validate(config):
    config.initialize_profile_groups(get_default_test_accounts(),
                                     get_test_service_roles(),
                                     'default-access-key',
                                     'defauls-sso-session',
                                     'default-sso-interval')
    config.validate()
    assert '' == config.error
    assert config.valid


def test_validate_empty_config(config):
    config.validate()
    assert not config.valid
    assert 'config is empty' == config.error


def test_validate_calls_validate_and_use_return_value(config, mocker):
    mock_group1 = mocker.Mock()
    mock_group1.validate.return_value = True, 'no error'
    mock_group2 = mocker.Mock()
    mock_group2.validate.return_value = False, 'some error'
    mock_group3 = mocker.Mock()
    mock_group3.validate.return_value = True, 'everything is okay'

    config.profile_groups['1'] = mock_group1
    config.profile_groups['2'] = mock_group2
    config.profile_groups['3'] = mock_group3
    config.validate()
    assert 1 == mock_group1.validate.call_count
    assert 1 == mock_group2.validate.call_count
    assert 0 == mock_group3.validate.call_count

    assert not config.valid
    assert 'some error' == config.error


def test_list_groups(config):
    config.profile_groups = {
        '1': 'group 1',
        '2': 'group 2'
    }
    expected = ['group 1', 'group 2']
    assert expected == config.list_groups()


def test_get_group(config):
    config.profile_groups = {
        '1': 'group 1',
        '2': 'group 2'
    }
    expected = 'group 1'
    assert expected == config.get_group('1')


def test_to_dict(config, mocker):
    mock_group1 = mocker.Mock()
    mock_group1.to_dict.return_value = 'group 1'
    mock_group2 = mocker.Mock()
    mock_group2.to_dict.return_value = 'group 2'
    mock_group3 = mocker.Mock()
    mock_group3.to_dict.return_value = 'group 3'

    config.profile_groups['1'] = mock_group1
    config.profile_groups['2'] = mock_group2
    config.profile_groups['3'] = mock_group3

    result = config.to_dict()
    assert 1 == mock_group1.to_dict.call_count
    assert 1 == mock_group2.to_dict.call_count
    assert 1 == mock_group3.to_dict.call_count

    expected = {'1': 'group 1', '2': 'group 2', '3': 'group 3'}

    assert expected == result

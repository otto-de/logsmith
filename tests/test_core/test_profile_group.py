
import pytest
from unittest.mock import Mock

from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts
from tests.test_data.test_accounts import get_test_accounts__mixed_auth_modes, get_test_group, get_test_group__with_key, get_test_group__with_sso, get_test_group_no_default, \
    get_test_group_with_specific_access_key, get_test_group_with_specific_sso_session, get_test_profile_group


#######################
# Fixures


@pytest.fixture(scope="function")
def profile_group():
    return ProfileGroup('test', get_test_group(), 'default-key', 'default-session', 'default-sso-interval')

#######################
# Tests

def test_init__defaults(profile_group):
    assert 'test' == profile_group.name
    assert 'awesome-team' == profile_group.team
    assert 'us-east-1' == profile_group.region
    assert '#388E3C' == profile_group.color
    assert 'default-key' == profile_group.default_access_key
    assert 'default-session' == profile_group.default_sso_session
    assert 'key' == profile_group.auth_mode
    assert 'key' == profile_group.write_mode
    assert None == profile_group.access_key
    assert None == profile_group.sso_session
    assert './some-script.sh' == profile_group.script
    assert 'aws' == profile_group.type
    assert 2 == len(profile_group.profiles)
    
def test_init__sso_auth_modes():
    profile_group = ProfileGroup('test', get_test_group__with_sso(), 'default-key', 'default-session', 'default-sso-interval')
    assert 'test' == profile_group.name
    assert 'awesome-team' == profile_group.team
    assert 'us-east-1' == profile_group.region
    assert '#388E3C' == profile_group.color
    assert 'default-key' == profile_group.default_access_key
    assert 'default-session' == profile_group.default_sso_session
    assert 'sso' == profile_group.auth_mode
    assert 'sso' == profile_group.write_mode
    assert None == profile_group.access_key
    assert 'specific-sso-session' == profile_group.sso_session
    assert './some-script.sh' == profile_group.script
    assert 'aws' == profile_group.type
    assert 2 == len(profile_group.profiles)
    
def test_init__key_auth_modes():
    profile_group = ProfileGroup('test', get_test_group__with_key(), 'default-key', 'default-session', 'default-sso-interval')
    assert 'test' == profile_group.name
    assert 'awesome-team' == profile_group.team
    assert 'us-east-1' == profile_group.region
    assert '#388E3C' == profile_group.color
    assert 'default-key' == profile_group.default_access_key
    assert 'default-session' == profile_group.default_sso_session
    assert 'key' == profile_group.auth_mode
    assert 'key' == profile_group.write_mode
    assert 'specific-access-key' == profile_group.access_key
    assert None == profile_group.sso_session
    assert './some-script.sh' == profile_group.script
    assert 'aws' == profile_group.type
    assert 2 == len(profile_group.profiles)
    
def test_init__write_mode_override():
    group = {**get_test_group(), 'write_mode': 'sso'}
    profile_group = ProfileGroup('test', group, 'default-key', 'default-session', 'default-sso-interval')

    assert 'key' == profile_group.auth_mode
    assert 'sso' == profile_group.write_mode

def test_validate(profile_group):
    result = profile_group.validate()
    expected = (True, '')
    assert expected == result

def test_validate__no_team(profile_group):
    profile_group.team = None
    result = profile_group.validate()

    expected = (False, 'test has no team')
    assert expected == result

def test_validate__no_region(profile_group):
    profile_group.region = None
    result = profile_group.validate()

    expected = (False, 'test has no region')
    assert expected == result

def test_validate__no_color(profile_group):
    profile_group.color = None
    result = profile_group.validate()

    expected = (False, 'test has no color')
    assert expected == result
    
def test_validate__no_auth_mode(profile_group):
    profile_group.auth_mode = None
    result = profile_group.validate()

    expected = (False, 'test has an invalid auth_mode (either key or sso)')
    assert expected == result

def test_validate__auth_mode_malformed(profile_group):
    profile_group.auth_mode = 'no-auth'
    result = profile_group.validate()

    expected = (False, 'test has an invalid auth_mode (either key or sso)')
    assert expected == result

def test_validate__write_mode_malformed(profile_group):
    profile_group.write_mode = 'no-write-mode'
    result = profile_group.validate()

    expected = (False, 'test has an invalid write_mode (either key or sso)')
    assert expected == result

def test_validate__write_mode_incompatible_with_auth_mode(profile_group):
    profile_group.auth_mode = 'key'
    profile_group.write_mode = 'sso'
    result = profile_group.validate()

    expected = (False, "test has auth_mode 'key' and write_mode 'sso', \nwhich are not compatible")
    assert expected == result
    
def test_validate__access_key_malformed(profile_group):
    profile_group.access_key = 'no-key'
    result = profile_group.validate()

    expected = (False, 'access-key no-key must have the prefix \"access-key\"')
    assert expected == result
    
def test_validate__sso_session_malformed(profile_group):
    profile_group.sso_session = 'no-session'
    result = profile_group.validate()

    expected = (False, 'sso_session \"no-session\" must have the prefix \"sso\"')
    assert expected == result

def test_validate__sso_interval_malformed(profile_group):
    profile_group.sso_interval = 'not-an-int'
    result = profile_group.validate()

    expected = (False, 'sso_interval \"not-an-int\" must be a positive integer or 0')
    assert expected == result

def test_validate__aws_type_must_have_profiled(profile_group):
    profile_group.profiles = []
    result = profile_group.validate()

    expected = (False, 'aws \"test\" has no profiles')
    assert expected == result

def test_validate__gcp_allows_no_profiles():
    profile_group = ProfileGroup(
        'gcp-group',
        {
            'color': '#123456',
            'team': 'data',
            'region': 'europe-west1',
            'type': 'gcp',
            'profiles': []
        },
        'default-key',
        'default-session',
        'default-sso-interval'
    )

    result = profile_group.validate()
    assert (True, '') == result

def test_validate__calls_profile_validate(profile_group, mocker):
    mock_profile1 = mocker.Mock()
    mock_profile1.validate.return_value = True, 'no error'
    mock_profile2 = mocker.Mock()
    mock_profile2.validate.return_value = False, 'some error'
    mock_profile3 = mocker.Mock()
    mock_profile3.validate.return_value = True, 'everything is okay'

    profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]
    result = profile_group.validate()
    assert 1 == mock_profile1.validate.call_count
    assert 1 == mock_profile2.validate.call_count
    assert 0 == mock_profile3.validate.call_count

    expected = (False, 'some error')
    assert expected == result

def test_list_profile_names(profile_group):
    expected = ['developer', 'readonly', 'default']
    assert expected == profile_group.list_profile_names()

def test_list_profile_names__no_default():
    profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
    expected = ['developer', 'readonly']
    assert expected == profile_group.list_profile_names()

def test_get_default_profile(profile_group):
    result = profile_group.get_default_profile()
    assert 'readonly' == result.profile

def test_get_default_profile__no_default():
    profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
    result = profile_group.get_default_profile()
    assert None == result
    
def test_get_access_key__with_defaults():
    profile_group = test_accounts.get_test_profile_group()
    auth_mode = profile_group.get_auth_mode()
    access_key = profile_group.get_access_key()
    sso_session = profile_group.get_sso_session()
    assert 'key' == auth_mode
    assert 'some-access-key' == access_key
    assert 'some-sso-session' == sso_session

def test_get_access_key__with_specific_access_key():
    profile_group = test_accounts.get_test_profile_group_key()
    auth_mode = profile_group.get_auth_mode()
    access_key = profile_group.get_access_key()
    sso_session = profile_group.get_sso_session()
    assert 'key' == auth_mode
    assert 'specific-access-key' == access_key
    assert 'some-sso-session' == sso_session
    
def test_get_access_key__with_specific_sso_session():
    profile_group = test_accounts.get_test_profile_group_sso()
    auth_mode = profile_group.get_auth_mode()
    access_key = profile_group.get_access_key()
    sso_session = profile_group.get_sso_session()
    assert 'sso' == auth_mode
    assert 'some-access-key' == access_key
    assert 'specific-sso-session' == sso_session

def test_get_sso_interval__default(profile_group):
    assert 'default-sso-interval' == profile_group.get_sso_interval()

def test_get_sso_interval__specific_value():
    profile_group = ProfileGroup('test', {**get_test_group(), 'sso_interval': '5'}, 'default-key', 'default-session', '10')
    assert '5' == profile_group.get_sso_interval()

def test_to_dict():
    profile_group = get_test_profile_group()
    mock_profile1 = Mock()
    mock_profile1.to_dict.return_value = 'profile 1'
    mock_profile2 = Mock()
    mock_profile2.to_dict.return_value = 'profile 2'
    mock_profile3 = Mock()
    mock_profile3.to_dict.return_value = 'profile 3'
    profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

    result = profile_group.to_dict()
    assert 1 == mock_profile1.to_dict.call_count
    assert 1 == mock_profile2.to_dict.call_count
    assert 1 == mock_profile3.to_dict.call_count

    expected = {
        'color': '#388E3C',
        'profiles': ['profile 1', 'profile 2', 'profile 3'],
        'region': 'us-east-1',
        'team': 'awesome-team',
        'script': './some-script.sh',
        'auth_mode': 'key'
    }
    assert expected == result

def test_to_dict__with_write_mode_override():
    profile_group = ProfileGroup('test', {**get_test_group(), 'write_mode': 'sso'}, 'some-access-key', 'some-sso-session', 'some-sso-interval')
    mock_profile1 = Mock()
    mock_profile1.to_dict.return_value = 'profile 1'
    profile_group.profiles = [mock_profile1]

    result = profile_group.to_dict()
    assert 1 == mock_profile1.to_dict.call_count

    expected = {
        'color': '#388E3C',
        'profiles': ['profile 1'],
        'region': 'us-east-1',
        'team': 'awesome-team',
        'script': './some-script.sh',
        'auth_mode': 'key',
        'write_mode': 'sso'
    }
    assert expected == result

def test_to_dict__with_specific_access_key():
    profile_group = ProfileGroup('test', get_test_group_with_specific_access_key(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
    mock_profile1 = Mock()
    mock_profile1.to_dict.return_value = 'profile 1'
    mock_profile2 = Mock()
    mock_profile2.to_dict.return_value = 'profile 2'
    mock_profile3 = Mock()
    mock_profile3.to_dict.return_value = 'profile 3'
    profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

    result = profile_group.to_dict()
    assert 1 == mock_profile1.to_dict.call_count
    assert 1 == mock_profile2.to_dict.call_count
    assert 1 == mock_profile3.to_dict.call_count

    expected = {
        'color': '#388E3C',
        'profiles': ['profile 1', 'profile 2', 'profile 3'],
        'region': 'us-east-1',
        'team': 'awesome-team',
        'script': None,
        'auth_mode': 'key',
        'access_key': 'specific-access-key',
    }

    assert expected == result
    
def test_to_dict__with_specific_sso_session():
    profile_group = ProfileGroup('test', get_test_group_with_specific_sso_session(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
    mock_profile1 = Mock()
    mock_profile1.to_dict.return_value = 'profile 1'
    mock_profile2 = Mock()
    mock_profile2.to_dict.return_value = 'profile 2'
    mock_profile3 = Mock()
    mock_profile3.to_dict.return_value = 'profile 3'
    profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

    result = profile_group.to_dict()
    assert 1 == mock_profile1.to_dict.call_count
    assert 1 == mock_profile2.to_dict.call_count
    assert 1 == mock_profile3.to_dict.call_count

    expected = {
        'color': '#388E3C',
        'profiles': ['profile 1', 'profile 2', 'profile 3'],
        'region': 'us-east-1',
        'team': 'awesome-team',
        'script': None,
        'auth_mode': 'sso',
        'sso_session': 'specific-sso-session',
    }

    assert expected == result

def test_to_dict__with_specific_sso_interval():
    profile_group = ProfileGroup('test', {**get_test_group(), 'sso_interval': '5'}, 'some-access-key', 'some-sso-session', '10')
    mock_profile1 = Mock()
    mock_profile1.to_dict.return_value = 'profile 1'
    profile_group.profiles = [mock_profile1]

    result = profile_group.to_dict()
    assert 1 == mock_profile1.to_dict.call_count

    expected = {
        'color': '#388E3C',
        'profiles': ['profile 1'],
        'region': 'us-east-1',
        'team': 'awesome-team',
        'script': './some-script.sh',
        'auth_mode': 'key',
        'sso_interval': '5',
    }

    assert expected == result

def test_to_dict__gcp_includes_type():
    profile_group = ProfileGroup(
        'gcp-group',
        {
            'color': '#123456',
            'team': 'data',
            'region': 'europe-west1',
            'type': 'gcp',
            'profiles': []
        },
        'default-key',
        'default-session',
        'default-sso-interval'
    )

    result = profile_group.to_dict()
    expected = {
        'color': '#123456',
        'profiles': [],
        'region': 'europe-west1',
        'team': 'data',
        'script': None,
        'auth_mode': 'key',
        'type': 'gcp',
    }

    assert expected == result

def test_set_service_role_profile():
    profile_group = get_test_profile_group()
    profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

    result = profile_group.service_profile.to_dict()
    expected = {'account': '123456789012',
                'profile': 'service',
                'role': 'pipeline',
                'source': 'developer'}
    assert expected == result

def test_set_service_role_profile__source_profile_does_not_exist():
    profile_group = get_test_profile_group()
    profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

    assert None == profile_group.service_profile

def test_set_service_role_profile__source_profile_does_not_exist_resets_prior_service_role():
    profile_group = get_test_profile_group()
    profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

    result = profile_group.service_profile.to_dict()
    expected = {'account': '123456789012',
                'profile': 'service',
                'role': 'pipeline',
                'source': 'developer'}
    assert expected == result

    profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

    assert None == profile_group.service_profile

def test_get_profile_list():
    profile_group = get_test_profile_group()

    result = profile_group.get_profile_list()
    expected = [profile_group.profiles[0], profile_group.profiles[1]]

    assert expected == result

def test_get_profile_list__with_service_role():
    profile_group = get_test_profile_group()
    profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

    result = profile_group.get_profile_list(True)
    expected = [profile_group.profiles[0], profile_group.profiles[1], profile_group.service_profile]

    assert expected == result

def test_get_profile():
    profile_group = get_test_profile_group()

    result = profile_group.get_profile('developer')

    assert 'developer' == result.profile

def test_get_profile__non_existent_profile():
    profile_group = get_test_profile_group()
    assert None == profile_group.get_profile('dog')

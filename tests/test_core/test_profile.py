import pytest
from unittest.mock import Mock

from app.core.profile import Profile
from tests.test_data.test_accounts import get_test_profile, get_test_profile_no_default, get_test_profile_with_source

#######################
# Fixures


@pytest.fixture(scope="function")
def group_mock():
    group_mock = Mock()
    group_mock.name = 'test'
    return group_mock


@pytest.fixture(scope="function")
def profile(group_mock):
    return Profile(group_mock, get_test_profile())

#######################
# Tests


def test_profile(profile, group_mock):
    assert group_mock == profile.group
    assert 'readonly' == profile.profile
    assert '123456789012' == profile.account
    assert 'readonly-role' == profile.role
    assert True == profile.default
    assert None == profile.source


def test_profile_validate(profile):
    result = profile.validate()
    expected = (True, '')
    assert expected == result


def test_profile_validate__no_profile(profile):
    profile.profile = None
    result = profile.validate()

    expected = (False, 'a profile in test has no profile')
    assert expected == result


def test_profile_validate__no_account(profile):
    profile.account = None
    result = profile.validate()

    expected = (False, 'a profile in test has no account')
    assert expected == result


def test_profile_validate__no_role(profile):
    profile.role = None
    result = profile.validate()

    expected = (False, 'a profile in test has no role')
    assert expected == result


def test_profile_to_dict(profile):
    result = profile.to_dict()
    expected = {'account': '123456789012',
                'default': True,
                'profile': 'readonly',
                'role': 'readonly-role'}
    assert expected == result


def test_profile__no_default():
    profile = Profile('test', get_test_profile_no_default())
    assert 'readonly' == profile.profile
    assert '123456789012' == profile.account
    assert 'readonly-role' == profile.role
    assert False == profile.default
    assert None == profile.source


def test_profile_to_dict__no_default():
    profile = Profile('test', get_test_profile_no_default())
    result = profile.to_dict()
    expected = {'account': '123456789012', 'profile': 'readonly', 'role': 'readonly-role'}
    assert expected == result


def test_profile__with_source():
    profile = Profile('test', get_test_profile_with_source())
    assert 'readonly' == profile.profile
    assert '123456789012' == profile.account
    assert 'readonly-role' == profile.role
    assert False == profile.default
    assert 'some-source' == profile.source


def test_to_dict__with_source():
    profile = Profile('test', get_test_profile_with_source())
    result = profile.to_dict()
    expected = {'account': '123456789012', 'profile': 'readonly', 'role': 'readonly-role', 'source': 'some-source'}
    assert expected == result

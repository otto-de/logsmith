from unittest import TestCase
from unittest.mock import Mock

from app.core.config import Profile
from tests.test_data.test_accounts import get_test_profile, get_test_profile_no_default, get_test_profile_with_source


class TestProfile(TestCase):
    def setUp(self):
        self.group_mock = Mock()
        self.group_mock.name = 'test'
        self.profile = Profile(self.group_mock, get_test_profile())

    def test_profile(self):
        self.assertEqual(self.group_mock, self.profile.group)
        self.assertEqual('readonly', self.profile.profile)
        self.assertEqual('123456789012', self.profile.account)
        self.assertEqual('readonly-role', self.profile.role)
        self.assertEqual(True, self.profile.default)
        self.assertEqual(None, self.profile.source)

    def test_profile_validate(self):
        result = self.profile.validate()
        expected = (True, '')
        self.assertEqual(expected, result)

    def test_profile_validate__no_profile(self):
        self.profile.profile = None
        result = self.profile.validate()

        expected = (False, 'a profile in test has no profile')
        self.assertEqual(expected, result)

    def test_profile_validate__no_account(self):
        self.profile.account = None
        result = self.profile.validate()

        expected = (False, 'a profile in test has no account')
        self.assertEqual(expected, result)

    def test_profile_validate__no_role(self):
        self.profile.role = None
        result = self.profile.validate()

        expected = (False, 'a profile in test has no role')
        self.assertEqual(expected, result)

    def test_profile_to_dict(self):
        result = self.profile.to_dict()
        expected = {'account': '123456789012',
                    'default': True,
                    'profile': 'readonly',
                    'role': 'readonly-role'}
        self.assertEqual(expected, result)

    def test_profile__no_default(self):
        profile = Profile('test', get_test_profile_no_default())
        self.assertEqual('readonly', profile.profile)
        self.assertEqual('123456789012', profile.account)
        self.assertEqual('readonly-role', profile.role)
        self.assertEqual(False, profile.default)
        self.assertEqual(None, profile.source)

    def test_profile_to_dict__no_default(self):
        profile = Profile('test', get_test_profile_no_default())
        result = profile.to_dict()
        expected = {'account': '123456789012', 'profile': 'readonly', 'role': 'readonly-role'}
        self.assertEqual(expected, result)

    def test_profile__with_source(self):
        profile = Profile('test', get_test_profile_with_source())
        self.assertEqual('readonly', profile.profile)
        self.assertEqual('123456789012', profile.account)
        self.assertEqual('readonly-role', profile.role)
        self.assertEqual(False, profile.default)
        self.assertEqual('some-source', profile.source)

    def test_to_dict__with_source(self):
        profile = Profile('test', get_test_profile_with_source())
        result = profile.to_dict()
        expected = {'account': '123456789012', 'profile': 'readonly', 'role': 'readonly-role', 'source': 'some-source'}
        self.assertEqual(expected, result)

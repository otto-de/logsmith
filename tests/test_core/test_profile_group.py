from unittest import TestCase
from unittest.mock import Mock

from app.core.profile_group import ProfileGroup
from tests.test_data.test_accounts import get_test_group, get_test_group_no_default, \
    get_test_group_with_specific_access_key


class TestProfileGroup(TestCase):
    def setUp(self):
        self.profile_group = ProfileGroup('test', get_test_group(), 'default')

    def test_init(self):
        self.assertEqual('test', self.profile_group.name)
        self.assertEqual('awesome-team', self.profile_group.team)
        self.assertEqual('us-east-1', self.profile_group.region)
        self.assertEqual('#388E3C', self.profile_group.color)
        self.assertEqual('default', self.profile_group.default_access_key)
        self.assertEqual(None, self.profile_group.access_key)
        self.assertEqual('aws', self.profile_group.type)
        self.assertEqual(2, len(self.profile_group.profiles))

    def test_validate(self):
        result = self.profile_group.validate()
        expected = (True, '')
        self.assertEqual(expected, result)

    def test_validate__no_team(self):
        self.profile_group.team = None
        result = self.profile_group.validate()

        expected = (False, 'test has no team')
        self.assertEqual(expected, result)

    def test_validate__no_region(self):
        self.profile_group.region = None
        result = self.profile_group.validate()

        expected = (False, 'test has no region')
        self.assertEqual(expected, result)

    def test_validate__no_color(self):
        self.profile_group.color = None
        result = self.profile_group.validate()

        expected = (False, 'test has no color')
        self.assertEqual(expected, result)

    def test_validate__access_key_malformed(self):
        self.profile_group.access_key = 'no-key'
        result = self.profile_group.validate()

        expected = (False, 'access-key no-key must have the prefix \"access-key\"')
        self.assertEqual(expected, result)

    def test_validate__aws_type_must_have_profiled(self):
        self.profile_group.profiles = []
        result = self.profile_group.validate()

        expected = (False, 'aws \"test\" has no profiles')
        self.assertEqual(expected, result)

    def test_validate__calls_profile_validate(self):
        mock_profile1 = Mock()
        mock_profile1.validate.return_value = True, 'no error'
        mock_profile2 = Mock()
        mock_profile2.validate.return_value = False, 'some error'
        mock_profile3 = Mock()
        mock_profile3.validate.return_value = True, 'everything is okay'

        self.profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]
        result = self.profile_group.validate()
        self.assertEqual(1, mock_profile1.validate.call_count)
        self.assertEqual(1, mock_profile2.validate.call_count)
        self.assertEqual(0, mock_profile3.validate.call_count)

        expected = (False, 'some error')
        self.assertEqual(expected, result)

    def test_list_profile_names(self):
        expected = ['developer', 'readonly', 'default']
        self.assertEqual(expected, self.profile_group.list_profile_names())

    def test_list_profile_names__no_default(self):
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key')
        expected = ['developer', 'readonly']
        self.assertEqual(expected, profile_group.list_profile_names())

    def test_get_default_profile(self):
        result = self.profile_group.get_default_profile()
        self.assertEqual('readonly', result.profile)

    def test_get_default_profile__no_default(self):
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key')
        result = profile_group.get_default_profile()
        self.assertEqual(None, result)

    def test_get_access_key(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        result = profile_group.get_access_key()
        self.assertEqual('some-access-key', result)

    def test_get_access_key__with_specific_access_key(self):
        profile_group = ProfileGroup('test', get_test_group_with_specific_access_key(), 'some-access-key')
        result = profile_group.get_access_key()
        self.assertEqual('specific-access-key', result)

    def test_to_dict(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        mock_profile1 = Mock()
        mock_profile1.to_dict.return_value = 'profile 1'
        mock_profile2 = Mock()
        mock_profile2.to_dict.return_value = 'profile 2'
        mock_profile3 = Mock()
        mock_profile3.to_dict.return_value = 'profile 3'
        profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

        result = profile_group.to_dict()
        self.assertEqual(1, mock_profile1.to_dict.call_count)
        self.assertEqual(1, mock_profile2.to_dict.call_count)
        self.assertEqual(1, mock_profile3.to_dict.call_count)

        expected = {
            'color': '#388E3C',
            'profiles': ['profile 1', 'profile 2', 'profile 3'],
            'region': 'us-east-1',
            'team': 'awesome-team',
        }
        self.assertEqual(expected, result)

    def test_to_dict__with_specific_access_key(self):
        profile_group = ProfileGroup('test', get_test_group_with_specific_access_key(), 'some-access-key')
        mock_profile1 = Mock()
        mock_profile1.to_dict.return_value = 'profile 1'
        mock_profile2 = Mock()
        mock_profile2.to_dict.return_value = 'profile 2'
        mock_profile3 = Mock()
        mock_profile3.to_dict.return_value = 'profile 3'
        profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

        result = profile_group.to_dict()
        self.assertEqual(1, mock_profile1.to_dict.call_count)
        self.assertEqual(1, mock_profile2.to_dict.call_count)
        self.assertEqual(1, mock_profile3.to_dict.call_count)

        expected = {
            'color': '#388E3C',
            'profiles': ['profile 1', 'profile 2', 'profile 3'],
            'region': 'us-east-1',
            'team': 'awesome-team',
            'access_key': 'specific-access-key',
        }

        self.assertEqual(expected, result)

    def test_set_service_role_profile(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.service_profile.to_dict()
        expected = {'account': '123456789012',
                    'profile': 'service',
                    'role': 'pipeline',
                    'source': 'developer'}
        self.assertEqual(expected, result)

    def test_set_service_role_profile__source_profile_does_not_exist(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

        self.assertEqual(None, profile_group.service_profile)

    def test_set_service_role_profile__source_profile_does_not_exist_resets_prior_service_role(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.service_profile.to_dict()
        expected = {'account': '123456789012',
                    'profile': 'service',
                    'role': 'pipeline',
                    'source': 'developer'}
        self.assertEqual(expected, result)

        profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

        self.assertEqual(None, profile_group.service_profile)

    def test_get_profile_list__without_service_role(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')

        result = profile_group.get_profile_list()
        expected = [profile_group.profiles[0], profile_group.profiles[1]]

        self.assertEqual(expected, result)

    def test_get_profile_list__with_service_role(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.get_profile_list()
        expected = [profile_group.profiles[0], profile_group.profiles[1], profile_group.service_profile]

        self.assertEqual(expected, result)

    def test_get_profile(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')

        result = profile_group.get_profile('developer')

        self.assertEqual('developer', result.profile)

    def test_get_profile__non_existent_profile(self):
        profile_group = ProfileGroup('test', get_test_group(), 'some-access-key')
        self.assertEqual(None, profile_group.get_profile('dog'))

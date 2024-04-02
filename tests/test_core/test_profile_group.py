from unittest import TestCase
from unittest.mock import Mock

from app.core.config import ProfileGroup
from tests.test_data.test_accounts import get_test_group, get_test_group_no_default


class TestProfileGroup(TestCase):
    def setUp(self):
        self.profile_group = ProfileGroup('test', get_test_group(), 'default')

    def test_init(self):
        self.assertEqual('test', self.profile_group.name)
        self.assertEqual('awesome-team', self.profile_group.team)
        self.assertEqual('us-east-1', self.profile_group.region)
        self.assertEqual('#388E3C', self.profile_group.color)
        self.assertEqual(2, len(self.profile_group.profiles))

    def test_validate(self):
        result = self.profile_group.validate()

        expected = (True, '')
        self.assertEqual(expected, result)

    def test_validate_no_team(self):
        self.profile_group.team = None
        result = self.profile_group.validate()

        expected = (False, 'test has no team')
        self.assertEqual(expected, result)

    def test_validate_no_region(self):
        self.profile_group.region = None
        result = self.profile_group.validate()

        expected = (False, 'test has no region')
        self.assertEqual(expected, result)

    def test_validate_no_color(self):
        self.profile_group.color = None
        result = self.profile_group.validate()

        expected = (False, 'test has no color')
        self.assertEqual(expected, result)

    def test_validate_calls_profile_validate(self):
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

    def test_list_profile_names_no_default(self):
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key')
        expected = ['developer', 'readonly']
        self.assertEqual(expected, profile_group.list_profile_names())

    def test_get_default_profile(self):
        result = self.profile_group.get_default_profile()
        self.assertEqual('readonly', result.profile)

    def test_get_default_profile_no_default(self):
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key')
        result = profile_group.get_default_profile()
        self.assertEqual(None, result)

    def test_to_dict(self):
        mock_profile1 = Mock()
        mock_profile1.to_dict.return_value = 'profile 1'
        mock_profile2 = Mock()
        mock_profile2.to_dict.return_value = 'profile 2'
        mock_profile3 = Mock()
        mock_profile3.to_dict.return_value = 'profile 3'
        self.profile_group.profiles = [mock_profile1, mock_profile2, mock_profile3]

        result = self.profile_group.to_dict()
        self.assertEqual(1, mock_profile1.to_dict.call_count)
        self.assertEqual(1, mock_profile2.to_dict.call_count)
        self.assertEqual(1, mock_profile3.to_dict.call_count)

        expected = {
            'color': '#388E3C',
            'profiles': ['profile 1', 'profile 2', 'profile 3'],
            'region': 'us-east-1',
            'team': 'awesome-team',
            'access_key': None,
        }

        self.assertEqual(expected, result)

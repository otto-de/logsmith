from unittest import TestCase
from unittest.mock import Mock

from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts
from tests.test_data.test_accounts import get_test_accounts__mixed_auth_modes, get_test_group, get_test_group__with_key, get_test_group__with_sso, get_test_group_no_default, \
    get_test_group_with_specific_access_key, get_test_group_with_specific_sso_session, get_test_profile_group


class TestProfileGroup(TestCase):
    def setUp(self):
        self.profile_group = ProfileGroup('test', get_test_group(), 'default-key', 'default-session', 'default-sso-interval')

    def test_init__defaults(self):
        self.assertEqual('test', self.profile_group.name)
        self.assertEqual('awesome-team', self.profile_group.team)
        self.assertEqual('us-east-1', self.profile_group.region)
        self.assertEqual('#388E3C', self.profile_group.color)
        self.assertEqual('default-key', self.profile_group.default_access_key)
        self.assertEqual('default-session', self.profile_group.default_sso_session)
        self.assertEqual('key', self.profile_group.auth_mode)
        self.assertEqual('key', self.profile_group.write_mode)
        self.assertEqual(None, self.profile_group.access_key)
        self.assertEqual(None, self.profile_group.sso_session)
        self.assertEqual('./some-script.sh', self.profile_group.script)
        self.assertEqual('aws', self.profile_group.type)
        self.assertEqual(2, len(self.profile_group.profiles))
        
    def test_init__sso_auth_modes(self):
        self.profile_group = ProfileGroup('test', get_test_group__with_sso(), 'default-key', 'default-session', 'default-sso-interval')
        self.assertEqual('test', self.profile_group.name)
        self.assertEqual('awesome-team', self.profile_group.team)
        self.assertEqual('us-east-1', self.profile_group.region)
        self.assertEqual('#388E3C', self.profile_group.color)
        self.assertEqual('default-key', self.profile_group.default_access_key)
        self.assertEqual('default-session', self.profile_group.default_sso_session)
        self.assertEqual('sso', self.profile_group.auth_mode)
        self.assertEqual('sso', self.profile_group.write_mode)
        self.assertEqual(None, self.profile_group.access_key)
        self.assertEqual('specific-sso-session', self.profile_group.sso_session)
        self.assertEqual('./some-script.sh', self.profile_group.script)
        self.assertEqual('aws', self.profile_group.type)
        self.assertEqual(2, len(self.profile_group.profiles))        
        
    def test_init__key_auth_modes(self):
        self.profile_group = ProfileGroup('test', get_test_group__with_key(), 'default-key', 'default-session', 'default-sso-interval')
        self.assertEqual('test', self.profile_group.name)
        self.assertEqual('awesome-team', self.profile_group.team)
        self.assertEqual('us-east-1', self.profile_group.region)
        self.assertEqual('#388E3C', self.profile_group.color)
        self.assertEqual('default-key', self.profile_group.default_access_key)
        self.assertEqual('default-session', self.profile_group.default_sso_session)
        self.assertEqual('key', self.profile_group.auth_mode)
        self.assertEqual('key', self.profile_group.write_mode)
        self.assertEqual('specific-access-key', self.profile_group.access_key)
        self.assertEqual(None, self.profile_group.sso_session)
        self.assertEqual('./some-script.sh', self.profile_group.script)
        self.assertEqual('aws', self.profile_group.type)
        self.assertEqual(2, len(self.profile_group.profiles))
        
    def test_init__write_mode_override(self):
        group = {**get_test_group(), 'write_mode': 'sso'}
        profile_group = ProfileGroup('test', group, 'default-key', 'default-session', 'default-sso-interval')

        self.assertEqual('key', profile_group.auth_mode)
        self.assertEqual('sso', profile_group.write_mode)

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
        
    def test_validate__no_auth_mode(self):
        self.profile_group.auth_mode = None
        result = self.profile_group.validate()

        expected = (False, 'test has an invalid auth_mode (either key or sso)')
        self.assertEqual(expected, result)

    def test_validate__auth_mode_malformed(self):
        self.profile_group.auth_mode = 'no-auth'
        result = self.profile_group.validate()

        expected = (False, 'test has an invalid auth_mode (either key or sso)')
        self.assertEqual(expected, result)

    def test_validate__write_mode_malformed(self):
        self.profile_group.write_mode = 'no-write-mode'
        result = self.profile_group.validate()

        expected = (False, 'test has an invalid write_mode (either key or sso)')
        self.assertEqual(expected, result)

    def test_validate__write_mode_incompatible_with_auth_mode(self):
        self.profile_group.auth_mode = 'key'
        self.profile_group.write_mode = 'sso'
        result = self.profile_group.validate()

        expected = (False, "test has auth_mode 'key' and write_mode 'sso', \nwhich are not compatible")
        self.assertEqual(expected, result)
        
    def test_validate__access_key_malformed(self):
        self.profile_group.access_key = 'no-key'
        result = self.profile_group.validate()

        expected = (False, 'access-key no-key must have the prefix \"access-key\"')
        self.assertEqual(expected, result)
        
    def test_validate__sso_session_malformed(self):
        self.profile_group.sso_session = 'no-session'
        result = self.profile_group.validate()

        expected = (False, 'sso_session \"no-session\" must have the prefix \"sso\"')
        self.assertEqual(expected, result)

    def test_validate__sso_interval_malformed(self):
        self.profile_group.sso_interval = 'not-an-int'
        result = self.profile_group.validate()

        expected = (False, 'sso_interval \"not-an-int\" must be a positive integer or 0')
        self.assertEqual(expected, result)

    def test_validate__aws_type_must_have_profiled(self):
        self.profile_group.profiles = []
        result = self.profile_group.validate()

        expected = (False, 'aws \"test\" has no profiles')
        self.assertEqual(expected, result)

    def test_validate__gcp_allows_no_profiles(self):
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
        self.assertEqual((True, ''), result)

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
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
        expected = ['developer', 'readonly']
        self.assertEqual(expected, profile_group.list_profile_names())

    def test_get_default_profile(self):
        result = self.profile_group.get_default_profile()
        self.assertEqual('readonly', result.profile)

    def test_get_default_profile__no_default(self):
        profile_group = ProfileGroup('test', get_test_group_no_default(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
        result = profile_group.get_default_profile()
        self.assertEqual(None, result)
        
    def test_get_access_key__with_defaults(self):
        profile_group = test_accounts.get_test_profile_group()
        auth_mode = profile_group.get_auth_mode()
        access_key = profile_group.get_access_key()
        sso_session = profile_group.get_sso_session()
        self.assertEqual('key', auth_mode)
        self.assertEqual('some-access-key', access_key)
        self.assertEqual('some-sso-session', sso_session)

    def test_get_access_key__with_specific_access_key(self):
        profile_group = test_accounts.get_test_profile_group_key()
        auth_mode = profile_group.get_auth_mode()
        access_key = profile_group.get_access_key()
        sso_session = profile_group.get_sso_session()
        self.assertEqual('key', auth_mode)
        self.assertEqual('specific-access-key', access_key)
        self.assertEqual('some-sso-session', sso_session)
        
    def test_get_access_key__with_specific_sso_session(self):
        profile_group = test_accounts.get_test_profile_group_sso()
        auth_mode = profile_group.get_auth_mode()
        access_key = profile_group.get_access_key()
        sso_session = profile_group.get_sso_session()
        self.assertEqual('sso', auth_mode)
        self.assertEqual('some-access-key', access_key)
        self.assertEqual('specific-sso-session', sso_session)

    def test_get_sso_interval__default(self):
        self.assertEqual('default-sso-interval', self.profile_group.get_sso_interval())

    def test_get_sso_interval__specific_value(self):
        profile_group = ProfileGroup('test', {**get_test_group(), 'sso_interval': '5'}, 'default-key', 'default-session', '10')
        self.assertEqual('5', profile_group.get_sso_interval())

    def test_to_dict(self):
        profile_group = get_test_profile_group()
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
            'script': './some-script.sh',
            'auth_mode': 'key'
        }
        self.assertEqual(expected, result)

    def test_to_dict__with_write_mode_override(self):
        profile_group = ProfileGroup('test', {**get_test_group(), 'write_mode': 'sso'}, 'some-access-key', 'some-sso-session', 'some-sso-interval')
        mock_profile1 = Mock()
        mock_profile1.to_dict.return_value = 'profile 1'
        profile_group.profiles = [mock_profile1]

        result = profile_group.to_dict()
        self.assertEqual(1, mock_profile1.to_dict.call_count)

        expected = {
            'color': '#388E3C',
            'profiles': ['profile 1'],
            'region': 'us-east-1',
            'team': 'awesome-team',
            'script': './some-script.sh',
            'auth_mode': 'key',
            'write_mode': 'sso'
        }
        self.assertEqual(expected, result)

    def test_to_dict__with_specific_access_key(self):
        profile_group = ProfileGroup('test', get_test_group_with_specific_access_key(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
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
            'script': None,
            'auth_mode': 'key',
            'access_key': 'specific-access-key',
        }

        self.assertEqual(expected, result)
        
    def test_to_dict__with_specific_sso_session(self):
        profile_group = ProfileGroup('test', get_test_group_with_specific_sso_session(), 'some-access-key', 'some-sso-session', 'some-sso-interval')
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
            'script': None,
            'auth_mode': 'sso',
            'sso_session': 'specific-sso-session',
        }

        self.assertEqual(expected, result)

    def test_to_dict__with_specific_sso_interval(self):
        profile_group = ProfileGroup('test', {**get_test_group(), 'sso_interval': '5'}, 'some-access-key', 'some-sso-session', '10')
        mock_profile1 = Mock()
        mock_profile1.to_dict.return_value = 'profile 1'
        profile_group.profiles = [mock_profile1]

        result = profile_group.to_dict()
        self.assertEqual(1, mock_profile1.to_dict.call_count)

        expected = {
            'color': '#388E3C',
            'profiles': ['profile 1'],
            'region': 'us-east-1',
            'team': 'awesome-team',
            'script': './some-script.sh',
            'auth_mode': 'key',
            'sso_interval': '5',
        }

        self.assertEqual(expected, result)

    def test_to_dict__gcp_includes_type(self):
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

        self.assertEqual(expected, result)

    def test_set_service_role_profile(self):
        profile_group = get_test_profile_group()
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.service_profile.to_dict()
        expected = {'account': '123456789012',
                    'profile': 'service',
                    'role': 'pipeline',
                    'source': 'developer'}
        self.assertEqual(expected, result)

    def test_set_service_role_profile__source_profile_does_not_exist(self):
        profile_group = get_test_profile_group()
        profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

        self.assertEqual(None, profile_group.service_profile)

    def test_set_service_role_profile__source_profile_does_not_exist_resets_prior_service_role(self):
        profile_group = get_test_profile_group()
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.service_profile.to_dict()
        expected = {'account': '123456789012',
                    'profile': 'service',
                    'role': 'pipeline',
                    'source': 'developer'}
        self.assertEqual(expected, result)

        profile_group.set_service_role_profile(source_profile_name='non-existent', role_name='pipeline')

        self.assertEqual(None, profile_group.service_profile)

    def test_get_profile_list(self):
        profile_group = get_test_profile_group()

        result = profile_group.get_profile_list()
        expected = [profile_group.profiles[0], profile_group.profiles[1]]

        self.assertEqual(expected, result)

    def test_get_profile_list__with_service_role(self):
        profile_group = get_test_profile_group()
        profile_group.set_service_role_profile(source_profile_name='developer', role_name='pipeline')

        result = profile_group.get_profile_list(True)
        expected = [profile_group.profiles[0], profile_group.profiles[1], profile_group.service_profile]

        self.assertEqual(expected, result)

    def test_get_profile(self):
        profile_group = get_test_profile_group()

        result = profile_group.get_profile('developer')

        self.assertEqual('developer', result.profile)

    def test_get_profile__non_existent_profile(self):
        profile_group = get_test_profile_group()
        self.assertEqual(None, profile_group.get_profile('dog'))

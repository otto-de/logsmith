import os
from unittest import TestCase, mock
from unittest.mock import Mock, call

from botocore.exceptions import ClientError, EndpointConnectionError, ParamValidationError, \
    NoCredentialsError, ReadTimeoutError

from app.aws import credentials
from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts

script_dir = os.path.dirname(os.path.realpath(__file__))


class TestCredentials(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_credentials_file_path = f'{script_dir}/../test_resources/credential_file'
        cls.test_credentials_file_path_without_keys = f'{script_dir}/../test_resources/credential_file_no_key'
        cls.mock_credentials = Mock()

        parsed_response = {'Error': {'Code': '500', 'Message': 'Error'}}
        cls.client_error = ClientError(parsed_response, 'test')
        cls.param_validation_error = ParamValidationError(report='test')
        cls.no_credentials_error = NoCredentialsError()
        cls.endpoint_error = EndpointConnectionError(endpoint_url='test')
        cls.timeout_error = ReadTimeoutError(endpoint_url='test')

        cls.test_secrets = {'AccessKeyId': 'test-key-id',
                            'SecretAccessKey': 'test-access-key',
                            'SessionToken': 'test-session-token'}

    @mock.patch('app.aws.credentials.Path.home', return_value='home')
    def test___get_credentials_path(self, _):
        self.assertEqual('home/.aws/credentials', credentials._get_credentials_path())

    @mock.patch('app.aws.credentials.Path.home', return_value='home')
    def test___get_config_path(self, _):
        self.assertEqual('home/.aws/config', credentials._get_config_path())

    def test___load_file(self):
        config_parser = credentials._load_file(self.test_credentials_file_path)
        self.assertEqual('some_key_id', config_parser.get(section='access-key', option='aws_access_key_id'))
        self.assertEqual('some_access_key', config_parser.get(section='access-key', option='aws_secret_access_key'))

    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_has_access_key(self, mock_path):
        mock_path.return_value = self.test_credentials_file_path
        result = credentials.has_access_key('access-key')

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_has_access_key__no_access_key(self, mock_path):
        mock_path.return_value = self.test_credentials_file_path_without_keys
        result = credentials.has_access_key('access-key')

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('could not find access-key \'access-key\' in .aws/credentials', result.error_message)

    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_check_session__no_session_found(self, mock_path):
        mock_path.return_value = self.test_credentials_file_path_without_keys

        result = credentials.check_session('access-key')

        self.assertEqual(False, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.aws.credentials._get_client')
    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_check_session(self, mock_path, mock_get_client):
        mock_path.return_value = self.test_credentials_file_path

        result = credentials.check_session('access-key')
        expected_calls = [
            call('session-token-access-key', 'sts', timeout=2, retries=2),
            call().get_caller_identity()
        ]
        self.assertEqual(expected_calls, mock_get_client.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.aws.credentials._get_client')
    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_check_session__invalid_session(self, mock_path, mock_get_client):
        mock_path.return_value = self.test_credentials_file_path
        mock_client = Mock()
        mock_client.get_caller_identity.side_effect = self.client_error
        mock_get_client.return_value = mock_client

        result = credentials.check_session('access-key')

        self.assertEqual(False, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.aws.credentials._get_client')
    @mock.patch('app.aws.credentials._get_credentials_path')
    def test_check_session__connection_timeout(self, mock_path, mock_get_client):
        mock_path.return_value = self.test_credentials_file_path
        mock_client = Mock()
        mock_client.get_caller_identity.side_effect = self.timeout_error
        mock_get_client.return_value = mock_client

        result = credentials.check_session('access-key')

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._add_profile_credentials')
    @mock.patch('app.aws.credentials._get_session_token')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_session_token(self, mock_credentials, mock_session, mock_add_profile, mock_write):
        mock_session.return_value = self.test_secrets

        result = credentials.fetch_session_token('some-access-key', 'mfa-token')

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)
        expected = call(mock_credentials.return_value,
                        'session-token-some-access-key',
                        {'AccessKeyId': 'test-key-id',
                         'SecretAccessKey': 'test-access-key',
                         'SessionToken': 'test-session-token'})
        self.assertEqual(expected, mock_add_profile.call_args)

        expected = call(mock_credentials.return_value)
        self.assertEqual(expected, mock_write.call_args)

    @mock.patch('app.aws.credentials._get_session_token')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_session_token__client_error(self, _, mock_session):
        mock_session.return_value = {}
        mock_session.side_effect = self.client_error

        result = credentials.fetch_session_token('some-access-key', 'mfa-token')

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('could not fetch session token', result.error_message)

    @mock.patch('app.aws.credentials._get_session_token')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_session_token__client_error(self, _, mock_session):
        mock_session.return_value = {}
        mock_session.side_effect = self.param_validation_error

        result = credentials.fetch_session_token('some-access-key', 'mfa-token')

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('invalid mfa token', result.error_message)

    @mock.patch('app.aws.credentials._get_session_token')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_session_token__no_credentials_error(self, _, mock_session):
        mock_session.return_value = {}
        mock_session.side_effect = self.no_credentials_error

        result = credentials.fetch_session_token('some-access-key', 'mfa-token')

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('access_key credentials invalid', result.error_message)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._remove_unused_profiles')
    @mock.patch('app.aws.credentials._add_profile_credentials')
    @mock.patch('app.aws.credentials._assume_role')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_role_credentials(self, mock_credentials, mock_assume, mock_add_profile, mock_remove_profile,
                                    mock_write_credentials):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser
        mock_assume.return_value = self.test_secrets

        profile_group = ProfileGroup('test', test_accounts.get_test_group(), 'default-access-key')
        result = credentials.fetch_role_credentials('test_user', profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual(3, mock_write_credentials.call_count)

        expected_mock_assume_calls = [
            call('session-token-default-access-key', 'test_user', '123456789012', 'developer'),
            call('session-token-default-access-key', 'test_user', '012345678901', 'readonly')
        ]
        self.assertEqual(expected_mock_assume_calls, mock_assume.call_args_list)

        expected_mock_add_profile_calls = [
            call(mock_config_parser, 'developer', {'AccessKeyId': 'test-key-id',
                                                   'SecretAccessKey': 'test-access-key',
                                                   'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'readonly', {'AccessKeyId': 'test-key-id',
                                                  'SecretAccessKey': 'test-access-key',
                                                  'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'default', {'AccessKeyId': 'test-key-id',
                                                 'SecretAccessKey': 'test-access-key',
                                                 'SessionToken': 'test-session-token'})]
        self.assertEqual(expected_mock_add_profile_calls, mock_add_profile.call_args_list)
        expected_mock_remove_profile_calls = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._remove_unused_profiles')
    @mock.patch('app.aws.credentials._add_profile_credentials')
    @mock.patch('app.aws.credentials._assume_role')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_role_credentials_with_specific_access_key(self, mock_credentials, mock_assume, mock_add_profile,
                                                             mock_remove_profile,
                                                             mock_write_credentials):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser
        mock_assume.return_value = self.test_secrets

        profile_group = ProfileGroup('test', test_accounts.get_test_group_with_specific_access_key(),
                                     'default-access-key')
        result = credentials.fetch_role_credentials('test_user', profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual(3, mock_write_credentials.call_count)

        expected_mock_assume_calls = [
            call('session-token-specific-access-key', 'test_user', '123456789012', 'developer'),
            call('session-token-specific-access-key', 'test_user', '012345678901', 'readonly')
        ]
        self.assertEqual(expected_mock_assume_calls, mock_assume.call_args_list)

        expected_mock_add_profile_calls = [
            call(mock_config_parser, 'developer', {'AccessKeyId': 'test-key-id',
                                                   'SecretAccessKey': 'test-access-key',
                                                   'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'readonly', {'AccessKeyId': 'test-key-id',
                                                  'SecretAccessKey': 'test-access-key',
                                                  'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'default', {'AccessKeyId': 'test-key-id',
                                                 'SecretAccessKey': 'test-access-key',
                                                 'SessionToken': 'test-session-token'})]
        self.assertEqual(expected_mock_add_profile_calls, mock_add_profile.call_args_list)
        expected_mock_remove_profile_calls = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._remove_unused_profiles')
    @mock.patch('app.aws.credentials._add_profile_credentials')
    @mock.patch('app.aws.credentials._assume_role')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_role_credentials__no_default(self, mock_credentials, mock_assume, mock_add_profile,
                                                mock_remove_profile, mock_write_credentials):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser
        mock_assume.return_value = self.test_secrets

        profile_group = ProfileGroup('test', test_accounts.get_test_group_no_default(), 'default-access-key')
        result = credentials.fetch_role_credentials('test-user', profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual(3, mock_write_credentials.call_count)

        expected_mock_assume_calls = [
            call('session-token-default-access-key', 'test-user', '123456789012', 'developer'),
            call('session-token-default-access-key', 'test-user', '012345678901', 'readonly')
        ]
        self.assertEqual(expected_mock_assume_calls, mock_assume.call_args_list)

        expected_mock_add_profile_calls = [
            call(mock_config_parser, 'developer', {'AccessKeyId': 'test-key-id',
                                                   'SecretAccessKey': 'test-access-key',
                                                   'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'readonly', {'AccessKeyId': 'test-key-id',
                                                  'SecretAccessKey': 'test-access-key',
                                                  'SessionToken': 'test-session-token'})]
        self.assertEqual(expected_mock_add_profile_calls, mock_add_profile.call_args_list)
        expected_mock_remove_profile_calls = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._remove_unused_profiles')
    @mock.patch('app.aws.credentials._add_profile_credentials')
    @mock.patch('app.aws.credentials._assume_role')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_fetch_role_credentials__chain_assume(self, mock_credentials, mock_assume, mock_add_profile,
                                                  mock_remove_profile, mock_write_credentials):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser
        mock_assume.return_value = self.test_secrets

        profile_group = ProfileGroup('test', test_accounts.get_test_group_chain_assume(), 'default-access-key')
        result = credentials.fetch_role_credentials('test-user', profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual(3, mock_write_credentials.call_count)

        expected_mock_assume_calls = [
            call('session-token-default-access-key', 'test-user', '123456789012', 'developer'),
            call('developer', 'test-user', '012345678901', 'service')
        ]
        self.assertEqual(expected_mock_assume_calls, mock_assume.call_args_list)

        expected_mock_add_profile_calls = [
            call(mock_config_parser, 'developer', {'AccessKeyId': 'test-key-id',
                                                   'SecretAccessKey': 'test-access-key',
                                                   'SessionToken': 'test-session-token'}),
            call(mock_config_parser, 'service', {'AccessKeyId': 'test-key-id',
                                                 'SecretAccessKey': 'test-access-key',
                                                 'SessionToken': 'test-session-token'})]
        self.assertEqual(expected_mock_add_profile_calls, mock_add_profile.call_args_list)

        expected_mock_remove_profile_calls = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)
        self.assertEqual(expected_mock_remove_profile_calls, mock_remove_profile.call_args_list)

    def test__remove_unused_profiles(self):
        mock_config_parser = Mock()
        mock_config_parser.sections.return_value = [
            'developer', 'unused-profile',
            'access-key', 'session-token-access-key',
            'access-key-2', 'session-token-access-key-2'
        ]

        mock_profile_group = Mock()
        mock_profile_group.list_profile_names.return_value = ['developer']

        credentials._remove_unused_profiles(mock_config_parser, mock_profile_group)

        expected = [call('unused-profile')]
        self.assertEqual(expected, mock_config_parser.remove_section.call_args_list)

    @mock.patch('app.aws.credentials._write_config_file')
    @mock.patch('app.aws.credentials._remove_unused_configs')
    @mock.patch('app.aws.credentials._add_profile_config')
    @mock.patch('app.aws.credentials._load_config_file')
    def test_write_profile_config(self, mock_credentials, mock_add_profile, mock_remove_profile, _):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser

        profile_group = ProfileGroup('test', test_accounts.get_test_group(), 'default')
        result = credentials.write_profile_config(profile_group, 'us-east-12')

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected = [call(mock_config_parser, 'developer', 'us-east-12'),
                    call(mock_config_parser, 'readonly', 'us-east-12'),
                    call(mock_config_parser, 'default', 'us-east-12')]
        self.assertEqual(expected, mock_add_profile.call_args_list)
        expected = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected, mock_remove_profile.call_args_list)
        self.assertEqual(expected, mock_remove_profile.call_args_list)

    @mock.patch('app.aws.credentials._write_config_file')
    @mock.patch('app.aws.credentials._remove_unused_configs')
    @mock.patch('app.aws.credentials._add_profile_config')
    @mock.patch('app.aws.credentials._load_config_file')
    def test_write_profile_config__no_default_region(self, mock_credentials, mock_add_profile, mock_remove_profile, _):
        mock_config_parser = Mock()
        mock_credentials.return_value = mock_config_parser

        profile_group = ProfileGroup('test', test_accounts.get_test_group_no_default(), 'default')
        result = credentials.write_profile_config(profile_group, 'us-east-12')

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected = [call(mock_config_parser, 'developer', 'us-east-12'),
                    call(mock_config_parser, 'readonly', 'us-east-12')]
        self.assertEqual(expected, mock_add_profile.call_args_list)
        expected = [call(mock_config_parser, profile_group)]
        self.assertEqual(expected, mock_remove_profile.call_args_list)
        self.assertEqual(expected, mock_remove_profile.call_args_list)

    def test__remove_unused_configs(self):
        mock_config_parser = Mock()
        mock_config_parser.sections.return_value = ['profile developer',
                                                    'profile unused-profile',
                                                    'profile access-key',
                                                    'profile session-token']

        mock_profile_group = Mock()
        mock_profile_group.list_profile_names.return_value = ['developer']

        credentials._remove_unused_configs(mock_config_parser, mock_profile_group)

        expected = [call('profile unused-profile'),
                    call('profile access-key'),
                    call('profile session-token')]
        self.assertEqual(expected, mock_config_parser.remove_section.call_args_list)

    @mock.patch('app.aws.credentials._write_credentials_file')
    @mock.patch('app.aws.credentials._load_credentials_file')
    def test_set_access_key(self, mock_load_credentials_file, _):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False
        mock_load_credentials_file.return_value = mock_config_parser

        result = credentials.set_access_key('key-name', 'key-id', 'access-key')
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual([call('key-name')],
                         mock_config_parser.has_section.call_args_list)
        self.assertEqual([call('key-name')],
                         mock_config_parser.add_section.call_args_list)
        self.assertEqual([call('key-name', 'aws_access_key_id', 'key-id'),
                          call('key-name', 'aws_secret_access_key', 'access-key')],
                         mock_config_parser.set.call_args_list)

    def test__add_profile_credentials(self):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False

        credentials._add_profile_credentials(mock_config_parser, 'test-profile', self.test_secrets)
        self.assertEqual([call('test-profile')],
                         mock_config_parser.has_section.call_args_list)
        self.assertEqual([call('test-profile')],
                         mock_config_parser.add_section.call_args_list)
        self.assertEqual([call('test-profile', 'aws_access_key_id', 'test-key-id'),
                          call('test-profile', 'aws_secret_access_key', 'test-access-key'),
                          call('test-profile', 'aws_session_token', 'test-session-token')],
                         mock_config_parser.set.call_args_list)

    def test__add_profile_config(self):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False

        credentials._add_profile_config(mock_config_parser, 'test-profile', 'us-east-12')
        self.assertEqual([call('profile test-profile')],
                         mock_config_parser.has_section.call_args_list)
        self.assertEqual([call('profile test-profile')],
                         mock_config_parser.add_section.call_args_list)
        self.assertEqual([call('profile test-profile', 'region', 'us-east-12'),
                          call('profile test-profile', 'output', 'json')],
                         mock_config_parser.set.call_args_list)

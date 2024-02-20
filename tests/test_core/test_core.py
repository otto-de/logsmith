from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from app.core.result import Result
from app.core.core import Core
from tests.test_data.test_accounts import get_test_accounts
from tests.test_data.test_results import get_success_result, get_error_result, get_failed_result


class TestCore(TestCase):

    @mock.patch('app.core.core.Config.load_from_disk')
    def setUp(self, mock_config):
        self.core = Core()
        self.config = Config()
        self.config.set_accounts(get_test_accounts())
        self.core.config = self.config

        self.success_result = get_success_result()
        self.fail_result = get_failed_result()
        self.error_result = get_error_result()

    @mock.patch('app.core.core.credentials')
    def test_login__no_access_key(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.error_result
        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key()]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.credentials')
    def test_login__session_token_error(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.error_result

        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key(), call.check_session()]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.credentials')
    def test_login__mfa_error(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.fail_result
        self.core._renew_session = Mock()
        self.core._renew_session.return_value = self.error_result

        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key(), call.check_session()]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call(None)]
        self.assertEqual(expected, self.core._renew_session.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.files')
    @mock.patch('app.core.core.credentials')
    def test_login__successful_login(self, mock_credentials, _):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.success_result
        self.core._renew_session = Mock()
        self.core._renew_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.fetch_role_credentials.return_value = self.success_result
        mock_credentials.write_profile_config.return_value = self.success_result
        self.core._handle_support_files = Mock()

        mock_mfa_callback = Mock()
        profile_group = self.config.get_group('development')
        result = self.core.login(profile_group, mock_mfa_callback)

        expected = [call.check_access_key(),
                    call.check_session(),
                    call.get_user_name(),
                    call.fetch_role_credentials('test-user', profile_group),
                    call.write_profile_config(profile_group, 'us-east-1')]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call(profile_group)]
        self.assertEqual(expected, self.core._handle_support_files.mock_calls)

        self.assertEqual(profile_group, self.core.active_profile_group)
        self.assertEqual(None, self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test_login__logout(self, mock_credentials):
        mock_credentials.fetch_role_credentials.return_value = self.success_result
        mock_credentials.write_profile_config.return_value = self.success_result

        result = self.core.logout()

        expected = [call.fetch_role_credentials(user_name='none', profile_group=self.core.empty_profile_group),
                    call.write_profile_config(profile_group=self.core.empty_profile_group, region='')]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test_login__logout_error(self, mock_credentials):
        mock_credentials.fetch_role_credentials.return_value = self.error_result

        result = self.core.logout()

        expected = [call.fetch_role_credentials(user_name='none', profile_group=self.core.empty_profile_group)]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__no_access_key(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.error_result
        result = self.core.rotate_access_key()

        expected = [call.check_access_key()]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__successful_rotate(self, mock_credentials, mock_iam):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.get_access_key_id.return_value = '12345'

        access_key_result = Result()
        access_key_result.add_payload({
            'AccessKeyId': 12345,
            'SecretAccessKey': 67890
        })
        access_key_result.set_success()

        mock_iam.create_access_key.return_value = access_key_result

        result = self.core.rotate_access_key()

        expected = [call.check_access_key(),
                    call.check_session(),
                    call.get_user_name(),
                    call.get_access_key_id(),
                    call.set_access_key(key_id=12345, access_key=67890)]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call.create_access_key('test-user'),
                    call.delete_iam_access_key('test-user', '12345')]
        self.assertEqual(expected, mock_iam.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    def test_get_region__not_logged_in(self):
        region = self.core.get_region()
        self.assertEqual(None, region)

    def test_get_region__active_profile_group(self):
        self.core.active_profile_group = self.config.get_group('development')
        region = self.core.get_region()
        self.assertEqual('us-east-1', region)

    def test_get_region__region_overwrite(self):
        self.core.active_profile_group = self.config.get_group('development')
        self.core.region_override = 'eu-north-1'
        region = self.core.get_region()
        self.assertEqual('eu-north-1', region)

    def test_get_region__gcp(self):
        self.core.active_profile_group = self.config.get_group('gcp-project-dev')
        region = self.core.get_region()
        self.assertEqual('europe-west1', region)

    @mock.patch('app.core.core.mfa')
    @mock.patch('app.core.core.credentials')
    def test__renew_session__token_from_shell(self, mock_credentials, mock_mfa_shell):
        mock_mfa_shell.fetch_mfa_token_from_shell.return_value = '12345'
        mock_credentials.fetch_session_token.return_value = self.success_result

        mock_mfa_callback = Mock()
        result = self.core._renew_session(mock_mfa_callback)

        self.assertEqual(0, mock_mfa_callback.call_count)

        expected = [call.fetch_session_token('12345')]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.mfa')
    @mock.patch('app.core.core.credentials')
    def test__renew_session__no_token_from_mfa_callback(self, mock_credentials, mock_mfa_shell):
        mock_mfa_shell.fetch_mfa_token_from_shell.return_value = None
        mock_credentials.fetch_session_token.return_value = self.success_result

        mock_mfa_callback = Mock()
        mock_mfa_callback.return_value = ''
        result = self.core._renew_session(mock_mfa_callback)

        self.assertEqual(1, mock_mfa_callback.call_count)

        expected = []
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)

    @mock.patch('app.core.core.mfa')
    @mock.patch('app.core.core.credentials')
    def test__renew_session__token_from_mfa_callback(self, mock_credentials, mock_mfa_shell):
        mock_mfa_shell.fetch_mfa_token_from_shell.return_value = None
        mock_credentials.fetch_session_token.return_value = self.success_result

        mock_mfa_callback = Mock()
        mock_mfa_callback.return_value = '12345'
        result = self.core._renew_session(mock_mfa_callback)

        self.assertEqual(1, mock_mfa_callback.call_count)

        expected = [call.fetch_session_token('12345')]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test__set_region__not_logged_in(self, mock_credentials):
        mock_credentials.write_profile_config.return_value = self.success_result

        result = self.core.set_region('eu-north-1')

        expected = []
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual('eu-north-1', self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test__set_region__logged_in(self, mock_credentials):
        mock_credentials.write_profile_config.return_value = self.success_result
        self.core.active_profile_group = self.config.get_group('development')

        result = self.core.set_region('eu-north-1')

        expected = [call.write_profile_config(self.config.get_group('development'), 'eu-north-1')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual('eu-north-1', self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

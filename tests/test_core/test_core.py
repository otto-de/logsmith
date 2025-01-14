from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from app.core.core import Core
from app.core.result import Result
from tests.test_data.test_accounts import get_test_accounts
from tests.test_data.test_config import get_test_config
from tests.test_data.test_results import get_success_result, get_error_result, get_failed_result
from tests.test_data.test_service_roles import get_test_service_roles

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


class TestCore(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @mock.patch('app.core.config.files.load_service_roles')
    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def setUp(self, mock_load_accounts, mock_load_config, mock_service_roles):
        mock_load_accounts.return_value = get_test_accounts()
        mock_load_config.return_value = get_test_config()
        mock_service_roles.return_value = get_test_service_roles()

        self.core = Core()
        self.config = Config()
        self.config.initialize()
        self.core.config = self.config

        self.success_result = get_success_result()
        self.fail_result = get_failed_result()
        self.error_result = get_error_result()

    @mock.patch('app.core.core.credentials')
    def test_login__no_access_key(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.error_result
        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key(access_key='some-access-key')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.credentials')
    def test_login__session_token_error(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.error_result

        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key(access_key='some-access-key'),
                    call.check_session(access_key='some-access-key')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.credentials')
    def test_login__mfa_error(self, mock_credentials):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.fail_result
        self.core._renew_session = Mock()
        self.core._renew_session.return_value = self.error_result

        result = self.core.login(self.config.get_group('development'), None)

        expected = [call.check_access_key(access_key='some-access-key'),
                    call.check_session(access_key='some-access-key')]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call(access_key='some-access-key', mfa_callback=None)]
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

        expected = [call.check_access_key(access_key='some-access-key'),
                    call.check_session(access_key='some-access-key'),
                    call.get_user_name(access_key='some-access-key'),
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

    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__no_access_key(self, mock_credentials, mock_logout):
        mock_credentials.check_access_key.return_value = self.error_result
        mock_mfa_callback = Mock()
        result = self.core.rotate_access_key('rotate-this-key', mock_mfa_callback)

        expected = [call.check_access_key(access_key='rotate-this-key')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(self.error_result, result)
        self.assertEqual(1, mock_logout.call_count)

    @mock.patch('app.core.core.Core._renew_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__successful_rotate_with_valid_session(self, mock_credentials, mock_iam, mock_logout,
                                                                     mock_renew_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.get_access_key_id.return_value = '12345'
        mock_renew_session.return_value = self.success_result

        access_key_result = Result()
        access_key_result.add_payload({'AccessKeyId': 12345, 'SecretAccessKey': 67890})
        access_key_result.set_success()

        mock_iam.create_access_key.return_value = access_key_result
        mock_iam.delete_iam_access_key.return_value = self.success_result

        mock_mfa_callback = Mock()
        result = self.core.rotate_access_key('some-access-key', mock_mfa_callback)

        expected_credential_calls = [call.check_access_key(access_key='some-access-key'),
                                     call.check_session(access_key='some-access-key'),
                                     call.get_user_name('some-access-key'),
                                     call.get_access_key_id('some-access-key'),
                                     call.set_access_key(key_name='some-access-key', key_id=12345, key_secret=67890)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

        self.assertEqual(0, mock_renew_session.call_count)

        expected_iam_calls = [call.create_access_key('test-user', 'some-access-key'),
                              call.delete_iam_access_key('test-user', 'some-access-key', '12345')]
        self.assertEqual(expected_iam_calls, mock_iam.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)
        self.assertEqual(2, mock_logout.call_count)

    @mock.patch('app.core.core.Core._renew_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__successful_rotate_with_new_session(self, mock_credentials, mock_iam, mock_logout,
                                                                   mock_renew_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.check_session.return_value = self.fail_result
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.get_access_key_id.return_value = '12345'
        mock_renew_session.return_value = self.success_result

        access_key_result = Result()
        access_key_result.add_payload({'AccessKeyId': 12345, 'SecretAccessKey': 67890})
        access_key_result.set_success()

        mock_iam.create_access_key.return_value = access_key_result
        mock_iam.delete_iam_access_key.return_value = self.success_result

        mock_mfa_callback = Mock()
        result = self.core.rotate_access_key('some-access-key', mock_mfa_callback)

        expected_credential_calls = [call.check_access_key(access_key='some-access-key'),
                                     call.check_session(access_key='some-access-key'),
                                     call.get_user_name('some-access-key'),
                                     call.get_access_key_id('some-access-key'),
                                     call.set_access_key(key_name='some-access-key', key_id=12345, key_secret=67890)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

        renew_session_calls = [call(access_key='some-access-key', mfa_callback=mock_mfa_callback)]
        self.assertEqual(renew_session_calls, mock_renew_session.mock_calls)

        expected_iam_calls = [call.create_access_key('test-user', 'some-access-key'),
                              call.delete_iam_access_key('test-user', 'some-access-key', '12345')]
        self.assertEqual(expected_iam_calls, mock_iam.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)
        self.assertEqual(2, mock_logout.call_count)

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
        result = self.core._renew_session('access-key', mock_mfa_callback)

        self.assertEqual(0, mock_mfa_callback.call_count)

        expected = [call.fetch_session_token(access_key='access-key', mfa_token='12345')]
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
        result = self.core._renew_session('access-key', mock_mfa_callback)

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
        result = self.core._renew_session('access-key', mock_mfa_callback)

        self.assertEqual(1, mock_mfa_callback.call_count)

        expected = [call.fetch_session_token(access_key='access-key', mfa_token='12345')]
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

    def test__set_service_role(self):
        self.core.active_profile_group = self.config.get_group('development')
        save_selected_service_role_mock = Mock()
        self.core.config.save_selected_service_role = save_selected_service_role_mock

        result = self.core.set_service_role(profile_name='developer', role_name='some-role')

        expected_save = [call(group_name='development', profile_name='developer', role_name='some-role')]

        self.assertEqual(expected_save, save_selected_service_role_mock.mock_calls)
        self.assertEqual(self.core.active_profile_group.service_profile.to_dict(),
                         {'profile': 'service',
                          'account': '123495678901',
                          'role': 'some-role',
                          'source': 'developer'})
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    def test__set_service_role__non_existent_profile(self):
        self.core.active_profile_group = self.config.get_group('development')
        save_selected_service_role_mock = Mock()
        self.core.config.save_selected_service_role = save_selected_service_role_mock

        result = self.core.set_service_role(profile_name='developer', role_name='some-role')

        expected_save = [call(group_name='development', profile_name='developer', role_name='some-role')]

        self.assertEqual(expected_save, save_selected_service_role_mock.mock_calls)
        self.assertEqual(self.core.active_profile_group.service_profile.to_dict(),
                         {'profile': 'service',
                          'account': '123495678901',
                          'role': 'some-role',
                          'source': 'developer'})
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

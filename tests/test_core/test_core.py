from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from app.core.core import Core
from app.core.result import Result
from tests.test_data import test_accounts
from tests.test_data.test_accounts import get_test_profile_group, \
    get_default_test_accounts
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
        mock_load_accounts.return_value = get_default_test_accounts()
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
    def test_logout(self, mock_credentials):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.sso_logout.return_value = self.success_result

        result = self.core.logout()

        expected = [call.cleanup(), call.sso_logout()]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test_logout__error_on_cleanup(self, mock_credentials):
        mock_credentials.cleanup.return_value = self.error_result

        result = self.core.logout()

        expected = [call.cleanup()]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(self.error_result, result)
        
    @mock.patch('app.core.core.credentials')
    def test_logout__error_on_sso_logout(self, mock_credentials):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.sso_logout.return_value = self.error_result

        result = self.core.logout()

        expected = [call.cleanup(), call.sso_logout()]
        self.assertEqual(expected, mock_credentials.mock_calls)

        self.assertEqual(self.error_result, result)

    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__no_access_key(self, mock_credentials, mock_iam, mock_logout, mock_ensure_session):
        mock_credentials.check_access_key.return_value = self.fail_result

        result = self.core.rotate_access_key(access_key='rotate-this-key', mfa_token=None)
        self.assertEqual(self.fail_result, result)

        self.assertEqual(1, mock_logout.call_count)
        expected_credential_calls = [call.check_access_key(access_key='rotate-this-key')]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__fetch_session_failure(self, mock_credentials, mock_iam, mock_logout,
                                                      mock_ensure_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_ensure_session.return_value = self.fail_result

        result = self.core.rotate_access_key(access_key='rotate-this-key', mfa_token=None)
        self.assertEqual(self.fail_result, result)

        self.assertEqual(1, mock_logout.call_count)
        expected_ensure_session_calls = [call(access_key='rotate-this-key', mfa_token=None)]
        self.assertEqual(expected_ensure_session_calls, mock_ensure_session.mock_calls)
        expected_credential_calls = [call.check_access_key(access_key='rotate-this-key')]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__create_access_key_failure(self, mock_credentials, mock_iam, mock_logout,
                                                          mock_ensure_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_ensure_session.return_value = self.success_result
        mock_iam.create_access_key.return_value = self.fail_result

        result = self.core.rotate_access_key(access_key='rotate-this-key', mfa_token=None)
        self.assertEqual(self.fail_result, result)

        self.assertEqual(1, mock_logout.call_count)
        expected_ensure_session_calls = [call(access_key='rotate-this-key', mfa_token=None)]
        self.assertEqual(expected_ensure_session_calls, mock_ensure_session.mock_calls)
        expected_credential_calls = [call.check_access_key(access_key='rotate-this-key'),
                                     call.get_user_name('rotate-this-key')]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__delete_iam_access_key_failure(self, mock_credentials, mock_iam, mock_logout,
                                                              mock_ensure_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_ensure_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'some-user'
        mock_iam.create_access_key.return_value = self.success_result
        mock_credentials.get_access_key_id.return_value = 'some-old-access-key'
        mock_iam.delete_iam_access_key.return_value = self.fail_result

        result = self.core.rotate_access_key(access_key='rotate-this-key', mfa_token=None)
        self.assertEqual(self.fail_result, result)

        self.assertEqual(1, mock_logout.call_count)
        expected_ensure_session_calls = [call(access_key='rotate-this-key', mfa_token=None)]
        self.assertEqual(expected_ensure_session_calls, mock_ensure_session.mock_calls)
        expected_credential_calls = [call.create_access_key('some-user', 'rotate-this-key'),
                                     call.delete_iam_access_key('some-user', 'rotate-this-key', 'some-old-access-key')]
        self.assertEqual(expected_credential_calls, mock_iam.mock_calls)
        expected_credential_calls = [call.check_access_key(access_key='rotate-this-key'),
                                     call.get_user_name('rotate-this-key'),
                                     call.get_access_key_id('rotate-this-key')]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.Core.logout')
    @mock.patch('app.core.core.iam')
    @mock.patch('app.core.core.credentials')
    def test_rotate_access_key__successful_rotate(self, mock_credentials, mock_iam, mock_logout,
                                                  mock_ensure_session):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_ensure_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'some-user'

        create_access_key_result = Result()
        create_access_key_result.set_success()
        create_access_key_result.add_payload({'AccessKeyId': 'new-key', 'SecretAccessKey': '1234'})
        mock_iam.create_access_key.return_value = create_access_key_result

        mock_credentials.get_access_key_id.return_value = 'some-old-access-key'
        mock_iam.delete_iam_access_key.return_value = self.success_result

        result = self.core.rotate_access_key(access_key='rotate-this-key', mfa_token='123456')
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        self.assertEqual(2, mock_logout.call_count)
        expected_ensure_session_calls = [call(access_key='rotate-this-key', mfa_token='123456')]
        self.assertEqual(expected_ensure_session_calls, mock_ensure_session.mock_calls)
        expected_credential_calls = [call.create_access_key('some-user', 'rotate-this-key'),
                                     call.delete_iam_access_key('some-user', 'rotate-this-key', 'some-old-access-key')]
        self.assertEqual(expected_credential_calls, mock_iam.mock_calls)
        expected_credential_calls = [call.check_access_key(access_key='rotate-this-key'),
                                     call.get_user_name('rotate-this-key'),
                                     call.get_access_key_id('rotate-this-key'),
                                     call.set_access_key(key_name='rotate-this-key', key_id='new-key',
                                                         key_secret='1234')]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    def test_get_region__not_logged_in(self):
        region = self.core.get_region()
        self.assertEqual(None, region)

    def test_get_region__active_profile_group(self):
        self.core.active_profile_group = get_test_profile_group()
        region = self.core.get_region()
        self.assertEqual('us-east-1', region)

    def test_get_region__region_overwrite(self):
        self.core.active_profile_group = get_test_profile_group()
        self.core.region_override = 'eu-north-1'
        region = self.core.get_region()
        self.assertEqual('eu-north-1', region)

    def test_get_region__gcp(self):
        self.core.active_profile_group = self.config.get_group('gcp-project-dev')
        region = self.core.get_region()
        self.assertEqual('europe-west1', region)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__valid_session_and_token(self, mock_credentials):
        mock_credentials.check_session.return_value = self.success_result
        mock_credentials.fetch_session_token.return_value = self.success_result

        result = self.core._ensure_session(access_key='access-key', mfa_token='123456')
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = []
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__valid_session_and_no_token(self, mock_credentials):
        mock_credentials.check_session.return_value = self.success_result
        mock_credentials.fetch_session_token.return_value = self.success_result

        result = self.core._ensure_session(access_key='access-key', mfa_token=None)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = []
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__invalid_session_and_token(self, mock_credentials):
        mock_credentials.check_session.return_value = self.fail_result
        mock_credentials.fetch_session_token.return_value = self.success_result

        result = self.core._ensure_session(access_key='access-key', mfa_token='123456')
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = [call(access_key='access-key', mfa_token='123456')]
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__invalid_session_and_no_token(self, mock_credentials):
        mock_credentials.check_session.return_value = self.fail_result
        mock_credentials.fetch_session_token.return_value = self.success_result

        result = self.core._ensure_session(access_key='access-key', mfa_token=None)
        self.assertEqual(False, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = []
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__invalid_session_and_token_but_fetch_session_error(self, mock_credentials):
        mock_credentials.check_session.return_value = self.fail_result
        mock_credentials.fetch_session_token.return_value = self.error_result

        result = self.core._ensure_session(access_key='access-key', mfa_token='123456')
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = [call(access_key='access-key', mfa_token='123456')]
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__ensure_session__error_session_check(self, mock_credentials):
        mock_credentials.check_session.return_value = self.error_result
        mock_credentials.fetch_session_token.return_value = self.error_result

        result = self.core._ensure_session(access_key='access-key', mfa_token='123456')
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)

        expected_check_session_calls = [call(access_key='access-key')]
        self.assertEqual(expected_check_session_calls, mock_credentials.check_session.mock_calls)
        expected_fetch_session_calls = [call(access_key='access-key', mfa_token='123456')]
        self.assertEqual(expected_fetch_session_calls, mock_credentials.fetch_session_token.mock_calls)

    @mock.patch('app.core.core.credentials')
    def test__set_region__not_logged_in(self, mock_credentials):
        result = self.core.set_region('eu-north-1')

        self.assertEqual(0, mock_credentials.call_count)
        self.assertEqual('eu-north-1', self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test__set_region__successful(self, mock_credentials):
        mock_credentials.write_profile_config.return_value = self.success_result
        profile_group = get_test_profile_group()
        self.core.active_profile_group = profile_group

        result = self.core.set_region('eu-north-1')

        expected = [call.write_profile_config(profile_group, 'eu-north-1')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual('eu-north-1', self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test__set_region__successful_no_region_overwrite(self, mock_credentials):
        mock_credentials.write_profile_config.return_value = self.success_result
        profile_group = get_test_profile_group()
        self.core.active_profile_group = profile_group

        result = self.core.set_region(None)

        expected = [call.write_profile_config(profile_group, profile_group.region)]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual(None, self.core.region_override)

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    @mock.patch('app.core.core.credentials')
    def test__set_region__write_profile_failure(self, mock_credentials):
        mock_credentials.write_profile_config.return_value = self.fail_result
        profile_group = get_test_profile_group()
        self.core.active_profile_group = profile_group

        result = self.core.set_region('eu-north-1')
        self.assertEqual(self.fail_result, result)

        expected = [call.write_profile_config(profile_group, 'eu-north-1')]
        self.assertEqual(expected, mock_credentials.mock_calls)
        self.assertEqual('eu-north-1', self.core.region_override)

    def test__set_service_role(self):
        self.core.active_profile_group = get_test_profile_group()
        save_selected_service_role_mock = Mock()
        self.core.config.save_selected_service_role = save_selected_service_role_mock

        result = self.core.set_service_role(profile_name='developer', role_name='some-role')

        expected_save = [call(group_name='test', profile_name='developer', role_name='some-role')]

        self.assertEqual(expected_save, save_selected_service_role_mock.mock_calls)
        self.assertEqual(self.core.active_profile_group.service_profile.to_dict(),
                         {'profile': 'service',
                          'account': '123456789012',
                          'role': 'some-role',
                          'source': 'developer'})
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    def test__set_service_role__non_existent_profile(self):
        self.core.active_profile_group = get_test_profile_group()
        save_selected_service_role_mock = Mock()
        self.core.config.save_selected_service_role = save_selected_service_role_mock

        result = self.core.set_service_role(profile_name='developer', role_name='some-role')

        expected_save = [call(group_name='test', profile_name='developer', role_name='some-role')]

        self.assertEqual(expected_save, save_selected_service_role_mock.mock_calls)
        self.assertEqual(self.core.active_profile_group.service_profile.to_dict(),
                         {'profile': 'service',
                          'account': '123456789012',
                          'role': 'some-role',
                          'source': 'developer'})
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

    def test__run_script__no_active_profile_group(self):
        result = self.core.run_script(None)
        self.assertEqual(True, result.was_success)

    @mock.patch('app.core.core.files.file_exists', return_value=True)
    @mock.patch('app.core.core.shell.run')
    def test__run_script__script_successful(self, mock_shell_run, mock_files_exists):
        mock_shell_run.return_value = 'shell output'
        result = self.core.run_script(get_test_profile_group())

        self.assertEqual(True, result.was_success)
        self.assertEqual([call('./some-script.sh')], mock_files_exists.mock_calls)
        self.assertEqual([call(command='./some-script.sh', timeout=60)], mock_shell_run.mock_calls)

    @mock.patch('app.core.core.files.file_exists', return_value=False)
    @mock.patch('app.core.core.shell.run')
    def test__run_script__script_not_found(self, mock_shell_run, mock_files_exists):
        result = self.core.run_script(get_test_profile_group())

        self.assertEqual(True, result.was_error)
        self.assertEqual([call('./some-script.sh')], mock_files_exists.mock_calls)
        self.assertEqual([], mock_shell_run.mock_calls)

    @mock.patch('app.core.core.files.file_exists', return_value=True)
    @mock.patch('app.core.core.shell.run')
    def test__run_script__script_failed(self, mock_shell_run, mock_files_exists):
        mock_shell_run.return_value = None
        result = self.core.run_script(get_test_profile_group())

        self.assertEqual(True, result.was_error)
        self.assertEqual([call('./some-script.sh')], mock_files_exists.mock_calls)
        self.assertEqual([call(command='./some-script.sh', timeout=60)], mock_shell_run.mock_calls)

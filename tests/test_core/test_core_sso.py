from unittest import TestCase, mock
from unittest.mock import call, Mock

from app.core.config import Config
from app.core.core import Core
from app.core.result import Result
from tests.test_data import test_accounts
from tests.test_data.test_accounts import get_test_accounts__mixed_auth_modes, get_test_profile_group, \
    get_default_test_accounts
from tests.test_data.test_config import get_test_config
from tests.test_data.test_results import get_success_result, get_error_result, get_failed_result
from tests.test_data.test_service_roles import get_test_service_roles
from tests.test_data.test_toggles import get_test_toggles

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


class TestCoreSSO(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @mock.patch('app.core.config.files.load_toggles')
    @mock.patch('app.core.config.files.load_service_roles')
    @mock.patch('app.core.config.files.load_config')
    @mock.patch('app.core.config.files.load_accounts')
    def setUp(self, mock_load_accounts, mock_load_config, mock_service_roles, mock_toggles):
        mock_load_accounts.return_value = get_test_accounts__mixed_auth_modes()
        mock_load_config.return_value = get_test_config()
        mock_service_roles.return_value = get_test_service_roles()
        mock_toggles.return_value = get_test_toggles()

        self.core = Core()
        self.config = Config()
        self.config.initialize()
        self.core.config = self.config
        
        self.sso_profile_group = self.config.get_group('live')

        self.success_result = get_success_result()
        self.fail_result = get_failed_result()
        self.error_result = get_error_result()

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__cleanup_error(self, mock_credentials, mock_set_region,
                                  mock_handle_support_files, mock_run_script):       
        mock_credentials.cleanup.return_value = self.error_result

        result = self.core.login_with_sso(self.sso_profile_group)
        self.assertEqual(self.error_result, result)

        self.assertEqual([call.cleanup()], mock_credentials.mock_calls)
        self.assertEqual([], mock_set_region.mock_calls)
        self.assertEqual([], mock_handle_support_files.mock_calls)
        self.assertEqual([], mock_run_script.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__fetch_sso_credentials_failure(self, mock_credentials, mock_set_region,
                                                   mock_handle_support_files, mock_run_script):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.fetch_sso_credentials.return_value = self.fail_result

        profile_group = get_test_profile_group()
        result = self.core.login_with_sso(profile_group)
        self.assertEqual(self.fail_result, result)

        expected_credential_calls = [call.cleanup(),
                                     call.fetch_sso_credentials(profile_group)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)
        
        self.assertEqual([], mock_set_region.mock_calls)
        self.assertEqual([], mock_handle_support_files.mock_calls)
        self.assertEqual([], mock_run_script.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__set_region_failure(self, mock_credentials, mock_set_region,
                                       mock_handle_support_files, mock_run_script):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.fetch_sso_credentials.return_value = self.success_result
        mock_set_region.return_value = self.fail_result

        profile_group = get_test_profile_group()
        result = self.core.login_with_sso(profile_group)
        self.assertEqual(self.fail_result, result)

        expected_set_region_calls = [call(None)]
        self.assertEqual(expected_set_region_calls, mock_set_region.mock_calls)
       
        expected_credential_calls = [call.cleanup(),
                                     call.fetch_sso_credentials(profile_group)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)
        
        self.assertEqual([call(None)], mock_set_region.mock_calls)
        self.assertEqual([], mock_handle_support_files.mock_calls)
        self.assertEqual([], mock_run_script.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__run_script_failure(self, mock_credentials, mock_set_region,
                                       mock_handle_support_files, mock_run_script):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.fetch_sso_credentials.return_value = self.success_result
        mock_set_region.return_value = self.success_result
        mock_run_script.return_value = self.fail_result

        profile_group = get_test_profile_group()
        result = self.core.login_with_sso(profile_group)
        self.assertEqual(self.fail_result, result)

        expected_set_region_calls = [call(None)]
        self.assertEqual(expected_set_region_calls, mock_set_region.mock_calls)
        
        expected_handle_support_files_calls = [call(profile_group)]
        self.assertEqual(expected_handle_support_files_calls, mock_handle_support_files.mock_calls)
       
        expected_run_script_calls = [call(profile_group)]
        self.assertEqual(expected_run_script_calls, mock_run_script.mock_calls)
        
        expected_credential_calls = [call.cleanup(),
                                     call.fetch_sso_credentials(profile_group)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__successful_login_with_run_script_disabled(self, mock_credentials, mock_set_region,
                                        mock_handle_support_files, mock_run_script):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.fetch_sso_credentials.return_value = self.success_result
        mock_set_region.return_value = self.success_result
        mock_run_script.return_value = self.success_result

        self.core.toggles.run_script = False

        profile_group = get_test_profile_group()
        result = self.core.login_with_sso(profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_set_region_calls = [call(None)]
        self.assertEqual(expected_set_region_calls, mock_set_region.mock_calls)

        expected_handle_support_files_calls = [call(profile_group)]
        self.assertEqual(expected_handle_support_files_calls, mock_handle_support_files.mock_calls)

        self.assertEqual(0, mock_run_script.call_count)

        expected_credential_calls = [call.cleanup(),
                                     call.fetch_sso_credentials(profile_group)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__successful_login(self, mock_credentials, mock_set_region,
                                     mock_handle_support_files, mock_run_script):
        mock_credentials.cleanup.return_value = self.success_result
        mock_credentials.check_access_key.return_value = self.success_result
        mock_credentials.fetch_sso_credentials.return_value = self.success_result
        mock_set_region.return_value = self.success_result
        mock_run_script.return_value = self.success_result

        profile_group = get_test_profile_group()
        result = self.core.login_with_sso(profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected_set_region_calls = [call(None)]
        self.assertEqual(expected_set_region_calls, mock_set_region.mock_calls)

        expected_handle_support_files_calls = [call(profile_group)]
        self.assertEqual(expected_handle_support_files_calls, mock_handle_support_files.mock_calls)

        expected_run_script_calls = [call(profile_group)]
        self.assertEqual(expected_run_script_calls, mock_run_script.mock_calls)

        expected_credential_calls = [call.cleanup(),
                                     call.fetch_sso_credentials(profile_group)]
        self.assertEqual(expected_credential_calls, mock_credentials.mock_calls)

    @mock.patch('app.core.core.Core.run_script')
    @mock.patch('app.core.core.Core._handle_support_files')
    @mock.patch('app.core.core.Core.set_region')
    @mock.patch('app.core.core.Core._ensure_session')
    @mock.patch('app.core.core.credentials')
    def test_login_sso__successful_login_with_region_overwrite(self, mock_credentials, mock_ensure_session, mock_set_region,
                                                           mock_handle_support_files, mock_run_script):
        mock_credentials.check_access_key.return_value = self.success_result
        mock_ensure_session.return_value = self.success_result
        mock_credentials.get_user_name.return_value = 'user'
        mock_credentials.fetch_key_credentials.return_value = self.success_result
        mock_set_region.return_value = self.success_result
        mock_run_script.return_value = self.success_result

        self.core.region_override = 'eu-north-1'

        profile_group = get_test_profile_group()
        self.core.login_with_sso(profile_group)

        expected_set_region_calls = [call('eu-north-1')]
        self.assertEqual(expected_set_region_calls, mock_set_region.mock_calls)
        
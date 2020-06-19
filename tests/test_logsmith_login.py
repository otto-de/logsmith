from unittest import TestCase, mock
from unittest.mock import call, Mock

from PyQt5.QtWidgets import QApplication

from app.core.config import Config
from app.core.result import Result
from app.logsmith import MainWindow
from tests.test_data.test_accounts import get_test_accounts
from tests.test_data.test_results import get_success_result, get_error_result, get_failed_result


class TestLogsmith(TestCase):

    @mock.patch('app.logsmith.Config.load_from_disk')
    def setUp(self, mock_config):
        self.config = Config()
        self.config.set_accounts(get_test_accounts())
        app = QApplication([])
        self.logsmith = MainWindow(app)
        self.logsmith.config = self.config

        self.logsmith.to_reset_state = Mock()
        self.logsmith._to_login_state = Mock()
        self.logsmith._to_error_state = Mock()
        self.logsmith.set_region = Mock()

        self.logsmith.assets = Mock()
        self.logsmith.assets.get_icon.return_value = 'icon'
        self.logsmith.tray_icon = Mock()
        self.logsmith.log_dialog = Mock()
        self.logsmith.config_dialog = Mock()
        self.logsmith.set_key_dialog = Mock()
        self.logsmith.rotate_key_dialog = Mock()
        self.logsmith.login_repeater = Mock()
        self.logsmith._renew_session = Mock()
        self.logsmith._prepare_login = Mock(return_value='_prepare_login')

    @mock.patch('app.logsmith.credentials')
    def test_login__no_access_key(self, mock_credentials):
        result = Result()
        result.error('no access key')
        mock_credentials.has_access_key.return_value = result

        mock_action = Mock()
        self.logsmith.login(self.config.profile_groups['development'], mock_action)

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(0, self.logsmith._to_login_state.call_count)
        self.assertEqual(1, self.logsmith._to_error_state.call_count)

        expected = [call.has_access_key()]
        self.assertEqual(expected, mock_credentials.mock_calls)
        expected = [call.disable_actions(True),
                    call.show_message('Logsmith Error', 'no access key')]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

    @mock.patch('app.logsmith.credentials')
    def test_login__session_error(self, mock_credentials):
        mock_credentials.has_access_key.return_value = get_success_result()
        mock_credentials.check_session.return_value = get_error_result()

        mock_action = Mock()
        self.logsmith.login(self.config.profile_groups['development'], mock_action)

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(0, self.logsmith._to_login_state.call_count)
        self.assertEqual(1, self.logsmith._to_error_state.call_count)

        expected = [call.has_access_key(), call.check_session()]
        self.assertEqual(expected, mock_credentials.mock_calls)
        expected = [call.disable_actions(True),
                    call.show_message('Logsmith Error', 'some error')]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

    @mock.patch('app.logsmith.credentials')
    def test_login__mfa_error(self, mock_credentials):
        mock_credentials.has_access_key.return_value = get_success_result()
        mock_credentials.check_session.return_value = get_failed_result()
        self.logsmith._renew_session.return_value = get_error_result()

        mock_action = Mock()
        profile_group = self.config.profile_groups['development']
        self.logsmith.login(profile_group, mock_action)

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(0, self.logsmith._to_login_state.call_count)
        self.assertEqual(1, self.logsmith._to_error_state.call_count)
        self.assertEqual(1, self.logsmith._renew_session.call_count)
        self.assertEqual(0, self.logsmith.set_region.call_count)

        expected = [call.disable_actions(True), call.show_message('Logsmith Error', 'some error')]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

    @mock.patch('app.logsmith.credentials')
    def test_login__mfa_no_token(self, mock_credentials):
        mock_credentials.has_access_key.return_value = get_success_result()
        mock_credentials.check_session.return_value = get_failed_result()
        self.logsmith._renew_session.return_value = get_failed_result()

        mock_action = Mock()
        profile_group = self.config.profile_groups['development']
        self.logsmith.login(profile_group, mock_action)

        self.assertEqual(2, self.logsmith.to_reset_state.call_count)
        self.assertEqual(0, self.logsmith._to_login_state.call_count)
        self.assertEqual(0, self.logsmith._to_error_state.call_count)
        self.assertEqual(1, self.logsmith._renew_session.call_count)
        self.assertEqual(0, self.logsmith.set_region.call_count)

        expected = [call.disable_actions(True)]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

    @mock.patch('app.logsmith.credentials')
    def test_login__valid_session(self, mock_credentials):
        mock_credentials.has_access_key.return_value = get_success_result()
        mock_credentials.check_session.return_value = get_success_result()
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.fetch_role_credentials.return_value = get_success_result()

        mock_action = Mock()
        profile_group = self.config.profile_groups['development']
        self.logsmith.login(profile_group, mock_action)

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(1, self.logsmith._to_login_state.call_count)
        self.assertEqual(0, self.logsmith._to_error_state.call_count)
        self.assertEqual(0, self.logsmith._renew_session.call_count)
        self.assertEqual(1, self.logsmith.set_region.call_count)

        expected = [call.has_access_key(),
                    call.check_session(),
                    call.get_user_name(),
                    call.fetch_role_credentials('test-user', profile_group)]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call.disable_actions(True)]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

        expected = [call(profile_group=profile_group, action=mock_action)]
        self.assertEqual(expected, self.logsmith._prepare_login.mock_calls)
        expected = [call.start(delay_seconds=300,
                               task='_prepare_login')]
        self.assertEqual(expected, self.logsmith.login_repeater.mock_calls)

        self.assertEqual(profile_group, self.logsmith.active_profile_group)
        self.assertEqual(None, self.logsmith.region_override)

    @mock.patch('app.logsmith.credentials')
    def test_login__first_login(self, mock_credentials):
        mock_credentials.has_access_key.return_value = get_success_result()
        mock_credentials.check_session.return_value = get_failed_result()
        mock_credentials.get_user_name.return_value = 'test-user'
        mock_credentials.fetch_role_credentials.return_value = get_success_result()
        self.logsmith._renew_session.return_value = get_success_result()

        mock_action = Mock()
        profile_group = self.config.profile_groups['development']
        self.logsmith.login(profile_group, mock_action)

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(1, self.logsmith._to_login_state.call_count)
        self.assertEqual(0, self.logsmith._to_error_state.call_count)
        self.assertEqual(1, self.logsmith._renew_session.call_count)
        self.assertEqual(1, self.logsmith.set_region.call_count)

        expected = [call.has_access_key(),
                    call.check_session(),
                    call.get_user_name(),
                    call.fetch_role_credentials('test-user', profile_group)]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call.disable_actions(True)]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

        expected = [call(profile_group=profile_group, action=mock_action)]
        self.assertEqual(expected, self.logsmith._prepare_login.mock_calls)
        expected = [call.start(delay_seconds=300,
                               task='_prepare_login')]
        self.assertEqual(expected, self.logsmith.login_repeater.mock_calls)

        self.assertEqual(profile_group, self.logsmith.active_profile_group)
        self.assertEqual(None, self.logsmith.region_override)

    @mock.patch('app.logsmith.credentials')
    def test_login__logout(self, mock_credentials):
        mock_credentials.fetch_role_credentials.return_value = get_success_result()
        mock_credentials.write_profile_config.return_value = get_success_result()

        self.logsmith.logout()

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(1, mock_credentials.fetch_role_credentials.call_count)
        self.assertEqual(1, mock_credentials.write_profile_config.call_count)

        expected = [call.fetch_role_credentials(user_name='none', profile_group=self.logsmith.empty_profile_group),
                    call.write_profile_config(profile_group=self.logsmith.empty_profile_group, region='')]
        self.assertEqual(expected, mock_credentials.mock_calls)

    @mock.patch('app.logsmith.credentials')
    def test_login__logout_error(self, mock_credentials):
        mock_credentials.fetch_role_credentials.return_value = get_error_result()

        self.logsmith.logout()

        self.assertEqual(1, self.logsmith.to_reset_state.call_count)
        self.assertEqual(1, mock_credentials.fetch_role_credentials.call_count)
        self.assertEqual(0, mock_credentials.write_profile_config.call_count)

        expected = [call.fetch_role_credentials(user_name='none', profile_group=self.logsmith.empty_profile_group)]
        self.assertEqual(expected, mock_credentials.mock_calls)

        expected = [call.show_message('Logsmith Error', 'some error')]
        self.assertEqual(expected, self.logsmith.tray_icon.mock_calls)

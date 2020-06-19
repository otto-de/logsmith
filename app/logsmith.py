import logging
from datetime import datetime

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QAction

from app.aws import credentials, iam
from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.repeater import Repeater
from app.core.result import Result
from app.gui.access_key_dialog import SetKeyDialog
from app.gui.assets import Assets
from app.gui.config_dialog import ConfigDialog
from app.gui.key_rotation_dialog import RotateKeyDialog
from app.gui.log_dialog import LogDialog
from app.gui.mfa_dialog import MfaDialog
from app.gui.trayicon import SystemTrayIcon
from app.yubico import mfa

logger = logging.getLogger('logsmith')


# code source: https://stackoverflow.com/questions/893984/pyqt-show-menu-in-a-system-tray-application
# - add answer PyQt5
# PyQt4 to PyQt5 version: https://stackoverflow.com/questions/20749819/pyqt5-failing-import-of-qtgui
# QIcon.fromTheme('view-refresh')

class MainWindow(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)

        self.app = app
        self.config: Config = Config()
        self.config.load_from_disk()
        self.last_login: str = "never"
        self.active_profile_group: ProfileGroup = None
        self.empty_profile_group: ProfileGroup = ProfileGroup('logout', {})
        self.region_override: str = None
        self.assets: Assets = Assets()

        self.tray_icon = SystemTrayIcon(self, self.assets)
        self.tray_icon.show()

        self.log_dialog = LogDialog(self)
        self.config_dialog = ConfigDialog(self)
        self.set_key_dialog = SetKeyDialog(self)
        self.rotate_key_dialog = RotateKeyDialog(self)
        self.login_repeater = Repeater()

    def login(self, profile_group: ProfileGroup, action: QAction):
        logger.info(f'start login {profile_group.name}')
        self.to_reset_state()
        self.tray_icon.disable_actions(True)
        self.active_profile_group = profile_group

        access_key_result = credentials.has_access_key()
        if not self._check_and_signal_error(access_key_result):
            return

        session_result = credentials.check_session()
        if not self._check_and_signal_error(session_result):
            return

        if not session_result.was_success:
            renew_session_result = self._renew_session()
            if not self._check_and_signal_error(renew_session_result):
                return

            if not renew_session_result.was_success:
                self.to_reset_state()
                return

        user_name = credentials.get_user_name()
        role_result = credentials.fetch_role_credentials(user_name, profile_group)
        if not self._check_and_signal_error(role_result):
            return
        self.set_region()
        self._to_login_state()

        logger.info('login success')
        self.login_repeater.start(task=self._prepare_login(profile_group=profile_group,
                                                           action=action),
                                  delay_seconds=300)
        logger.info('repeater started')

    def logout(self):
        logger.info(f'start logout')
        self.to_reset_state()
        role_result = credentials.fetch_role_credentials(user_name='none', profile_group=self.empty_profile_group)
        if not self._check_and_signal_error(role_result):
            return

        config_result = credentials.write_profile_config(profile_group=self.empty_profile_group, region='')
        if not self._check_and_signal_error(config_result):
            return
        logger.info('logout success')

    def _renew_session(self) -> Result:
        logger.info('renew session')
        logger.info('get mfa from console')
        token = mfa.fetch_mfa_token_from_shell(self.config.mfa_shell_command)
        if not token:
            logger.info('get mfa from user')
            token = MfaDialog().get_mfa_token()
            if not token:
                return Result()
        logger.info(f'got token {token}')

        session_result = credentials.fetch_session_token(token)
        return session_result

    def _prepare_login(self, profile_group, action):
        def login():
            self.login(profile_group=profile_group, action=action)

        return login

    def _to_login_state(self):
        self.last_login = self.get_timestamp()
        self.tray_icon.setIcon(self.assets.get_icon(color_code=self.active_profile_group.color))
        self.tray_icon.disable_actions(False)
        self.tray_icon.update_last_login(self.last_login)

    def to_reset_state(self):
        if self.login_repeater:
            self.login_repeater.stop()
        self.tray_icon.setIcon(self.assets.get_icon())
        self.tray_icon.disable_actions(False)
        self.tray_icon.reset_previous_action(None)

    def _to_error_state(self):
        self.to_reset_state()
        self.tray_icon.setIcon(self.assets.get_icon(style='error', color_code='#ff0000'))

    def set_region(self) -> None:
        if not self.active_profile_group:
            self.tray_icon.update_region_text(self.region_override)
            return

        if self.region_override:
            region = self.region_override
        else:
            region = self.active_profile_group.region

        result = credentials.write_profile_config(self.active_profile_group, region)
        if not self._check_and_signal_error(result):
            return
        self.tray_icon.update_region_text(region)

    def rotate_access_key(self):
        logger.info('initiate key rotation')
        logger.info('check access key')
        access_key_result = credentials.has_access_key()
        if not self._check_and_signal_error(access_key_result):
            return

        logger.info('check session')
        check_session_result = credentials.check_session()
        if not check_session_result.was_success:
            check_session_result.error('Access Denied. Please log first')
        if not self._check_and_signal_error(check_session_result):
            return

        credentials.has_access_key()

        logger.info('create key')
        user = credentials.get_user_name()
        result = iam.create_access_key(user)
        if not self._check_and_signal_error(result):
            return

        logger.info('delete key')
        previous_access_key_id = credentials.get_access_key_id()
        iam.delete_iam_access_key(user, previous_access_key_id)

        logger.info('save key')
        credentials.set_access_key(key_id=result.payload['AccessKeyId'], access_key=result.payload['SecretAccessKey'])

        self._signal('Success', 'key was rotated')

    @staticmethod
    def set_access_key(key_id, access_key):
        credentials.set_access_key(key_id=key_id, access_key=access_key)

    def show_config_dialog(self):
        self.config_dialog.show_dialog(self.config)

    def show_set_key_dialog(self):
        text = ''
        if credentials.has_access_key().was_success:
            text = 'this will overwrite the existing key'
        self.set_key_dialog.show_dialog(text)

    def show_access_key_rotation_dialog(self):
        self.rotate_key_dialog.show_dialog()

    def show_logs(self):
        logs_as_text = files.load_logs()
        self.log_dialog.show_dialog(logs_as_text)

    def edit_config(self, config: Config):
        try:
            self.config = config
            self.config.save_to_disk()
            self.tray_icon.populate_context_menu()
            self.to_reset_state()
        except Exception as error:
            logger.error(str(error), exc_info=True)
            self._signal_error('could not save config')

    def _check_and_signal_error(self, result: Result):
        if result.was_error:
            self._signal_error(result.error_message)
            return False
        return True

    def _signal_error(self, message='unknown error'):
        self._signal(topic='Logsmith Error', message=message)
        self._to_error_state()

    def _signal(self, topic, message):
        self.tray_icon.show_message(topic, message)

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime('%H:%M')

    def stop_and_exit(self):
        if self.login_repeater:
            self.login_repeater.stop()
        self.exit()

    @staticmethod
    def exit():
        QCoreApplication.exit()

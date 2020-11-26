import logging
from datetime import datetime
from functools import partial

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMainWindow

from app.aws import credentials
from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.result import Result
from app.gui.access_key_dialog import SetKeyDialog
from app.gui.assets import Assets
from app.gui.config_dialog import ConfigDialog
from app.gui.key_rotation_dialog import RotateKeyDialog
from app.gui.log_dialog import LogDialog
from app.gui.trayicon import SystemTrayIcon
from core.core import Core
from gui.mfa_dialog import MfaDialog
from gui.repeater import Repeater

logger = logging.getLogger('logsmith')


class Gui(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.core = Core()
        self.assets: Assets = Assets()
        self.last_login: str = 'never'
        self.login_repeater = Repeater()
        self.tray_icon = SystemTrayIcon(parent=self,
                                        assets=self.assets,
                                        profile_list=self.core.config.list_groups())
        self.log_dialog = LogDialog(self)
        self.config_dialog = ConfigDialog(self)
        self.set_key_dialog = SetKeyDialog(self)
        self.rotate_key_dialog = RotateKeyDialog(self)
        self.tray_icon.show()

    def login(self, profile_group: ProfileGroup):
        self._to_reset_state()
        self.tray_icon.disable_actions(True)

        result = self.core.login(profile_group=profile_group,
                                 mfa_callback=self.show_mfa_token_fetch_dialog)
        if not self._check_and_signal_error(result):
            self._to_error_state()
            return

        logger.info('start repeater')
        prepare_login = partial(self.login, profile_group=profile_group)
        self.login_repeater.start(task=prepare_login,
                                  delay_seconds=300)
        self._to_login_state()

    def logout(self):
        result = self.core.logout()
        self._check_and_signal_error(result)
        self._to_reset_state()
        self.tray_icon.update_region_text('not logged in')

    def set_region(self, region: str) -> None:
        result = self.core.set_region(region)
        if not self._check_and_signal_error(result):
            return
        region = self.core.get_region()
        if not region:
            region = 'not logged in'
        self.tray_icon.update_region_text(region)

    def rotate_access_key(self):
        logger.info('initiate key rotation')
        logger.info('check access key')
        result = self.core.rotate_access_key()
        if not self._check_and_signal_error(result):
            return
        self._signal('Success', 'key was rotated')

    def edit_config(self, config: Config):
        result = self.core.edit_config(config)
        if self._check_and_signal_error(result):
            self.tray_icon.populate_context_menu(self.core.get_profile_group_list())
        self._to_reset_state()

    def set_access_key(self, key_id, access_key):
        self.core.set_access_key(key_id=key_id, access_key=access_key)
        self._signal('Success', 'access key was set')

    @staticmethod
    def show_mfa_token_fetch_dialog():
        return MfaDialog().get_mfa_token()

    def show_config_dialog(self):
        self.config_dialog.show_dialog(self.core.config)

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

    def _to_login_state(self):
        self.tray_icon.setIcon(self.assets.get_icon(color_code=self.core.get_active_profile_color()))
        self.tray_icon.disable_actions(False)
        self.tray_icon.update_last_login(self.get_timestamp())

    def _to_reset_state(self):
        self.login_repeater.stop()
        self.tray_icon.setIcon(self.assets.get_icon())
        self.tray_icon.disable_actions(False)
        self.tray_icon.update_last_login('never')

    def _to_error_state(self):
        self._to_reset_state()
        self.tray_icon.setIcon(self.assets.get_icon(style='error', color_code='#ff0000'))

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
        self.login_repeater.stop()
        self.exit()

    @staticmethod
    def exit():
        QCoreApplication.exit()

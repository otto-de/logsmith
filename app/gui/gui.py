import logging
from datetime import datetime
from functools import partial
from typing import List, Optional

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QMainWindow
from core.core import Core
from gui.mfa_dialog import MfaDialog
from gui.repeater import Repeater

from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.core import Core
from app.core.result import Result
from app.gui.access_key_dialog import SetKeyDialog
from app.gui.assets import Assets, ICON_STYLE_OUTLINE, ICON_STYLE_ERROR, ICON_STYLE_FULL, ICON_STYLE_GCP, \
    ICON_STYLE_BUSY
from app.gui.background_task import BackgroundTask
from app.gui.config_dialog import ConfigDialog
from app.gui.key_rotation_dialog import RotateKeyDialog
from app.gui.log_dialog import LogDialog
from app.gui.mfa_dialog import MfaDialog
from app.gui.repeater import Repeater
from app.gui.service_profile_dialog import ServiceProfileDialog
from app.gui.trayicon import SystemTrayIcon
from app.yubico import mfa

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
        self.service_profile_dialog = ServiceProfileDialog(self)

        # This is needed to keep the task alive, otherwise it crashes the application
        self.task: Optional[BackgroundTask] = None

        self.tray_icon.show()

    def login(self, profile_group: ProfileGroup, mfa_token: Optional[str] = None):
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.login,
            func_kwargs={'profile_group': profile_group, 'mfa_token': mfa_token},
            on_success=self._on_login_success,
            on_failure=partial(self._on_login_failure, profile_group=profile_group),
            on_error=self._on_error
        )
        self.task.start()

    def _on_login_success(self):
        logger.info('login success')
        if self.core.active_profile_group.service_profile:
            self.tray_icon.set_service_role(profile_name=self.core.active_profile_group.service_profile.source,
                                            role_name=self.core.active_profile_group.service_profile.role)
        self.tray_icon.update_region_text(self.core.get_region())
        self.tray_icon.update_copy_menus(self.core.active_profile_group)

        logger.info('start repeater')
        prepare_login = partial(self.login, profile_group=self.core.active_profile_group)
        self.login_repeater.start(task=prepare_login,
                                  delay_seconds=300)
        self._to_login_state()

    def _on_login_failure(self, profile_group: ProfileGroup):
        logger.info('login failure')

        mfa_token = mfa.fetch_mfa_token_from_shell(self.core.config.mfa_shell_command)
        if not mfa_token:
            mfa_token = self.show_mfa_token_fetch_dialog()
            if not mfa_token:
                logger.warning('no mfa token provided')
                self._to_error_state()
                return

        self.login(profile_group=profile_group, mfa_token=mfa_token)

    def login_gcp(self, profile_group: ProfileGroup):
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.login_gcp,
            func_kwargs={'profile_group': profile_group},
            on_success=self._on_login_gcp_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_login_gcp_success(self):
        logger.info('start repeater to remind login in 8 hours')
        prepare_login = partial(self.login_gcp, profile_group=self.core.active_profile_group)
        self.login_repeater.start(task=prepare_login,
                                  delay_seconds=8 * 60 * 60)
        self._to_login_state()

    def logout(self):
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.logout,
            func_kwargs={},
            on_success=self._on_logout_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_logout_success(self):
        self._to_reset_state()
        self.tray_icon.update_region_text('not logged in')
        self.tray_icon.reset_copy_menus()

    def set_region(self, region: str) -> None:
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.set_region,
            func_kwargs={'region': region},
            on_success=self._on_set_region_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_set_region_success(self) -> None:
        region = self.core.get_region()
        if not region:
            region = 'not logged in'
        self.tray_icon.update_region_text(region)
        self._to_login_state()

    def edit_config(self, config: Config):
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.edit_config,
            func_kwargs={'new_config': config},
            on_success=self._on_edit_config_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_edit_config_success(self):
        self.tray_icon.populate_context_menu(self.core.get_profile_group_list())
        self._to_reset_state()

    def set_access_key(self, key_name, key_id, key_secret):
        self._to_busy_state()
        logger.info('initiate set key')
        self.task = BackgroundTask(
            func=self.core.set_access_key,
            func_kwargs={'key_name': key_name, 'key_id': key_id, 'key_secret': key_secret},
            on_success=self._on_set_access_key_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_set_access_key_success(self):
        logger.info('access key set')
        self._signal('Success', 'access key set')
        self._to_login_state()

    def rotate_access_key(self, key_name: str, mfa_token: Optional[str] = None):
        self._to_busy_state()
        logger.info('initiate key rotation')
        self.task = BackgroundTask(
            func=self.core.rotate_access_key,
            func_kwargs={'access_key': key_name, 'mfa_token': mfa_token},
            on_success=self._on_rotate_access_key_success,
            on_failure=partial(self._on_rotate_access_key_failure, key_name=key_name),
            on_error=self._on_error
        )
        self.task.start()

    def _on_rotate_access_key_success(self):
        logger.info('key was rotated')
        self._signal('Success', 'key was rotated')
        self._to_login_state()

    def _on_rotate_access_key_failure(self, key_name: str):
        logger.info('rotation failure')

        mfa_token = mfa.fetch_mfa_token_from_shell(self.core.config.mfa_shell_command)
        if not mfa_token:
            mfa_token = self.show_mfa_token_fetch_dialog()
            if not mfa_token:
                logger.warning('no mfa token provided')
                self._to_error_state()
                return

        self.rotate_access_key(key_name=key_name, mfa_token=mfa_token)

    def set_service_role(self, profile: str, role: str):
        self._to_busy_state()
        self.task = BackgroundTask(
            func=self.core.set_service_role,
            func_kwargs={'profile_name': profile, 'role_name': role},
            on_success=self._on_set_service_role_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_set_service_role_success(self):
        logger.info('service role was set')
        self.login(profile_group=self.core.active_profile_group)

    def set_assumable_roles(self, profile: str, role_list: List[str]):
        self.task = BackgroundTask(
            func=self.core.set_available_service_roles,
            func_kwargs={'profile': profile, 'role_list': role_list},
            on_success=self._on_set_assumable_roles_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self.task.start()

    def _on_set_assumable_roles_success(self):
        logger.info('assumable roles were set')
        self._signal('Success', 'available role list was set')

    def _on_error(self, error_message):
        logger.error(error_message)
        self._signal_error(error_message)
        self._to_error_state()

    @staticmethod
    def show_mfa_token_fetch_dialog():
        return MfaDialog().get_mfa_token()

    def show_config_dialog(self):
        self.config_dialog.show_dialog(self.core.config)

    def show_set_key_dialog(self):
        self.set_key_dialog.show_dialog(access_key_list=self.core.get_access_key_list())

    def show_access_key_rotation_dialog(self):
        self.rotate_key_dialog.show_dialog(access_key_list=self.core.get_access_key_list())

    def show_service_role_dialog(self):
        self.service_profile_dialog.show_dialog(core=self.core, config=self.core.config)

    def show_logs(self):
        logs_as_text = files.load_logs()
        self.log_dialog.show_dialog(logs_as_text)

    def _to_login_state(self):
        if self.core.active_profile_group:
            style = ICON_STYLE_FULL if self.core.active_profile_group.type == "aws" else ICON_STYLE_GCP
            self.tray_icon.setIcon(self.assets.get_icon(style=style, color_code=self.core.get_active_profile_color()))
            self.tray_icon.disable_actions(False)
            self.tray_icon.update_last_login(self.get_timestamp())
        else:
            self._to_reset_state()

    def _to_busy_state(self):
        self.tray_icon.setIcon(self.assets.get_icon(ICON_STYLE_BUSY))
        self.tray_icon.disable_actions(True)

    def _to_reset_state(self):
        self.login_repeater.stop()
        self.tray_icon.setIcon(self.assets.get_icon(ICON_STYLE_OUTLINE))
        self.tray_icon.disable_actions(False)
        self.tray_icon.update_last_login('never')

    def _to_error_state(self):
        self._to_reset_state()
        self.tray_icon.setIcon(self.assets.get_icon(style=ICON_STYLE_ERROR, color_code='#ff0000'))

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

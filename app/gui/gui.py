import logging
from datetime import datetime
from functools import partial
from typing import List, Optional
from datetime import timezone
from datetime import datetime

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QMainWindow
from app.core.profile import Profile
from app.util import util
from core.core import Core
from gui.mfa_dialog import MfaDialog
from gui.repeater import Repeater

from app.core.config import Config, ProfileGroup
from app.core.core import Core
from app.core.result import Result
from app.gui.access_key_dialog import SetKeyDialog
from app.gui.assets import ICON_DISCONNECTED, Assets, ICON_STYLE_OUTLINE, ICON_STYLE_ERROR, ICON_STYLE_FULL, ICON_STYLE_GCP, \
    ICON_STYLE_BUSY, COLOR_RED
from app.gui.background_task import BackgroundTask, Task
from app.gui.config_dialog import ConfigDialog
from app.gui.key_rotation_dialog import RotateKeyDialog
from app.gui.log_dialog import LogDialog
from app.gui.mfa_dialog import MfaDialog
from app.gui.repeater import Repeater
from app.gui.service_profile_dialog import ServiceProfileDialog
from app.gui.sso_session_dialog import SetSsoSessionDialog
from app.gui.trayicon import SystemTrayIcon
from app.yubico import mfa

logger = logging.getLogger('logsmith')
STANDARD_LOGIN_REPEATER_INTERVAL = 600


class Gui(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.core = Core()
        self.assets: Assets = Assets()
        self.last_login: None | datetime = None
        self.last_login_text: str = 'never'
        self.login_repeater = Repeater()
        self.tray_icon = SystemTrayIcon(parent=self,
                                        assets=self.assets,
                                        toggles=self.core.toggles,
                                        profile_list=self.core.config.list_groups())
        self.log_dialog = LogDialog(self)
        self.config_dialog = ConfigDialog(self)
        self.set_key_dialog = SetKeyDialog(self)
        self.rotate_key_dialog = RotateKeyDialog(self)
        self.set_sso_session_dialog = SetSsoSessionDialog(self)
        self.service_profile_dialog = ServiceProfileDialog(self)

        # This is needed to keep the task alive, otherwise it crashes the application
        self.task: Optional[BackgroundTask] = None
        self._active_tasks: set[BackgroundTask] = set()

        self.tray_icon.show()

    def login(self, profile_group: ProfileGroup, force: bool= False):
        if profile_group.type == "aws" and profile_group.auth_mode == "key":
            self.login_key(profile_group=profile_group)
        elif profile_group.type == "aws" and profile_group.auth_mode == "sso" and profile_group.write_mode == "sso":
            self.login_sso(profile_group=profile_group, force=force)
        elif profile_group.type == "aws" and profile_group.auth_mode == "sso" and profile_group.write_mode == "key":
            self.login_sso_as_key(profile_group=profile_group, force=force)
        elif profile_group.type == "gcp":
            self.login_gcp(profile_group=profile_group)

    def _start_task(self, task: BackgroundTask):
        self._active_tasks.add(task)
        task.finished.connect(partial(self._on_task_finished, task))
        task.start()

    def _on_task_finished(self, task: BackgroundTask):
        self._active_tasks.discard(task)
        task.deleteLater()

    ########################
    # SSO LOGIN
    def login_sso(self, profile_group: ProfileGroup, force: bool):
        logger.info('-- sso login --')
        self.login_repeater.stop()
        self._to_busy_state()
        tasks = []

        sso_interval = profile_group.get_sso_interval()
        if not util.is_positive_int(sso_interval):
            logger.info(f'sso interval was {sso_interval}, but must be a positive integer or 0 (disabled)')
            self._to_error_state()
            return

        elapsed_seconds = self.elapsed_seconds_since_login()
        if force or self.should_login(elapsed_seconds, sso_interval):
            tasks.append(Task(self.core.login_with_sso, profile_group=profile_group))
        tasks.append(Task(self.core.verify))

        self.task = BackgroundTask(
            task=tasks,
            on_success=self._on_login_sso_success,
            on_failure=self._on_login_sso_failure,
            on_error=self._on_error
        )
        self._start_task(self.task)

    ########################
    # SSO-KEY LOGIN
    def login_sso_as_key(self, profile_group: ProfileGroup, force: bool):
        logger.info('-- sso-key login --')
        self.login_repeater.stop()
        self._to_busy_state()
        tasks = []

        sso_interval = profile_group.get_sso_interval()
        if not util.is_positive_int(sso_interval):
            logger.info(f'sso interval was {sso_interval}, but must be a positive integer or 0 (disabled)')
            self._to_error_state()
            return

        elapsed_seconds = self.elapsed_seconds_since_login()
        if force or self.should_login(elapsed_seconds, sso_interval):
            logger.info("trigger full login")
            tasks.append(Task(self.core.login_with_sso, profile_group=profile_group))
        else:
            logger.info("trigger refresh login")
            tasks.append(Task(self.core.login_with_sso_write_key, profile_group=profile_group))
        tasks.append(Task(self.core.verify))

        self.task = BackgroundTask(
            task=tasks,
            on_success=self._on_login_sso_success,
            on_failure=self._on_login_sso_failure,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_login_sso_success(self):
        self.save_login_datetime()
        logger.info('-- sso login success --')

        if self.core.active_profile_group.service_profile:
            self.tray_icon.set_service_role(profile_name=self.core.active_profile_group.service_profile.source,
                                            role_name=self.core.active_profile_group.service_profile.role)
        self.tray_icon.update_region_text(self.core.get_region())
        self.tray_icon.update_copy_menus(self.core.active_profile_group)
        self.tray_icon.refresh_profile_status(self.core.active_profile_group, self.core.default_profile_override)

        self._to_login_state()
        self.start_login_repeater(STANDARD_LOGIN_REPEATER_INTERVAL)

    def _on_login_sso_failure(self):
        logger.info('-- sso login failure --')
        self._to_error_state()

    ########################
    # ACCESS KEY LOGIN
    def login_key(self, profile_group: ProfileGroup, mfa_token: Optional[str] = None):
        self.login_repeater.stop()
        self._to_busy_state()
        self.task = BackgroundTask(
            task=[
                Task(self.core.login_with_key, profile_group=profile_group, mfa_token=mfa_token),
                Task(self.core.verify),
            ],
            on_success=self._on_login_key_success,
            on_failure=partial(self._on_login_key_failure, profile_group=profile_group),
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_login_key_success(self):
        self.save_login_datetime()
        logger.info('-- key login success --')

        if self.core.active_profile_group.service_profile:
            self.tray_icon.set_service_role(profile_name=self.core.active_profile_group.service_profile.source,
                                            role_name=self.core.active_profile_group.service_profile.role)
        self.tray_icon.update_region_text(self.core.get_region())
        self.tray_icon.update_copy_menus(self.core.active_profile_group)
        self.tray_icon.refresh_profile_status(self.core.active_profile_group, self.core.default_profile_override)

        self._to_login_state()
        self.start_login_repeater(STANDARD_LOGIN_REPEATER_INTERVAL)

    def _on_login_key_failure(self, profile_group: ProfileGroup):
        logger.info('-- key login failure --')

        mfa_token = mfa.fetch_mfa_token_from_shell(self.core.config.mfa_shell_command)
        if not mfa_token:
            mfa_token = self.show_mfa_token_fetch_dialog()
            if not mfa_token:
                logger.warning('no mfa token provided')
                self._to_error_state()
                return

        self.login_key(profile_group=profile_group, mfa_token=mfa_token)

    ########################
    # GCP
    def login_gcp(self, profile_group: ProfileGroup):
        self.login_repeater.stop()
        self._to_busy_state()
        self.task = BackgroundTask(
            task=Task(self.core.login_with_sso, profile_group=profile_group),
            on_success=self._on_login_gcp_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_login_gcp_success(self):
        self.save_login_datetime()
        logger.info('-- gcp login success --')

        self._to_login_state()
        self.start_login_repeater(8 * 60 * 60)

    ########################
    # REPEATER
    def start_login_repeater(self, delay_seconds):
        prepared_login = partial(self.login, profile_group=self.core.active_profile_group)
        self.login_repeater.start(task=prepared_login,
                                  delay_seconds=delay_seconds)

    def save_login_datetime(self):
        self.last_login = datetime.now(timezone.utc)

    def elapsed_seconds_since_login(self) -> int | None:
        if self.last_login is None:
            return None
        return int((datetime.now(timezone.utc) - self.last_login).total_seconds())

    def should_login(self, elapsed: int | None, threshold: int | str | None) -> bool:
        logger.info(f'elapsed {elapsed}s / {threshold}s since login')
        if elapsed is None:
            return True

        if threshold is None or threshold == 0 or threshold == "0":
            return False

        elapsed_seconds = int(elapsed)
        threshold_seconds = int(threshold)
        if elapsed_seconds >= threshold_seconds:
            return True
        return False

    ########################
    # SET DEFAULT PROFILE
    def set_default(self, profile_name: str):
        self.task = BackgroundTask(
            task=Task(self.core.set_default_profile, profile_name=profile_name),
            on_success=partial(self._on_set_default_success, default_profile_name=profile_name),
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_default_success(self, default_profile_name):
        logger.info('-- set default profile success --')
        if self.core.active_profile_group:
            self.tray_icon.refresh_profile_status(self.core.active_profile_group, default_profile_name)

    ########################
    # LOGOUT
    def logout(self):
        self._to_busy_state()
        self.task = BackgroundTask(
            task=Task(self.core.logout),
            on_success=self._on_logout_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_logout_success(self):
        logger.info('logout success')
        self._to_reset_state()
        self.tray_icon.update_region_text('not logged in')
        self.tray_icon.reset_copy_menus()

    ########################
    # REGION
    def set_region(self, region: str) -> None:
        self.task = BackgroundTask(
            task=Task(self.core.set_region, region=region),
            on_success=self._on_set_region_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_region_success(self) -> None:
        logger.info('-- set region success --')
        region = self.core.get_region()
        if not region:
            region = 'not logged in'
        self.tray_icon.update_region_text(region)
        self._to_login_state()

    ########################
    # CONFIG
    def edit_config(self, config: Config):
        self._to_busy_state()
        self.task = BackgroundTask(
            task=Task(self.core.edit_config, new_config=config),
            on_success=self._on_edit_config_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_edit_config_success(self):
        logger.info('-- edit config success --')
        self.tray_icon.populate_context_menu(self.core.get_profile_group_list())
        self._to_reset_state()

    ########################
    # MANAGE ACCESS KEY
    def set_access_key(self, key_name, key_id, key_secret):
        self._to_busy_state()
        logger.info('-- initiate set key --')
        self.task = BackgroundTask(
            task=Task(self.core.set_access_key, key_name=key_name, key_id=key_id, key_secret=key_secret),
            on_success=self._on_set_access_key_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_access_key_success(self):
        logger.info('-- access key set success --')
        self._signal('Success', 'access key set')
        self._to_login_state()

    def rotate_access_key(self, key_name: str, mfa_token: Optional[str] = None):
        self._to_busy_state()
        logger.info('-- initiate key rotation --')
        self.task = BackgroundTask(
            task=Task(self.core.rotate_access_key, access_key=key_name, mfa_token=mfa_token),
            on_success=self._on_rotate_access_key_success,
            on_failure=partial(self._on_rotate_access_key_failure, key_name=key_name),
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_rotate_access_key_success(self):
        logger.info('-- key was rotation success --')
        self._signal('Success', 'key was rotated')
        self._to_login_state()

    def _on_rotate_access_key_failure(self, key_name: str):
        logger.info('-- rotation failure --')

        mfa_token = mfa.fetch_mfa_token_from_shell(self.core.config.mfa_shell_command)
        if not mfa_token:
            mfa_token = self.show_mfa_token_fetch_dialog()
            if not mfa_token:
                logger.warning('no mfa token provided')
                self._to_error_state()
                return

        self.rotate_access_key(key_name=key_name, mfa_token=mfa_token)

    def set_sso_session(self, sso_name, sso_url, sso_region, sso_scopes):
        self._to_busy_state()
        logger.info('-- initiate set sso session --')
        self.task = BackgroundTask(
            task=Task(self.core.set_sso_session, sso_name=sso_name, sso_url=sso_url,
                      sso_region=sso_region, sso_scopes=sso_scopes),
            on_success=self._on_set_sso_session_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_sso_session_success(self):
        logger.info('-- set sso session success --')
        self._signal('Success', 'sso session set')
        self._to_login_state()

    def set_service_role(self, profile: str, role: str):
        self._to_busy_state()
        self.task = BackgroundTask(
            task=Task(self.core.set_service_role, profile_name=profile, role_name=role),
            on_success=self._on_set_service_role_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_service_role_success(self):
        self._to_reset_state()
        logger.info('-- set service role success --')
        if self.core.active_profile_group:
            self.login(profile_group=self.core.active_profile_group, force=True)

    def set_assumable_roles(self, profile: str, role_list: List[str]):
        self.task = BackgroundTask(
            task=Task(self.core.set_available_service_roles, profile=profile, role_list=role_list),
            on_success=self._on_set_assumable_roles_success,
            on_failure=self._on_error,
            on_error=self._on_error
        )
        self._start_task(self.task)

    def _on_set_assumable_roles_success(self):
        logger.info('-- set assumable roles success --')
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

    def show_sso_session_dialog(self):
        self.set_sso_session_dialog.show_dialog(sso_session_list=self.core.get_sso_sessions_list())

    def show_service_role_dialog(self):
        self.service_profile_dialog.show_dialog(core=self.core, config=self.core.config)

    def show_logs(self):
        self.log_dialog.show_dialog()

    def _to_login_state(self):
        if self.core.active_profile_group:
            style = ICON_STYLE_FULL if self.core.active_profile_group.type == "aws" else ICON_STYLE_GCP
            color = self.core.get_active_profile_color()
            if all(profile.verified for profile in self.core.active_profile_group.get_profile_list(include_service_profile=True)):
                self.tray_icon.setIcon(self.assets.get_icon(style=style, color_code=color))
            else:
                self.tray_icon.setIcon(self.assets.get_icon(style=ICON_DISCONNECTED, color_code=color))
            self.tray_icon.disable_actions(False)
            self.tray_icon.update_last_login(self.get_timestamp())
        else:
            self._to_reset_state()

    def _to_busy_state(self):
        self.tray_icon.setIcon(self.assets.get_icon(ICON_STYLE_BUSY))
        self.tray_icon.set_service_role(None, None)
        self.tray_icon.refresh_profile_status(None)
        self.tray_icon.disable_actions(True)

    def _to_reset_state(self):
        self.login_repeater.stop()
        self.last_login = None
        self.tray_icon.setIcon(self.assets.get_icon(ICON_STYLE_OUTLINE))
        self.tray_icon.set_service_role(None, None)
        self.tray_icon.refresh_profile_status(None)
        self.tray_icon.disable_actions(False)
        self.tray_icon.update_last_login('never')
        self.tray_icon.set_service_role(None, None)

    def _to_error_state(self):
        self._to_reset_state()
        self.tray_icon.setIcon(self.assets.get_icon(style=ICON_STYLE_ERROR, color_code=COLOR_RED))

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

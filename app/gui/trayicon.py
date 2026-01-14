from functools import partial
from typing import List, TYPE_CHECKING

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu 
from PyQt6.QtGui import QAction

from app.version import version
from app.aws import regions
from app.core.profile_group import ProfileGroup
from app.core.toggles import Toggles
from app.gui.assets import ICON_STYLE_OUTLINE, ICON_STYLE_GCP, ICON_STYLE_FULL, ICON_VALID, ICON_INVALID

if TYPE_CHECKING:
    from gui.gui import Gui


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent, assets, toggles: Toggles, profile_list: List[ProfileGroup]):
        self.gui: Gui = parent
        self.assets = assets
        self.toggles = toggles

        self.menu = None
        self.script_checkbox = None
        self.log_action = None
        self.config_action = None
        self.last_login = None
        self.active_region_text = None
        self.default_region_text = 'default region'
        self.region_menu = None
        self.add_access_key_action = None
        self.rotate_access_key_action = None
        self.add_sso_session_action = None
        self.service_role_action = None
        self.service_role_info = None

        self.actions = []
        self.all_actions = []
        self.profile_status_list = []
        self.profile_status_anchor = None

        QSystemTrayIcon.__init__(self, self.assets.standard, self.gui)
        self.setIcon(self.assets.get_icon(style=ICON_STYLE_OUTLINE))
        self.populate_context_menu(profile_list)

    def populate_context_menu(self, profile_list: List[ProfileGroup]):
        menu = QMenu(self.gui)
        self.menu = menu

        self.actions = []
        for profile_group in profile_list:
            if profile_group.type == "aws":
                action = menu.addAction(profile_group.name)
                action.setIconVisibleInMenu(True)
                action.triggered.connect(partial(self.gui.login, profile_group=profile_group))
                action.setIcon(self.assets.get_icon(style=ICON_STYLE_FULL, color_code=profile_group.color))
                self.actions.append(action)

        # log out
        logut_action = menu.addAction('logout')
        logut_action.setIconVisibleInMenu(True)
        logut_action.triggered.connect(self.gui.logout)
        logut_action.setIcon(self.assets.get_icon(style=ICON_STYLE_OUTLINE, color_code='#FFFFFF'))
        self.actions.append(logut_action)

        # gcp profiles
        menu.addSeparator()
        for profile_group in profile_list:
            if profile_group.type == "gcp":
                action = menu.addAction("[GCP] " + profile_group.name)
                action.setIconVisibleInMenu(True)
                action.triggered.connect(partial(self.gui.login_gcp,
                                                 profile_group=profile_group))
                action.setIcon(self.assets.get_icon(style=ICON_STYLE_GCP, color_code=profile_group.color))
                self.actions.append(action)

        menu.addSeparator()
        # script checkbox
        self.script_checkbox = menu.addAction("enable script")
        self.script_checkbox.setCheckable(True)
        self.script_checkbox.setChecked(self.toggles.run_script)
        self.script_checkbox.toggled.connect(self.toggles.toggle_run_script)

        menu.addSeparator()
        # region
        ## active region
        self.active_region_text = menu.addAction('no region set')
        self.active_region_text.setDisabled(True)

        ## region menu
        self.region_menu = QMenu('Overwrite region', menu)
        menu.addMenu(self.region_menu)
        ## default region action
        default_region_action = self.region_menu.addAction(self.default_region_text)
        default_region_action.triggered.connect(self.set_region_to_default)
        ## region overwrite
        for region in regions.region_list:
            region_action = self.region_menu.addAction(region)
            region_action.triggered.connect(partial(self.set_override_region, region=region))

        menu.addSeparator()
        # service profile
        self.service_role_info = menu.addAction(f'no service profile')
        self.service_role_info.setDisabled(True)
        self.service_role_action = menu.addAction('Set service profile')
        self.service_role_action.triggered.connect(self.gui.show_service_role_dialog)

        menu.addSeparator()
        # access keys
        self.add_access_key_action = menu.addAction('Set access key')
        self.add_access_key_action.triggered.connect(self.gui.show_set_key_dialog)
        self.rotate_access_key_action = menu.addAction('Rotate access key')
        self.rotate_access_key_action.triggered.connect(self.gui.show_access_key_rotation_dialog)
        self.add_access_key_action = menu.addAction('Set SSO session')
        self.add_access_key_action.triggered.connect(self.gui.show_sso_session_dialog)

        menu.addSeparator()
        
        # configuration
        self.config_action = menu.addAction('Edit config')
        self.config_action.triggered.connect(self.gui.show_config_dialog)

        self.log_action = menu.addAction("Show logs")
        self.log_action.triggered.connect(self.gui.show_logs)

        self.last_login = menu.addAction(f'last login: never')
        self.last_login.setDisabled(True)

        menu.addSeparator()
        self.copy_text = menu.addAction("Copy profile name:")
        self.copy_text.setDisabled(True)
        # profile status
        self.profile_status_anchor = menu.addSeparator()
        
        # copy
        self.copy_id_menu = QMenu('Copy Account Id', menu)
        self.copy_id_menu.setDisabled(True)
        menu.addMenu(self.copy_id_menu)
        
        menu.addSeparator()
        # version
        self.version_action = menu.addAction(f"Version: {version}")
        self.version_action.setDisabled(True)

        # exit
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.gui.stop_and_exit)

        self.setContextMenu(menu)
        menu.repaint()

        self.all_actions = self.actions + [self.script_checkbox, self.service_role_action, self.region_menu,
                                           self.add_access_key_action, self.rotate_access_key_action,
                                        #    self.copy_name_menu, 
                                           self.copy_id_menu]

    def refresh_profile_status(self, active_profile_group: ProfileGroup) -> bool:
        for action in self.profile_status_list:
            self.menu.removeAction(action)
            action.deleteLater()
        self.profile_status_list.clear()

        if active_profile_group is None or active_profile_group.type != "aws":
            return True

        all_connected = True
        for profile in active_profile_group.get_profile_list(include_service_profile=True):
            action = QAction(f'{profile.profile} ({profile.account})')
            action.triggered.connect(partial(self.copy_to_clipboard, text=profile.profile))
            action.setIconVisibleInMenu(True)
            if profile.verified:
                action.setIcon(self.assets.get_icon(style=ICON_VALID))
            else:
                all_connected = False
                action.setIcon(self.assets.get_icon(style=ICON_INVALID))
            self.menu.insertAction(self.profile_status_anchor, action)
            self.profile_status_list.append(action)
        return all_connected

    def update_copy_menus(self, active_profile_group: ProfileGroup):
        # self.copy_name_menu.setDisabled(False)
        # self.copy_name_menu.clear()
        self.copy_id_menu.setDisabled(False)
        self.copy_id_menu.clear()

        for profile in active_profile_group.get_profile_list():
            # copy_name_action = self.copy_name_menu.addAction(f'{profile.profile} ({profile.account})')
            # copy_name_action.triggered.connect(partial(self.copy_to_clipboard, text=profile.profile))
            copy_id_action = self.copy_id_menu.addAction(f'{profile.account} ({profile.profile})')
            copy_id_action.triggered.connect(partial(self.copy_to_clipboard, text=str(profile.account)))


    def reset_copy_menus(self):
        # self.copy_name_menu.setDisabled(True)
        # self.copy_name_menu.clear()
        self.copy_id_menu.setDisabled(True)
        self.copy_id_menu.clear()

    def disable_actions(self, state: bool):
        for action in self.all_actions:
            action.setDisabled(state)

    def update_last_login(self, timestamp: str):
        self.last_login.setText(f'last login {timestamp}')

    def set_region_to_default(self):
        self.gui.set_region(None)

    def set_override_region(self, region: str):
        self.gui.set_region(region)

    def copy_to_clipboard(self, text):
        clipboard = self.gui.app.clipboard()
        clipboard.setText(text)

    def set_service_role(self, profile_name: str, role_name: str):
        if profile_name and role_name:
            text = f'{profile_name} : {role_name}'
            if len(text) > 50:
                text = text[:50] + '...'
            self.service_role_info.setText(text)
        else:
            self.service_role_info.setText('no service profile')

    def update_region_text(self, region: str):
        if region:
            self.active_region_text.setText(region)
        else:
            self.active_region_text.setText(self.default_region_text)

    def show_message(self, title, message):
        self.showMessage(
            title,
            message,
            self.assets.get_icon(),
            8000)

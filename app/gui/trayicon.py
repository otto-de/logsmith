from functools import partial
from typing import List, TYPE_CHECKING

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

from app.aws import regions
from app.core.profile_group import ProfileGroup
from app.gui.assets import ICON_STYLE_OUTLINE, ICON_STYLE_FULL, ICON_STYLE_GCP, ICON_STYLE_BUSY

if TYPE_CHECKING:
    from gui.gui import Gui


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent, assets, profile_list: List[ProfileGroup]):
        self.gui: Gui = parent
        self.assets = assets

        self.log_action = None
        self.config_action = None
        self.last_login = None
        self.active_region_text = None
        self.default_region_text = 'default region'
        self.region_menu = None
        self.add_access_key_action = None
        self.rotate_access_key_action = None
        self.service_role_action = None
        self.service_role_info = None

        self.actions = []
        self.previous_action = None

        QSystemTrayIcon.__init__(self, self.assets.standard, self.gui)
        self.setIcon(self.assets.get_icon(style=ICON_STYLE_OUTLINE))
        self.populate_context_menu(profile_list)

    def populate_context_menu(self, profile_list: List[ProfileGroup]):
        menu = QMenu(self.gui)

        self.actions = []
        for profile_group in profile_list:
            if profile_group.type == "aws":
                action = menu.addAction(profile_group.name)
                action.triggered.connect(partial(self.gui.login,
                                                 profile_group=profile_group))
                action.setIcon(self.assets.get_icon(style=ICON_STYLE_FULL, color_code=profile_group.color))
                self.actions.append(action)

        # log out
        action = menu.addAction('logout')
        action.triggered.connect(self.gui.logout)
        action.setIcon(self.assets.get_icon(style=ICON_STYLE_OUTLINE, color_code='#FFFFFF'))
        self.actions.append(action)

        # gcp profiles
        menu.addSeparator()
        for profile_group in profile_list:
            if profile_group.type == "gcp":
                action = menu.addAction("[GCP] " + profile_group.name)
                action.triggered.connect(partial(self.gui.login_gcp,
                                                 profile_group=profile_group))
                action.setIcon(self.assets.get_icon(style=ICON_STYLE_GCP, color_code=profile_group.color))
                self.actions.append(action)

        menu.addSeparator()
        # region
        # active region
        self.active_region_text = menu.addAction('no region set')
        self.active_region_text.setDisabled(True)
        # region menu
        self.region_menu = QMenu('Overwrite region', menu)
        menu.addMenu(self.region_menu)
        # default region action
        default_region_action = self.region_menu.addAction(self.default_region_text)
        default_region_action.triggered.connect(self.set_region_to_default)
        # region overwrite
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

        menu.addSeparator()
        self.config_action = menu.addAction('Edit config')
        self.config_action.triggered.connect(self.gui.show_config_dialog)

        self.log_action = menu.addAction("Show logs")
        self.log_action.triggered.connect(self.gui.show_logs)

        self.last_login = menu.addAction(f'last login: never')
        self.last_login.setDisabled(True)

        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.gui.stop_and_exit)

        self.setContextMenu(menu)
        menu.repaint()

    def disable_actions(self, state: bool):
        for action in self.actions:
            action.setDisabled(state)

    def update_last_login(self, timestamp: str):
        self.last_login.setText(f'last login {timestamp}')

    def set_region_to_default(self):
        self.gui.set_region(None)

    def set_override_region(self, region: str):
        self.gui.set_region(region)

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

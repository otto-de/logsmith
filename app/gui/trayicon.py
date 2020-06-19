import os
from functools import partial

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu

from app.aws import regions

script_dir = os.path.dirname(os.path.realpath(__file__))


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent, assets):
        self.parent = parent
        self.assets = assets

        self.log_action = None
        self.config_action = None
        self.last_login = None
        self.active_region = None
        self.default_region_text = 'default region'
        self.region_menu = None
        self.add_access_key_action = None
        self.rotate_access_key_action = None

        self.actions = []
        self.previous_action = None

        QSystemTrayIcon.__init__(self, self.assets.standard, self.parent)
        self.setIcon(self.assets.get_icon(style='full'))
        self.populate_context_menu()

    def populate_context_menu(self):
        menu = QMenu(self.parent)

        self.actions = []
        for profile_group in self.parent.config.list_groups():
            action = menu.addAction(profile_group.name)
            action.triggered.connect(partial(self.parent.login,
                                             profile_group=profile_group,
                                             action=action))
            action.setIcon(self.assets.get_icon(style='full', color_code=profile_group.color))
            self.actions.append(action)

        # log out
        action = menu.addAction('logout')
        action.triggered.connect(self.parent.logout)
        action.setIcon(self.assets.get_icon(style='outline', color_code='#FFFFFF'))
        self.actions.append(action)

        menu.addSeparator()
        # active region
        self.active_region = menu.addAction('not logged in')
        self.active_region.setDisabled(True)
        # region menu
        self.region_menu = QMenu(self.default_region_text, menu)
        menu.addMenu(self.region_menu)
        # default region action
        default_region_action = self.region_menu.addAction(self.default_region_text)
        default_region_action.triggered.connect(self.set_region_to_default)
        # region overwrite
        for region in regions.region_list:
            region_action = self.region_menu.addAction(region)
            region_action.triggered.connect(partial(self.set_override_region,
                                                    region=region))

        menu.addSeparator()
        self.config_action = menu.addAction('Edit config')
        self.config_action.triggered.connect(self.parent.show_config_dialog)

        key_menu = QMenu('Access Key', menu)
        menu.addMenu(key_menu)
        self.add_access_key_action = key_menu.addAction('Set access key')
        self.add_access_key_action.triggered.connect(self.parent.show_set_key_dialog)
        self.rotate_access_key_action = key_menu.addAction('Rotate access key')
        self.rotate_access_key_action.triggered.connect(self.parent.show_access_key_rotation_dialog)

        menu.addSeparator()
        self.log_action = menu.addAction("Show logs")
        self.log_action.triggered.connect(self.parent.show_logs)

        menu.addSeparator()
        self.last_login = menu.addAction(f'last login {self.parent.last_login}')
        self.last_login.setDisabled(True)

        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.parent.stop_and_exit)

        self.setContextMenu(menu)
        menu.repaint()

    def disable_actions(self, state: bool):
        for action in self.actions:
            action.setDisabled(state)

    def update_last_login(self, timestamp: str):
        self.last_login.setText(f'last login {timestamp}')

    def set_override_region(self, region: str):
        self.parent.region_override = region
        self.parent.set_region()

    def set_region_to_default(self):
        self.parent.region_override = None
        self.parent.set_region()

    def update_region_text(self, region: str):
        if self.parent.region_override:
            self.region_menu.setTitle(region)
        else:
            self.region_menu.setTitle('default region')

        if region:
            self.active_region.setText(region)
        else:
            self.active_region.setText(self.default_region_text)

    def reset_previous_action(self, action):
        pass
        # if self.previous_action:
        #     self.previous_action.setIcon(self.assets.get_icon(style='full'))
        #
        #     text = action.text()
        #     text.replace('-> ', '')
        #     action.setText(text)
        # self.previous_action = action

    def show_message(self, title, message):
        self.showMessage(
            title,
            message,
            # QSystemTrayIcon.Information,
            self.assets.get_icon(),
            8000)

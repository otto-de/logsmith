from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QListWidget

from app.aws import iam
from app.core.config import Config
from app.core.core import Core
from app.gui.background_task import BackgroundTask

if TYPE_CHECKING:
    from gui.gui import Gui


class ServiceProfileDialog(QDialog):
    def __init__(self, parent=None):
        super(ServiceProfileDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.core: Core = None
        self.config: Config = None
        self.setWindowTitle('Select Service Role')

        self.core: Core = None
        self.config: Config = None

        self.active_group: str = None
        self.source_profile_list: List[str] = []
        self.selected_source_profile: str = None
        self.selected_service_role: str = None
        self.role_name_filter: str = None

        # This is needed to keep the task alive, otherwise it crashes the application
        self.fetch_roles_task: BackgroundTask = None

        self.width = 400
        self.height = 150

        self.resize(self.width, self.height)

        self.help_text = QLabel(
            "Please be advised that only roles with a trust relationship with your source role can be assumed.\nDepending on how many roles the source role can assume, fetching may take longer.",
            self)
        # TODO extract styles in own file
        self.help_text.setStyleSheet('color: lightgrey; font-style: italic; padding: 5px;')

        self.group_headline = QLabel("Active group:", self)
        self.active_group_text = QLabel(self.active_group, self)
        self.active_group_text.setStyleSheet("padding-left: 5px;")

        self.source_profile_selection_headline = QLabel("Select source profile:", self)
        self.source_profile_selection = QListWidget()
        self.source_profile_selection.clicked.connect(self.select_profile)

        self.available_roles_headline = QLabel("Available roles:", self)
        self.available_role_selection = QListWidget()
        self.available_role_selection.clicked.connect(self.select_role)

        self.history_headline = QLabel("History:", self)
        self.history_selection = QListWidget()
        self.history_selection.clicked.connect(self.select_from_history)

        self.filter_roles_headline = QLabel("Filter Roles:", self)
        self.filter_roles_input = QLineEdit(self)
        self.filter_roles_input.textChanged.connect(self.on_role_name_filter_input_changed)

        self.fetch_button = QPushButton("Fetch Roles")
        self.fetch_button.clicked.connect(self.fetch_roles)
        self.unset_button = QPushButton("unset service role")
        self.unset_button.setStyleSheet("color: red;")
        self.unset_button.clicked.connect(self.unset_service_role)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        self.error_text = QLabel('', self)
        self.error_text.setStyleSheet('color: rgb(255, 0, 0);')

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.error_text)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.help_text)
        vbox.addWidget(self.group_headline)
        vbox.addWidget(self.active_group_text)
        vbox.addWidget(self.source_profile_selection_headline)
        vbox.addWidget(self.source_profile_selection)
        vbox.addWidget(self.available_roles_headline)
        vbox.addWidget(self.available_role_selection)
        vbox.addWidget(self.filter_roles_headline)
        vbox.addWidget(self.filter_roles_input)
        vbox.addWidget(self.history_headline)
        vbox.addWidget(self.history_selection)

        vbox.addWidget(self.fetch_button)
        vbox.addWidget(self.unset_button)

        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def select_profile(self):
        self.selected_source_profile = self.source_profile_selection.currentItem().text()
        self.update_available_role_selection()
        self.set_error_text('')

    def select_role(self):
        self.selected_service_role = self.available_role_selection.currentItem().text()
        self.set_error_text('')

    def select_from_history(self):
        history_string = self.history_selection.currentItem().text()
        history_string_parts = history_string.split(' : ')
        self.selected_source_profile = history_string_parts[0]
        self.selected_service_role = history_string_parts[1]
        self.set_error_text('')

    def fetch_roles(self):
        if self.selected_source_profile:
            self.available_role_selection.clear()
            self.fetch_button.setText('fetching roles... Please wait.')
            self.fetch_roles_task = BackgroundTask(
                func=iam.list_assumable_roles,
                on_success=self.on_fetch_roles_success,
                on_error=self.on_fetch_roles_error,
                kwargs={'source_profile': self.selected_source_profile})
            self.fetch_roles_task.start()
        else:
            self.set_error_text('Please select a profile')
        self.set_error_text('')

    def on_fetch_roles_success(self, role_list):
        self.available_role_selection.addItems(role_list)
        self.fetch_button.setText('Fetch Roles')
        self.gui.set_assumable_roles(profile=self.selected_source_profile, role_list=role_list)

    def on_fetch_roles_error(self, error_message):
        self.set_error_text(error_message)
        self.fetch_button.setText('Fetch Roles')

    def on_role_name_filter_input_changed(self, text):
        self.role_name_filter = text.lower().strip()
        self.update_available_role_selection()

    def unset_service_role(self):
        if not self.source_profile_list:
            self.set_error_text('No source profiles available. Please login first.')
        else:
            self.source_profile_selection.clearSelection()
            self.available_role_selection.clearSelection()
            self.history_selection.clearSelection()
            self.gui.set_service_role(profile=None, role=None)

    def ok(self):
        if not self.selected_source_profile or not self.selected_service_role:
            self.set_error_text('Please select a profile and role')
        else:
            self.gui.set_service_role(profile=self.selected_source_profile, role=self.selected_service_role)
            self.hide()

    def cancel(self):
        self.hide()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.ok()
        elif event.key() == Qt.Key.Key_Enter:
            self.ok()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel()

    def set_error_text(self, message):
        self.error_text.setText(message)
        self.error_text.repaint()

    def show_dialog(self, core: Core, config: Config):
        self.core = core
        self.config = config

        if core.active_profile_group:
            self.active_group = core.active_profile_group.name
            self.active_group_text.setText(self.active_group)

            self.source_profile_list = [profile for profile in self.core.active_profile_group.list_profile_names() if
                                        profile != 'default']

            self.selected_source_profile = self.config.get_selected_service_role_source_profile(group=self.active_group)
            self.selected_service_role = self.config.get_selected_service_role(group=self.active_group)

            self.update_source_profile_selection()
            self.select_in_source_profile_selection(profile=self.selected_source_profile)
            self.update_available_role_selection()
            self.select_in_available_role_selection(role=self.selected_service_role)
            self.update_history_selection()

        if not self.source_profile_list:
            self.set_error_text('No source profiles available. Please login first.')
        else:
            self.set_error_text('')

        self.filter_roles_input.setFocus()

        self.show()
        self.raise_()
        self.activateWindow()

    def update_source_profile_selection(self):
        self.selected_source_profile = self.config.get_selected_service_role_source_profile(group=self.active_group)
        self.source_profile_selection.clear()
        self.source_profile_selection.addItems(self.source_profile_list)

    def select_in_source_profile_selection(self, profile):
        if profile:
            item_to_select = self.source_profile_selection.findItems(profile, Qt.MatchFlag.MatchExactly)
            if item_to_select:
                self.source_profile_selection.setCurrentItem(item_to_select[0])

    def update_available_role_selection(self):
        self.available_role_selection.clear()
        if not self.role_name_filter:
            self.available_role_selection.addItems(
                self.config.get_available_service_roles(group=self.active_group,
                                                        profile=self.selected_source_profile))
        else:
            self.available_role_selection.addItems(
                [role for role in self.config.get_available_service_roles(group=self.active_group,
                                                                          profile=self.selected_source_profile) if
                 self.role_name_filter in role.lower()])

    def select_in_available_role_selection(self, role):
        if role:
            item_to_select = self.available_role_selection.findItems(role, Qt.MatchFlag.MatchExactly)
            if item_to_select:
                self.available_role_selection.setCurrentItem(item_to_select[0])

    def update_history_selection(self):
        self.history_selection.clear()
        self.history_selection.addItems(self.config.get_history(group=self.active_group))


if __name__ == '__main__':
    app = QApplication([])
    ex = ServiceProfileDialog()
    ex.show()
    app.exec()

from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QListWidget

from app.aws import iam
from app.gui.background_task import BackgroundTask

if TYPE_CHECKING:
    from gui.gui import Gui


class ServiceProfileDialog(QDialog):
    def __init__(self, parent=None):
        super(ServiceProfileDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle('Select Service Role')
        self.profile_list: List[str] = []
        self.selected_profile: str = None
        self.available_roles: List[str] = []
        # This is needed to keep the task alive. Otherwise it crashes the application
        self.fetch_roles_task: BackgroundTask = None

        self.width = 400
        self.height = 150

        self.resize(self.width, self.height)

        self.help_text = QLabel(
            "Please be advised that only roles with a trust relationship with your source role can be assumed.\nDepending on how many roles the source role can assume, fetching may take longer.",
            self)
        # TODO extract styles in own file
        self.help_text.setStyleSheet('color: lightgrey; font-style: italic; padding: 5px;')

        self.source_profile_selection_text = QLabel("Select source profile:", self)
        self.source_profile_selection = QListWidget()
        self.source_profile_selection.clicked.connect(self.select_profile)

        self.available_roles_text = QLabel("Available roles:", self)
        self.available_role_selection = QListWidget()
        self.filter_roles_text = QLabel("Filter Roles:", self)
        self.filter_roles_input = QLineEdit(self)

        self.fetch_button = QPushButton("Fetch Roles")
        self.fetch_button.clicked.connect(self.fetch_roles)

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
        vbox.addWidget(self.source_profile_selection_text)
        vbox.addWidget(self.source_profile_selection)
        vbox.addWidget(self.available_roles_text)
        vbox.addWidget(self.available_role_selection)
        vbox.addWidget(self.filter_roles_text)
        vbox.addWidget(self.filter_roles_input)

        vbox.addWidget(self.fetch_button)

        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def select_profile(self):
        self.selected_profile = self.source_profile_selection.currentItem().text()
        self.set_error_text('')

    def fetch_roles(self):
        self.set_error_text('')
        if self.selected_profile:
            self.available_role_selection.clear()
            self.fetch_button.setText('fetching roles... Please wait.')
            self.fetch_roles_task = BackgroundTask(
                func=iam.list_assumable_roles,
                on_success=self.on_fetch_roles_success,
                on_error=self.on_fetch_roles_error,
                kwargs={'source_profile': self.selected_profile})
            self.fetch_roles_task.start()
        else:
            self.set_error_text('Please select a profile')

    def on_fetch_roles_success(self, roles):
        self.gui.core.config.set_assumable_roles(self.selected_profile, roles)
        self.available_role_selection.addItems(roles)
        self.fetch_button.setText('Fetch Roles')

    def on_fetch_roles_error(self, error_message):
        self.set_error_text(error_message)
        self.fetch_button.setText('Fetch Roles')

    def ok(self):
        pass
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

    def show_dialog(self, profile_list: List[str]):
        self.profile_list = profile_list
        self.profile_list = [profile for profile in profile_list if profile != 'default']
        self.source_profile_selection.clear()
        self.source_profile_selection.addItems(self.profile_list)

        if not self.profile_list:
            self.set_error_text('No source profiles available. Please login first.')
        else:
            self.set_error_text('')

        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = ServiceProfileDialog()
    ex.show()
    app.exec()

import sys
from typing import TYPE_CHECKING

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton, \
    QHBoxLayout, QVBoxLayout, QDialog, QLineEdit

from app import __version__
from app.core import files
from app.core.config import Config
from app.gui import styles
from app.yubico import mfa

if TYPE_CHECKING:
    from gui.gui import Gui


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.gui: Gui = parent

        self.setWindowTitle(f'Config - v{__version__.__version_string__}')
        self.initial_width = 600
        self.initial_height = 600
        self.resize(self.initial_width, self.initial_height)

        self.text_box = QPlainTextEdit(self)
        font = QtGui.QFont("Courier New")
        font.setPointSize(14)
        self.text_box.setFont(font)
        self.text_box.setStyleSheet(styles.input_field_style)
        self.text_box.setTabStopDistance(16)

        self.mfa_command_label = QLabel("Shell command to fetch mfa token:", self)
        self.mfa_command_input = QLineEdit(self)
        self.mfa_command_input.setStyleSheet(styles.input_field_style)

        self.default_access_key_label = QLabel("Default access key name:", self)
        self.default_access_key_input = QLineEdit(self)
        self.default_access_key_input.setStyleSheet(styles.input_field_style)
        
        self.default_sso_session_label = QLabel("Default sso session name:", self)
        self.default_sso_session_input = QLineEdit(self)
        self.default_sso_session_input.setStyleSheet(styles.input_field_style)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        self.check_command_button = QPushButton("test command")
        self.check_command_button.clicked.connect(self.check_command)

        self.info_text = QLabel('', self)
        self.info_text.setGeometry(QRect(0, 0, self.width(), 30))

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.info_text)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(10, 0, 10, 10)
        vbox.addWidget(self.text_box)

        vbox.addWidget(self.mfa_command_label)
        vbox.addWidget(self.mfa_command_input)
        vbox.addWidget(self.check_command_button, alignment=Qt.AlignmentFlag.AlignLeft)
        vbox.addWidget(self.default_access_key_label)
        vbox.addWidget(self.default_access_key_input)
        vbox.addWidget(self.default_sso_session_label)
        vbox.addWidget(self.default_sso_session_input)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def ok(self):
        text = self.text_box.toPlainText()
        text = text.replace('\t', '  ')

        raw_config_dict = files.parse_yaml(text)
        if not raw_config_dict:
            self.set_error_text('config invalid')
            return

        default_access_key = self.default_access_key_input.text()
        if not default_access_key:
            self.set_error_text('default access-key must not be empty')
            return
        
        default_sso_session = self.default_sso_session_input.text()
        if not default_sso_session:
            self.set_error_text('default sso session must not be empty')
            return

        config = Config()
        config.initialize_profile_groups(accounts=raw_config_dict, service_roles={},
                                         default_access_key=default_access_key,
                                         default_sso_session=default_sso_session)
        if config.valid:
            config.set_mfa_shell_command(self.mfa_command_input.text())
            config.set_default_access_key(default_access_key)
            config.set_default_sso_session(default_sso_session)
            self.gui.edit_config(config)
            self.hide()
        else:
            self.set_error_text(config.error)

    def cancel(self):
        self.hide()

    def check_command(self):
        token = mfa.fetch_mfa_token_from_shell(self.mfa_command_input.text())
        if token:
            self.set_success_text('command successful')
        else:
            self.set_error_text('command failed')

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

    def update_error_text(self, config: Config):
        if config.valid:
            self.set_error_text('')
        else:
            self.set_error_text(config.error)
        return config

    def set_error_text(self, message):
        self.info_text.setText(message)
        self.info_text.setStyleSheet(styles.error_text_style)
        self.info_text.repaint()

    def set_success_text(self, message):
        self.info_text.setText(message)
        self.info_text.setStyleSheet(styles.success_text_style)
        self.info_text.repaint()

    def show_dialog(self, config: Config):
        config_dict = config.to_dict()
        if config_dict:
            raw_config = files.dump_yaml(config_dict)
        else:
            raw_config = ''
        self.text_box.setPlainText(raw_config)
        self.update_error_text(config)

        self.mfa_command_input.setText(config.mfa_shell_command)
        self.default_access_key_input.setText(config.default_access_key)
        self.default_sso_session_input.setText(config.default_sso_session)

        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = ConfigDialog()
    ex.show()
    sys.exit(app.exec())

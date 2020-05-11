import sys

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton, \
    QHBoxLayout, QVBoxLayout, QDialog, QCheckBox, QLineEdit

from app import __version__
from app.core import files
from app.core.config import Config
from app.yubico import mfa


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.parent = parent

        version = '.'.join(str(i) for i in __version__.__version__)
        self.setWindowTitle(f'Config - v{version}')
        self.initial_width = 600
        self.initial_height = 600
        self.resize(self.initial_width, self.initial_height)

        self.text_box = QPlainTextEdit(self)
        font = QtGui.QFont("Courier")
        font.setPointSize(14)
        self.text_box.setFont(font)
        self.text_box.setStyleSheet('color: rgb(0, 0, 0);')
        self.text_box.setTabStopDistance(16)

        self.mfa_command_label = QLabel("Shell command to fetch mfa token:", self)
        self.mfa_command_input = QLineEdit(self)
        self.mfa_command_input.setStyleSheet("color: rgb(0, 0, 0);")

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
        vbox.setContentsMargins(10, 0, 0, 0)
        vbox.addWidget(self.text_box)

        vbox.addWidget(self.mfa_command_label)
        vbox.addWidget(self.mfa_command_input)
        vbox.addWidget(self.check_command_button, alignment=Qt.AlignRight)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def ok(self):
        text = self.text_box.toPlainText()
        text = text.replace('\t', '  ')

        account_dict = files._parse_yaml(text)
        if not account_dict:
            self.set_error_text('config invalid')
            return

        config = Config()
        config.set_accounts(account_dict)
        if config.valid:
            config.mfa_shell_command = self.mfa_command_input.text()
            self.parent.edit_config(config)
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
        if event.key() == Qt.Key_Return:
            self.ok()
        elif event.key() == Qt.Key_Enter:
            self.ok()
        elif event.key() == Qt.Key_Escape:
            self.cancel()

    def update_error_text(self, config: Config):
        if config.valid:
            self.set_error_text('')
        else:
            self.set_error_text(config.error)
        return config

    def set_error_text(self, message):
        self.info_text.setText(message)
        self.info_text.setStyleSheet('color: rgb(255, 0, 0);')
        self.info_text.repaint()

    def set_success_text(self, message):
        self.info_text.setText(message)
        self.info_text.setStyleSheet('color: rgb(0, 255, 0);')
        self.info_text.repaint()

    def show_dialog(self, config: Config):
        self.text_box.setPlainText(files._dump_yaml(config.to_dict()))
        self.update_error_text(config)
        self.mfa_command_input.setText(config.mfa_shell_command)
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    ex = ConfigDialog()
    ex.show()
    sys.exit(app.exec_())

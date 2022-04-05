from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton

if TYPE_CHECKING:
    from gui.gui import Gui


class SetKeyDialog(QDialog):
    def __init__(self, parent=None):
        super(SetKeyDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle('Access Key')

        self.width = 400
        self.height = 150

        self.resize(self.width, self.height)

        self.key_id_text = QLabel("Key ID:", self)

        self.key_id_input = QLineEdit(self)
        self.key_id_input.setStyleSheet("color: black; background-color: white;")

        self.access_key_text = QLabel("Secret Access Key:", self)

        self.access_key_input = QLineEdit(self)
        self.access_key_input.setStyleSheet("color: black; background-color: white;")
        self.access_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        self.error_text = QLabel('access key will be overwritten!', self)
        self.error_text.setStyleSheet('color: rgb(255, 0, 0);')

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.error_text)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.key_id_text)
        vbox.addWidget(self.key_id_input)
        vbox.addWidget(self.access_key_text)
        vbox.addWidget(self.access_key_input)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def ok(self):
        key_id = self.key_id_input.text()
        key_id = key_id.strip()
        access_key = self.access_key_input.text()
        access_key = access_key.strip()

        if not key_id:
            self.set_error_text('missing key id')
            return
        if not access_key:
            self.set_error_text('missing access key')
            return
        self.gui.set_access_key(key_id=key_id, access_key=access_key)
        self.hide()

    def cancel(self):
        self.hide()

    def get_value(self):
        return self.input_field.text()

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

    def show_dialog(self, message):
        self.access_key_input.setText('')
        self.access_key_input.repaint()
        self.key_id_input.setText('')
        self.key_id_input.repaint()
        self.set_error_text(message)
        self.show()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = SetKeyDialog()
    ex.show()
    app.exec_()

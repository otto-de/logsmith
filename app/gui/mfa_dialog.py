from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton

if TYPE_CHECKING:
    from gui.gui import Gui


class MfaDialog(QDialog):
    def __init__(self, parent=None):
        super(MfaDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.pressed_cancel = False
        self.setWindowTitle('Mfa')

        self.text = QLabel("Mfa Token:", self)

        self.input_field = QLineEdit(self)
        self.input_field.setStyleSheet("color: black; background-color: white;")

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)

        vbox = QVBoxLayout()
        vbox.addWidget(self.text)
        vbox.addWidget(self.input_field)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def ok(self):
        self.pressed_cancel = False
        self.hide()

    def cancel(self):
        self.pressed_cancel = True
        self.hide()

    def get_value(self):
        return self.input_field.text()

    def closeEvent(self, event):
        self.pressed_cancel = True
        event.ignore()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.ok()
        elif event.key() == Qt.Key.Key_Enter:
            self.ok()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel()

    def get_mfa_token(self):
        self.exec()
        self.activateWindow()
        if self.pressed_cancel:
            return None
        return self.get_value()


if __name__ == '__main__':
    app = QApplication([])
    ex = MfaDialog()
    ex.show()
    app.exec()

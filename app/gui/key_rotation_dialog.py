from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QListWidget

if TYPE_CHECKING:
    from gui.gui import Gui


class RotateKeyDialog(QDialog):
    def __init__(self, parent=None):
        super(RotateKeyDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle('Rotate Access Key')

        self.width = 400
        self.height = 100

        self.resize(self.width, self.height)

        self.access_key_selection = QListWidget()

        self.text = QLabel("This will create a new key and delete the old one!", self)
        self.text.setStyleSheet('color: rgb(255, 0, 0);')

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.access_key_selection)
        vbox.addWidget(self.text)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def ok(self):
        selected_key = self.access_key_selection.currentItem().text()
        self.gui.rotate_access_key(key_name=selected_key)
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

    def show_dialog(self, access_key_list: List[str]):
        self.access_key_selection.clear()
        for access_key in access_key_list:
            self.access_key_selection.addItem(access_key)
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = RotateKeyDialog()
    ex.show_dialog(['access-key-test'])
    app.exec()

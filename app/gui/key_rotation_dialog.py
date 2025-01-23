from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QListWidget

from app.gui import styles

if TYPE_CHECKING:
    from gui.gui import Gui


class RotateKeyDialog(QDialog):
    def __init__(self, parent=None):
        super(RotateKeyDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle('Rotate Access Key')

        self.width = 600
        self.height = 200

        self.resize(self.width, self.height)

        self.help_text = [
            "This will use an the selected access-key to create a new one (in the account where this key is from)",
            "and will then proceed to delete the old key and update your local credentials file, overwriting it.",
            "",
            "Rotating a key this way is only possible if your account has a minimum access key limit of 2,",
            "they can not be rotated in place. ",
            ]
        self.help_text_label = QLabel(
            '\n'.join(self.help_text),
            self)
        self.help_text_label.setStyleSheet(styles.help_text_style)

        self.access_key_selection_text = QLabel("Select existing access-key:", self)
        self.access_key_selection = QListWidget()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.help_text_label)
        vbox.addWidget(self.access_key_selection_text)
        vbox.addWidget(self.access_key_selection)
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
        self.access_key_selection.addItems(access_key_list)
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = RotateKeyDialog()
    ex.show_dialog(['access-key-test'])
    app.exec()

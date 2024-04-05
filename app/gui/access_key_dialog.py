from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QApplication, QHBoxLayout, QVBoxLayout, \
    QPushButton, QListWidget

if TYPE_CHECKING:
    from gui.gui import Gui


class SetKeyDialog(QDialog):
    def __init__(self, parent=None):
        super(SetKeyDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle('Set Access Key')
        self.existing_access_key_list: List[str] = []

        self.width = 400
        self.height = 150

        self.resize(self.width, self.height)

        self.access_key_selection_text = QLabel("Select existing access-key:", self)
        self.access_key_selection = QListWidget()
        self.deselect_button = QPushButton("Deselect")
        self.deselect_button.clicked.connect(self.deselect)

        self.key_name_text = QLabel("New Key name:", self)
        self.key_name_input = QLineEdit(self)
        self.key_name_input.setStyleSheet("color: black; background-color: white;")
        self.key_name_input.textChanged.connect(self.check_access_key_name)
        self.key_name_input.setPlaceholderText('access-key-<name>')

        self.key_id_text = QLabel("Key ID:", self)
        self.key_id_input = QLineEdit(self)
        self.key_id_input.setStyleSheet("color: black; background-color: white;")

        self.key_secret_text = QLabel("Key secret:", self)
        self.key_secret_input = QLineEdit(self)
        self.key_secret_input.setStyleSheet("color: black; background-color: white;")
        self.key_secret_input.setEchoMode(QLineEdit.EchoMode.Password)

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
        vbox.addWidget(self.access_key_selection_text)
        vbox.addWidget(self.access_key_selection)
        vbox.addWidget(self.deselect_button)
        vbox.addWidget(self.key_name_text)
        vbox.addWidget(self.key_name_input)
        vbox.addWidget(self.key_id_text)
        vbox.addWidget(self.key_id_input)
        vbox.addWidget(self.key_secret_text)
        vbox.addWidget(self.key_secret_input)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def check_access_key_name(self, new_value: str):
        if new_value in self.existing_access_key_list:
            self.set_error_text('access key name already exists and will be overwritten')
        elif new_value != '' and not new_value.startswith('access-key'):
            self.set_error_text('new key names must start with \'access-key\'')
        else:
            self.set_error_text('')
        self.access_key_selection.clearSelection()

    def deselect(self):
        self.access_key_selection.clearSelection()

    def ok(self):
        if self.access_key_selection.selectedItems():
            selected_key = self.access_key_selection.currentItem().text()
        else:
            selected_key = ''
        new_key_name = self.key_name_input.text()
        new_key_name = new_key_name.strip()

        if selected_key != '':
            key_name = selected_key
        else:
            key_name = new_key_name

        key_id = self.key_id_input.text()
        key_id = key_id.strip()
        key_secret = self.key_secret_input.text()
        key_secret = key_secret.strip()

        if not key_name:
            self.set_error_text('missing key name')
            return
        if not key_id:
            self.set_error_text('missing key id')
            return
        if not key_secret:
            self.set_error_text('missing access key')
            return
        if key_name != '' and not key_name.startswith('access-key'):
            self.set_error_text('new key names must start with \'access-key\'')
            return
        if key_name != '' and key_name.startswith('session-token'):
            self.set_error_text('new key names must not start with \'session-token\'')
            return
        self.gui.set_access_key(key_name=key_name, key_id=key_id, key_secret=key_secret)
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

    def show_dialog(self, access_key_list: List[str]):
        self.access_key_selection.clear()
        self.access_key_selection.addItems(access_key_list)
        self.key_name_input.setText('')
        self.key_name_input.repaint()
        self.key_id_input.setText('')
        self.key_id_input.repaint()
        self.key_secret_input.setText('')
        self.key_secret_input.repaint()
        self.set_error_text('')

        self.existing_access_key_list = access_key_list
        self.check_access_key_name(self.key_name_input.text())

        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = SetKeyDialog()
    ex.show()
    app.exec()

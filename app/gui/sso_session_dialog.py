from typing import TYPE_CHECKING, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QListWidget,
)

from app.gui import styles

if TYPE_CHECKING:
    from gui.gui import Gui


class SetSsoSessionDialog(QDialog):
    def __init__(self, parent=None):
        super(SetSsoSessionDialog, self).__init__(parent)
        self.gui: Gui = parent
        self.setWindowTitle("Set SSO Session")
        self.existing_sso_session_list: List[str] = []

        self.width = 600
        self.height = 150

        self.resize(self.width, self.height)

        self.help_text = [
            "Select the sso session you want to set or create.",
            "All sso sessions name must start with the prefix 'sso'",
            "The default name is simply 'sso'.",
        ]
        self.help_text_label = QLabel("\n".join(self.help_text), self)
        self.help_text_label.setStyleSheet(styles.help_text_style)

        self.sso_session_selection_text = QLabel("Select existing sessions:", self)
        self.sso_session_selection = QListWidget()
        self.sso_session_selection.clicked.connect(self.select_sso_session)

        self.deselect_button = QPushButton("Deselect")
        self.deselect_button.clicked.connect(self.deselect)

        self.sso_name_text = QLabel("SSO Session Name:", self)
        self.sso_name_input = QLineEdit(self)
        self.sso_name_input.setStyleSheet(styles.input_field_style)
        self.sso_name_input.textChanged.connect(self.check_sso_session_name)
        self.sso_name_input.setPlaceholderText("sso-<name>")

        self.sso_url_text = QLabel("SSO Url:", self)
        self.sso_url_input = QLineEdit(self)
        self.sso_url_input.setStyleSheet(styles.input_field_style)

        self.sso_region_text = QLabel("SSO Region:", self)
        self.sso_region_input = QLineEdit(self)
        self.sso_region_input.setStyleSheet(styles.input_field_style)

        self.sso_scopes_text = QLabel("SSO Scopes:", self)
        self.sso_scopes_input = QLineEdit(self)
        self.sso_scopes_input.setStyleSheet(styles.input_field_style)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        self.error_text = QLabel("", self)
        self.error_text.setStyleSheet(styles.error_text_style)

        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.error_text)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.help_text_label)
        vbox.addWidget(self.sso_session_selection_text)
        vbox.addWidget(self.sso_session_selection)
        vbox.addWidget(self.deselect_button)
        vbox.addWidget(self.sso_name_text)
        vbox.addWidget(self.sso_name_input)
        vbox.addWidget(self.sso_url_text)
        vbox.addWidget(self.sso_url_input)
        vbox.addWidget(self.sso_region_text)
        vbox.addWidget(self.sso_region_input)
        vbox.addWidget(self.sso_scopes_text)
        vbox.addWidget(self.sso_scopes_input)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.installEventFilter(self)

    def select_sso_session(self):
        self.sso_name_input.setText(self.sso_session_selection.currentItem().text())

    def check_sso_session_name(self, new_value: str):
        if new_value in self.existing_sso_session_list:
            self.set_error_text("sso session already exists and will be overwritten")
        elif new_value != "" and not new_value.startswith("sso"):
            self.set_error_text("new session names must start with 'sso'")
        else:
            self.set_error_text("")
        self.sso_session_selection.clearSelection()

    def deselect(self):
        self.sso_session_selection.clearSelection()
        self.sso_name_input.setText("")

    def ok(self):
        if self.sso_session_selection.selectedItems():
            selected_sso_session = self.sso_session_selection.currentItem().text()
        else:
            selected_sso_session = ""
        new_sso_name = self.sso_name_input.text()
        new_sso_name = new_sso_name.strip()

        if selected_sso_session != "":
            sso_name = selected_sso_session
        else:
            sso_name = new_sso_name

        sso_name = self.sso_name_input.text()
        sso_name = sso_name.strip()
        sso_url = self.sso_url_input.text()
        sso_url = sso_url.strip()
        sso_region = self.sso_region_input.text()
        sso_region = sso_region.strip()
        sso_scopes = self.sso_scopes_input.text()
        sso_scopes = sso_scopes.strip()

        if not sso_name:
            self.set_error_text("missing sso name")
            return
        if not sso_url:
            self.set_error_text("missing sso url")
            return
        if not sso_region:
            self.set_error_text("missing sso region")
            return
        if not sso_scopes:
            self.set_error_text("missing sso scopes")
            return
        if sso_name != "" and not sso_name.startswith("sso"):
            self.set_error_text("new sso session names must start with 'sso'")
            return

        self.gui.set_sso_session(
            sso_name=sso_name,
            sso_url=sso_url,
            sso_region=sso_region,
            sso_scopes=sso_scopes,
        )
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

    def show_dialog(self, sso_session_list: List[str]):
        self.sso_session_selection.clear()
        self.sso_session_selection.addItems(sso_session_list)
        self.sso_name_input.setText("")
        self.sso_name_input.repaint()
        self.sso_url_input.setText("")
        self.sso_url_input.repaint()
        self.sso_region_input.setText("")
        self.sso_region_input.repaint()
        self.sso_scopes_input.setText("")
        self.sso_scopes_input.repaint()
        self.set_error_text("")

        self.existing_sso_session_list = sso_session_list
        self.check_sso_session_name(self.sso_name_input.text())

        if not sso_session_list:
            self.sso_name_input.setText("sso")

        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == "__main__":
    app = QApplication([])
    ex = SetSsoSessionDialog()
    ex.show_dialog([])
    app.exec()

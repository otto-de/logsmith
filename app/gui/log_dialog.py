from typing import TYPE_CHECKING

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QPlainTextEdit, QVBoxLayout, QDialog, QSizePolicy, QPushButton, QLabel, \
    QCheckBox, QHBoxLayout

from app.core import files
from app.gui import styles

if TYPE_CHECKING:
    from gui.gui import Gui


class LogDialog(QDialog):
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.gui: Gui = parent

        self.setWindowTitle('Logs')
        self.initial_width = 600
        self.initial_height = 600
        self.resize(self.initial_width, self.initial_height)

        self.logs = ''
        self.trailing_logs = True
        self.last_read_position = 0

        self.text_box = QPlainTextEdit(self)
        font = QtGui.QFont("Courier New")
        font.setPointSize(14)
        self.text_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_box.setStyleSheet(styles.input_field_style)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_log_text_box)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        self.trailing_label = QLabel("Trail logs")
        self.trailing_checkbox = QCheckBox()
        self.trailing_checkbox.setChecked(self.trailing_logs)  # Set checkbox to checked by default
        self.trailing_checkbox.stateChanged.connect(self.check_trailing_logs)

        hbox = QHBoxLayout()
        hbox.addWidget(self.trailing_checkbox)
        hbox.addWidget(self.trailing_label)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(10, 0, 10, 10)
        vbox.addWidget(self.text_box)
        vbox.addLayout(hbox)
        vbox.addWidget(self.refresh_button)
        vbox.addWidget(self.close_button)

        self.setLayout(vbox)

        self.fetch_logs_timer = None

    def closeEvent(self, event):
        event.ignore()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def close(self):
        self.stop_timer()
        self.hide()

    def check_trailing_logs(self, state):
        self.trailing_logs = not self.trailing_logs
        # if state == 2:
        # elif state == 0:
        #     self.trailing_logs = False
        print('trailing logs:', self.trailing_logs)
        print('state:', state)

    def start_timer(self):
        timer = QTimer()
        timer.setSingleShot(False)
        timer.timeout.connect(self.update_log_text_box)
        timer.start(1000)
        self.fetch_logs_timer = timer

    def stop_timer(self):
        if self.fetch_logs_timer:
            self.fetch_logs_timer.stop()

    def reset_log_text_box(self):
        self.logs = ''
        self.text_box.clear()

    def update_log_text_box(self):
        logs_as_text, self.last_read_position = files.load_log_with_position(self.last_read_position)
        if logs_as_text:
            self.text_box.appendPlainText(logs_as_text)
            self.text_box.repaint()
            if self.trailing_logs:
                self.text_box.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def show_dialog(self):
        self.reset_log_text_box()
        self.update_log_text_box()
        self.start_timer()

        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = LogDialog()
    ex.show_dialog('')
    app.exec()

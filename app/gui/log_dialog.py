from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy, QScrollArea, QVBoxLayout, \
    QDialog


class LogDialog(QDialog):
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle('Logs')

        self.initial_width = 600
        self.initial_height = 400
        self.resize(self.initial_width, self.initial_height)

        self.text_box = QLabel('no logs', self)
        self.text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_box.setAlignment(Qt.AlignTop)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setVisible(True)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.text_box)
        self.scroll_area.resize(self.initial_width, self.initial_height)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(1, 1, 1, 1)
        vbox.addWidget(self.scroll_area)

        self.setLayout(vbox)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def show_dialog(self, logs_as_text):
        self.text_box.setText(logs_as_text)
        self.text_box.repaint()
        self.scroll_area.repaint()
        self.show()
        self.resizeEvent(None)
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
        self.activateWindow()


if __name__ == '__main__':
    app = QApplication([])
    ex = LogDialog()
    ex.show_dialog('')
    app.exec_()

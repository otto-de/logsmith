import logging
import os
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from app.core import files
from app.logsmith import MainWindow


def main():
    app_path = files.get_app_path()
    if not os.path.exists(app_path):
        os.mkdir(app_path)
    if not os.path.isfile(files.get_config_path()):
        open(files.get_config_path(), 'w')
    if not os.path.isfile(files.get_accounts_path()):
        open(files.get_accounts_path(), 'w')

    aws_path = files.get_aws_path()
    if not os.path.exists(aws_path):
        os.mkdir(aws_path)

    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger('logsmith')
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(asctime)12s [%(levelname)s] %(threadName)-12.12s %(message)s")

    file_handler = logging.FileHandler(f'{app_path}/app.log', mode='w')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logging.info(f'config dir {app_path}')
    logging.info('start app')

    try:
        app = QApplication(sys.argv)
        MainWindow(app)

        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        sys.exit(app.exec_())
    except Exception:
        logging.error('unexpected error', exc_info=True)


if __name__ == '__main__':
    main()

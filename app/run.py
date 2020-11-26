import logging
import os
import sys

import arguments
from app.core import files
from cli.main import start_cli
from gui.main import start_gui


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

    args = arguments.parse(sys.argv[1:])
    logging.basicConfig(level=logging.getLevelName(args.loglevel))
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

    if arguments.use_cli(args):
        start_cli(args)
    else:
        start_gui()


if __name__ == '__main__':
    main()

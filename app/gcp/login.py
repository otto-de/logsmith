import logging

from app.shell import shell

logger = logging.getLogger('logsmith')


def gcloud_auth_login():
    logger.info(f'run gcloud auth login and wait for 60 seconds to complete login flow!')
    return shell.run("gcloud auth login", timeout=60)


def gcloud_auth_application_login():
    logger.info(f'run gcloud auth application-default login and wait for 60 seconds to complete login flow!')
    return shell.run("gcloud auth application-default login", timeout=60)
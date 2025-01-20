import logging

from app.shell import shell

logger = logging.getLogger('logsmith')


def set_default_project(project: str):
    logger.info(f'set default project to: {project}')
    return shell.run(f"gcloud config set project {project}", timeout=5)


def set_default_quota_project(project: str):
    logger.info(f'set default quota-project to: {project}')
    return shell.run(f"gcloud auth application-default set-quota-project {project}", timeout=5)


def set_default_region(region: str):
    logger.info(f'set default region to: {region}')
    return shell.run(f"gcloud config set compute/region {region}", timeout=5)

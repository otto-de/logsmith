import logging

from app.shell import shell
from core.result import Result

logger = logging.getLogger('logsmith')


def set_default_project(project: str) -> Result:
    logger.info(f'set default project to: {project}')
    result = Result()
    
    script_result = shell.run(f"gcloud config set project {project}", timeout=5)
    if not script_result.was_success:
        return script_result
    
    if script_result.payload is None:
        result.error("config gcp project failed")
    else:
        result.set_success()
    return result


def set_default_quota_project(project: str) -> Result:
    logger.info(f'set default quota-project to: {project}')
    result = Result()
    
    script_result = shell.run(f"gcloud auth application-default set-quota-project {project}", timeout=5)
    if not script_result.was_success:
        return script_result
    
    if script_result.payload is None:
        result.error("config gcp quota-project failed")
    else:
        result.set_success()
    return result


def set_default_region(region: str) -> Result:
    logger.info(f'set default region to: {region}')
    result = Result()
    
    script_result = shell.run(f"gcloud config set compute/region {region}", timeout=5)
    if not script_result.was_success:
        return script_result
    
    if script_result.payload is None:
        result.error("config gcp region failed")
    else:
        result.set_success()
    return result

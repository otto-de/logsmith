import logging

from app.shell import shell
from core.result import Result

logger = logging.getLogger('logsmith')


def gcloud_auth_login() -> Result:
    logger.info(f'run gcloud auth login and wait for 60 seconds to complete login flow!')
    result = Result()
    
    script_result = shell.run("gcloud auth login", timeout=60)
    if not script_result.was_success:
        return script_result
    
    if script_result.payload is None:
        result.error("gcloud auth login command failed")
    else:
        result.set_success()
    return result


def gcloud_auth_application_login() -> Result:
    logger.info(f'run gcloud auth application-default login and wait for 60 seconds to complete login flow!')
    result = Result()
    
    script_result = shell.run("gcloud auth application-default login", timeout=60)
    if not script_result.was_success:
        return script_result
    
    if script_result.payload is None:
        result.error("gcloud auth application-default login command failed")
    else:
        result.set_success()
    return result

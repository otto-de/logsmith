import logging
import os
import pwd
import subprocess

from core.result import Result

logger = logging.getLogger('logsmith')

def get_login_shell():
    return os.environ.get("SHELL") or pwd.getpwuid(os.getuid()).pw_shell or "/bin/sh"

def login_shell_env():
    shell = get_login_shell()
    cmd = [shell, "-l", "-c", "printenv"]
    out = subprocess.check_output(cmd).decode()
    env = {}
    for kv in out.split("\n"):
        if not kv:
            continue
        k, _, v = kv.partition("=")
        env[k] = v
    return env

def run(command, timeout=5) -> Result:
    logger.info(f"run command: {command}")
    shell = get_login_shell()
    logger.info(f"shell: {shell}")

    result = Result()
    proc = None
    try:
        proc = subprocess.run(command,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=timeout,
                              shell=True,
                              text=True,
                              universal_newlines=True,
                              executable=shell,
                              env=login_shell_env())
        proc.check_returncode()       
        result.add_payload(proc.stdout.rstrip())
        result.set_success()
    
    except subprocess.TimeoutExpired:
        error_message = f'command {command} took too long and was aborted'
        logger.warning(error_message)
        result.error(error_message)
        
    except FileNotFoundError:
        error_message = f'command {command} not found'
        logger.warning(error_message)
        result.error(error_message)
        
    except subprocess.CalledProcessError as error:
        error_message = f'command {command} failed'
        logger.warning(error_message)
        logger.warning(str(error), exc_info=True)
        result.error(error_message)
        
    except Exception as error:
        error_message = f'command {command} failed with unknown error'
        logger.error(error_message)
        logger.error(str(error), exc_info=True)
        result.error(error_message)
        
    if proc is not None:
        logger.info(f'--- shell output start ---\n{proc.stdout.rstrip()}')
        logger.info(f'--- shell output end ---')
    else:
        logger.info(f'--- no shell output ---')
        
    return result

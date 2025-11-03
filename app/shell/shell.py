import logging
import subprocess

from core.result import Result

logger = logging.getLogger('logsmith')


def run(command, timeout=5) -> Result:
    result = Result()
    proc = None
    bash_command = ['bash', '-c', command]
    try:
        proc = subprocess.run(bash_command,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=timeout,
                              shell=False,
                              text=True,
                              universal_newlines=True)
        proc.check_returncode()       
        result.add_payload(proc.stdout.rstrip())
        result.set_success()
        return result
    
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
        logger.info(f'--- script output start ---\n{proc.stdout.rstrip()}')
        logger.info(f'--- script output end ---')
    else:
        logger.info(f'--- no script output ---')
        
    return result

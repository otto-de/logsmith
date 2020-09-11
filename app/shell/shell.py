import logging
import subprocess

logger = logging.getLogger('logsmith')


def run(command, timeout=5):
    proc = None
    try:
        bash_command = ['bash', '-c', command]
        proc = subprocess.run(bash_command,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=timeout,
                              shell=False,
                              text=True,
                              universal_newlines=True)
        proc.check_returncode()
        return proc.stdout.rstrip()
    except subprocess.TimeoutExpired:
        logger.warning(f'command {command} took too long and was aborted')
        return None
    except FileNotFoundError:
        logger.warning(f'command {command} not found')
        return None
    except subprocess.CalledProcessError:
        logger.warning(f'command {command} failed')
        if proc:
            logger.warning(proc.stderr)
        else:
            logger.warning('could not fetch output')
        return None

import logging
import shlex
import subprocess as sp

logger = logging.getLogger('logsmith')


def run(command):
    try:
        proc = sp.run(shlex.split(command),
                      stdout=sp.PIPE,
                      check=True,
                      universal_newlines=True)
        return proc.stdout.rstrip()
    except FileNotFoundError:
        logger.warning(f'command {command} not found')
        return None
    except sp.CalledProcessError:
        logger.warning(f'command {command} failed')
        return None

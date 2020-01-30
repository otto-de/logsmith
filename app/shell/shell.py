import logging
import shlex
import subprocess as sp

logger = logging.getLogger('logsmith')


def run(command):
    proc = None
    try:
        proc = sp.run(shlex.split(command),
                      stdout=sp.PIPE,
                      stderr=sp.PIPE,
                      timeout=3,
                      universal_newlines=True)
        proc.check_returncode()
        return proc.stdout.rstrip()
    except FileNotFoundError:
        logger.warning(f'command {command} not found')
        return None
    except sp.CalledProcessError:
        logger.warning(f'command {command} failed')
        if proc:
            logger.warning(proc.stderr)
        else:
            logger.warning('could not fetch output')
        return None

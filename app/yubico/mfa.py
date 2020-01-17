import logging
import re
from typing import Optional

from app.shell import shell

logger = logging.getLogger('logsmith')


def fetch_mfa_token_from_shell(command):
    if not command:
        return None
    logger.info(f'run {command}')
    result = shell.run(command)
    logger.info(result)
    if result:
        token = _extract_token(result)
        if token:
            return token
    return None


def _extract_token(stout: str) -> Optional[str]:
    for line in stout.split('\n'):
        if 'Amazon Web Services' in line:
            line = line.rstrip()
            token_list = re.findall(r'\d{6}$', line)
            if len(token_list) == 1:
                return token_list[0]
            else:
                logger.error(f'could not find mfa token in {line}')
    return None

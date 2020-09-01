import logging

from app.shell import shell

logger = logging.getLogger('logsmith')


def fetch_mfa_token_from_shell(command):
    if not command:
        return None
    logger.info(f'run shell command {command}')
    token = shell.run(command)
    if token:
        token = token.strip()
        if len(token) == 6 and token.isdigit():
            return token
    return None

import logging

from app.shell import shell

logger = logging.getLogger("logsmith")


def fetch_mfa_token_from_shell(command) -> str | None:
    if not command:
        return None
    logger.info("Fetch MFA token with command")
    script_result = shell.run(command)
    if not script_result.was_success:
        return None

    token = script_result.payload
    if token:
        token = token.strip()
        if len(token) == 6 and token.isdigit():
            return token
    return None

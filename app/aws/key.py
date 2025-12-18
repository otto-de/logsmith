import logging
from app.aws import iam, credentials
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    ParamValidationError,
    ReadTimeoutError,
)

from app.core.profile_group import ProfileGroup
from app.core.result import Result
from app.util import util

logger = logging.getLogger("logsmith")

def has_access_key(access_key: str) -> Result:
    logger.info("has access key")
    result = Result()
    credentials_file = credentials.load_credentials_file()

    if not credentials_file.has_section(access_key):
        error_text = f"could not find access-key '{access_key}' in .aws/credentials"
        result.error(error_text)
        logger.warning(error_text)
        return result
    result.set_success()
    return result


def check_access_key(access_key: str) -> Result:
    access_key_result = has_access_key(access_key=access_key)
    if not access_key_result.was_success:
        return access_key_result

    logger.info("check access key")
    result = Result()
    try:
        client = credentials.get_client(access_key, "sts", timeout=2, retries=2)
        client.get_caller_identity()
    except ClientError:
        error_text = "access key is not valid"
        result.error(error_text)
        logger.warning(error_text)
        return result
    except (EndpointConnectionError, ReadTimeoutError):
        error_text = "could not reach sts service"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    result.set_success()
    return result


def has_session(session_profile_name: str) -> Result:
    logger.info(f"has session {session_profile_name}")
    result = Result()
    credentials_file = credentials.load_credentials_file()

    if credentials_file.has_section(session_profile_name):
        result.set_success()
    else:
        logger.warning("no session found")
    return result


def check_session(access_key: str) -> Result:
    session_token_profile_name = util.generate_session_name(access_key)
    session_result = has_session(session_profile_name=session_token_profile_name)
    if not session_result.was_success:
        return session_result

    logger.info(f"check session {session_token_profile_name}")
    result = Result()
    try:
        client = credentials.get_client(session_token_profile_name, "sts", timeout=2, retries=2)
        client.get_caller_identity()
    except ClientError:
        # this is the normal case when the session token is not valid. Proceed then to fetch a new one
        return result
    except (EndpointConnectionError, ReadTimeoutError):
        error_text = "could not reach sts service"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    logger.info("check session - valid")
    result.set_success()
    return result


def fetch_session_token(access_key: str, mfa_token: str) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info(f"fetch session-token for {access_key}")
    session_token_profile_name = util.generate_session_name(access_key)

    try:
        secrets = _get_session_token(access_key=access_key, mfa_token=mfa_token)
    except ClientError:
        error_text = "could not fetch session token"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    except ParamValidationError:
        error_text = "invalid mfa token"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    except NoCredentialsError:
        error_text = "access_key credentials invalid"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    credentials.add_profile_credentials(credentials_file, session_token_profile_name, secrets)
    credentials.write_credentials_file(credentials_file)
    logger.info(f"{session_token_profile_name} successfully fetched")
    result.set_success()
    return result


def fetch_key_credentials(user_name: str, profile_group: ProfileGroup) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info("fetch role credentials")

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f"fetch {profile.profile}")
            source_profile = profile.source or util.generate_session_name(
                profile_group.get_access_key()
            )
            secrets = iam.assume_role(
                source_profile, user_name, profile.account, profile.role
            )
            credentials.add_profile_credentials(credentials_file, profile.profile, secrets)
            if profile.default:
                credentials.add_profile_credentials(credentials_file, "default", secrets)
            credentials.write_credentials_file(credentials_file)
    except Exception:
        error_text = "error while fetching role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result

def fetch_key_service_profile(profile_group: ProfileGroup) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info("add service profile via access-key")

    service_profile = profile_group.service_profile

    try:
        logger.info(f"fetch {service_profile.profile}")
        secrets = iam.assume_role(
            service_profile.source,
            service_profile.role,
            service_profile.account,
            service_profile.role,
        )
        credentials.add_profile_credentials(credentials_file, service_profile.profile, secrets)
        credentials.write_credentials_file(credentials_file)
    except Exception:
        error_text = "error while fetching role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result

def set_access_key(key_name: str, key_id: str, key_secret: str) -> Result:
    result = Result()

    credentials_file = credentials.load_credentials_file()
    if not credentials_file.has_section(key_name):
        credentials_file.add_section(key_name)
    credentials_file.set(key_name, "aws_access_key_id", key_id)
    credentials_file.set(key_name, "aws_secret_access_key", key_secret)
    credentials.write_credentials_file(credentials_file)

    result.set_success()
    return result

def get_access_key_list() -> list:
    credentials_file = credentials.load_credentials_file()
    access_key_list = []
    for profile in credentials_file.sections():
        if profile.startswith("access-key"):
            access_key_list.append(profile)
    return access_key_list


def get_access_key_id(key_name: str) -> str:
    credentials_file = credentials.load_credentials_file()
    return credentials_file.get(key_name, "aws_access_key_id")

def get_user_name(access_key) -> str:
    logger.info("fetch user name")
    client = credentials.get_client(access_key, "sts")
    identity = client.get_caller_identity()
    return _extract_user_from_identity(identity)


def _extract_user_from_identity(identity):
    return identity["Arn"].split("/")[-1]


def _get_session_token(access_key: str, mfa_token: str) -> dict:
    client = credentials.get_client(access_key, "sts")

    identity = client.get_caller_identity()
    duration = 43200  # 12 * 60 * 60
    user = _extract_user_from_identity(identity)
    mfa_arn = f'arn:aws:iam::{identity["Account"]}:mfa/{user}'

    response = client.get_session_token(
        DurationSeconds=duration, SerialNumber=mfa_arn, TokenCode=mfa_token
    )
    return response["Credentials"]

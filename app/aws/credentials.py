import configparser
import logging
import os
from pathlib import Path

import boto3
import botocore
from botocore.exceptions import ClientError, ParamValidationError, EndpointConnectionError, \
    NoCredentialsError, ReadTimeoutError

from app.core.profile_group import ProfileGroup
from app.core.result import Result
from app.util import util

logger = logging.getLogger('logsmith')


def _get_credentials_path() -> str:
    return os.path.join(str(Path.home()), '.aws', 'credentials')


def _get_config_path() -> str:
    return os.path.join(str(Path.home()), '.aws', 'config')


def _load_file(path: str) -> configparser.ConfigParser:
    config_parser = configparser.ConfigParser()
    config_parser.read(path)
    return config_parser


def _write_file(path: str, config_parser: configparser) -> None:
    with open(path, 'w') as file:
        config_parser.write(file)


def _load_credentials_file() -> configparser.ConfigParser:
    return _load_file(_get_credentials_path())


def _load_config_file() -> configparser.ConfigParser:
    return _load_file(_get_config_path())


def _write_credentials_file(credentials: configparser) -> None:
    _write_file(_get_credentials_path(), credentials)


def _write_config_file(config: configparser) -> None:
    _write_file(_get_config_path(), config)


def _get_client(profile_name: str, service: str, timeout: int = None, retries: int = None):
    session = boto3.Session(profile_name=profile_name)
    config_dict = {}
    if timeout is not None:
        config_dict['connect_timeout'] = timeout
    if retries is not None:
        config_dict['retries'] = {'total_max_attempts': retries}
    if timeout is not None or retries is not None:
        config = botocore.config.Config(**config_dict)
        return session.client(service, config=config)
    return session.client(service)


def has_access_key(access_key: str) -> Result:
    logger.info('has access key')
    result = Result()
    credentials_file = _load_credentials_file()

    if not credentials_file.has_section(access_key):
        error_text = f'could not find access-key \'{access_key}\' in .aws/credentials'
        result.error(error_text)
        logger.warning(error_text)
        return result
    result.set_success()
    return result


def check_access_key(access_key: str) -> Result:
    access_key_result = has_access_key(access_key=access_key)
    if not access_key_result.was_success:
        return access_key_result

    logger.info('check access key')
    result = Result()
    try:
        client = _get_client(access_key, 'sts', timeout=2, retries=2)
        client.get_caller_identity()
    except ClientError:
        error_text = 'access key is not valid'
        result.error(error_text)
        logger.warning(error_text)
        return result
    except (EndpointConnectionError, ReadTimeoutError):
        error_text = 'could not reach sts service'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    result.set_success()
    return result


def has_session(session_profile_name: str) -> Result:
    logger.info(f'has session {session_profile_name}')
    result = Result()
    credentials_file = _load_credentials_file()

    if credentials_file.has_section(session_profile_name):
        result.set_success()
    else:
        logger.warning('no session found')
    return result


def check_session(access_key: str) -> Result:
    session_token_profile_name = util.generate_session_name(access_key)
    session_result = has_session(session_profile_name=session_token_profile_name)
    if not session_result.was_success:
        return session_result

    logger.info(f'check session {session_token_profile_name}')
    result = Result()
    try:
        client = _get_client(session_token_profile_name, 'sts', timeout=2, retries=2)
        client.get_caller_identity()
    except ClientError:
        # this is the normal case when the session token is not valid. Proceed then to fetch a new one
        return result
    except (EndpointConnectionError, ReadTimeoutError):
        error_text = 'could not reach sts service'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    logger.info('check session - valid')
    result.set_success()
    return result


def fetch_session_token(access_key: str, mfa_token: str) -> Result:
    result = Result()
    credentials_file = _load_credentials_file()
    logger.info(f'fetch session-token for {access_key}')
    session_token_profile_name = util.generate_session_name(access_key)

    try:
        secrets = _get_session_token(access_key=access_key, mfa_token=mfa_token)
    except ClientError:
        error_text = 'could not fetch session token'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    except ParamValidationError:
        error_text = 'invalid mfa token'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    except NoCredentialsError:
        error_text = 'access_key credentials invalid'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    _add_profile_credentials(credentials_file, session_token_profile_name, secrets)
    _write_credentials_file(credentials_file)
    logger.info(f'{session_token_profile_name} successfully fetched')
    result.set_success()
    return result


def fetch_role_credentials(user_name: str, profile_group: ProfileGroup) -> Result:
    result = Result()
    credentials_file = _load_credentials_file()
    logger.info('fetch role credentials')

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f'fetch {profile.profile}')
            source_profile = profile.source or util.generate_session_name(profile_group.get_access_key())
            secrets = _assume_role(source_profile, user_name, profile.account, profile.role)
            _add_profile_credentials(credentials_file, profile.profile, secrets)
            if profile.default:
                _add_profile_credentials(credentials_file, 'default', secrets)
            _write_credentials_file(credentials_file)

        credentials_file = _remove_unused_profiles(credentials_file, profile_group)
    except Exception:
        error_text = 'error while fetching role credentials'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    _write_credentials_file(credentials_file)
    result.set_success()
    return result


def _remove_unused_profiles(credentials_file, profile_group: ProfileGroup):
    used_profiles = profile_group.list_profile_names()
    for profile in credentials_file.sections():
        if profile not in used_profiles and \
                not profile.startswith('access-key') and \
                not profile.startswith('session-token'):
            credentials_file.remove_section(profile)
    return credentials_file


def write_profile_config(profile_group: ProfileGroup, region: str):
    result = Result()
    config_file = _load_config_file()

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f'add config for {profile.profile}')
            _add_profile_config(config_file, profile.profile, region)
            if profile.default:
                _add_profile_config(config_file, 'default', region)
        config_file = _remove_unused_configs(config_file, profile_group)
    except Exception:
        error_text = 'error writing config'
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    _write_config_file(config_file)
    result.set_success()
    return result


def _remove_unused_configs(config_file: configparser, profile_group: ProfileGroup):
    used_profiles = profile_group.list_profile_names()

    for config_name in config_file.sections():
        profile = config_name.replace('profile ', '')
        if profile not in used_profiles:
            config_file.remove_section(config_name)
    return config_file


def set_access_key(key_name: str, key_id: str, key_secret: str) -> None:
    credentials_file = _load_credentials_file()
    if not credentials_file.has_section(key_name):
        credentials_file.add_section(key_name)
    credentials_file.set(key_name, 'aws_access_key_id', key_id)
    credentials_file.set(key_name, 'aws_secret_access_key', key_secret)
    _write_credentials_file(credentials_file)


def get_access_key_list() -> list:
    credentials_file = _load_credentials_file()
    access_key_list = []
    for profile in credentials_file.sections():
        if profile.startswith('access-key'):
            access_key_list.append(profile)
    return access_key_list


def get_access_key_id(key_name: str) -> str:
    credentials_file = _load_credentials_file()
    return credentials_file.get(key_name, 'aws_access_key_id')


def _add_profile_credentials(credentials_file: configparser, profile: str, secrets: dict) -> None:
    if not credentials_file.has_section(profile):
        credentials_file.add_section(profile)
    credentials_file.set(profile, 'aws_access_key_id', str(secrets['AccessKeyId']))
    credentials_file.set(profile, 'aws_secret_access_key', str(secrets['SecretAccessKey']))
    credentials_file.set(profile, 'aws_session_token', str(secrets['SessionToken']))


def _add_profile_config(option_file: configparser, profile: str, region: str) -> None:
    config_name = f'profile {profile}'
    if not option_file.has_section(config_name):
        option_file.add_section(config_name)
    option_file.set(config_name, 'region', region)
    option_file.set(config_name, 'output', 'json')


def get_user_name(access_key) -> str:
    logger.info('fetch user name')
    client = _get_client(access_key, 'sts')
    identity = client.get_caller_identity()
    return _extract_user_from_identity(identity)


def _extract_user_from_identity(identity):
    return identity['Arn'].split('/')[-1]


def _get_session_token(access_key: str, mfa_token: str) -> dict:
    client = _get_client(access_key, 'sts')

    identity = client.get_caller_identity()
    duration = 43200  # 12 * 60 * 60
    user = _extract_user_from_identity(identity)
    mfa_arn = f'arn:aws:iam::{identity["Account"]}:mfa/{user}'

    response = client.get_session_token(
        DurationSeconds=duration,
        SerialNumber=mfa_arn,
        TokenCode=mfa_token
    )
    return response['Credentials']


def _assume_role(source_profile: str, user_name: str, account_id: str, role: str) -> dict:
    client = _get_client(source_profile, 'sts')
    response = client.assume_role(RoleArn=f'arn:aws:iam::{account_id}:role/{role}',
                                  RoleSessionName=user_name)
    return response['Credentials']

from configparser import ConfigParser
import logging
import os
from pathlib import Path
from typing import Optional

import boto3
import botocore
from app.aws import iam
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    ParamValidationError,
    ReadTimeoutError,
)
from app.core import files
from app.shell import shell

from app.core.profile_group import ProfileGroup
from app.core.result import Result
from app.util import util

logger = logging.getLogger("logsmith")


def _get_credentials_path() -> str:
    return os.path.join(str(Path.home()), ".aws", "credentials")


def _get_config_path() -> str:
    return os.path.join(str(Path.home()), ".aws", "config")


def _load_file(path: str) -> ConfigParser:
    config_parser = ConfigParser()
    config_parser.read(path)
    return config_parser


def _write_file(path: str, config_parser: ConfigParser) -> None:
    with open(path, "w") as file:
        config_parser.write(file)


def load_credentials_file() -> ConfigParser:
    return _load_file(_get_credentials_path())


def load_config_file() -> ConfigParser:
    return _load_file(_get_config_path())


def write_credentials_file(credentials: ConfigParser) -> None:
    _write_file(_get_credentials_path(), credentials)


def write_config_file(config: ConfigParser) -> None:
    _write_file(_get_config_path(), config)


def get_client(
    profile_name: str, service: str, timeout: Optional[int] = None, retries: Optional[int] = None
):
    session = boto3.Session(profile_name=profile_name)
    config_dict = {}
    if timeout is not None:
        config_dict["connect_timeout"] = timeout
    if retries is not None:
        config_dict["retries"] = {"total_max_attempts": retries}
    if timeout is not None or retries is not None:
        config = botocore.config.Config(**config_dict)
        return session.client(service, config=config)
    return session.client(service)


def cleanup():
    logger.info("cleanup credentials")
    result = Result()
    try:
        credentials_file = load_credentials_file()
        credentials_file = _cleanup_profiles(credentials_file)
        write_credentials_file(credentials_file)

        config_file = load_config_file()
        config_file = _cleanup_configs(config_file)
        write_config_file(config_file)
    except:
        error_text = "could not cleanup credential files"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result
    result.set_success()
    return result


def _cleanup_profiles(credentials_file: ConfigParser) -> ConfigParser:
    for profile in credentials_file.sections():
        if not profile.startswith("access-key") and not profile.startswith(
            "session-token"
        ):
            credentials_file.remove_section(profile)
    return credentials_file


def write_profile_config(profile_group: ProfileGroup, region: str) -> Result:
    result = Result()
    config_file = load_config_file()

    try:
        for profile in profile_group.get_profile_list(include_service_profile=True):
            logger.info(f"add region config for {profile.profile}")
            add_profile_config(config_file, profile.profile, region)
            if profile.default:
                add_profile_config(config_file, "default", region)
        write_config_file(config_file)
    except Exception:
        error_text = "error writing config"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def _cleanup_configs(config_file: ConfigParser) -> ConfigParser:
    for config_name in config_file.sections():
        if "profile" in config_name:
            config_file.remove_section(config_name)
    return config_file


def add_profile_credentials(credentials_file: ConfigParser, profile: str, secrets: dict) -> None:
    if not credentials_file.has_section(profile):
        credentials_file.add_section(profile)
    credentials_file.set(profile, "aws_access_key_id",
                         str(secrets["AccessKeyId"]))
    credentials_file.set(
        profile, "aws_secret_access_key", str(secrets["SecretAccessKey"])
    )
    credentials_file.set(profile, "aws_session_token",
                         str(secrets["SessionToken"]))


def add_profile_config(config_file: ConfigParser, profile: str, region: str) -> None:
    config_name = f"profile {profile}"
    if not config_file.has_section(config_name):
        config_file.add_section(config_name)
    config_file.set(config_name, "region", region)
    config_file.set(config_name, "output", "json")


def add_sso_profile(
    config_file: ConfigParser,
    sso_session_name: str,
    profile: str,
    account_id: str,
    role: str,
    region: str,
):
    config_name = f"profile {profile}"
    if not config_file.has_section(config_name):
        config_file.add_section(config_name)
    config_file.set(config_name, "sso_session", sso_session_name)
    config_file.set(config_name, "sso_account_id", account_id)
    config_file.set(config_name, "sso_role_name", role)
    config_file.set(config_name, "region", region)
    config_file.set(config_name, "output", "json")


def add_sso_chain_profile(
    config_file: ConfigParser,
    profile: str,
    role_arn: str,
    source_profile: str,
    region: str,
):
    config_name = f"profile {profile}"
    if not config_file.has_section(config_name):
        config_file.add_section(config_name)
    config_file.set(config_name, "role_arn", role_arn)
    config_file.set(config_name, "source_profile", source_profile)
    config_file.set(config_name, "region", region)
    config_file.set(config_name, "output", "json")

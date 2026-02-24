import logging

import boto3
from app.aws import iam, credentials
from app.core import files
from app.core.profile import Profile
from app.shell import shell

from app.core.profile_group import ProfileGroup
from app.core.result import Result
from app.util.util import use_as_default

logger = logging.getLogger("logsmith")

sso_shadow_prefix = "sso-shadow-"


def write_sso_profiles(profile_group: ProfileGroup, default_override: str | None, shadow_mode: bool) -> Result:
    result = Result()
    config_file = credentials.load_config_file()
    sso_session = profile_group.get_sso_session()

    sso_prefix = sso_shadow_prefix if shadow_mode else ""

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f"write {profile.profile}")

            if profile.source:
                source = profile_group.get_profile(profile.source)
                if source is None:
                    result.error(f"Source profile {profile.source} not found")
                    return result

                chain_args = {
                    "config_file": config_file,
                    "profile": f"{sso_prefix}{profile.profile}",
                    "role_arn": f"arn:aws:iam::{source.account}:role/{profile.role}",
                    "source_profile": f"{sso_prefix}{profile.source}",
                    "region": profile_group.region,
                }

                credentials.add_sso_chain_profile(**chain_args)
                if use_as_default(profile, default_override, shadow_mode):
                    logger.info(f"set {profile.profile} to default")
                    chain_args["profile"] = "default"
                    credentials.add_sso_chain_profile(**chain_args)
            else:

                profile_args = {
                    "config_file": config_file,
                    "sso_session_name": sso_session,
                    "profile": f"{sso_prefix}{profile.profile}",
                    "account_id": profile.account,
                    "role": profile.role,
                    "region": profile_group.region,
                }
                credentials.add_sso_profile(**profile_args)
                if use_as_default(profile, default_override, shadow_mode):
                    logger.info(f"set {profile.profile} to default")
                    profile_args["profile"] = "default"
                    credentials.add_sso_profile(**profile_args)

            credentials.write_config_file(config_file)
    except Exception:
        error_text = "error while fetching role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def write_sso_service_profile(profile_group: ProfileGroup, default_override: str | None, shadow_mode: bool | None) -> Result:
    result = Result()
    config_file = credentials.load_config_file()
    logger.info("add service profile via sso")

    sso_prefix = sso_shadow_prefix if shadow_mode else ""

    if profile_group.service_profile is None:
        result.error("service profile was not set")
        return result

    service_profile = profile_group.service_profile
    service_profile_name = service_profile.profile

    try:
        logger.info(f"fetch {service_profile_name}")
        role_arn = iam.fetch_role_arn(
            profile=f"{sso_prefix}{service_profile.source}", role_name=service_profile.role
        )

        args = {
            "config_file": config_file,
            "profile": f"{sso_prefix}{service_profile_name}",
            "role_arn": role_arn,
            "source_profile": f"{sso_prefix}{service_profile.source}",
            "region": profile_group.region,
        }

        credentials.add_sso_chain_profile(**args)
        if use_as_default(service_profile, default_override):
            logger.info(f"set {service_profile_name} to default")
            args["profile"] = "default"
            credentials.add_sso_chain_profile(**args)

        credentials.write_config_file(config_file)
    except Exception:
        error_text = "error while writing sso service profile"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def write_sso_as_key_credentials(profile_group: ProfileGroup, default_override: str | None) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info("fetch credentials via sso (as key)")

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f"fetch {profile.profile}")

            secrets = iam.get_frozen_credentials(f"{sso_shadow_prefix}{profile.profile}")

            credentials.add_profile_credentials(credentials_file, profile.profile, secrets)
            if use_as_default(profile, default_override):
                logger.info(f"set {profile.profile} to default")
                credentials.add_profile_credentials(credentials_file, "default", secrets)

            credentials.write_credentials_file(credentials_file)
    except Exception:
        error_text = "error while fetching role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def write_sso_as_key_credentials2(profile_group: ProfileGroup, default_override: str | None) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info("fetch credentials via sso (as key)")

    try:
        for profile in profile_group.get_profile_list():
            logger.info(f"fetch {profile.profile}")

            if not profile.source:
                credential_result = fetch_role_credentials_via_sso(account_id=profile.account,
                                                                   region=profile_group.region,
                                                                   role_name=profile.role)
                if not credential_result.was_success:
                    return credential_result
                secrets = credential_result.payload
            else:
                secrets = iam.assume_role(profile.source, profile.role, profile.account, profile.role)

            credentials.add_profile_credentials(credentials_file, profile.profile, secrets)
            if use_as_default(profile, default_override):
                logger.info(f"set {profile.profile} to default")
                credentials.add_profile_credentials(credentials_file, "default", secrets)

            credentials.write_credentials_file(credentials_file)
    except Exception:
        error_text = "error while fetching role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def write_sso_service_profile_as_key_credentials(profile_group: ProfileGroup, default_override: str | None) -> Result:
    result = Result()
    credentials_file = credentials.load_credentials_file()
    logger.info("add service profile via sso (as key)")

    service_profile = profile_group.service_profile

    try:
        logger.info(f"fetch {service_profile.profile}")

        secrets = iam.assume_role(service_profile.source,
                                  service_profile.role,
                                  service_profile.account,
                                  service_profile.role)

        credentials.add_profile_credentials(credentials_file,
                                            service_profile.profile,
                                            secrets)
        if use_as_default(service_profile, default_override):
            credentials.add_profile_credentials(credentials_file,
                                                "default",
                                                secrets)

        credentials.write_credentials_file(credentials_file)
    except Exception:
        error_text = "error while fetching service role credentials"
        result.error(error_text)
        logger.error(error_text, exc_info=True)
        return result

    result.set_success()
    return result


def write_profile_config(profile_group: ProfileGroup, region: str) -> Result:
    return credentials.write_profile_config(profile_group, region)


def set_sso_session(sso_name: str, sso_url: str, sso_region: str, sso_scopes: str) -> Result:
    result = Result()

    config_file = credentials.load_config_file()
    sso_session_section = f"sso-session {sso_name}"
    if not config_file.has_section(sso_session_section):
        config_file.add_section(sso_session_section)
    config_file.set(sso_session_section, "sso_start_url", sso_url)
    config_file.set(sso_session_section, "sso_region", sso_region)
    config_file.set(sso_session_section, "sso_registration_scopes", sso_scopes)
    credentials.write_config_file(config_file)

    result.set_success()
    return result


def get_sso_sessions_list() -> list:
    config_file = credentials.load_config_file()
    session_name_list = []
    for session in config_file.sections():
        if session.startswith("sso-session"):
            session_name = session.replace("sso-session ", "")
            session_name_list.append(session_name)
    return session_name_list


def sso_login(profile_group: ProfileGroup) -> Result:
    sso_session_name = profile_group.get_sso_session()

    # boto3 does not support login at the moment
    # unset AWS_PROFILE and AWS_DEFAULT_PROFILE because sso login fails is profile is present
    # or aborts when profiles are not found.
    return shell.run(
        command=f"unset AWS_PROFILE && unset AWS_DEFAULT_PROFILE && aws sso login --sso-session {sso_session_name}",
        timeout=600,
    )


def sso_logout() -> Result:
    return shell.run(
        command=f"unset AWS_PROFILE && unset AWS_DEFAULT_PROFILE && aws sso logout",
        timeout=600,
    )

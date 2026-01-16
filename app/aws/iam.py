import logging

import boto3
import botocore
from botocore import exceptions
from app.core.result import Result
from app.util import util

logger = logging.getLogger("logsmith")


def create_access_key(user_name, key_name) -> Result:
    result = Result()
    session = boto3.Session(profile_name=util.generate_session_name(key_name))
    client = session.client("iam")

    try:
        response = client.create_access_key(UserName=user_name)
    except client.exceptions.LimitExceededException:
        error_text = "key limit reached, creation failed"
        logger.warning(error_text)
        result.error(error_text)
        return result

    if "AccessKey" not in response:
        error_text = "unknown error with iam"
        logger.error(error_text)
        logger.error(response)
        result.error(error_text)
        return result

    result.add_payload(response["AccessKey"])
    result.set_success()
    return result


def delete_iam_access_key(user_name, key_name, key_id) -> Result:
    result = Result()
    session = boto3.Session(profile_name=util.generate_session_name(key_name))
    client = session.client("iam")

    try:
        client.delete_access_key(UserName=user_name, AccessKeyId=key_id)
    except Exception:
        error_text = "could not remove old key"
        logger.error(error_text, exc_info=True)
        result.error(error_text)
        return result

    result.set_success()
    return result


def get_role_name(profile: str):
    session = boto3.Session(profile_name=profile)
    client = session.client("sts")
    arn = client.get_caller_identity()["Arn"]
    return arn.split("/")[-2]


def fetch_role_arn(profile: str, role_name: str):
    session = boto3.Session(profile_name=profile)
    client = session.client("iam")
    role = client.get_role(RoleName=role_name)
    return role["Role"]["Arn"]


def list_assumable_roles(source_profile: str) -> Result:
    logger.info(f"list assumable roles with profile {source_profile}")
    result = Result()
    session = boto3.Session(profile_name=source_profile)
    client = session.client("iam")

    source_role_name = get_role_name(source_profile)
    source_role_arn = fetch_role_arn(source_profile, source_role_name)
    logger.info(f"source-arn: {source_role_arn}")

    assumable_roles = []

    role_list = client.list_roles()["Roles"]
    for role in role_list:
        response = client.get_role(RoleName=role["RoleName"])
        assume_role_policy = response["Role"]["AssumeRolePolicyDocument"]
        for statement in assume_role_policy["Statement"]:
            if "Principal" in statement and "AWS" in statement["Principal"]:
                if (
                    statement["Effect"] == "Allow"
                    and source_role_arn in statement["Principal"]["AWS"]
                ):
                    assumable_roles.append(role["RoleName"])

    if not assumable_roles:
        result.error("no assumable roles found")
    else:
        result.set_success()
        result.add_payload(assumable_roles)
    return result


def assume_role(profile: str, session_name: str, account_id: str, role: str) -> dict:
    session = boto3.Session(profile_name=profile)
    client = session.client("sts")
    response = client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{role}", RoleSessionName=session_name
    )
    return response["Credentials"]

def get_caller_identity(profile: str) -> bool:
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client("sts")
        client.get_caller_identity()
        return True
    except Exception:
        return False

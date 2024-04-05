import logging

import boto3

from app.core.result import Result
from app.util import util

logger = logging.getLogger('logsmith')


def create_access_key(user_name, key_name) -> Result:
    result = Result()
    session = boto3.Session(profile_name=util.generate_session_name(key_name))
    client = session.client('iam')

    try:
        response = client.create_access_key(
            UserName=user_name
        )
    except client.exceptions.LimitExceededException:
        error_text = 'key limit reached, creation failed'
        logger.warning(error_text)
        result.error(error_text)
        return result

    if 'AccessKey' not in response:
        error_text = 'unknown error with iam'
        logger.error(error_text)
        logger.error(response)
        result.error(error_text)
        return result

    result.add_payload(response['AccessKey'])
    result.set_success()
    return result


def delete_iam_access_key(user_name, key_name, key_id):
    result = Result()
    session = boto3.Session(profile_name=util.generate_session_name(key_name))
    client = session.client('iam')

    try:
        client.delete_access_key(
            UserName=user_name,
            AccessKeyId=key_id
        )
    except Exception:
        error_text = 'could not remove old key'
        logger.error(error_text, exc_info=True)
        result.error(error_text)
        return result

    result.set_success()
    return result

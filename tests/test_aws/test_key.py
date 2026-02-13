import os
from unittest.mock import call

from botocore.exceptions import (ClientError, EndpointConnectionError,
                                 NoCredentialsError, ParamValidationError,
                                 ReadTimeoutError)

from app.aws import credentials, key
from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts
from tests.test_data.test_results import (get_error_result, get_failed_result,
                                          get_success_result)

script_dir = os.path.dirname(os.path.realpath(__file__))

test_credentials_file_path = f"{script_dir}/../test_resources/credential_file"
test_credentials_file_path_without_keys = f"{script_dir}/../test_resources/credential_file_no_key"

parsed_response = {"Error": {"Code": "500", "Message": "Error"}}
client_error = ClientError(parsed_response, "test")
param_validation_error = ParamValidationError(report="test")
no_credentials_error = NoCredentialsError()
endpoint_error = EndpointConnectionError(endpoint_url="test")
timeout_error = ReadTimeoutError(endpoint_url="test")

test_secrets = {
    "AccessKeyId": "test-key-id",
    "SecretAccessKey": "test-access-key",
    "SessionToken": "test-session-token",
}

success_result = get_success_result()
fail_result = get_failed_result()
error_result = get_error_result()


def test_has_access_key(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path)
    result = key.has_access_key("access-key")

    assert result.was_success
    assert not result.was_error


def test_has_access_key__no_access_key(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path_without_keys)
    result = key.has_access_key("access-key")

    assert not result.was_success
    assert result.was_error
    assert "could not find access-key 'access-key' in .aws/credentials" == result.error_message


def test_check_session(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_get_client = mocker.patch.object(credentials, "get_client")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path)

    result = key.check_session("access-key")
    expected_calls = [
        call("session-token-access-key", "sts", timeout=2, retries=2),
        call().get_caller_identity(),
    ]
    assert expected_calls == mock_get_client.mock_calls

    assert result.was_success
    assert not result.was_error


def test_check_session__invalid_session(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_get_client = mocker.patch.object(credentials, "get_client")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path)
    mock_client = mocker.Mock()
    mock_client.get_caller_identity.side_effect = client_error
    mock_get_client.return_value = mock_client

    result = key.check_session("access-key")

    assert not result.was_success
    assert not result.was_error


def test_check_session__connection_timeout(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_get_client = mocker.patch.object(credentials, "get_client")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path)
    mock_client = mocker.Mock()
    mock_client.get_caller_identity.side_effect = timeout_error
    mock_get_client.return_value = mock_client

    result = key.check_session("access-key")

    assert not result.was_success
    assert result.was_error


def test_fetch_session_token(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_write = mocker.patch.object(credentials, "write_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_session = mocker.patch.object(key, "_get_session_token")

    mock_session.return_value = test_secrets
    mock_credentials_file = mocker.Mock()
    mock_load_credentials.return_value = mock_credentials_file

    result = key.fetch_session_token("some-access-key", "mfa-token")

    assert result.was_success
    assert not result.was_error
    mock_add_profile.assert_called_once_with(mock_credentials_file, "session-token-some-access-key", test_secrets)
    mock_write.assert_called_once_with(mock_credentials_file)


def test_fetch_session_token__param_validation_error(mocker):
    mock_session = mocker.patch.object(key, "_get_session_token")

    mock_session.return_value = {}
    mock_session.side_effect = client_error

    result = key.fetch_session_token("some-access-key", "mfa-token")

    assert not result.was_success
    assert result.was_error
    assert "could not fetch session token" == result.error_message


def test_fetch_session_token__client_error(mocker):
    mock_session = mocker.patch.object(key, "_get_session_token")

    mock_session.return_value = {}
    mock_session.side_effect = param_validation_error

    result = key.fetch_session_token("some-access-key", "mfa-token")

    assert not result.was_success
    assert result.was_error
    assert "invalid mfa token" == result.error_message


def test_fetch_session_token__no_credentials_error(mocker):
    mock_session = mocker.patch.object(key, "_get_session_token")

    mock_session.return_value = {}
    mock_session.side_effect = no_credentials_error

    result = key.fetch_session_token("some-access-key", "mfa-token")

    assert not result.was_success
    assert result.was_error
    assert "access_key credentials invalid" == result.error_message


def test_fetch_key_credentials(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume = mocker.patch.object(key.iam, "assume_role")

    mock_config_parser = mocker.Mock()
    mock_load_credentials.return_value = mock_config_parser
    mock_assume.return_value = test_secrets

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = key.fetch_key_credentials("test_user", profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_assume_calls = [
        call("session-token-default-access-key", "test_user", "123456789012", "developer"),
        call("session-token-default-access-key", "test_user", "012345678901", "readonly"),
    ]
    assert expected_mock_assume_calls == mock_assume.mock_calls

    expected_mock_add_profile_calls = [
        call(
            mock_config_parser,
            "developer",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "readonly",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "default",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_profile.mock_calls

    assert 2 == mock_write_credentials.call_count


def test_fetch_key_credentials_with_specific_access_key(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume = mocker.patch.object(key.iam, "assume_role")

    mock_config_parser = mocker.Mock()
    mock_load_credentials.return_value = mock_config_parser
    mock_assume.return_value = test_secrets

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group_with_specific_access_key(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = key.fetch_key_credentials("test_user", profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_assume_calls = [
        call("session-token-specific-access-key", "test_user", "123456789012", "developer"),
        call("session-token-specific-access-key", "test_user", "012345678901", "readonly"),
    ]
    assert expected_mock_assume_calls == mock_assume.mock_calls

    expected_mock_add_profile_calls = [
        call(
            mock_config_parser,
            "developer",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "readonly",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "default",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_profile.mock_calls

    assert 2 == mock_write_credentials.call_count


def test_fetch_key_credentials__no_default(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume = mocker.patch.object(key.iam, "assume_role")

    mock_config_parser = mocker.Mock()
    mock_load_credentials.return_value = mock_config_parser
    mock_assume.return_value = test_secrets

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group_no_default(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = key.fetch_key_credentials("test-user", profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_assume_calls = [
        call("session-token-default-access-key", "test-user", "123456789012", "developer"),
        call("session-token-default-access-key", "test-user", "012345678901", "readonly"),
    ]
    assert expected_mock_assume_calls == mock_assume.mock_calls

    expected_mock_add_profile_calls = [
        call(
            mock_config_parser,
            "developer",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "readonly",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_profile.mock_calls

    assert 2 == mock_write_credentials.call_count


def test_fetch_key_credentials__chain_assume(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume = mocker.patch.object(key.iam, "assume_role")

    mock_config_parser = mocker.Mock()
    mock_load_credentials.return_value = mock_config_parser
    mock_assume.return_value = test_secrets

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group_chain_assume(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = key.fetch_key_credentials("test-user", profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_assume_calls = [
        call("session-token-default-access-key", "test-user", "123456789012", "developer"),
        call("developer", "test-user", "012345678901", "service"),
    ]
    assert expected_mock_assume_calls == mock_assume.mock_calls

    expected_mock_add_profile_calls = [
        call(
            mock_config_parser,
            "developer",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
        call(
            mock_config_parser,
            "service",
            {
                "AccessKeyId": "test-key-id",
                "SecretAccessKey": "test-access-key",
                "SessionToken": "test-session-token",
            },
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_profile.mock_calls

    assert 2 == mock_write_credentials.call_count


def test_fetch_key_service_profile(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume = mocker.patch.object(key.iam, "assume_role")

    mock_config_parser = mocker.Mock()
    mock_load_credentials.return_value = mock_config_parser
    mock_assume.return_value = "secrets"

    profile_group = test_accounts.get_test_profile_group(include_service_role=True)
    result = key.fetch_key_service_profile(profile_group)
    assert result.was_success

    expected_assume_role_calls = [call("developer", "dummy", "123456789012", "dummy")]
    assert expected_assume_role_calls == mock_assume.mock_calls

    expected_add_profile_credentialscalls = [call(mock_config_parser, "service", "secrets")]
    assert expected_add_profile_credentialscalls == mock_add_profile.mock_calls

    expected_write_credentials_file_calls = [call(mock_config_parser)]
    assert expected_write_credentials_file_calls == mock_write_credentials.mock_calls


def test_set_access_key(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")

    mock_config_parser = mocker.Mock()
    mock_config_parser.has_section.return_value = False
    mock_load_credentials.return_value = mock_config_parser

    result = key.set_access_key("key-name", "key-id", "access-key")
    assert result.was_success
    assert not result.was_error

    mock_config_parser.has_section.assert_called_once_with("key-name")
    mock_config_parser.add_section.assert_called_once_with("key-name")
    assert [call("key-name", "aws_access_key_id", "key-id"),
            call("key-name", "aws_secret_access_key", "access-key")] == mock_config_parser.set.mock_calls
    mock_write_credentials.assert_called_once_with(mock_config_parser)


def test_get_access_key_list(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")

    mock_config_parser = mocker.Mock()
    mock_config_parser.sections.return_value = ["access-key-1", "session-token", "access-key-2", "other"]
    mock_load_credentials.return_value = mock_config_parser

    result = key.get_access_key_list()

    assert ["access-key-1", "access-key-2"] == result


def test_get_access_key_id(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")

    mock_config_parser = mocker.Mock()
    mock_config_parser.get.return_value = "some-key-id"
    mock_load_credentials.return_value = mock_config_parser

    result = key.get_access_key_id("access-key")

    assert "some-key-id" == result
    mock_config_parser.get.assert_called_once_with("access-key", "aws_access_key_id")


def test_check_session__no_session_found(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")

    mock_load_credentials.return_value = credentials._load_file(test_credentials_file_path_without_keys)

    result = key.check_session("access-key")

    assert not result.was_success
    assert not result.was_error

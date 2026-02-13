import os
from unittest.mock import call

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError, ParamValidationError, ReadTimeoutError

from app.aws import iam, sso
from app.aws.sso import credentials
from app.core import files
from app.core.profile_group import ProfileGroup
from app.shell import shell
from tests.test_data import test_accounts
from tests.test_data.test_results import get_error_result, get_failed_result, get_success_result

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


class Unauthorized(Exception):
    pass


def test_write_sso_credentials(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_sso_profile = mocker.patch.object(credentials, "add_sso_profile")
    mock_add_sso_chain = mocker.patch.object(credentials, "add_sso_chain_profile")
    mock_write_config = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_credentials(profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_add_profile_calls = [
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="developer",
            account_id="123456789012",
            role="developer",
            region="us-east-1",
        ),
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="readonly",
            account_id="012345678901",
            role="readonly",
            region="us-east-1",
        ),
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="default",
            account_id="012345678901",
            role="readonly",
            region="us-east-1",
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_sso_profile.mock_calls
    mock_add_sso_chain.assert_not_called()
    assert [call(mock_config_parser), call(mock_config_parser)] == mock_write_config.mock_calls


def test_write_sso_credentials__no_default(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_sso_profile = mocker.patch.object(credentials, "add_sso_profile")
    mock_add_sso_chain = mocker.patch.object(credentials, "add_sso_chain_profile")
    mock_write_config = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso__no_default(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_credentials(profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_add_profile_calls = [
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="developer",
            account_id="123456789012",
            role="developer",
            region="us-east-1",
        ),
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="readonly",
            account_id="012345678901",
            role="readonly",
            region="us-east-1",
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_sso_profile.mock_calls
    mock_add_sso_chain.assert_not_called()
    assert [call(mock_config_parser), call(mock_config_parser)] == mock_write_config.mock_calls


def test_write_sso_credentials__chain_assume(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_sso_profile = mocker.patch.object(credentials, "add_sso_profile")
    mock_add_sso_chain = mocker.patch.object(credentials, "add_sso_chain_profile")
    mock_write_config = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso__chain_assume(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_credentials(profile_group)
    assert result.was_success
    assert not result.was_error

    expected_mock_add_profile_calls = [
        call(
            config_file=mock_config_parser,
            sso_session_name="specific-sso-session",
            profile="developer",
            account_id="123456789012",
            role="developer",
            region="us-east-1",
        ),
    ]
    assert expected_mock_add_profile_calls == mock_add_sso_profile.mock_calls

    expected_mock_chain_profile_calls = [
        call(
            config_file=mock_config_parser,
            profile="pipeline",
            role_arn="arn:aws:iam::123456789012:role/pipeline",
            source_profile="developer",
            region="us-east-1",
        ),
    ]
    assert expected_mock_chain_profile_calls == mock_add_sso_chain.mock_calls
    assert [call(mock_config_parser), call(mock_config_parser)] == mock_write_config.mock_calls


def test_write_sso_credentials__source_profile_missing(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_sso_profile = mocker.patch.object(credentials, "add_sso_profile")
    mock_add_sso_chain = mocker.patch.object(credentials, "add_sso_chain_profile")
    mock_write_config = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        {
            "color": "#123456",
            "team": "team",
            "region": "us-east-1",
            "auth_mode": "sso",
            "profiles": [
                {"profile": "pipeline", "account": "123", "role": "pipeline", "source": "missing"}
            ],
        },
        "default-access-key",
        "sso-session",
        "default-sso-interval",
    )

    result = sso.write_sso_credentials(profile_group)
    assert not result.was_success
    assert result.was_error
    assert "Source profile missing not found" == result.error_message

    mock_add_sso_profile.assert_not_called()
    mock_add_sso_chain.assert_not_called()
    mock_write_config.assert_not_called()


def test_write_sso_service_profile(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_sso_chain = mocker.patch.object(credentials, "add_sso_chain_profile")
    mock_write_config = mocker.patch.object(credentials, "write_config_file")
    mock_fetch_role_arn = mocker.patch.object(iam, "fetch_role_arn")

    mock_load_config.return_value = "config-file"
    mock_fetch_role_arn.return_value = "some-arn"

    profile_group = test_accounts.get_test_profile_group(include_service_role=True)
    result = sso.write_sso_service_profile(profile_group)
    assert result.was_success

    mock_fetch_role_arn.assert_called_once_with(profile="developer", role_name="dummy")
    expected_add_profile_credentialscalls = [
        call(config_file="config-file", profile="service", role_arn="some-arn",
             source_profile="developer", region="us-east-1")
    ]
    assert expected_add_profile_credentialscalls == mock_add_sso_chain.mock_calls
    mock_write_config.assert_called_once_with("config-file")


def test_write_sso_service_profile_as_key_credentials(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume_role = mocker.patch.object(iam, "assume_role")

    mock_load_credentials.return_value = "credentials-file"
    mock_assume_role.return_value = test_secrets

    profile_group = test_accounts.get_test_profile_group_sso(include_service_role=True)
    result = sso.write_sso_service_profile_as_key_credentials(profile_group)

    assert result.was_success
    mock_assume_role.assert_called_once_with("developer", "dummy", "123456789012", "dummy")
    mock_add_profile.assert_called_once_with("credentials-file", "service", test_secrets)
    mock_write_credentials.assert_called_once_with("credentials-file")


def test_write_sso_service_profile_as_key_credentials__error(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_assume_role = mocker.patch.object(iam, "assume_role")

    mock_load_credentials.return_value = "credentials-file"
    mock_assume_role.side_effect = Exception("boom")

    profile_group = test_accounts.get_test_profile_group_sso(include_service_role=True)
    result = sso.write_sso_service_profile_as_key_credentials(profile_group)

    assert result.was_error
    assert "error while fetching service role credentials" == result.error_message
    mock_add_profile.assert_not_called()
    mock_write_credentials.assert_not_called()


def test_sso_login(mocker):
    mock_shell_run = mocker.patch.object(shell, "run")

    mock_shell_run.return_value = success_result
    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )

    result = sso.sso_login(profile_group)

    expected_command = (
        "unset AWS_PROFILE && unset AWS_DEFAULT_PROFILE && aws sso login --sso-session specific-sso-session"
    )
    mock_shell_run.assert_called_once_with(command=expected_command, timeout=600)
    assert result.was_success


def test_sso_logout(mocker):
    mock_shell_run = mocker.patch.object(shell, "run")

    result = sso.sso_logout()

    expected_command = "unset AWS_PROFILE && unset AWS_DEFAULT_PROFILE && aws sso logout"
    mock_shell_run.assert_called_once_with(command=expected_command, timeout=600)
    assert result.was_success


def test_write_sso_as_key_credentials(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_fetch_role = mocker.patch.object(sso, "fetch_role_credentials_via_sso")
    mock_assume_role = mocker.patch.object(iam, "assume_role")

    mock_credentials_file = mocker.Mock()
    mock_load_credentials.return_value = mock_credentials_file

    def _success_result():
        res = get_success_result()
        res.add_payload(test_secrets)
        return res

    mock_fetch_role.side_effect = [_success_result(), _success_result()]

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_as_key_credentials(profile_group)
    assert result.was_success

    expected_fetch_calls = [
        call(account_id="123456789012", region="us-east-1", role_name="developer"),
        call(account_id="012345678901", region="us-east-1", role_name="readonly"),
    ]
    assert expected_fetch_calls == mock_fetch_role.mock_calls
    mock_assume_role.assert_not_called()

    expected_add_calls = [
        call(mock_credentials_file, "developer", test_secrets),
        call(mock_credentials_file, "readonly", test_secrets),
        call(mock_credentials_file, "default", test_secrets),
    ]
    assert expected_add_calls == mock_add_profile.mock_calls
    assert 2 == mock_write_credentials.call_count


def test_write_sso_as_key_credentials__chain_assume(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_fetch_role = mocker.patch.object(sso, "fetch_role_credentials_via_sso")
    mock_assume_role = mocker.patch.object(iam, "assume_role")

    mock_credentials_file = mocker.Mock()
    mock_load_credentials.return_value = mock_credentials_file
    mock_assume_role.return_value = test_secrets

    fetch_result = get_success_result()
    fetch_result.add_payload(test_secrets)
    mock_fetch_role.return_value = fetch_result

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group_chain_assume(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_as_key_credentials(profile_group)
    assert result.was_success

    mock_fetch_role.assert_called_once_with(account_id="123456789012", region="us-east-1", role_name="developer")
    mock_assume_role.assert_called_once_with("developer", "service", "012345678901", "service")

    expected_add_calls = [
        call(mock_credentials_file, "developer", test_secrets),
        call(mock_credentials_file, "service", test_secrets),
    ]
    assert expected_add_calls == mock_add_profile.mock_calls
    assert 2 == mock_write_credentials.call_count


def test_write_sso_as_key_credentials__fetch_error(mocker):
    mock_load_credentials = mocker.patch.object(credentials, "load_credentials_file")
    mock_write_credentials = mocker.patch.object(credentials, "write_credentials_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_credentials")
    mock_fetch_role = mocker.patch.object(sso, "fetch_role_credentials_via_sso")

    mock_load_credentials.return_value = mocker.Mock()
    mock_fetch_role.return_value = error_result

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group__with_sso(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = sso.write_sso_as_key_credentials(profile_group)

    assert result.was_error
    assert error_result.error_message == result.error_message
    mock_add_profile.assert_not_called()
    mock_write_credentials.assert_not_called()


def test_fetch_role_credentials_via_sso(mocker):
    mock_boto_client = mocker.patch.object(boto3, "client")
    mock_get_tokens = mocker.patch.object(files, "get_local_sso_access_token")

    mock_get_tokens.return_value = ["token-a", "token-b"]
    mock_sso = mocker.Mock()
    mock_sso.exceptions = mocker.Mock(UnauthorizedException=Unauthorized)
    mock_sso.get_role_credentials.side_effect = [
        Unauthorized("unauthorized"),
        {
            "roleCredentials": {
                "accessKeyId": "key-id",
                "secretAccessKey": "secret",
                "sessionToken": "token",
            }
        },
    ]
    mock_boto_client.return_value = mock_sso

    result = sso.fetch_role_credentials_via_sso("123", "us-east-1", "role-name")

    expected_calls = [
        call(accessToken="token-a", accountId="123", roleName="role-name"),
        call(accessToken="token-b", accountId="123", roleName="role-name"),
    ]
    assert expected_calls == mock_sso.get_role_credentials.mock_calls
    assert result.was_success
    assert {"AccessKeyId": "key-id", "SecretAccessKey": "secret", "SessionToken": "token"} == result.payload


def test_fetch_role_credentials_via_sso__no_valid_token(mocker):
    mock_boto_client = mocker.patch.object(boto3, "client")
    mock_get_tokens = mocker.patch.object(files, "get_local_sso_access_token")

    mock_get_tokens.return_value = ["token-a"]
    mock_sso = mocker.Mock()
    mock_sso.exceptions = mocker.Mock(UnauthorizedException=Unauthorized)
    mock_sso.get_role_credentials.side_effect = Unauthorized("unauthorized")
    mock_boto_client.return_value = mock_sso

    result = sso.fetch_role_credentials_via_sso("123", "us-east-1", "role-name")

    assert result.was_error
    assert not result.was_success
    assert "no valid sso access-token found" == result.error_message


def test_get_sso_sessions_list(mocker):
    mock_load_config_file = mocker.patch.object(credentials, "load_config_file")

    mock_config_parser = mocker.Mock()
    mock_config_parser.sections.return_value = ["sso-session one", "profile developer", "sso-session two"]
    mock_load_config_file.return_value = mock_config_parser

    result = sso.get_sso_sessions_list()

    assert ["one", "two"] == result


def test_set_sso_session(mocker):
    mock_write_config_file = mocker.patch.object(credentials, "write_config_file")
    mock_load_config_file = mocker.patch.object(credentials, "load_config_file")

    mock_config_parser = mocker.Mock()
    mock_config_parser.has_section.return_value = False
    mock_load_config_file.return_value = mock_config_parser

    result = sso.set_sso_session("sso-session", "https://url", "us-east-1", "scope")
    assert result.was_success

    mock_config_parser.has_section.assert_called_once_with("sso-session sso-session")
    mock_config_parser.add_section.assert_called_once_with("sso-session sso-session")

    parser_calls = [call("sso-session sso-session", "sso_start_url", "https://url"),
                    call("sso-session sso-session", "sso_region", "us-east-1"),
                    call("sso-session sso-session", "sso_registration_scopes", "scope")]
    assert parser_calls == mock_config_parser.set.mock_calls
    mock_write_config_file.assert_called_once_with(mock_config_parser)

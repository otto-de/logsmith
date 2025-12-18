import os
from unittest import TestCase, mock
from unittest.mock import Mock, call

from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError, ParamValidationError, ReadTimeoutError

from app.aws import sso
from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts
from tests.test_data.test_results import get_error_result, get_failed_result, get_success_result

script_dir = os.path.dirname(os.path.realpath(__file__))


class TestSso(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_credentials_file_path = f"{script_dir}/../test_resources/credential_file"
        cls.test_credentials_file_path_without_keys = f"{script_dir}/../test_resources/credential_file_no_key"

        parsed_response = {"Error": {"Code": "500", "Message": "Error"}}
        cls.client_error = ClientError(parsed_response, "test")
        cls.param_validation_error = ParamValidationError(report="test")
        cls.no_credentials_error = NoCredentialsError()
        cls.endpoint_error = EndpointConnectionError(endpoint_url="test")
        cls.timeout_error = ReadTimeoutError(endpoint_url="test")

        cls.test_secrets = {
            "AccessKeyId": "test-key-id",
            "SecretAccessKey": "test-access-key",
            "SessionToken": "test-session-token",
        }

        cls.success_result = get_success_result()
        cls.fail_result = get_failed_result()
        cls.error_result = get_error_result()

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.add_sso_chain_profile")
    @mock.patch("app.aws.sso.credentials.add_sso_profile")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_write_sso_credentials(self, mock_load_config, mock_add_sso_profile, mock_add_sso_chain, mock_write_config):
        mock_config_parser = Mock()
        mock_load_config.return_value = mock_config_parser

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group__with_sso(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = sso.write_sso_credentials(profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

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
        self.assertEqual(expected_mock_add_profile_calls, mock_add_sso_profile.call_args_list)

        self.assertEqual(0, mock_add_sso_chain.call_count)
        self.assertEqual([call(mock_config_parser), call(mock_config_parser)], mock_write_config.call_args_list)

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.add_sso_chain_profile")
    @mock.patch("app.aws.sso.credentials.add_sso_profile")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_write_sso_credentials__no_default(
        self, mock_load_config, mock_add_sso_profile, mock_add_sso_chain, mock_write_config
    ):
        mock_config_parser = Mock()
        mock_load_config.return_value = mock_config_parser

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group__with_sso__no_default(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = sso.write_sso_credentials(profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

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
        self.assertEqual(expected_mock_add_profile_calls, mock_add_sso_profile.call_args_list)

        self.assertEqual(0, mock_add_sso_chain.call_count)
        self.assertEqual([call(mock_config_parser), call(mock_config_parser)], mock_write_config.call_args_list)

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.add_sso_chain_profile")
    @mock.patch("app.aws.sso.credentials.add_sso_profile")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_write_sso_credentials__chain_assume(
        self, mock_load_config, mock_add_sso_profile, mock_add_sso_chain, mock_write_config
    ):
        mock_config_parser = Mock()
        mock_load_config.return_value = mock_config_parser

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group__with_sso__chain_assume(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = sso.write_sso_credentials(profile_group)
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

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
        self.assertEqual(expected_mock_add_profile_calls, mock_add_sso_profile.call_args_list)

        expected_mock_chain_profile_calls = [
            call(
                config_file=mock_config_parser,
                profile="pipeline",
                role_arn="arn:aws:iam::123456789012:role/pipeline",
                source_profile="developer",
                region="us-east-1",
            ),
        ]
        self.assertEqual(expected_mock_chain_profile_calls, mock_add_sso_chain.call_args_list)

        self.assertEqual([call(mock_config_parser), call(mock_config_parser)], mock_write_config.call_args_list)

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.add_sso_chain_profile")
    @mock.patch("app.aws.sso.credentials.add_sso_profile")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_write_sso_credentials__source_profile_missing(
        self, mock_load_config, mock_add_sso_profile, mock_add_sso_chain, mock_write_config
    ):
        mock_config_parser = Mock()
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
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual("Source profile missing not found", result.error_message)

        self.assertEqual(0, mock_add_sso_profile.call_count)
        self.assertEqual(0, mock_add_sso_chain.call_count)
        self.assertEqual(0, mock_write_config.call_count)

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.add_sso_chain_profile")
    @mock.patch("app.aws.sso.iam.fetch_role_arn")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_write_sso_service_profile(self, mock_load_config, mock_fetch_role_arn, mock_add_sso_chain, mock_write_config_file):
        mock_load_config.return_value = "config-file"
        mock_fetch_role_arn.return_value = "some-arn"

        profile_group = test_accounts.get_test_profile_group(include_service_role=True)
        result = sso.write_sso_service_profile(profile_group)
        self.assertEqual(True, result.was_success)

        expected_assume_role_calls = [call(profile="developer", role_name="dummy")]
        self.assertEqual(expected_assume_role_calls, mock_fetch_role_arn.call_args_list)

        expected_add_profile_credentialscalls = [
            call(config_file="config-file", profile="service", role_arn="some-arn", source_profile="developer", region="us-east-1")
        ]
        self.assertEqual(expected_add_profile_credentialscalls, mock_add_sso_chain.call_args_list)

        expected_write_credentials_file_calls = [call("config-file")]
        self.assertEqual(expected_write_credentials_file_calls, mock_write_config_file.call_args_list)

    @mock.patch("app.aws.sso.shell.run")
    def test_sso_login(self, mock_shell_run):
        mock_shell_run.return_value = self.success_result
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
        self.assertEqual([call(command=expected_command, timeout=600)], mock_shell_run.call_args_list)
        self.assertEqual(True, result.was_success)

    @mock.patch("app.aws.sso.shell.run")
    def test_sso_logout(self, mock_shell_run):
        mock_shell_run.return_value = self.success_result

        result = sso.sso_logout()

        expected_command = "unset AWS_PROFILE && unset AWS_DEFAULT_PROFILE && aws sso logout"
        self.assertEqual([call(command=expected_command, timeout=600)], mock_shell_run.call_args_list)
        self.assertEqual(True, result.was_success)

    @mock.patch("app.aws.sso.credentials.write_credentials_file")
    @mock.patch("app.aws.sso.credentials.add_profile_credentials")
    @mock.patch("app.aws.sso.iam.assume_role")
    @mock.patch("app.aws.sso.fetch_role_credentials_via_sso")
    @mock.patch("app.aws.sso.credentials.load_credentials_file")
    def test_write_sso_as_key_credentials(
        self,
        mock_load_credentials,
        mock_fetch_role,
        mock_assume_role,
        mock_add_profile,
        mock_write_credentials,
    ):
        mock_credentials_file = Mock()
        mock_load_credentials.return_value = mock_credentials_file

        def _success_result():
            res = get_success_result()
            res.add_payload(self.test_secrets)
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
        self.assertEqual(True, result.was_success)

        expected_fetch_calls = [
            call(account_id="123456789012", region="us-east-1", role_name="developer"),
            call(account_id="012345678901", region="us-east-1", role_name="readonly"),
        ]
        self.assertEqual(expected_fetch_calls, mock_fetch_role.call_args_list)
        self.assertEqual(0, mock_assume_role.call_count)

        expected_add_calls = [
            call(mock_credentials_file, "developer", self.test_secrets),
            call(mock_credentials_file, "readonly", self.test_secrets),
            call(mock_credentials_file, "default", self.test_secrets),
        ]
        self.assertEqual(expected_add_calls, mock_add_profile.call_args_list)
        self.assertEqual(2, mock_write_credentials.call_count)

    @mock.patch("app.aws.sso.credentials.write_credentials_file")
    @mock.patch("app.aws.sso.credentials.add_profile_credentials")
    @mock.patch("app.aws.sso.iam.assume_role")
    @mock.patch("app.aws.sso.fetch_role_credentials_via_sso")
    @mock.patch("app.aws.sso.credentials.load_credentials_file")
    def test_write_sso_as_key_credentials__chain_assume(
        self,
        mock_load_credentials,
        mock_fetch_role,
        mock_assume_role,
        mock_add_profile,
        mock_write_credentials,
    ):
        mock_credentials_file = Mock()
        mock_load_credentials.return_value = mock_credentials_file
        mock_assume_role.return_value = self.test_secrets

        fetch_result = get_success_result()
        fetch_result.add_payload(self.test_secrets)
        mock_fetch_role.return_value = fetch_result

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group_chain_assume(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = sso.write_sso_as_key_credentials(profile_group)
        self.assertEqual(True, result.was_success)

        expected_fetch_calls = [
            call(account_id="123456789012", region="us-east-1", role_name="developer"),
        ]
        self.assertEqual(expected_fetch_calls, mock_fetch_role.call_args_list)
        expected_assume_calls = [
            call("developer", "service", "012345678901", "service"),
        ]
        self.assertEqual(expected_assume_calls, mock_assume_role.call_args_list)

        expected_add_calls = [
            call(mock_credentials_file, "developer", self.test_secrets),
            call(mock_credentials_file, "service", self.test_secrets),
        ]
        self.assertEqual(expected_add_calls, mock_add_profile.call_args_list)
        self.assertEqual(2, mock_write_credentials.call_count)

    @mock.patch("app.aws.sso.credentials.write_credentials_file")
    @mock.patch("app.aws.sso.credentials.add_profile_credentials")
    @mock.patch("app.aws.sso.iam._assume_role", create=True)
    @mock.patch("app.aws.sso.fetch_role_credentials_via_sso")
    @mock.patch("app.aws.sso.credentials.load_credentials_file")
    def test_write_sso_as_key_credentials__fetch_error(
        self,
        mock_load_credentials,
        mock_fetch_role,
        mock_assume_role,
        mock_add_profile,
        mock_write_credentials,
    ):
        mock_load_credentials.return_value = Mock()
        mock_fetch_role.return_value = self.error_result

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group__with_sso(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = sso.write_sso_as_key_credentials(profile_group)

        self.assertEqual(True, result.was_error)
        self.assertEqual(self.error_result.error_message, result.error_message)
        self.assertEqual(0, mock_add_profile.call_count)
        self.assertEqual(0, mock_write_credentials.call_count)

    @mock.patch("boto3.client")
    @mock.patch("app.aws.sso.files.get_local_sso_access_token")
    def test_fetch_role_credentials_via_sso(self, mock_get_tokens, mock_boto_client):
        class Unauthorized(Exception):
            pass

        mock_get_tokens.return_value = ["token-a", "token-b"]
        mock_sso = Mock()
        mock_sso.exceptions = Mock(UnauthorizedException=Unauthorized)
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
        self.assertEqual(expected_calls, mock_sso.get_role_credentials.call_args_list)
        self.assertEqual(True, result.was_success)
        self.assertEqual(
            {"AccessKeyId": "key-id", "SecretAccessKey": "secret", "SessionToken": "token"}, result.payload
        )

    @mock.patch("boto3.client")
    @mock.patch("app.aws.sso.files.get_local_sso_access_token")
    def test_fetch_role_credentials_via_sso__no_valid_token(self, mock_get_tokens, mock_boto_client):
        class Unauthorized(Exception):
            pass

        mock_get_tokens.return_value = ["token-a"]
        mock_sso = Mock()
        mock_sso.exceptions = Mock(UnauthorizedException=Unauthorized)
        mock_sso.get_role_credentials.side_effect = Unauthorized("unauthorized")
        mock_boto_client.return_value = mock_sso

        result = sso.fetch_role_credentials_via_sso("123", "us-east-1", "role-name")

        self.assertEqual(True, result.was_error)
        self.assertEqual("no valid sso access-token found", result.error_message)
        self.assertEqual(0, result.was_success)

    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_get_sso_sessions_list(self, mock_load_config_file):
        mock_config_parser = Mock()
        mock_config_parser.sections.return_value = ["sso-session one", "profile developer", "sso-session two"]
        mock_load_config_file.return_value = mock_config_parser

        result = sso.get_sso_sessions_list()

        self.assertEqual(["one", "two"], result)

    @mock.patch("app.aws.sso.credentials.write_config_file")
    @mock.patch("app.aws.sso.credentials.load_config_file")
    def test_set_sso_session(self, mock_load_config_file, mock_write_config_file):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False
        mock_load_config_file.return_value = mock_config_parser

        result = sso.set_sso_session("sso-session", "https://url", "us-east-1", "scope")
        self.assertEqual(True, result.was_success)

        self.assertEqual([call("sso-session sso-session")], mock_config_parser.has_section.call_args_list)
        self.assertEqual([call("sso-session sso-session")], mock_config_parser.add_section.call_args_list)
        self.assertEqual(
            [
                call("sso-session sso-session", "sso_start_url", "https://url"),
                call("sso-session sso-session", "sso_region", "us-east-1"),
                call("sso-session sso-session", "sso_registration_scopes", "scope"),
            ],
            mock_config_parser.set.call_args_list,
        )
        self.assertEqual([call(mock_config_parser)], mock_write_config_file.call_args_list)

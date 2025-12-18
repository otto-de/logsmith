import os
from unittest import TestCase, mock
from unittest.mock import Mock, call

from app.aws import credentials
from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts

script_dir = os.path.dirname(os.path.realpath(__file__))


class TestCredentials(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_credentials_file_path = f"{script_dir}/../test_resources/credential_file"
        cls.test_secrets = {
            "AccessKeyId": "test-key-id",
            "SecretAccessKey": "test-access-key",
            "SessionToken": "test-session-token",
        }

    @mock.patch("app.aws.credentials.Path.home", return_value="home")
    def test___get_credentials_path(self, _):
        self.assertEqual("home/.aws/credentials", credentials._get_credentials_path())

    @mock.patch("app.aws.credentials.Path.home", return_value="home")
    def test___get_config_path(self, _):
        self.assertEqual("home/.aws/config", credentials._get_config_path())

    def test___load_file(self):
        config_parser = credentials._load_file(self.test_credentials_file_path)
        self.assertEqual(
            "some_key_id",
            config_parser.get(section="access-key", option="aws_access_key_id"),
        )
        self.assertEqual(
            "some_access_key",
            config_parser.get(section="access-key", option="aws_secret_access_key"),
        )

    def test__cleanup_profiles(self):
        mock_config_parser = Mock()
        mock_config_parser.sections.return_value = [
            "developer",
            "unused-profile",
            "access-key",
            "session-token-access-key",
            "access-key-2",
            "session-token-access-key-2",
            "session-token-access-key-2",
        ]

        credentials._cleanup_profiles(mock_config_parser)

        expected = [call("developer"), call("unused-profile")]
        self.assertEqual(expected, mock_config_parser.remove_section.call_args_list)

    @mock.patch("app.aws.credentials.write_config_file")
    @mock.patch("app.aws.credentials.add_profile_config")
    @mock.patch("app.aws.credentials.load_config_file")
    def test_write_profile_config(self, mock_load_config, mock_add_profile, mock_write_config_file):
        mock_config_parser = Mock()
        mock_load_config.return_value = mock_config_parser

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = credentials.write_profile_config(profile_group, "us-east-12")

        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected = [
            call(mock_config_parser, "developer", "us-east-12"),
            call(mock_config_parser, "readonly", "us-east-12"),
            call(mock_config_parser, "default", "us-east-12"),
        ]
        self.assertEqual(expected, mock_add_profile.call_args_list)

        expected = [call(mock_config_parser)]
        self.assertEqual(expected, mock_write_config_file.call_args_list)

    @mock.patch("app.aws.credentials.write_config_file")
    @mock.patch("app.aws.credentials.add_profile_config")
    @mock.patch("app.aws.credentials.load_config_file")
    def test_write_profile_config__no_default_region(
        self, mock_load_config, mock_add_profile, mock_write_config_file
    ):
        mock_config_parser = Mock()
        mock_load_config.return_value = mock_config_parser

        profile_group = ProfileGroup(
            "test",
            test_accounts.get_test_group_no_default(),
            "default-access-key",
            "default-sso-session",
            "default-sso-interval",
        )
        result = credentials.write_profile_config(profile_group, "us-east-12")
        self.assertEqual(True, result.was_success)
        self.assertEqual(False, result.was_error)

        expected = [
            call(mock_config_parser, "developer", "us-east-12"),
            call(mock_config_parser, "readonly", "us-east-12"),
        ]
        self.assertEqual(expected, mock_add_profile.call_args_list)

        expected = [call(mock_config_parser)]
        self.assertEqual(expected, mock_write_config_file.call_args_list)

    def test__cleanup_configs(self):
        mock_config_parser = Mock()
        mock_config_parser.sections.return_value = [
            "profile developer",
            "profile unused-profile",
            "profile access-key",
            "profile session-token",
            "default",
            "s3",
        ]

        credentials._cleanup_configs(mock_config_parser)

        expected = [
            call("profile developer"),
            call("profile unused-profile"),
            call("profile access-key"),
            call("profile session-token"),
        ]
        self.assertEqual(expected, mock_config_parser.remove_section.call_args_list)

    def test__add_profile_credentials(self):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False

        credentials.add_profile_credentials(mock_config_parser, "test-profile", self.test_secrets)
        self.assertEqual([call("test-profile")], mock_config_parser.has_section.call_args_list)
        self.assertEqual([call("test-profile")], mock_config_parser.add_section.call_args_list)
        self.assertEqual(
            [
                call("test-profile", "aws_access_key_id", "test-key-id"),
                call("test-profile", "aws_secret_access_key", "test-access-key"),
                call("test-profile", "aws_session_token", "test-session-token"),
            ],
            mock_config_parser.set.call_args_list,
        )

    def test__add_profile_config(self):
        mock_config_parser = Mock()
        mock_config_parser.has_section.return_value = False

        credentials.add_profile_config(mock_config_parser, "test-profile", "us-east-12")
        self.assertEqual([call("profile test-profile")], mock_config_parser.has_section.call_args_list)
        self.assertEqual([call("profile test-profile")], mock_config_parser.add_section.call_args_list)
        self.assertEqual(
            [
                call("profile test-profile", "region", "us-east-12"),
                call("profile test-profile", "output", "json"),
            ],
            mock_config_parser.set.call_args_list,
        )

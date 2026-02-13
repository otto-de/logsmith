import os
from unittest.mock import call

from app.aws import credentials
from app.core.profile_group import ProfileGroup
from tests.test_data import test_accounts

script_dir = os.path.dirname(os.path.realpath(__file__))

test_credentials_file_path = f"{script_dir}/../test_resources/credential_file"
test_secrets = {
    "AccessKeyId": "test-key-id",
    "SecretAccessKey": "test-access-key",
    "SessionToken": "test-session-token",
}


def test___get_credentials_path(mocker):
    mocker.patch.object(credentials.Path, "home", return_value="home")
    assert "home/.aws/credentials" == credentials._get_credentials_path()


def test___get_config_path(mocker):
    mocker.patch.object(credentials.Path, "home", return_value="home")
    assert "home/.aws/config" == credentials._get_config_path()


def test___load_file():
    config_parser = credentials._load_file(test_credentials_file_path)
    assert "some_key_id" == config_parser.get(section="access-key", option="aws_access_key_id")
    assert "some_access_key" == config_parser.get(section="access-key", option="aws_secret_access_key")


def test__cleanup_profiles(mocker):
    mock_config_parser = mocker.Mock()
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
    assert expected == mock_config_parser.remove_section.mock_calls


def test_write_profile_config(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_config")
    mock_write_config_file = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = credentials.write_profile_config(profile_group, "us-east-12")

    assert result.was_success
    assert not result.was_error

    add_profile_calls = [
        call(mock_config_parser, "developer", "us-east-12"),
        call(mock_config_parser, "readonly", "us-east-12"),
        call(mock_config_parser, "default", "us-east-12"),
    ]
    assert add_profile_calls == mock_add_profile.mock_calls
    mock_write_config_file.assert_called_once_with(mock_config_parser)


def test_write_profile_config__no_default_region(mocker):
    mock_load_config = mocker.patch.object(credentials, "load_config_file")
    mock_add_profile = mocker.patch.object(credentials, "add_profile_config")
    mock_write_config_file = mocker.patch.object(credentials, "write_config_file")

    mock_config_parser = mocker.Mock()
    mock_load_config.return_value = mock_config_parser

    profile_group = ProfileGroup(
        "test",
        test_accounts.get_test_group_no_default(),
        "default-access-key",
        "default-sso-session",
        "default-sso-interval",
    )
    result = credentials.write_profile_config(profile_group, "us-east-12")
    assert result.was_success
    assert not result.was_error

    expected = [
        call(mock_config_parser, "developer", "us-east-12"),
        call(mock_config_parser, "readonly", "us-east-12"),
    ]
    assert expected == mock_add_profile.mock_calls
    mock_write_config_file.assert_called_once_with(mock_config_parser)


def test__cleanup_configs(mocker):
    mock_config_parser = mocker.Mock()
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
    assert expected == mock_config_parser.remove_section.mock_calls


def test__add_profile_credentials(mocker):
    mock_config_parser = mocker.Mock()
    mock_config_parser.has_section.return_value = False

    credentials.add_profile_credentials(
        mock_config_parser, "test-profile", test_secrets)
    mock_config_parser.has_section.assert_called_once_with("test-profile")
    mock_config_parser.add_section.assert_called_once_with("test-profile")
    expected_calls = [
        call("test-profile", "aws_access_key_id", "test-key-id"),
        call("test-profile", "aws_secret_access_key", "test-access-key"),
        call("test-profile", "aws_session_token", "test-session-token")]
    assert expected_calls == mock_config_parser.set.mock_calls


def test__add_profile_config(mocker):
    mock_config_parser = mocker.Mock()
    mock_config_parser.has_section.return_value = False

    credentials.add_profile_config(
        mock_config_parser, "test-profile", "us-east-12")
    mock_config_parser.has_section.assert_called_once_with("profile test-profile")
    mock_config_parser.add_section.assert_called_once_with("profile test-profile")
    expected_calls = [
        call("profile test-profile", "region", "us-east-12"),
        call("profile test-profile", "output", "json")]
    assert expected_calls == mock_config_parser.set.mock_calls


def test_set_as_default_profile(mocker):
    mock_load_credentials_file = mocker.patch.object(credentials, "load_credentials_file")
    mock_load_config_file = mocker.patch.object(credentials, "load_config_file")
    mock_replace_profile = mocker.patch.object(credentials, "replace_profile")
    mock_write_credentials_file = mocker.patch.object(credentials, "write_credentials_file")
    mock_write_config_file = mocker.patch.object(credentials, "write_config_file")

    mock_credentials = mocker.Mock()
    mock_config = mocker.Mock()
    mock_load_credentials_file.return_value = mock_credentials
    mock_load_config_file.return_value = mock_config

    result = credentials.set_as_default_profile("developer")

    assert result.was_success
    assert not result.was_error
    assert [call(mock_credentials, "developer", "default"),
            call(mock_config, "profile developer", "profile default")] == mock_replace_profile.mock_calls
    assert [call(mock_credentials)] == mock_write_credentials_file.mock_calls
    assert [call(mock_config)] == mock_write_config_file.mock_calls


def test_set_as_default_profile__error(mocker):
    mock_load_credentials_file = mocker.patch.object(credentials, "load_credentials_file")
    mock_load_config_file = mocker.patch.object(credentials, "load_config_file")
    mock_replace_profile = mocker.patch.object(credentials, "replace_profile")
    mock_write_credentials_file = mocker.patch.object(credentials, "write_credentials_file")
    mock_write_config_file = mocker.patch.object(credentials, "write_config_file")

    mock_load_credentials_file.return_value = mocker.Mock()
    mock_load_config_file.return_value = mocker.Mock()
    mock_replace_profile.side_effect = Exception("boom")

    result = credentials.set_as_default_profile("developer")

    assert not result.was_success
    assert result.was_error
    mock_write_credentials_file.assert_not_called()
    mock_write_config_file.assert_not_called()


def test_replace_profile():
    config = credentials.ConfigParser()
    config.add_section("source")
    config.set("source", "region", "us-east-1")
    config.set("source", "output", "json")
    config.add_section("target")
    config.set("target", "region", "eu-west-1")

    credentials.replace_profile(config, "source", "target")

    assert config.has_section("target")
    assert "us-east-1" == config.get("target", "region")
    assert "json" == config.get("target", "output")


def test_replace_profile__missing_source():
    config = credentials.ConfigParser()
    config.add_section("target")
    config.set("target", "region", "eu-west-1")

    credentials.replace_profile(config, "missing", "target")

    assert config.has_section("target")
    assert "eu-west-1" == config.get("target", "region")


def test_replace_profile__same_name():
    config = credentials.ConfigParser()
    config.add_section("same")
    config.set("same", "region", "us-east-1")

    credentials.replace_profile(config, "same", "same")

    assert config.has_section("same")
    assert "us-east-1" == config.get("same", "region")

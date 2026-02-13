from dataclasses import dataclass
from unittest.mock import Mock, call

import pytest

from app.core import core as core_module
from app.core import files
from app.core.core import Core
from app.core.result import Result
from tests.test_data.test_accounts import get_default_test_accounts, get_test_profile_group
from tests.test_data.test_config import get_test_config
from tests.test_data.test_results import (
    get_error_result,
    get_failed_result,
    get_success_result,
)
from tests.test_data.test_service_roles import get_test_service_roles
from tests.test_data.test_toggles import get_test_toggles


@dataclass
class Ctx:
    core: Core
    success_result: object
    fail_result: object
    error_result: object


@pytest.fixture
def ctx(mocker) -> Ctx:
    mocker.patch.object(files, "load_accounts", return_value=get_default_test_accounts())
    mocker.patch.object(files, "load_config", return_value=get_test_config())
    mocker.patch.object(files, "load_service_roles", return_value=get_test_service_roles())
    mocker.patch.object(files, "load_toggles", return_value=get_test_toggles())

    core = Core()
    return Ctx(
        core=core,
        success_result=get_success_result(),
        fail_result=get_failed_result(),
        error_result=get_error_result(),
    )


def test_logout(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_logout.return_value = ctx.success_result

    result = ctx.core.logout()

    mock_credentials.cleanup.assert_called_once_with()
    mock_sso.sso_logout.assert_called_once_with()
    assert result.was_success
    assert not result.was_error


def test_logout__error_on_cleanup(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_credentials.cleanup.return_value = ctx.error_result

    result = ctx.core.logout()

    mock_credentials.cleanup.assert_called_once_with()
    mock_sso.assert_not_called()
    assert result == ctx.error_result


def test_logout__error_on_sso_logout(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_logout.return_value = ctx.error_result

    result = ctx.core.logout()

    mock_credentials.cleanup.assert_called_once_with()
    mock_sso.sso_logout.assert_called_once_with()
    assert result == ctx.error_result


def test_rotate_access_key__no_access_key(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mocker.patch.object(core_module, "iam")
    mock_logout = mocker.patch.object(Core, "logout")
    mocker.patch.object(Core, "_ensure_session")
    mock_key.check_access_key.return_value = ctx.fail_result

    result = ctx.core.rotate_access_key(access_key="rotate-this-key", mfa_token=None)

    assert result == ctx.fail_result
    assert mock_logout.call_count == 1
    assert [call.check_access_key(access_key="rotate-this-key")] == mock_key.mock_calls


def test_rotate_access_key__fetch_session_failure(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mocker.patch.object(core_module, "iam")
    mock_logout = mocker.patch.object(Core, "logout")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.fail_result

    result = ctx.core.rotate_access_key(access_key="rotate-this-key", mfa_token=None)

    assert result == ctx.fail_result
    assert mock_logout.call_count == 1
    mock_ensure_session.assert_called_once_with(access_key="rotate-this-key", mfa_token=None)
    assert [call.check_access_key(access_key="rotate-this-key")] == mock_key.mock_calls


def test_rotate_access_key__create_access_key_failure(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_iam = mocker.patch.object(core_module, "iam")
    mock_logout = mocker.patch.object(Core, "logout")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_iam.create_access_key.return_value = ctx.fail_result

    result = ctx.core.rotate_access_key(access_key="rotate-this-key", mfa_token=None)

    assert result == ctx.fail_result
    assert mock_logout.call_count == 1
    mock_ensure_session.assert_called_once_with(access_key="rotate-this-key", mfa_token=None)
    assert [call.check_access_key(access_key="rotate-this-key"),
            call.get_user_name("rotate-this-key")] == mock_key.mock_calls


def test_rotate_access_key__delete_iam_access_key_failure(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_iam = mocker.patch.object(core_module, "iam")
    mock_logout = mocker.patch.object(Core, "logout")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "some-user"
    mock_iam.create_access_key.return_value = ctx.success_result
    mock_key.get_access_key_id.return_value = "some-old-access-key"
    mock_iam.delete_iam_access_key.return_value = ctx.fail_result

    result = ctx.core.rotate_access_key(access_key="rotate-this-key", mfa_token=None)

    assert result == ctx.fail_result
    assert mock_logout.call_count == 1
    mock_ensure_session.assert_called_once_with(access_key="rotate-this-key", mfa_token=None)

    mock_iam_calls = [call.create_access_key("some-user", "rotate-this-key"),
                      call.delete_iam_access_key("some-user", "rotate-this-key", "some-old-access-key")]

    assert mock_iam_calls == mock_iam.mock_calls

    mock_key_calls = [call.check_access_key(access_key="rotate-this-key"),
                      call.get_user_name("rotate-this-key"),
                      call.get_access_key_id("rotate-this-key")]

    assert mock_key_calls == mock_key.mock_calls


def test_rotate_access_key__successful_rotate(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_iam = mocker.patch.object(core_module, "iam")
    mock_logout = mocker.patch.object(Core, "logout")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "some-user"

    create_access_key_result = Result()
    create_access_key_result.set_success()
    create_access_key_result.add_payload({"AccessKeyId": "new-key", "SecretAccessKey": "1234"})
    mock_iam.create_access_key.return_value = create_access_key_result

    mock_key.get_access_key_id.return_value = "some-old-access-key"
    mock_iam.delete_iam_access_key.return_value = ctx.success_result

    result = ctx.core.rotate_access_key(access_key="rotate-this-key", mfa_token="123456")

    assert result.was_success
    assert not result.was_error
    assert mock_logout.call_count == 2
    mock_ensure_session.assert_called_once_with(access_key="rotate-this-key", mfa_token="123456")

    mock_iam_calls = [call.create_access_key("some-user", "rotate-this-key"),
                      call.delete_iam_access_key("some-user", "rotate-this-key", "some-old-access-key")]
    assert mock_iam_calls == mock_iam.mock_calls

    mock_key_calls = [call.check_access_key(access_key="rotate-this-key"),
                      call.get_user_name("rotate-this-key"),
                      call.get_access_key_id("rotate-this-key"),
                      call.set_access_key(key_name="rotate-this-key", key_id="new-key", key_secret="1234")]
    assert mock_key_calls == mock_key.mock_calls


def test_get_region__not_logged_in(ctx):
    assert ctx.core.get_region() is None


def test_get_region__active_profile_group(ctx):
    ctx.core.active_profile_group = get_test_profile_group()
    assert ctx.core.get_region() == "us-east-1"


def test_get_region__region_overwrite(ctx):
    ctx.core.active_profile_group = get_test_profile_group()
    ctx.core.region_override = "eu-north-1"
    assert ctx.core.get_region() == "eu-north-1"


def test_get_region__gcp(ctx):
    ctx.core.active_profile_group = ctx.core.config.get_group("gcp-project-dev")
    assert ctx.core.get_region() == "europe-west1"


def test__ensure_session__valid_session_and_token(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.success_result
    mock_key.fetch_session_token.return_value = ctx.success_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token="123456")

    assert result.was_success
    assert not result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_not_called()


def test__ensure_session__valid_session_and_no_token(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.success_result
    mock_key.fetch_session_token.return_value = ctx.success_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token=None)

    assert result.was_success
    assert not result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_not_called()


def test__ensure_session__invalid_session_and_token(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.fail_result
    mock_key.fetch_session_token.return_value = ctx.success_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token="123456")

    assert result.was_success
    assert not result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_called_once_with(access_key="access-key", mfa_token="123456")


def test__ensure_session__invalid_session_and_no_token(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.fail_result
    mock_key.fetch_session_token.return_value = ctx.success_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token=None)

    assert not result.was_success
    assert not result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_not_called()


def test__ensure_session__invalid_session_and_token_but_fetch_session_error(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.fail_result
    mock_key.fetch_session_token.return_value = ctx.error_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token="123456")

    assert not result.was_success
    assert result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_called_once_with(access_key="access-key", mfa_token="123456")


def test__ensure_session__error_session_check(ctx, mocker):
    mock_key = mocker.patch.object(core_module, "key")
    mock_key.check_session.return_value = ctx.error_result
    mock_key.fetch_session_token.return_value = ctx.error_result

    result = ctx.core._ensure_session(access_key="access-key", mfa_token="123456")

    assert not result.was_success
    assert result.was_error
    mock_key.check_session.assert_called_once_with(access_key="access-key")
    mock_key.fetch_session_token.assert_called_once_with(access_key="access-key", mfa_token="123456")


def test__set_region__not_logged_in(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")

    result = ctx.core.set_region("eu-north-1")

    assert mock_credentials.call_count == 0
    assert ctx.core.region_override == "eu-north-1"
    assert result.was_success
    assert not result.was_error


def test__set_region__successful(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_credentials.write_profile_config.return_value = ctx.success_result
    profile_group = get_test_profile_group()
    ctx.core.active_profile_group = profile_group

    result = ctx.core.set_region("eu-north-1")

    assert [call.write_profile_config(profile_group, "eu-north-1")] == mock_credentials.mock_calls
    assert ctx.core.region_override == "eu-north-1"
    assert result.was_success
    assert not result.was_error


def test__set_region__successful_no_region_overwrite(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_credentials.write_profile_config.return_value = ctx.success_result
    profile_group = get_test_profile_group()
    ctx.core.active_profile_group = profile_group

    result = ctx.core.set_region(None)

    assert [call.write_profile_config(profile_group, profile_group.region)] == mock_credentials.mock_calls
    assert ctx.core.region_override is None
    assert result.was_success
    assert not result.was_error


def test__set_region__write_profile_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_credentials.write_profile_config.return_value = ctx.fail_result
    profile_group = get_test_profile_group()
    ctx.core.active_profile_group = profile_group

    result = ctx.core.set_region("eu-north-1")

    assert result == ctx.fail_result
    assert [call.write_profile_config(profile_group, "eu-north-1")] == mock_credentials.mock_calls
    assert ctx.core.region_override == "eu-north-1"


def test__set_service_role(ctx):
    ctx.core.active_profile_group = get_test_profile_group()
    save_selected_service_role_mock = Mock()
    ctx.core.config.save_selected_service_role = save_selected_service_role_mock

    result = ctx.core.set_service_role(profile_name="developer", role_name="some-role")

    save_selected_service_role_mock.assert_called_once_with(group_name="test", profile_name="developer", role_name="some-role")
    assert ctx.core.active_profile_group.service_profile.to_dict() == {
        "profile": "service",
        "account": "123456789012",
        "role": "some-role",
        "source": "developer",
    }
    assert result.was_success
    assert not result.was_error


def test__set_service_role__non_existent_profile(ctx):
    ctx.core.active_profile_group = get_test_profile_group()
    save_selected_service_role_mock = Mock()
    ctx.core.config.save_selected_service_role = save_selected_service_role_mock

    result = ctx.core.set_service_role(profile_name="developer", role_name="some-role")

    save_selected_service_role_mock.assert_called_once_with(group_name="test", profile_name="developer", role_name="some-role")
    assert ctx.core.active_profile_group.service_profile.to_dict() == {
        "profile": "service",
        "account": "123456789012",
        "role": "some-role",
        "source": "developer",
    }
    assert result.was_success
    assert not result.was_error


def test__run_script__no_active_profile_group(ctx):
    result = ctx.core.run_script(None)
    assert result.was_success


def test__run_script__script_successful(ctx, mocker):
    mock_files_exists = mocker.patch.object(core_module.files, "file_exists", return_value=True)
    mock_shell_run = mocker.patch.object(core_module.shell, "run")
    mock_shell_run.return_value = ctx.success_result

    result = ctx.core.run_script(get_test_profile_group())

    assert result.was_success
    mock_files_exists.assert_called_once_with("./some-script.sh")
    mock_shell_run.assert_called_once_with(command="./some-script.sh", timeout=60)


def test__run_script__script_not_found(ctx, mocker):
    mock_files_exists = mocker.patch.object(core_module.files, "file_exists", return_value=False)
    mock_shell_run = mocker.patch.object(core_module.shell, "run")

    result = ctx.core.run_script(get_test_profile_group())

    assert result.was_error
    mock_files_exists.assert_called_once_with("./some-script.sh")
    mock_shell_run.assert_not_called()


def test__run_script__script_failed(ctx, mocker):
    mock_files_exists = mocker.patch.object(core_module.files, "file_exists", return_value=True)
    mock_shell_run = mocker.patch.object(core_module.shell, "run")
    mock_shell_run.return_value = ctx.error_result

    result = ctx.core.run_script(get_test_profile_group())

    assert result.was_error
    mock_files_exists.assert_called_once_with("./some-script.sh")
    mock_shell_run.assert_called_once_with(command="./some-script.sh", timeout=60)


def test__check_name(ctx):
    result = ctx.core.check_name("sso", "sso-test")

    assert not result.was_error
    assert result.was_success


def test__check_name__does_not_start_right(ctx):
    result = ctx.core.check_name("sso", "test")

    assert result.was_error
    assert result.error_message == "'test' must start with sso"
    assert not result.was_success


def test__check_name__contain_spaces(ctx):
    result = ctx.core.check_name("sso", "sso test")

    assert result.was_error
    assert result.error_message == "'sso test' must not contain spaces"
    assert not result.was_success

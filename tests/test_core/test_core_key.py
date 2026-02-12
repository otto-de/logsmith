from dataclasses import dataclass
from unittest.mock import call

import pytest

from app.core import files
from app.core import core as core_module
from app.core.core import Core
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
    key_profile_group: object
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
        key_profile_group=core.config.get_group("development"),
        success_result=get_success_result(),
        fail_result=get_failed_result(),
        error_result=get_error_result(),
    )


def test_login_key__cleanup_error(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.error_result

    result = ctx.core.login_with_key(ctx.key_profile_group, None)
    assert ctx.error_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    mock_ensure_session.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()
    mock_key.assert_not_called()
    mock_set_region.assert_not_called()


def test_login_key__no_access_key(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.error_result

    result = ctx.core.login_with_key(ctx.key_profile_group, None)
    assert ctx.error_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    mock_key.assert_has_calls([call.check_access_key(access_key="some-access-key")])
    mock_set_region.assert_not_called()
    mock_ensure_session.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_key__fetch_session_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.fail_result

    result = ctx.core.login_with_key(get_test_profile_group(), None)
    assert ctx.fail_result == result

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token=None)])
    mock_credentials.assert_has_calls([call.cleanup()])
    mock_key.assert_has_calls([call.check_access_key(access_key="some-access-key")])
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_key__fetch_key_credentials_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.fail_result

    profile_group = get_test_profile_group()
    result = ctx.core.login_with_key(profile_group, None)
    assert ctx.fail_result == result

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token=None)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_key__set_region_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.fail_result

    profile_group = get_test_profile_group()
    result = ctx.core.login_with_key(profile_group, None)
    assert ctx.fail_result == result

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token=None)])
    mock_set_region.assert_has_calls([call(None)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_key__run_script_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.fail_result

    profile_group = get_test_profile_group()

    result = ctx.core.login_with_key(profile_group, None)
    assert ctx.fail_result == result

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token=None)])
    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(profile_group)])
    mock_run_script.assert_has_calls([call(profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)


def test_login_key__successful_login_with_run_script_disabled(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    ctx.core.toggles.run_script = False

    profile_group = get_test_profile_group()
    result = ctx.core.login_with_key(profile_group, "123456")
    assert result.was_success
    assert not result.was_error

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token="123456")])
    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(profile_group)])
    assert 0 == mock_run_script.call_count
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)


def test_login_key__successful_login(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    profile_group = get_test_profile_group()
    result = ctx.core.login_with_key(profile_group, "123456")
    assert result.was_success
    assert not result.was_error

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token="123456")])
    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(profile_group)])
    mock_run_script.assert_has_calls([call(profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)


def test_login_key__successful_login_with_region_overwrite(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    ctx.core.region_override = "eu-north-1"

    profile_group = get_test_profile_group()
    ctx.core.login_with_key(profile_group, None)

    mock_set_region.assert_has_calls([call("eu-north-1")])


def test_login_key__fetch_service_role_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_key.fetch_key_service_profile.return_value = ctx.fail_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    profile_group = get_test_profile_group(include_service_role=True)
    result = ctx.core.login_with_key(profile_group, "123456")
    assert result == ctx.fail_result

    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
        call.fetch_key_service_profile(profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)

    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_key__successfull_login_with_service_role(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_key = mocker.patch.object(core_module, "key")
    mock_ensure_session = mocker.patch.object(Core, "_ensure_session")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_key.check_access_key.return_value = ctx.success_result
    mock_ensure_session.return_value = ctx.success_result
    mock_key.get_user_name.return_value = "user"
    mock_key.fetch_key_credentials.return_value = ctx.success_result
    mock_key.fetch_key_service_profile.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    profile_group = get_test_profile_group(include_service_role=True)
    result = ctx.core.login_with_key(profile_group, "123456")
    assert result.was_success
    assert not result.was_error

    mock_ensure_session.assert_has_calls([call(access_key="some-access-key", mfa_token="123456")])
    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(profile_group)])
    mock_run_script.assert_has_calls([call(profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_key_calls = [
        call.check_access_key(access_key="some-access-key"),
        call.get_user_name(access_key="some-access-key"),
        call.fetch_key_credentials("user", profile_group),
        call.fetch_key_service_profile(profile_group),
    ]
    mock_key.assert_has_calls(expected_key_calls)

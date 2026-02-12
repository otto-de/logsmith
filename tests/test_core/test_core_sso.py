from dataclasses import dataclass
from unittest.mock import call

import pytest

from app.core import files
from app.core import core as core_module
from app.core.core import Core
from tests.test_data.test_accounts import (
    get_test_accounts__mixed_auth_modes,
    get_test_profile_group_sso,
)
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
    sso_profile_group: object
    success_result: object
    fail_result: object
    error_result: object


@pytest.fixture
def ctx(mocker) -> Ctx:
    mocker.patch.object(files, "load_accounts", return_value=get_test_accounts__mixed_auth_modes())
    mocker.patch.object(files, "load_config", return_value=get_test_config())
    mocker.patch.object(files, "load_service_roles", return_value=get_test_service_roles())
    mocker.patch.object(files, "load_toggles", return_value=get_test_toggles())

    core = Core()
    return Ctx(
        core=core,
        sso_profile_group=core.config.get_group("live"),
        success_result=get_success_result(),
        fail_result=get_failed_result(),
        error_result=get_error_result(),
    )


def test_login_sso__cleanup_error(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.error_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert ctx.error_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    mock_sso.assert_not_called()
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__sso_login_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.fail_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert ctx.fail_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    mock_sso.assert_has_calls([call.sso_login(ctx.sso_profile_group)])
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__write_sso_credentials_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.fail_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert ctx.fail_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(ctx.sso_profile_group),
        call.write_sso_credentials(ctx.sso_profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__write_sso_as_key_credentials_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_as_key_credentials.return_value = ctx.fail_result

    profile_group = get_test_profile_group_sso()
    profile_group.write_mode = "key"

    result = ctx.core.login_with_sso(profile_group)
    assert ctx.fail_result == result

    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(profile_group),
        call.write_sso_as_key_credentials(profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__set_region_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.fail_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert ctx.fail_result == result

    mock_set_region.assert_has_calls([call(None)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(ctx.sso_profile_group),
        call.write_sso_credentials(ctx.sso_profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__run_script_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.fail_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert ctx.fail_result == result

    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(ctx.sso_profile_group)])
    mock_run_script.assert_has_calls([call(ctx.sso_profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(ctx.sso_profile_group),
        call.write_sso_credentials(ctx.sso_profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)


def test_login_sso__successful_login_with_run_script_disabled(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result

    ctx.core.toggles.run_script = False

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert result.was_success
    assert not result.was_error

    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(ctx.sso_profile_group)])
    assert 0 == mock_run_script.call_count
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(ctx.sso_profile_group),
        call.write_sso_credentials(ctx.sso_profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)


def test_login_sso__successful_login(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    result = ctx.core.login_with_sso(ctx.sso_profile_group)
    assert result.was_success
    assert not result.was_error

    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(ctx.sso_profile_group)])
    mock_run_script.assert_has_calls([call(ctx.sso_profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(ctx.sso_profile_group),
        call.write_sso_credentials(ctx.sso_profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)


def test_login_sso__successful_login_with_region_overwrite(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    ctx.core.region_override = "eu-north-1"

    ctx.core.login_with_sso(ctx.sso_profile_group)

    mock_set_region.assert_has_calls([call("eu-north-1")])


def test_login_sso__fetch_service_role_failure(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_sso.write_sso_service_profile.return_value = ctx.fail_result

    profile_group = get_test_profile_group_sso(include_service_role=True)
    result = ctx.core.login_with_sso(profile_group)
    assert ctx.fail_result == result

    expected_sso_calls = [
        call.sso_login(profile_group),
        call.write_sso_credentials(profile_group),
        call.write_sso_service_profile(profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)
    mock_credentials.assert_has_calls([call.cleanup()])
    mock_set_region.assert_not_called()
    mock_handle_support_files.assert_not_called()
    mock_run_script.assert_not_called()


def test_login_sso__successfull_login_with_service_role(ctx, mocker):
    mock_credentials = mocker.patch.object(core_module, "credentials")
    mock_sso = mocker.patch.object(core_module, "sso")
    mock_set_region = mocker.patch.object(Core, "set_region")
    mock_handle_support_files = mocker.patch.object(Core, "_handle_support_files")
    mock_run_script = mocker.patch.object(Core, "run_script")

    mock_credentials.cleanup.return_value = ctx.success_result
    mock_sso.sso_login.return_value = ctx.success_result
    mock_sso.write_sso_credentials.return_value = ctx.success_result
    mock_sso.write_sso_service_profile.return_value = ctx.success_result
    mock_set_region.return_value = ctx.success_result
    mock_run_script.return_value = ctx.success_result

    profile_group = get_test_profile_group_sso(include_service_role=True)
    result = ctx.core.login_with_sso(profile_group)
    assert result.was_success
    assert not result.was_error

    mock_set_region.assert_has_calls([call(None)])
    mock_handle_support_files.assert_has_calls([call(profile_group)])
    mock_run_script.assert_has_calls([call(profile_group)])
    mock_credentials.assert_has_calls([call.cleanup()])
    expected_sso_calls = [
        call.sso_login(profile_group),
        call.write_sso_credentials(profile_group),
        call.write_sso_service_profile(profile_group),
    ]
    mock_sso.assert_has_calls(expected_sso_calls)

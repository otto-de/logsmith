import os
import pytest
from unittest.mock import call
from pathlib import Path
from app.core import files

script_dir = os.path.dirname(os.path.realpath(__file__))

test_file = f'{script_dir}/../test_resources/test_file'
test_file_positions = f'{script_dir}/../test_resources/test_file_positions'
non_existing_test_file = f'{script_dir}/../test_resources/test_file_does_not_exist'
test_home = f'{script_dir}/../test_resources'

#######################
# Fixures


@pytest.fixture(autouse=True)
def before_after_each_test(mocker, monkeypatch):
    # before each test
    mocker.patch.object(Path, "home", return_value='home')
    yield
    # after each test


#######################
# Test
def test_get_app_path():
    assert 'home/.logsmith' == files.get_app_path()


def test_get_aws_path():
    assert 'home/.aws' == files.get_aws_path()


def test_get_config_path():
    assert 'home/.logsmith/config.yaml' == files.get_config_path()


def test_get_accounts_path():
    assert 'home/.logsmith/accounts.yaml' == files.get_accounts_path()


def test_get_service_roles_path():
    assert 'home/.logsmith/service_roles.yaml' == files.get_service_roles_path()


def test_get_log_path():
    assert 'home/.logsmith/app.log' == files.get_log_path()


def test_get_active_group_file_path():
    assert 'home/.logsmith/active_group' == files.get_active_group_file_path()


def test_parse_yaml():
    yaml = files.parse_yaml('test: true')
    expected = {'test': True}
    assert expected == yaml


def test_parse_yaml__invalid_yaml():
    yaml = files.parse_yaml('test: true test: true')
    assert {} == yaml


def test_dump_yaml():
    text = files.dump_yaml({'test': True})
    expected = 'test: true\n'
    assert expected == text


def test_dump_yaml__leading_zero():
    text = files.dump_yaml({'test': '043156558'})
    expected = 'test: \'043156558\'\n'
    assert expected == text


def test_dump_yaml__do_not_sort_keys():
    text = files.dump_yaml({'z': 'dog', 'a': 'cat'})
    expected = 'z: dog\na: cat\n'
    assert expected == text


def test_dump_yaml__indentation():
    text = files.dump_yaml({'a': 'cat', 'b': {'c': 'dog'}})
    expected = 'a: cat\nb:\n  c: dog\n'
    assert expected == text


def test__load_file():
    text = files._load_file(test_file)
    expected = 'this is a test'
    assert expected == text


def test__load_file__file_not_found():
    text = files._load_file('no_file')
    expected = ''
    assert expected == text


def test_load_config(mocker):
    mocker.patch.object(Path, "home", return_value=test_home)

    file = files.load_config()
    expected = {'test': 'config'}
    assert expected == file


def test_load_config__files_does_not_exist(mocker):
    mocker.patch.object(Path, "home", return_value='wrong_home')

    file = files.load_config()
    expected = {}
    assert expected == file


def test_load_accounts(mocker):
    mock_home = mocker.patch.object(Path, "home", return_value=test_home)

    mock_home.return_value = test_home
    file = files.load_accounts()
    expected = {'test': 'accounts'}
    assert expected == file


def test_load_accounts__files_does_not_exist(mocker):
    mocker.patch.object(Path, "home", return_value='wrong_home')

    file = files.load_accounts()
    expected = {}
    assert expected == file


def test_load_service_roles(mocker):
    mocker.patch.object(Path, "home", return_value=test_home)

    file = files.load_service_roles()
    expected = {'test': 'service_roles'}
    assert expected == file


def test_load_service_roles__files_does_not_exist(mocker):
    mocker.patch.object(Path, "home", return_value='wrong_home')

    file = files.load_service_roles()
    expected = {}
    assert expected == file


def test_save_config_file(mocker):
    mock_write = mocker.patch.object(files, "_write_file")

    files.save_config_file({'test': True})
    expected = [
        call('home/.logsmith/config.yaml', 'test: true\n')
    ]
    assert expected == mock_write.mock_calls


def test_save_accounts_file(mocker):
    mock_write = mocker.patch.object(files, "_write_file")

    files.save_accounts_file({'test': True})
    expected = [
        call('home/.logsmith/accounts.yaml', 'test: true\n')
    ]
    assert expected == mock_write.mock_calls


def test_save_service_roles_file(mocker):
    mock_write = mocker.patch.object(files, "_write_file")

    files.save_service_roles_file({'test': True})
    expected = [
        call('home/.logsmith/service_roles.yaml', 'test: true\n')
    ]
    assert expected == mock_write.mock_calls


def test_file_exists():
    assert files.file_exists(test_file)


def test_file_exists__files_does_not_exist():
    assert not files.file_exists(non_existing_test_file)

# @mock.patch('app.core.files.os.path.exists', return_value=True)
def test_file_exists__script_path_without_arguments(mocker):
    mock_os_path_exists = mocker.patch.object(files, "_path_exist", return_value=True)

    files.file_exists(test_file)
    expected = [call(test_file)]
    assert expected == mock_os_path_exists.mock_calls


def test_file_exists__script_path_with_arguments(mocker):
    mock_os_path_exists = mocker.patch.object(files, "_path_exist", return_value=True)

    files.file_exists(f'{test_file} argument1 argument2')
    expected = [call(test_file)]
    assert expected == mock_os_path_exists.mock_calls


def test__replace_home_variable(mocker):
    mocker.patch.object(files, "get_home_dir", return_value='/home/user')
    
    assert '/home/user/some/path' == files.replace_home_variable('\"${HOME}\"/some/path')
    assert '/home/user/some/path' == files.replace_home_variable('\"$HOME\"/some/path')
    assert '/home/user/some/path' == files.replace_home_variable('${HOME}/some/path')
    assert '/home/user/some/path' == files.replace_home_variable('$HOME/some/path')
    assert '/home/user/some/path' == files.replace_home_variable('~/some/path')


def test__load_file_window__beginning():
    text, position = files._load_file_window(test_file_positions, 0)
    assert 20 == position
    assert '1\n2\n3\n4\n5\n6\n7\n8\n9\n10' == text


def test__load_file_window__middle():
    text, position = files._load_file_window(test_file_positions, 10)
    assert 20 == position
    assert '6\n7\n8\n9\n10' == text

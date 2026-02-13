import os
import subprocess
from unittest import TestCase
from unittest.mock import patch

from app.shell import shell

script_dir = os.path.dirname(os.path.realpath(__file__))


def test_run():
    result = shell.run('echo test')
    assert True == result.was_success
    assert 'test' == result.payload

def test_run__command_not_found():
    result = shell.run('this_commando_does_not_exist')
    assert False == result.was_success
    assert True == result.was_error
    assert '' == result.payload

def test_run__command_error():
    result = shell.run(f'{script_dir}/../test_resources/fail.sh')
    assert False == result.was_success
    assert True == result.was_error
    assert '' == result.payload

def test_run__command_timeout():
    result = shell.run(f'{script_dir}/../test_resources/timeout.sh', 1)
    assert False == result.was_success
    assert True == result.was_error
    assert '' == result.payload

def test_login_shell_env__uses_login_shell_and_parses_env():
    env_output = "A=1\nB=two\nPATH=/usr/bin\n"
    with patch('app.shell.shell.get_login_shell', return_value='/bin/zsh') as get_shell:
        with patch('app.shell.shell.subprocess.check_output', return_value=env_output.encode()) as check_output:
            env = shell.login_shell_env()

    check_output.assert_called_once_with(['/bin/zsh', '-l', '-c', 'printenv'])
    assert '/bin/zsh' == get_shell.return_value
    assert {'A': '1', 'B': 'two', 'PATH': '/usr/bin'} == env

def test_login_shell_env__extends_path_when_requested():
    env_output = "PATH=/usr/local/bin\nOTHER=value\n"
    with patch('app.shell.shell.get_login_shell', return_value='/bin/bash'):
        with patch('app.shell.shell.subprocess.check_output', return_value=env_output.encode()):
            env = shell.login_shell_env(path_extension='/custom/bin')

    assert '/custom/bin:/usr/local/bin' == env['PATH']
    assert 'value' == env['OTHER']
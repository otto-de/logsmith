import os
import subprocess
from unittest import TestCase
from unittest.mock import patch

from app.shell import shell

script_dir = os.path.dirname(os.path.realpath(__file__))


class Test(TestCase):
    
    def test_run(self):
        result = shell.run('echo test')
        self.assertEqual(True, result.was_success)
        self.assertEqual('test', result.payload)

    def test_run__command_not_found(self):
        result = shell.run('this_commando_does_not_exist')
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('', result.payload)

    def test_run__command_error(self):
        result = shell.run(f'{script_dir}/../test_resources/fail.sh')
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('', result.payload)

    def test_run__command_timeout(self):
        result = shell.run(f'{script_dir}/../test_resources/timeout.sh', 1)
        self.assertEqual(False, result.was_success)
        self.assertEqual(True, result.was_error)
        self.assertEqual('', result.payload)

    def test_login_shell_env__uses_login_shell_and_parses_env(self):
        env_output = "A=1\nB=two\nPATH=/usr/bin\n"
        with patch('app.shell.shell.get_login_shell', return_value='/bin/zsh') as get_shell:
            with patch('app.shell.shell.subprocess.check_output', return_value=env_output.encode()) as check_output:
                env = shell.login_shell_env()

        check_output.assert_called_once_with(['/bin/zsh', '-l', '-c', 'printenv'])
        self.assertEqual('/bin/zsh', get_shell.return_value)
        self.assertEqual({'A': '1', 'B': 'two', 'PATH': '/usr/bin'}, env)

    def test_login_shell_env__extends_path_when_requested(self):
        env_output = "PATH=/usr/local/bin\nOTHER=value\n"
        with patch('app.shell.shell.get_login_shell', return_value='/bin/bash'):
            with patch('app.shell.shell.subprocess.check_output', return_value=env_output.encode()):
                env = shell.login_shell_env(path_extension='/custom/bin')

        self.assertEqual('/custom/bin:/usr/local/bin', env['PATH'])
        self.assertEqual('value', env['OTHER'])

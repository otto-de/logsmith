import os
from unittest import TestCase

from app.shell import shell

script_dir = os.path.dirname(os.path.realpath(__file__))


class Test(TestCase):
    def test_run(self):
        self.assertEqual('test', shell.run('echo test'))

    def test_run__command_not_found(self):
        self.assertEqual(None, shell.run('this_commando_does_not_exist'))

    def test_run__command_error(self):
        self.assertEqual(None, shell.run(f'{script_dir}/../test_resources/fail.sh'))

    def test_run__command_timeout(self):
        self.assertEqual(None, shell.run(f'{script_dir}/../test_resources/timeout.sh', 1))

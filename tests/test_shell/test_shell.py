import os
from unittest import TestCase

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

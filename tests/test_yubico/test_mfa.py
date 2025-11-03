from unittest import TestCase, mock
from unittest.mock import Mock, call

from app.yubico import mfa
from core.result import Result


class TestStart(TestCase):

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell__command_failes(self, mock_run):
        result = Result()
        result.error('')
        mock_run.return_value = result

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('fail_command'))

        expected = [call('fail_command')]
        self.assertEqual(expected, mock_run.mock_calls)

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell(self, mock_run):
        result = Result()
        result.set_success()
        result.add_payload('123456')
        mock_run.return_value = result
    
        self.assertEqual('123456', mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, mock_run.mock_calls)

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell__command_succeedes_but_None_instead_of_token(self, mock_run):
        result = Result()
        result.set_success()
        mock_run.return_value = result

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, mock_run.mock_calls)

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell__command_succeedes_but_no_valid_token(self, mock_run):
        result = Result()
        result.set_success()
        result.add_payload('Some Token 123456')
        mock_run.return_value = result
        
        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, mock_run.mock_calls)

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell__command_succeedes_token_has_spaces(self, mock_run):
        result = Result()
        result.set_success()
        result.add_payload(' 123456 ')
        mock_run.return_value = result

        self.assertEqual('123456', mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, mock_run.mock_calls)

    @mock.patch('app.yubico.mfa.shell.run')
    def test_fetch_mfa_token_from_shell__no_command(self, mock_run):
        result = Result()
        result.set_success()
        mock_run.return_value = result
        
        self.assertEqual(None, mfa.fetch_mfa_token_from_shell(''))

        expected = []
        self.assertEqual(expected, mock_run.mock_calls)

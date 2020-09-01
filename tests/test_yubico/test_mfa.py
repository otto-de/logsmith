from unittest import TestCase, mock
from unittest.mock import Mock, call

from app.yubico import mfa


def shell(command):
    if command == 'success_command':
        return True
    return False


class TestStart(TestCase):

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell__command_failes(self, m_shell):
        m_shell.run = Mock()
        m_shell.run.side_effect = shell

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('fail_command'))

        expected = [call('fail_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell(self, m_shell):
        m_shell.run = Mock()
        m_shell.run.return_value = '123456'

        self.assertEqual('123456', mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell__command_succeedes_but_None_instead_of_token(self, m_shell):
        m_shell.run = Mock()
        m_shell.run.return_value = None

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell__command_succeedes_but_no_valid_token(self, m_shell):
        m_shell.run = Mock()
        m_shell.run.return_value = 'Some Token 123456'

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell__command_succeedes_token_has_spaces(self, m_shell):
        m_shell.run = Mock()
        m_shell.run.return_value = ' 123456 '

        self.assertEqual('123456', mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    def test_fetch_mfa_token_from_shell__no_command(self, m_shell):
        self.assertEqual(None, mfa.fetch_mfa_token_from_shell(''))

        expected = []
        self.assertEqual(expected, m_shell.run.mock_calls)

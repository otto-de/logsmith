from unittest import TestCase, mock
from unittest.mock import Mock, call

from app.yubico import mfa


def shell(command):
    if command == 'success_command':
        return True
    return False


class TestStart(TestCase):
    def test__extract_token(self):
        stout = 'Amazon Web Services:user@12345678901  123456'
        self.assertEqual('123456', mfa._extract_token(stout))

    def test__extract_token__no_token_from_amazon(self):
        stout = 'Google Web Services:user@12345678901  123456'
        self.assertEqual(None, mfa._extract_token(stout))

    def test__extract_token__no_token(self):
        stout = '12'
        self.assertEqual(None, mfa._extract_token(stout))

    @mock.patch('app.yubico.mfa.shell')
    @mock.patch('app.yubico.mfa._extract_token')
    def test_fetch_mfa_token_from_shell__command_failes(self, m_extract, m_shell):
        m_shell.run = Mock()
        m_shell.run.side_effect = shell

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('fail_command'))

        expected = [call('fail_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    @mock.patch('app.yubico.mfa._extract_token')
    def test_fetch_mfa_token_from_shell(self, m_extract, m_shell):
        m_shell.run = Mock()
        m_shell.run.side_effect = shell
        m_extract.return_value = '123456'

        self.assertEqual('123456', mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    @mock.patch('app.yubico.mfa._extract_token')
    def test_fetch_mfa_token_from_shell__command_succeedes_but_no_token(self, m_extract, m_shell):
        m_shell.run = Mock()
        m_shell.run.side_effect = shell
        m_extract.return_value = None

        self.assertEqual(None, mfa.fetch_mfa_token_from_shell('success_command'))

        expected = [call('success_command')]
        self.assertEqual(expected, m_shell.run.mock_calls)

    @mock.patch('app.yubico.mfa.shell')
    @mock.patch('app.yubico.mfa._extract_token')
    def test_fetch_mfa_token_from_shell__no_command(self, *_):
        self.assertEqual(None, mfa.fetch_mfa_token_from_shell(None))

from unittest import TestCase, mock
from unittest.mock import Mock, call

from app.core.result import Result
from app.yubico import mfa
from app.shell import shell



def test_fetch_mfa_token_from_shell__command_failes(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.error('')
    mock_run.return_value = result

    assert None == mfa.fetch_mfa_token_from_shell('fail_command')

    expected = [call('fail_command')]
    assert expected == mock_run.mock_calls

def test_fetch_mfa_token_from_shell(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.set_success()
    result.add_payload('123456')
    mock_run.return_value = result

    assert '123456' == mfa.fetch_mfa_token_from_shell('success_command')

    expected = [call('success_command')]
    assert expected == mock_run.mock_calls

def test_fetch_mfa_token_from_shell__command_succeedes_but_None_instead_of_token(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.set_success()
    mock_run.return_value = result

    assert None == mfa.fetch_mfa_token_from_shell('success_command')

    expected = [call('success_command')]
    assert expected == mock_run.mock_calls

def test_fetch_mfa_token_from_shell__command_succeedes_but_no_valid_token(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.set_success()
    result.add_payload('Some Token 123456')
    mock_run.return_value = result
    
    assert None == mfa.fetch_mfa_token_from_shell('success_command')

    expected = [call('success_command')]
    assert expected == mock_run.mock_calls

def test_fetch_mfa_token_from_shell__command_succeedes_token_has_spaces(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.set_success()
    result.add_payload(' 123456 ')
    mock_run.return_value = result

    assert '123456' == mfa.fetch_mfa_token_from_shell('success_command')

    expected = [call('success_command')]
    assert expected == mock_run.mock_calls

def test_fetch_mfa_token_from_shell__no_command(mocker):
    mock_run = mocker.patch.object(shell, "run")
    
    result = Result()
    result.set_success()
    mock_run.return_value = result
    
    assert None == mfa.fetch_mfa_token_from_shell('')

    expected = []
    assert expected == mock_run.mock_calls

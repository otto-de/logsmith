import pytest

from app.core.result import Result



def test___unsuccessful_by_default():
    result = Result()
    assert False == result.was_success
    assert False == result.was_error

def test_set_success():
    result = Result()
    result.set_success()
    assert True == result.was_success
    assert False == result.was_error

def test_add_payload():
    result = Result()
    result.add_payload('test')
    assert False == result.was_success
    assert False == result.was_error
    assert 'test' == result.payload

def test_error():
    result = Result()
    error_message = 'there was an error'
    result.error(error_message)
    assert False == result.was_success
    assert True == result.was_error
    assert error_message == result.error_message

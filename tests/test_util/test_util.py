import pytest

from app.util.util import generate_session_name, is_positive_int


def test_generate_session_name():
    result = generate_session_name('key-name')
    expected = 'session-token-key-name'
    assert expected == result

def test_is_positive_int__accepts_int_like_values():
    assert is_positive_int(5)
    assert is_positive_int('7')
    assert is_positive_int(' 8 ')
    assert is_positive_int(0)
    assert is_positive_int('0')

def test_is_positive_int__rejects_non_digits_or_negative():
    assert not is_positive_int(-1)
    assert not is_positive_int('-2')
    assert not is_positive_int('abc')
    assert not is_positive_int('1.2')
    assert not is_positive_int(None)

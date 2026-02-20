import pytest
from types import SimpleNamespace

from app.util.util import generate_session_name, is_positive_int, use_as_default


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


def test_use_as_default__override_match_returns_true():
    profile = SimpleNamespace(profile='dev', default=False)
    assert use_as_default(profile, override='dev')


def test_use_as_default__override_mismatch_returns_false_even_if_default():
    profile = SimpleNamespace(profile='prod', default=True)
    assert not use_as_default(profile, override='dev')


def test_use_as_default__without_override_uses_default_flag():
    default_profile = SimpleNamespace(profile='dev', default=True)
    non_default_profile = SimpleNamespace(profile='prod', default=False)

    assert use_as_default(default_profile, override=None)
    assert not use_as_default(non_default_profile, override=None)


def test_use_as_default__empty_override_is_treated_like_no_override():
    profile = SimpleNamespace(profile='dev', default=True)
    assert use_as_default(profile, override='')

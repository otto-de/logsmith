import pytest

from app import arguments
from app import version


def test_version_short(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["-v"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == f"logsmith {version.version}\n"
    assert exc.value.code == 0


def test_version_long(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["--version"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == f"logsmith {version.version}\n"
    assert exc.value.code == 0


def test_help_short(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["-h"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("usage: logsmith [-h]")
    assert exc.value.code == 0


def test_help_long(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["--help"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("usage: logsmith [-h]")
    assert exc.value.code == 0


def test_loglevel_default():
    args = arguments.parse([])
    assert args.loglevel == "WARN"


def test_loglevel_valid():
    args = arguments.parse(["-l", "INFO"])
    assert args.loglevel == "INFO"


def test_loglevel_invalid(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["-l", "LOTS"])

    captured = capsys.readouterr()
    assert "logsmith: error: argument -l/--loglevel: invalid choice" in captured.err
    assert captured.out == ""
    assert exc.value.code != 0


def test_unknown_parameter(capsys):
    with pytest.raises(SystemExit) as exc:
        arguments.parse(["--foobar"])

    captured = capsys.readouterr()
    assert "logsmith: error: unrecognized arguments: --foobar" in captured.err
    assert captured.out == ""
    assert exc.value.code != 0

import contextlib
import io
from unittest import TestCase

import sys

from app import arguments
from app import __version__


@contextlib.contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test(TestCase):

    def test_version_short(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(["-v"])

        self.assertEqual(err.getvalue(), '')
        self.assertEqual(out.getvalue(), 'logsmith {0}\n'.format(__version__.__version_string__))
        self.assertEqual(cm.exception.code, 0)

    def test_version_long(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(["--version"])

        self.assertEqual(err.getvalue(), '')
        self.assertEqual(out.getvalue(), 'logsmith {0}\n'.format(__version__.__version_string__))
        self.assertEqual(cm.exception.code, 0)

    def test_help_short(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(["-h"])

        self.assertEqual(err.getvalue(), '')
        self.assertRegex(out.getvalue(), "^usage: logsmith \\[-h\\].*")
        self.assertEqual(cm.exception.code, 0)

    def test_help_long(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(["--help"])

        self.assertEqual(err.getvalue(), '')
        self.assertRegex(out.getvalue(), "^usage: logsmith \\[-h\\].*")
        self.assertEqual(cm.exception.code, 0)

    def test_loglevel_default(self):
        args = arguments.parse([])
        self.assertEqual(args.loglevel, 'WARN')

    def test_loglevel_valid(self):
        args = arguments.parse(['-l', 'INFO'])
        self.assertEqual(args.loglevel, 'INFO')

    def test_loglevel_invalid(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(['-l', 'LOTS'])

        self.assertRegex(err.getvalue(), "logsmith: error: argument -l/--loglevel: invalid choice")
        self.assertEqual(out.getvalue(), '')
        self.assertNotEqual(cm.exception.code, 0)

    def test_unknown_parameter(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            arguments.parse(['--foobar'])

        self.assertRegex(err.getvalue(), "logsmith: error: unrecognized arguments: --foobar")
        self.assertEqual(out.getvalue(), '')
        self.assertNotEqual(cm.exception.code, 0)

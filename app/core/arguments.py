from argparse import ArgumentParser

from app import __version__


def parse(args):
    parser = ArgumentParser(prog='logsmith')
    parser.add_argument("-l", "--loglevel", dest="loglevel", default="WARN",
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
                        help="set the loglevel")
    parser.add_argument('-v', '--version', action='version',
                version="{prog}s {version}".format(prog="%(prog)", version=__version__.__version_string__))

    return parser.parse_args(args)


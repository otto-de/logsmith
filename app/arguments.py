from argparse import ArgumentParser

from app import __version__


def parse(args):
    parser = ArgumentParser(prog='logsmith', description='login into your favorite aws profiles')
    parser.add_argument("-l", "--loglevel", dest="loglevel", default="WARN",
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
                        help="set the loglevel")
    parser.add_argument('-v', '--version', action='version',
                        version="{prog}s {version}".format(prog="%(prog)", version=__version__.__version_string__))
    parser.add_argument('--list', action='store_true',
                        help='lists profile groups')
    parser.add_argument('--login',
                        help='Login with group')
    parser.add_argument('--logout', action='store_true',
                        help='Remove profiles')
    parser.add_argument('--region',
                        help='Overwrite region to login to')
    parser.add_argument('--set-access-key', action='store_true',
                        help='set access key')
    parser.add_argument('--rotate-access-key', action='store_true',
                        help='rotate access key')
    parser.add_argument('-o', '--oneshot', action='store_true',
                        help='When used in combination with --login, the program will finish after login instead of running an infinite refresh loop')
    return parser.parse_args(args)


def use_cli(args):
    if args.list:
        return True
    if args.login:
        return True
    if args.logout:
        return True
    if args.region:
        return True
    if args.rotate_access_key:
        return True
    if args.set_access_key:
        return True
    return False

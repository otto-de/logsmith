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
    parser.add_argument('--login', metavar='GROUP',
                        help='Login with group')
    parser.add_argument('--logout', action='store_true',
                        help='Remove profiles')
    parser.add_argument('--region',
                        help='Overwrite region to login to')
    parser.add_argument('--set-access-key', action='store_true',
                        help='start dialog to set access key')
    parser.add_argument('--rotate-access-key', metavar='KEY_NAME',
                        help='rotate given access key')
    parser.add_argument('--set-sso-session', action='store_true',
                        help='start dialog to set sso session')
    parser.add_argument('--list-service-roles', metavar='PROFILE',
                        help='list assumable roles for the given profile')
    parser.add_argument('--set-service-roles', nargs=3, metavar=('GROUP', 'PROFILE', 'ROLE'),
                        help='set service role for the given profile')
    parser.add_argument('--toggle', nargs=2, metavar=('TOGGLE', 'VALUE'),
                        help='set given toggle to either true or false. Toggles: script')
    parser.add_argument('-o', '--oneshot', action='store_true',
                        help='When used in combination with --login, the program will finish after login instead of running an infinite refresh loop')
    return parser.parse_args(args)


def use_cli(args):
    return any([
        args.list,
        args.login,
        args.logout,
        args.region,
        args.rotate_access_key,
        args.set_access_key,
        args.set_sso_session,
        args.list_service_roles,
        args.set_service_roles,
        args.toggle,
    ])

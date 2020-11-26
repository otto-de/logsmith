from cli.cli import Cli


def start_cli(args):
    cli = Cli()
    if args.list:
        cli.list()
    if args.login:
        cli.login(args.login, args.region)
    if args.logout:
        cli.logout()
    if args.rotate_access_key:
        cli.rotate_access_key()
    if args.set_access_key:
        cli.set_access_key()

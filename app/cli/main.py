from app.cli.cli import Cli


def start_cli(args):
    cli = Cli()
    if args.list:
        cli.list()
    if args.login:
        cli.login(args.login, args.region, args.oneshot)
    if args.logout:
        cli.logout()
    if args.rotate_access_key:
        cli.rotate_access_key(args.rotate_access_key)
    if args.set_access_key:
        cli.set_access_key()
    if args.list_service_roles:
        cli.list_service_roles(args.list_service_roles)
    if args.set_service_roles:
        group = args.set_service_roles[0]
        profile = args.set_service_roles[1]
        role = args.set_service_roles[2]
        cli.set_service_role(group, profile, role)

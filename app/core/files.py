import io
import logging
import os
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError, ScannerError

logger = logging.getLogger('logsmith')
config_file_name = 'config.yaml'
accounts_file_name = 'accounts.yaml'
service_roles_file_name = 'service_roles.yaml'
log_file_name = 'app.log'
active_group_file_name = 'active_group'

yamli = YAML(typ='safe')
yamli.default_flow_style = False
yamli.sort_base_mapping_type_on_output = False
yamli.indent(sequence=4)


def get_app_path() -> str:
    return f'{str(Path.home())}/.logsmith'


def get_aws_path() -> str:
    return os.path.join(str(Path.home()), '.aws')


def get_config_path() -> str:
    return f'{get_app_path()}/{config_file_name}'


def get_accounts_path() -> str:
    return f'{get_app_path()}/{accounts_file_name}'


def get_service_roles_path() -> str:
    return f'{get_app_path()}/{service_roles_file_name}'


def get_log_path() -> str:
    return f'{get_app_path()}/{log_file_name}'


def get_active_group_file_path() -> str:
    return f'{get_app_path()}/{active_group_file_name}'


def parse_yaml(text: str):
    try:
        return yamli.load(text) or {}
    except (ParserError, ScannerError):
        return {}


def dump_yaml(d: dict):
    buffer = io.BytesIO()
    yamli.dump(d, buffer)
    return buffer.getvalue().decode("utf-8")


def _load_file(path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            return file.read()
    return ''


def _write_file(path, content):
    print(f'writing to {path} {content}')
    with open(path, 'w') as file:
        file.write(str(content))


def remove_file(path):
    if os.path.exists(path):
        os.remove(path)


def load_config():
    return parse_yaml(_load_file(get_config_path()))


def load_accounts():
    return parse_yaml(_load_file(get_accounts_path()))


def load_service_roles():
    return parse_yaml(_load_file(get_service_roles_path()))


def save_config_file(config_dict: dict):
    _write_file(get_config_path(), dump_yaml(config_dict))


def save_accounts_file(account_dict: dict):
    _write_file(get_accounts_path(), dump_yaml(account_dict))


def save_service_roles_file(service_roles: dict):
    _write_file(get_service_roles_path(), dump_yaml(service_roles))


def load_logs():
    return _load_file(get_log_path()) or 'no logs found'


def write_active_group_file(group_name):
    _write_file(get_active_group_file_path(), group_name)

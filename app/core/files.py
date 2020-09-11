import logging
import os
from pathlib import Path

import yaml
from yaml.parser import ParserError, ScannerError

logger = logging.getLogger('logsmith')
config_file_name = 'config.yaml'
accounts_file_name = 'accounts.yaml'
log_file_name = 'app.log'
active_group_file_name = 'active_group'


def get_app_path() -> str:
    return f'{str(Path.home())}/.logsmith'


def get_aws_path() -> str:
    return os.path.join(str(Path.home()), '.aws')


def get_config_path() -> str:
    return f'{get_app_path()}/{config_file_name}'


def get_accounts_path() -> str:
    return f'{get_app_path()}/{accounts_file_name}'


def get_log_path() -> str:
    return f'{get_app_path()}/{log_file_name}'


def get_active_group_file_path() -> str:
    return f'{get_app_path()}/{active_group_file_name}'


def parse_yaml(text: str):
    try:
        return yaml.safe_load(text) or {}
    except (ParserError, ScannerError):
        return {}


def dump_yaml(d: dict):
    return yaml.dump(d, indent=4, default_flow_style=False, sort_keys=False)


def _load_file(path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            return file.read()
    return ''


def _write_file(path, content):
    with open(path, 'w') as file:
        file.write(str(content))


def remove_file(path):
    if os.path.exists(path):
        os.remove(path)


def load_config():
    return parse_yaml(_load_file(get_config_path()))


def load_accounts():
    return parse_yaml(_load_file(get_accounts_path()))


def save_config_file(config_dict: dict):
    _write_file(get_config_path(), dump_yaml(config_dict))


def save_accounts_file(account_dict: dict):
    _write_file(get_accounts_path(), dump_yaml(account_dict))


def load_logs():
    return _load_file(get_log_path()) or 'no logs found'


def write_active_group_file(group_name):
    _write_file(get_active_group_file_path(), group_name)

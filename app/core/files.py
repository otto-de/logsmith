import io
import json
import logging
import os
from pathlib import Path
from typing import List

from ruamel.yaml import YAML

logger = logging.getLogger('logsmith')
config_file_name = 'config.yaml'
toggles_file_name = 'toggles.yaml'
accounts_file_name = 'accounts.yaml'
accounts_state_file_name = 'accounts_state.yaml'
service_roles_file_name = 'service_roles.yaml'
log_file_name = 'app.log'
active_group_file_name = 'active_group'

# TODO set to base to avoid automatic conversion
yamli = YAML(typ='safe')
yamli.default_flow_style = False
yamli.sort_base_mapping_type_on_output = False
yamli.indent(sequence=4)

home_variables = ['\"${HOME}\"', '\"$HOME\"', '${HOME}', '$HOME', '~']
yaml_extensions = ('.yaml', '.yml')
accounts_path_config_key = 'accounts_path'
accounts_state_selected_path_key = 'selected_path'
accounts_state_config_accounts_path_key = 'config_accounts_path'
accounts_state_history_key = 'history'


def get_app_path() -> str:
    return f'{str(Path.home())}/.logsmith'


def get_aws_path() -> str:
    return os.path.join(str(Path.home()), '.aws')

def get_aws_cache_path() -> str:
    return os.path.join(get_aws_path(), 'sso', 'cache')

def get_config_path() -> str:
    return f'{get_app_path()}/{config_file_name}'


def get_toggles_path() -> str:
    return f'{get_app_path()}/{toggles_file_name}'


def get_default_accounts_path() -> str:
    return f'{get_app_path()}/{accounts_file_name}'


def get_accounts_state_path() -> str:
    return f'{get_app_path()}/{accounts_state_file_name}'


def get_accounts_path() -> str:
    return resolve_active_accounts_path(config_accounts_path=load_config().get(accounts_path_config_key),
                                        accounts_state=load_accounts_state())


def resolve_active_accounts_path(config_accounts_path: str | None, accounts_state: dict) -> str:
    # The file selected in the tray menu wins, unless accounts_path in config.yaml was
    # changed since the selection was made or the selected file no longer exists.
    selected_path = accounts_state.get(accounts_state_selected_path_key)
    selected_with = accounts_state.get(accounts_state_config_accounts_path_key)
    if selected_path and selected_with == config_accounts_path and is_yaml_file_path(selected_path):
        selected_path = expand_path(selected_path)
        if is_file(selected_path):
            return selected_path
    return resolve_accounts_path(config_accounts_path)


def resolve_accounts_path(custom_accounts_path: str | None) -> str:
    if not custom_accounts_path:
        return get_default_accounts_path()
    if not is_yaml_file_path(custom_accounts_path):
        logger.warning(f'{accounts_path_config_key} "{custom_accounts_path}" must have a yaml extension '
                       f'{yaml_extensions}, falling back to {get_default_accounts_path()}')
        return get_default_accounts_path()
    return expand_path(custom_accounts_path)


def is_yaml_file_path(path: str) -> bool:
    return str(path).strip().lower().endswith(yaml_extensions)


def expand_path(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(str(path).strip()))


def get_service_roles_path() -> str:
    return f'{get_app_path()}/{service_roles_file_name}'


def get_log_path() -> str:
    return f'{get_app_path()}/{log_file_name}'


def get_active_group_file_path() -> str:
    return f'{get_app_path()}/{active_group_file_name}'


def parse_yaml(text: str) -> dict:
    try:
        return yamli.load(text) or {}
    except Exception as e:
        logging.warning('error while parsing yaml', exc_info=True)
        return {}


def dump_yaml(d: dict) -> str:
    buffer = io.BytesIO()
    yamli.dump(d, buffer)
    return buffer.getvalue().decode("utf-8")


def _load_file(path) -> str:
    if path_exist(path):
        with open(path, 'r') as file:
            return file.read()
    return ''


def _load_file_window(path, position) -> (str, int):
    if path_exist(path):
        with open(path, 'r') as file:
            file.seek(position)
            content = file.read()
            new_position = file.tell()
            return content, new_position
    return '', 0


def _write_file(path, content) -> None:
    with open(path, 'w') as file:
        file.write(str(content))


def remove_file(path) -> None:
    if path_exist(path):
        os.remove(path)


def file_exists(file_path) -> bool:
    file_path = file_path.strip()
    if ' ' in file_path:
        file_path = file_path.split(' ')[0]
    return path_exist(file_path)

def path_exist(path):
    return os.path.exists(path)

def is_file(path) -> bool:
    return os.path.isfile(path)

def load_config() -> dict:
    return parse_yaml(_load_file(get_config_path()))


def load_toggles() -> dict:
    return parse_yaml(_load_file(get_toggles_path()))


def load_accounts() -> dict:
    return parse_yaml(_load_file(get_accounts_path()))


def load_accounts_state() -> dict:
    return parse_yaml(_load_file(get_accounts_state_path()))


def load_service_roles() -> dict:
    return parse_yaml(_load_file(get_service_roles_path()))


def save_config_file(config_dict: dict) -> None:
    _write_file(get_config_path(), dump_yaml(config_dict))


def save_toggles_file(toggles_dict: dict) -> None:
    _write_file(get_toggles_path(), dump_yaml(toggles_dict))


def save_accounts_file(account_dict: dict) -> None:
    accounts_path = get_accounts_path()
    ensure_parent_dir(accounts_path)
    _write_file(accounts_path, dump_yaml(account_dict))


def save_accounts_state_file(accounts_state: dict) -> None:
    _write_file(get_accounts_state_path(), dump_yaml(accounts_state))


def ensure_parent_dir(path: str) -> None:
    parent_dir = os.path.dirname(path)
    if parent_dir and not path_exist(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)


def save_service_roles_file(service_roles: dict) -> None:
    _write_file(get_service_roles_path(), dump_yaml(service_roles))


def load_logs() -> str:
    return _load_file(get_log_path()) or ''


def load_log_with_position(position: int) -> (str, int):
    return _load_file_window(get_log_path(), position) or ('', 0)


def write_active_group_file(group_name) -> None:
    _write_file(get_active_group_file_path(), group_name)


def get_home_dir():
    return os.path.expanduser("~")


def replace_home_variable(script_path: str) -> str | None:
    for variable_name in home_variables:
        if variable_name in script_path:
            return script_path.replace(variable_name, get_home_dir())
    return script_path

def get_local_sso_access_token() -> List[str]:
    json_files = sorted(Path(get_aws_cache_path()).glob("*.json"))
    access_tokens = []
    
    for p in json_files:
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        
        token = data.get("accessToken")
        if token is not None:
            access_tokens.append(token)
    return access_tokens

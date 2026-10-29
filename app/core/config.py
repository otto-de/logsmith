from typing import List, Dict, Optional

from app.core import files
from app.core.profile_group import ProfileGroup

_default_access_key = 'access-key'
_default_sso_sesson = 'sso'
_default_sso_interval = '8'
_accounts_path_history_size = 10


class Config:
    def __init__(self):
        self.profile_groups: Dict[str, ProfileGroup] = {}
        self.service_roles: Dict = {}

        self.valid = False
        self.error = False

        self.mfa_shell_command = None
        self.shell_path_extension = None
        self.default_access_key = None
        self.default_sso_session = None
        self.default_sso_interval = None
        self.accounts_path = None
        self.selected_accounts_path = None
        self.selected_with_accounts_path = None
        self.accounts_path_history: List[str] = []

    def initialize(self) -> None:
        config = files.load_config()
        self.mfa_shell_command = config.get('mfa_shell_command', None)
        self.shell_path_extension = config.get('shell_path_extension', None)
        self.default_access_key = config.get('default_access_key', _default_access_key)
        self.default_sso_session = config.get('default_sso_session', _default_sso_sesson)
        self.default_sso_interval = config.get('default_sso_interval', _default_sso_interval)
        self.accounts_path = config.get(files.accounts_path_config_key, None)

        accounts_state = files.load_accounts_state()
        self.selected_accounts_path = accounts_state.get(files.accounts_state_selected_path_key, None)
        self.selected_with_accounts_path = accounts_state.get(files.accounts_state_config_accounts_path_key, None)
        self.accounts_path_history = self._add_to_accounts_path_history(
            accounts_path=self.get_active_accounts_path(),
            history=accounts_state.get(files.accounts_state_history_key, None) or [])

        self.service_roles = files.load_service_roles()

        accounts = files.load_accounts()
        self.initialize_profile_groups(accounts=accounts, service_roles=self.service_roles,
                                       default_access_key=self.default_access_key,
                                       default_sso_session=self.default_sso_session,
                                       default_sso_interval=self.default_sso_interval)

    def initialize_profile_groups(self, accounts: dict, service_roles: dict, 
                                  default_access_key: str, 
                                  default_sso_session: str,
                                  default_sso_interval: str) -> None:
        self.profile_groups = {}
        for group_name, group_data in accounts.items():
            profile_group = ProfileGroup(name=group_name,
                                         group=group_data,
                                         default_access_key=default_access_key,
                                         default_sso_session=default_sso_session,
                                         default_sso_interval=default_sso_interval)
            self.profile_groups[group_name] = profile_group

            if group_name in service_roles:
                selected_service_source_profile = service_roles[group_name].get('selected_profile', None)
                selected_service_role = service_roles[group_name].get('selected_role', None)
                if selected_service_source_profile and selected_service_role:
                    profile_group.set_service_role_profile(
                        source_profile_name=selected_service_source_profile,
                        role_name=selected_service_role)
        self.validate()

    def set_mfa_shell_command(self, mfa_shell_command: str) -> None:
        self.mfa_shell_command = mfa_shell_command
        
    def set_path_extension(self, shell_path_extension: str) -> None:
        self.shell_path_extension = shell_path_extension

    def set_default_access_key(self, default_access_key: str) -> None:
        self.default_access_key = default_access_key
        
    def set_default_sso_interval(self, default_sso_interval: str) -> None:
        if default_sso_interval == 'None':
            self.default_sso_interval = None
        else:
            self.default_sso_interval = default_sso_interval

    def set_default_sso_session(self, default_sso_session: str) -> None:
        self.default_sso_session = default_sso_session

    def set_accounts_path(self, accounts_path: Optional[str]) -> None:
        self.accounts_path = accounts_path

    def select_accounts_path(self, accounts_path: str) -> None:
        self.selected_accounts_path = files.expand_path(accounts_path)
        self.selected_with_accounts_path = self.accounts_path
        self.accounts_path_history = self._add_to_accounts_path_history(accounts_path=self.selected_accounts_path,
                                                                        history=self.accounts_path_history)

    def get_active_accounts_path(self) -> str:
        return files.resolve_active_accounts_path(config_accounts_path=self.accounts_path,
                                                  accounts_state=self._accounts_state())

    def get_available_accounts_paths(self) -> List[str]:
        return [path for path in self.accounts_path_history if files.is_file(path)]

    def save_config(self) -> None:
        files.save_config_file({
            'mfa_shell_command': self.mfa_shell_command,
            'shell_path_extension': self.shell_path_extension,
            'default_access_key': self.default_access_key,
            'default_sso_session': self.default_sso_session,
            'default_sso_interval': self.default_sso_interval,
            files.accounts_path_config_key: self.accounts_path,
        })

    def save_accounts_state(self) -> None:
        files.save_accounts_state_file(self._accounts_state())

    def _accounts_state(self) -> dict:
        return {
            files.accounts_state_selected_path_key: self.selected_accounts_path,
            files.accounts_state_config_accounts_path_key: self.selected_with_accounts_path,
            files.accounts_state_history_key: self.accounts_path_history,
        }

    def save_accounts(self) -> None:
        files.save_accounts_file(self.to_dict())

    def save_selected_service_role(self, group_name: str, profile_name: str, role_name: str) -> None:
        if group_name not in self.service_roles:
            self.service_roles[group_name] = {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []
            }
        self.service_roles[group_name]['selected_profile'] = profile_name
        self.service_roles[group_name]['selected_role'] = role_name
        history = self._add_to_history(profile=profile_name, role=role_name, history=self.get_history(group_name))
        self.service_roles[group_name]['history'] = history
        files.save_service_roles_file(self.service_roles)

    def save_available_service_roles(self, group_name: str, profile_name: str, role_list: List[str]) -> None:
        if group_name not in self.service_roles:
            self.service_roles[group_name] = {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []
            }
        self.service_roles[group_name]['available'][profile_name] = role_list
        files.save_service_roles_file(self.service_roles)

    def get_selected_service_role_source_profile(self, group: str) -> Optional[str]:
        return self.service_roles.get(group, {}).get('selected_profile')

    def get_selected_service_role(self, group: str) -> Optional[str]:
        return self.service_roles.get(group, {}).get('selected_role')

    def get_available_service_roles(self, group: str, profile: str) -> List[str]:
        return self.service_roles.get(group, {}).get('available', {}).get(profile, [])

    def get_history(self, group: str):
        return self.service_roles.get(group, {}).get('history', [])

    @staticmethod
    def _add_to_history(profile: str, role: str, history: List[str]) -> List[str]:
        if not profile or not role:
            return history
        history_string = f'{profile} : {role}'
        history.insert(0, history_string)
        clean_history = []
        for item in history:
            if item not in clean_history:
                clean_history.append(item)
        return list(clean_history[:10])

    @staticmethod
    def _add_to_accounts_path_history(accounts_path: str, history: List[str]) -> List[str]:
        clean_history = []
        for path in [accounts_path, *history]:
            if not path or not files.is_yaml_file_path(path):
                continue
            path = files.expand_path(path)
            if path not in clean_history:
                clean_history.append(path)
        return clean_history[:_accounts_path_history_size]

    def validate(self) -> None:
        valid = False
        error = ''

        if not self.profile_groups:
            valid = False
            error = 'config is empty'
        for name, profile_group in self.profile_groups.items():
            valid, error = profile_group.validate()
            if not valid:
                break

        if self.accounts_path and not files.is_yaml_file_path(self.accounts_path):
            valid = False
            error = f'{files.accounts_path_config_key} must have a yaml extension'

        self.valid = valid
        self.error = error

    def list_groups(self) -> List[ProfileGroup]:
        return list(self.profile_groups.values())

    def get_group(self, name) -> Optional[ProfileGroup]:
        return self.profile_groups.get(name, None)

    def to_dict(self) -> dict:
        d = {}
        for name, group in self.profile_groups.items():
            d[name] = group.to_dict()
        return d

from typing import List, Dict

from app.core import files
from app.core.profile_group import ProfileGroup

_default_access_key = 'access-key'


class Config:
    def __init__(self):
        self.profile_groups: Dict[str, ProfileGroup] = {}
        self.service_roles: Dict = {}

        self.valid = False
        self.error = False

        self.mfa_shell_command = None
        self.default_access_key = None

    def initialize(self):
        config = files.load_config()
        self.mfa_shell_command = config.get('mfa_shell_command', None)
        self.default_access_key = config.get('default_access_key', _default_access_key)

        self.service_roles = files.load_service_roles()

        accounts = files.load_accounts()
        self.initialize_profile_groups(accounts=accounts, service_roles=self.service_roles,
                                       default_access_key=self.default_access_key)

    def initialize_profile_groups(self, accounts: dict, service_roles: dict, default_access_key: str):
        for group_name, group_data in accounts.items():
            profile_group = ProfileGroup(name=group_name,
                                         group=group_data,
                                         default_access_key=default_access_key)
            self.profile_groups[group_name] = profile_group

            if group_name in service_roles:
                selected_service_source_profile = service_roles[group_name].get('selected_profile', None)
                selected_service_role = service_roles[group_name].get('selected_role', None)
                if selected_service_source_profile and selected_service_role:
                    profile_group.set_service_role_profile(
                        source_profile_name=selected_service_source_profile,
                        role_name=selected_service_role)
        self.validate()

    def set_mfa_shell_command(self, mfa_shell_command: str):
        self.mfa_shell_command = mfa_shell_command

    def save_config(self):
        files.save_config_file({
            'mfa_shell_command': self.mfa_shell_command,
            'default_access_key': self.default_access_key,
        })

    def save_accounts(self):
        files.save_accounts_file(self.to_dict())

    def save_selected_service_role(self, group_name: str, profile_name: str, role_name: str):
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

    def save_available_service_roles(self, group_name: str, profile_name: str, role_list: List[str]):
        if group_name not in self.service_roles:
            self.service_roles[group_name] = {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []
            }
        self.service_roles[group_name]['available'][profile_name] = role_list
        files.save_service_roles_file(self.service_roles)

    def get_selected_service_role_source_profile(self, group: str):
        return self.service_roles.get(group, {}).get('selected_profile')

    def get_selected_service_role(self, group: str):
        return self.service_roles.get(group, {}).get('selected_role')

    def get_available_service_roles(self, group: str, profile: str):
        return self.service_roles.get(group, {}).get('available', {}).get(profile, [])

    def get_history(self, group: str):
        return self.service_roles.get(group, {}).get('history', [])

    @staticmethod
    def _add_to_history(profile: str, role: str, history: List[str]):
        if not profile or not role:
            return history
        history_string = f'{profile} : {role}'
        history.insert(0, history_string)
        clean_history = []
        for item in history:
            if item not in clean_history:
                clean_history.append(item)
        return list(clean_history[:10])

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

        self.valid = valid
        self.error = error

    def list_groups(self):
        return list(self.profile_groups.values())

    def get_group(self, name):
        return self.profile_groups.get(name, None)

    def to_dict(self):
        d = {}
        for name, group in self.profile_groups.items():
            d[name] = group.to_dict()
        return d

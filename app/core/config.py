from typing import List, Dict

from app.core import files

_default_access_key = 'access-key'


class Config:
    def __init__(self):
        self.profile_groups: Dict[ProfileGroup] = {}
        self.access_keys: List[str] = []  # TODO is this still needed?
        self.valid = False
        self.error = False

        self.mfa_shell_command = None
        self.default_access_key = None

        self.service_roles: Dict = {}

    def load_from_disk(self):
        config = files.load_config()
        self.mfa_shell_command = config.get('mfa_shell_command', None)
        access_key = config.get('default_access_key', _default_access_key)

        accounts = files.load_accounts()
        self.set_accounts(accounts, access_key)

        # TODO write test
        service_roles = files.load_service_roles()
        self.service_roles = service_roles

    def save_to_disk(self):
        files.save_accounts_file(self.to_dict())
        files.save_config_file({
            'mfa_shell_command': self.mfa_shell_command,
            'default_access_key': self.default_access_key,
        })

    def set_accounts(self, accounts: dict, access_key: str):
        if not access_key:
            self.default_access_key = _default_access_key
        else:
            self.default_access_key = access_key
        self.access_keys.append(self.default_access_key)

        for group_name, group_data in accounts.items():
            profile_group = ProfileGroup(name=group_name,
                                         group=group_data,
                                         default_access_key=self.default_access_key)
            self.profile_groups[group_name] = profile_group
            if profile_group.access_key:
                self.access_keys.append(profile_group.access_key)

        self.validate()

    def set_mfa_shell_command(self, mfa_shell_command: str):
        self.mfa_shell_command = mfa_shell_command

    # TODO write test
    def set_service_role(self, group: str, profile: str, role: str):
        if group not in self.service_roles:
            self.service_roles[group] = {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []
            }
        self.service_roles[group]['selected_profile'] = profile
        self.service_roles[group]['selected_role'] = role
        history = self._add_to_history(profile=profile, role=role, history=self.get_history(group))
        self.service_roles[group]['history'] = history
        files.save_service_roles(self.service_roles)

    # TODO write test
    def set_available_service_roles(self, group: str, profile: str, role_list: List[str]):
        if group not in self.service_roles:
            self.service_roles[group] = {
                'selected_profile': None,
                'selected_role': None,
                'available': {},
                'history': []
            }
        self.service_roles[group]['available'][profile] = role_list
        files.save_service_roles(self.service_roles)

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


class ProfileGroup:
    def __init__(self, name, group: dict, default_access_key: str):
        self.name: str = name
        self.team: str = group.get('team', None)
        self.region: str = group.get('region', None)
        self.color: str = group.get('color', None)
        self.default_access_key = default_access_key
        self.access_key: str = group.get('access_key', None)
        self.profiles: List[Profile] = []
        self.type: str = group.get('type', 'aws')  # only aws (default) & gcp as values are allowed

        for profile in group.get('profiles', []):
            self.profiles.append(Profile(self, profile))

    def validate(self) -> (bool, str):
        if not self.team:
            return False, f'{self.name} has no team'
        if not self.region:
            return False, f'{self.name} has no region'
        if not self.color:
            return False, f'{self.name} has no color'
        if self.access_key and not self.access_key.startswith('access-key'):
            return False, f'access-key {self.access_key} must have the prefix \"access-key\"'
        if self.type == "aws" and len(self.profiles) == 0:
            return False, f'aws "{self.name}" has no profiles'
        for profile in self.profiles:
            valid, error = profile.validate()
            if not valid:
                return valid, error
        return True, ''

    def list_profile_names(self):
        profile_list = []
        for profile in self.profiles:
            profile_list.append(profile.profile)
            if profile.default:
                profile_list.append('default')
        return profile_list

    def get_default_profile(self):
        return next((profile for profile in self.profiles if profile.default), None)

    def get_access_key(self):
        if self.access_key:
            return self.access_key
        return self.default_access_key

    def to_dict(self):
        result_dict = {
            'color': self.color,
            'team': self.team,
            'region': self.region,
            'profiles': [profile.to_dict() for profile in self.profiles],
        }
        if self.access_key and self.access_key != self.default_access_key:
            result_dict['access_key'] = self.access_key
        if self.type != "aws":
            result_dict["type"] = self.type
        return result_dict


class Profile:
    def __init__(self, group, profile: dict):
        self.group = group
        self.profile = profile.get('profile', None)
        self.account = profile.get('account', None)
        self.role = profile.get('role', None)
        self.default = profile.get('default', 'false') in ['True', 'true', True]
        self.source = profile.get('source', None)

    def validate(self) -> (bool, str):
        if not self.profile:
            return False, f'a profile in {self.group.name} has no profile'
        if not self.account:
            return False, f'a profile in {self.group.name} has no account'
        if not self.role:
            return False, f'a profile in {self.group.name} has no role'
        return True, ''

    def to_dict(self):
        d = {
            'profile': self.profile,
            'account': self.account,
            'role': self.role,
        }
        if self.source:
            d['source'] = self.source
        if self.default:
            d['default'] = True
        return d

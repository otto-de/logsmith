from typing import List, Dict

from app.core import files


class Config:
    def __init__(self):
        self.profile_groups: Dict[ProfileGroup] = {}
        self.valid = False
        self.error = False

        self.mfa_shell_command = None

    def load_from_disk(self):
        config = files.load_config()
        self.mfa_shell_command = config.get('mfa_shell_command', None)

        accounts = files.load_accounts()
        self.set_accounts(accounts)

    def save_to_disk(self):
        files.save_accounts_file(self.to_dict())
        files.save_config_file({
            'mfa_shell_command': self.mfa_shell_command,
        })

    def set_accounts(self, accounts: dict):
        for group_name, group_data in accounts.items():
            self.profile_groups[group_name] = ProfileGroup(group_name, group_data)
        self.validate()

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
    def __init__(self, name, group: dict):
        self.name: str = name
        self.team: str = group.get('team', None)
        self.region: str = group.get('region', None)
        self.color: str = group.get('color', None)
        self.profiles: List[Profile] = []
        for profile in group.get('profiles', []):
            self.profiles.append(Profile(self, profile))

    def validate(self) -> (bool, str):
        if not self.team:
            return False, f'{self.name} has no team'
        if not self.region:
            return False, f'{self.name} has no region'
        if not self.color:
            return False, f'{self.name} has no color'
        if len(self.profiles) == 0:
            return False, f'{self.name} has no profiles'
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

    def to_dict(self):
        profiles = []
        for profile in self.profiles:
            profiles.append(profile.to_dict())
        return {
            'color': self.color,
            'team': self.team,
            'region': self.region,
            'profiles': profiles,
        }


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

import logging
from typing import List, Optional

from app.core.profile import Profile

logger = logging.getLogger('logsmith')


class ProfileGroup:
    def __init__(self, name, group: dict, default_access_key: str, default_sso_session: str):
        self.name: str = name
        self.team: str = group.get('team', None)
        self.region: str = group.get('region', None)
        self.color: str = group.get('color', None)
        self.auth_mode: str = group.get('auth_mode', 'key')
        self.default_access_key = default_access_key
        self.access_key: str = group.get('access_key', None)
        self.default_sso_session = default_sso_session
        self.sso_session: str = group.get('sso_session', None)
        self.profiles: List[Profile] = []
        self.type: str = group.get('type', 'aws')  # only aws (default) & gcp as values are allowed
        self.script: str = group.get('script', None)  # only aws (default) & gcp as values are allowed

        self.service_profile: Optional[Profile] = None

        for profile_data in group.get('profiles', []):
            self.profiles.append(Profile(self, profile_data))

    def validate(self) -> (bool, str):
        if not self.team:
            return False, f'{self.name} has no team'
        if not self.region:
            return False, f'{self.name} has no region'
        if not self.color:
            return False, f'{self.name} has no color'
        if not self.auth_mode:
            return False, f'{self.name} has no auth_mode (either key or sso)'
        if self.access_key and not self.access_key.startswith('access-key'):
            return False, f'access-key {self.access_key} must have the prefix \"access-key\"'
        if self.sso_session and not self.sso_session.startswith('sso'):
            return False, f'sso session {self.sso_session} must have the prefix \"sso\"'
        if self.type == "aws" and len(self.profiles) == 0:
            return False, f'aws "{self.name}" has no profiles'
        for profile in self.profiles:
            valid, error = profile.validate()
            if not valid:
                return valid, error
        return True, ''

    def list_profile_names(self) -> List[str]:
        profile_list = []
        for profile in self.profiles:
            profile_list.append(profile.profile)
            if profile.default:
                profile_list.append('default')
            if self.service_profile:
                profile_list.append('service')
        return profile_list

    def get_profile_list(self) -> List[Profile]:
        profile_list = self.profiles.copy()
        if self.service_profile:
            profile_list.append(self.service_profile)
        return profile_list

    def get_profile(self, profile_name) -> Optional[Profile]:
        return next((profile for profile in self.profiles if profile.profile == profile_name), None)

    def get_default_profile(self) -> Optional[Profile]:
        return next((profile for profile in self.profiles if profile.default), None)

    def get_auth_mode(self) -> str:
        if self.auth_mode:
            return self.auth_mode
        return self.default_access_key
    
    def get_access_key(self) -> str:
        if self.access_key:
            return self.access_key
        return self.default_access_key
    
    def get_sso_session(self) -> str:
        if self.sso_session:
            return self.sso_session
        return self.default_sso_session

    def set_service_role_profile(self, source_profile_name, role_name) -> None:
        source_profile = self.get_profile(profile_name=source_profile_name)
        if not source_profile:
            logger.warning(f'source profile {source_profile_name} not found. Unset service_profile.')
            self.service_profile = None
        else:
            self.service_profile = Profile(self, {
                'profile': 'service',
                'account': source_profile.account,
                'role': role_name,
                'default': False,
                'source': source_profile_name
            })

    def to_dict(self) -> dict:
        result_dict = {
            'color': self.color,
            'team': self.team,
            'region': self.region,
            'script': self.script,
            'auth_mode': self.auth_mode,
            'profiles': [profile.to_dict() for profile in self.profiles],
        }
        if self.access_key and self.access_key != self.default_access_key:
            result_dict['access_key'] = self.access_key
        if self.sso_session and self.sso_session != self.default_sso_session:
            result_dict['sso_session'] = self.sso_session
        if self.type != "aws":
            result_dict["type"] = self.type
        return result_dict

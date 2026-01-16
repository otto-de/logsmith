import os
import sys
import time
from getpass import getpass

from app.aws import iam
from app.aws.regions import region_list
from app.core.core import Core
from app.core.result import Result
from core.profile_group import ProfileGroup

script_dir = os.path.dirname(os.path.realpath(__file__))
work_dir = os.getcwd()
C = "\x1b[1m"
CO = "\x1b[1m\x1b[38;5;208m"
CB = "\x1b[1m\x1b[34m"
CR = "\x1b[1m\x1b[31m"
CG = "\x1b[1m\x1b[32m"
CY = "\x1b[1m\x1b[93m"
CC = "\x1b[0m"


class Cli:
    def __init__(self):
        self.core = Core()

    def list(self):
        self._info('available profile groups:')
        profile_groups_list = self.core.config.list_groups()
        for group in profile_groups_list:
            print(group.name)

    def login(self, profile_group_name, region, oneshot=False):
        profile_group = self.core.config.get_group(profile_group_name)
        if not profile_group:
            self._error('profile group not found')
            self.list()
            sys.exit(1)

        if region is not None and region not in region_list:
            self._error(f'invalid region: {region}')
            self._warning('available regions:')
            self._print_regions()
            sys.exit(1)
            
        if profile_group.get_auth_mode() == 'key':
            self.login_with_key(profile_group=profile_group, region=region, oneshot=oneshot)
        elif profile_group.get_auth_mode() == 'sso':
            self.login_with_sso(profile_group=profile_group, region=region, oneshot=oneshot)
        result = Result()
        result.error('auth_mode was neither key or sso.')
        return result

    def login_with_key(self, profile_group: ProfileGroup, region: str, oneshot: bool):
        login_result = self.core.login_with_key(profile_group=profile_group, mfa_token=None)
        self._check_and_signal_error(login_result)
        if not login_result.was_success:
            mfa_token = self.ask_for_mfa_token()
            login_with_mfa_result = self.core.login_with_key(profile_group=profile_group, mfa_token=mfa_token)
            self._check_and_signal_error(login_with_mfa_result)

        if region:
            region_result = self.core.set_region(region=region)
            self._check_and_signal_error(region_result)
        self._info('login successful')

        if oneshot:
            sys.exit(0)

        seconds = 300
        self._info(f'start timer for {seconds}')
        time.sleep(seconds)
        self.login(profile_group.name, region)


    def login_with_sso(self, profile_group: ProfileGroup, region: str, oneshot: bool):
        login_result = self.core.login_with_sso(profile_group=profile_group)
        self._check_and_signal_error(login_result)
    
        if region:
            region_result = self.core.set_region(region=region)
            self._check_and_signal_error(region_result)
        self._info('login successful')

        if oneshot:
            sys.exit(0)

        seconds = 28800
        self._info(f'start timer for {seconds}')
        time.sleep(seconds)
        self.login(profile_group.name, region)

    def logout(self):
        logout_result = self.core.logout()
        self._check_and_signal_error(logout_result)

    def rotate_access_key(self, key_name):
        rotate_result = self.core.rotate_access_key(access_key=key_name, mfa_token=None)
        self._check_and_signal_error(rotate_result)

        if not rotate_result.was_success:
            mfa_token = self.ask_for_mfa_token()
            rotate_with_mfa_result = self.core.rotate_access_key(access_key=key_name, mfa_token=mfa_token)
            self._check_and_signal_error(rotate_with_mfa_result)
        self._info('key was successfully rotated')

    def set_access_key(self):
        print("Set Access Key")
        print("You will be ask to input the key Name, ID and Secret.")
        print("The Name must have the prefix 'access-key' and contains no spaces.")
        while True:
            key_name = input('Key Name: ')
            result = self.core.check_name('access-key', key_name)
            if result.was_error:
                self._error(result.error_message)
            else:
                break
        key_id = getpass(prompt='Key ID: ')
        key_secret = getpass(prompt='Secret Access Key: ')
        self.core.set_access_key(key_name=key_name, key_id=key_id, key_secret=key_secret)
        self._info('key was successfully set')

    def set_sso_session(self):
        print("Set SSO Session")
        print("You will be ask to input the Name, URL, Region and Scope of your SSO session.")
        print("The Name must have the prefix 'sso' and contain no spaces.")
        while True:
            sso_name = input('Session Name: ')
            result = self.core.check_name('sso', sso_name)
            if result.was_error:
                self._error(result.error_message)
            else:
                break
        sso_url = getpass(prompt='URL: ')
        sso_region = getpass(prompt='Region: ')
        sso_scopes = getpass(prompt='Scopes: ')
        self.core.set_sso_session(sso_name=sso_name, sso_url=sso_url, sso_region=sso_region, sso_scopes=sso_scopes)
        self._info('sso session was successfully set')

    def set_service_role(self, group, profile, role):
        self.core.config.save_selected_service_role(group_name=group, profile_name=profile, role_name=role)
        self._info('service role was successfully set')

    def list_service_roles(self, profile):
        result = iam.list_assumable_roles(source_profile=profile)
        if not self._check_and_signal_error(result):
            return

        self._info(f'assumable roles for profile: {profile}')
        for role in result.payload:
            print(role)

    def toggle(self, toggle, value):
        boolean = self._parse_boolean(value)
        if toggle == 'script':
            self.core.toggles.run_script = boolean
            self.core.toggles.save_toggles()
            return

        self._error('Could not set toggle')
        self._error('Valid toggles are: script')
        sys.exit(1)

    @staticmethod
    def ask_for_mfa_token():
        return input(f'mfa token: ')

    def _check_and_signal_error(self, result: Result):
        if result.was_error:
            self._error(result.error_message)
            sys.exit(1)
        return True

    @staticmethod
    def _info(s):
        print(f'{CG}{s}{CC}')

    @staticmethod
    def _error(s):
        print(f'{CR}{s}{CC}')

    @staticmethod
    def _warning(s):
        print(f'{CY}{s}{CC}')

    @staticmethod
    def _print_regions():
        for region in region_list:
            print(region)

    def _parse_boolean(self, value):
        if isinstance(value, str):
            value_lower = value.strip().lower()
            if value_lower == "true":
                return True
            elif value_lower == "false":
                return False

        self._error(f"Invalid value: {value}. Expected 'true' or 'false'.")
        sys.exit(1)

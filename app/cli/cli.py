import os
import sys
import time
from getpass import getpass

from aws.regions import region_list
from core.core import Core
from core.result import Result

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

        login_result = self.core.login(profile_group=profile_group,
                                       mfa_callback=self.ask_for_mfa_token)
        self._check_and_signal_error(login_result)

        if region:
            region_result = self.core.set_region(region=region)
            self._check_and_signal_error(region_result)
        self._info('login successful')

        if oneshot:
            return

        time.sleep(300)
        self.login(profile_group_name, region)

    def logout(self):
        logout_result = self.core.logout()
        self._check_and_signal_error(logout_result)

    def rotate_access_key(self):
        rotate_result = self.core.rotate_access_key()
        if not self._check_and_signal_error(rotate_result):
            return
        self._info('key was successfully rotated')

    def set_access_key(self):
        key_id = getpass(prompt='Key ID: ')
        access_key = getpass(prompt='Secret Access Key: ')
        self.core.set_access_key(key_id=key_id, access_key=access_key)
        self._info('key was successfully rotated')

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

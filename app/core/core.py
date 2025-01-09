import logging
from typing import Optional, Callable, List

from app.aws import credentials, iam
from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.result import Result
from app.gcp import login, config
from app.yubico import mfa

logger = logging.getLogger('logsmith')


class Core:
    def __init__(self):
        self.config: Config = Config()
        self.config.load_from_disk()
        self.active_profile_group: ProfileGroup = None
        self.empty_profile_group: ProfileGroup = ProfileGroup('logout', {}, '')
        self.region_override: str = None

    def login(self, profile_group: ProfileGroup, mfa_callback: Callable) -> Result:
        result = Result()
        logger.info(f'start login {profile_group.name}')
        self.active_profile_group = profile_group
        access_key = profile_group.get_access_key()

        access_key_result = credentials.check_access_key(access_key=access_key)
        if not access_key_result.was_success:
            return access_key_result

        session_result = credentials.check_session(access_key=access_key)
        if session_result.was_error:
            return session_result
        if not session_result.was_success:
            renew_session_result = self._renew_session(access_key=access_key, mfa_callback=mfa_callback)
            if not renew_session_result.was_success:
                return renew_session_result

        user_name = credentials.get_user_name(access_key=access_key)
        role_result = credentials.fetch_role_credentials(user_name, profile_group)
        if not role_result.was_success:
            return role_result

        set_region_result = self.set_region(self.region_override)
        if not set_region_result.was_success:
            return set_region_result

        logger.info('login success')
        self._handle_support_files(profile_group)
        result.set_success()
        return result

    def login_gcp(self, profile_group: ProfileGroup) -> Result:
        result = Result()
        self.active_profile_group = profile_group
        logger.info('gcp login detected')

        # first login
        user_login = login.gcloud_auth_login()
        if user_login is None:
            result.error("gcloud auth login command failed")
            return result

        # second login for application default credentials
        adc_login = login.gcloud_auth_application_login()
        if adc_login is None:
            result.error("gcloud auth application-default login command failed")
            return result

        # set project
        config_project = config.set_default_project(project=profile_group.name)
        if config_project is None:
            result.error("config gcp project failed")
            return result

        # set region
        config_region = config.set_default_region(region=profile_group.region)
        if config_region is None:
            result.error("config gcp region failed")
            return result

        # set quota-project
        config_quota_project = config.set_default_quota_project(project=profile_group.name)
        if config_quota_project is None:
            result.error("config gcp quota-project failed")
            return result

        logger.info('login success')
        self._handle_support_files(profile_group)
        result.set_success()

        return result

    def logout(self):
        result = Result()
        logger.info(f'start logout')

        role_result = credentials.fetch_role_credentials(user_name='none', profile_group=self.empty_profile_group)
        if not role_result.was_success:
            return role_result

        config_result = credentials.write_profile_config(profile_group=self.empty_profile_group, region='')
        if not config_result.was_success:
            return config_result

        logger.info('logout success')
        result.set_success()
        return result

    def set_region(self, region: str) -> Result:
        self.region_override = region
        if not self.active_profile_group:
            result = Result()
            result.set_success()
            return result
        return credentials.write_profile_config(self.active_profile_group, self.get_region())

    def get_region(self) -> Optional[str]:
        if self.region_override:
            return self.region_override
        if self.active_profile_group:
            return self.active_profile_group.region
        return None

    def get_profile_group_list(self):
        return self.config.list_groups()

    def get_active_profile_color(self):
        return self.active_profile_group.color

    def rotate_access_key(self, key_name: str, mfa_callback: Callable) -> Result:
        result = Result()
        logger.info('initiate key rotation')

        logger.info('logout')
        self.logout()

        logger.info('check access key')
        access_key_result = credentials.check_access_key(access_key=key_name)
        if not access_key_result.was_success:
            return access_key_result

        logger.info('fetch session')
        session_result = credentials.check_session(access_key=key_name)
        if session_result.was_error:
            return session_result
        if not session_result.was_success:
            renew_session_result = self._renew_session(access_key=key_name, mfa_callback=mfa_callback)
            if not renew_session_result.was_success:
                return renew_session_result

        logger.info('create key')
        user = credentials.get_user_name(key_name)
        create_access_key_result = iam.create_access_key(user, key_name)
        if not create_access_key_result.was_success:
            return create_access_key_result

        logger.info('delete key')
        previous_access_key_id = credentials.get_access_key_id(key_name)
        delete_access_key_result = iam.delete_iam_access_key(user, key_name, previous_access_key_id)
        if not delete_access_key_result.was_success:
            return delete_access_key_result

        logger.info('save key')
        credentials.set_access_key(key_name=key_name,
                                   key_id=create_access_key_result.payload['AccessKeyId'],
                                   key_secret=create_access_key_result.payload['SecretAccessKey'])

        self.logout()
        result.set_success()
        return result

    def edit_config(self, config: Config) -> Result:
        result = Result()
        try:
            self.config = config
            self.config.save_to_disk()
        except Exception as error:
            logger.error(str(error), exc_info=True)
            result.error('could not save config')
            return result
        result.set_success()
        return result

    def set_service_role(self, profile: str, role: str) -> Result:
        result = Result()
        logger.info('set service role')
        self.config.set_service_role(group=self.active_profile_group.name, profile=profile, role=role)

        result.set_success()
        return result

    def set_available_service_roles(self, profile, role_list: List[str]):
        result = Result()
        logger.info('set available service roles')
        self.config.set_available_service_roles(group=self.active_profile_group.name, profile=profile, role_list=role_list)

        result.set_success()
        return result

    def _renew_session(self, access_key: str, mfa_callback: Callable) -> Result:
        logger.info('renew session')
        logger.info('get mfa from console')
        token = mfa.fetch_mfa_token_from_shell(self.config.mfa_shell_command)
        if not token:
            logger.info('get mfa from user')
            token = mfa_callback()
            if not token:
                result = Result()
                result.error('invalid mfa token')
                return result
        session_result = credentials.fetch_session_token(access_key=access_key, mfa_token=token)
        return session_result

    @staticmethod
    def _handle_support_files(profile_group: ProfileGroup):
        logger.info('handle support files')
        files.write_active_group_file(profile_group.name)

    @staticmethod
    def set_access_key(key_name: str, key_id: str, key_secret: str):
        credentials.set_access_key(key_name=key_name, key_id=key_id, key_secret=key_secret)

    @staticmethod
    def get_access_key_list():
        return credentials.get_access_key_list()

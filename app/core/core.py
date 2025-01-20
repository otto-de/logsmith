import logging
from typing import Optional, List

from app.aws import credentials, iam
from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.result import Result
from app.gcp import login, config
from app.shell import shell

logger = logging.getLogger('logsmith')


class Core:
    def __init__(self):
        self.config: Config = Config()
        self.config.initialize()
        self.active_profile_group: ProfileGroup = None
        self.empty_profile_group: ProfileGroup = ProfileGroup('logout', {}, '')
        self.region_override: str = None

    def login(self, profile_group: ProfileGroup, mfa_token: Optional[str]) -> Result:
        result = Result()
        logger.info(f'start login {profile_group.name} with token {mfa_token}')
        self.active_profile_group = profile_group
        access_key = profile_group.get_access_key()

        access_key_result = credentials.check_access_key(access_key=access_key)
        if not access_key_result.was_success:
            return access_key_result

        session_result = self._ensure_session(access_key=access_key, mfa_token=mfa_token)
        if not session_result.was_success:
            return session_result

        user_name = credentials.get_user_name(access_key=access_key)
        role_result = credentials.fetch_role_credentials(user_name, profile_group)
        if not role_result.was_success:
            return role_result

        set_region_result = self.set_region(self.region_override)
        if not set_region_result.was_success:
            return set_region_result

        logger.info('login success')
        self._handle_support_files(profile_group)

        run_script_result = self.run_script(profile_group)
        if not run_script_result.was_success:
            return run_script_result

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

        run_script_result = self.run_script(profile_group)
        if not run_script_result.was_success:
            return run_script_result

        result.set_success()
        return result

    def logout(self) -> Result:
        result = Result()
        logger.info(f'start logout')
        self.active_profile_group = None

        role_result = credentials.fetch_role_credentials(user_name='none', profile_group=self.empty_profile_group)
        if not role_result.was_success:
            return role_result

        config_result = credentials.write_profile_config(profile_group=self.empty_profile_group, region='')
        if not config_result.was_success:
            return config_result

        logger.info('logout success')
        result.set_success()
        return result

    def set_region(self, region: Optional[str]) -> Result:
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

    def get_profile_group_list(self) -> List[ProfileGroup]:
        return self.config.list_groups()

    def get_active_profile_color(self) -> str:
        return self.active_profile_group.color

    def rotate_access_key(self, access_key: str, mfa_token: Optional[str]) -> Result:
        result = Result()
        logger.info(f'initiate key rotation for {access_key} with token {mfa_token}')

        logger.info('logout before key rotation')
        self.logout()

        access_key_result = credentials.check_access_key(access_key=access_key)
        if not access_key_result.was_success:
            return access_key_result

        session_result = self._ensure_session(access_key=access_key, mfa_token=mfa_token)
        if not session_result.was_success:
            return session_result

        logger.info('create key')
        user = credentials.get_user_name(access_key)
        create_access_key_result = iam.create_access_key(user, access_key)
        if not create_access_key_result.was_success:
            return create_access_key_result

        logger.info('delete key')
        previous_access_key_id = credentials.get_access_key_id(access_key)
        delete_access_key_result = iam.delete_iam_access_key(user, access_key, previous_access_key_id)
        if not delete_access_key_result.was_success:
            return delete_access_key_result

        logger.info('save key')
        credentials.set_access_key(key_name=access_key,
                                   key_id=create_access_key_result.payload['AccessKeyId'],
                                   key_secret=create_access_key_result.payload['SecretAccessKey'])

        self.logout()
        result.set_success()
        return result

    def edit_config(self, new_config: Config) -> Result:
        result = Result()
        try:
            new_config.save_config()
            new_config.save_accounts()
            self.config.initialize()
            self.logout()
        except Exception as error:
            logger.error(str(error), exc_info=True)
            result.error('could not save config or accounts')
            return result
        result.set_success()
        return result

    def set_service_role(self, profile_name: str, role_name: str) -> Result:
        result = Result()
        logger.info('set service role')
        self.config.save_selected_service_role(group_name=self.active_profile_group.name,
                                               profile_name=profile_name,
                                               role_name=role_name)
        self.active_profile_group.set_service_role_profile(source_profile_name=profile_name,
                                                           role_name=role_name)

        result.set_success()
        return result

    def set_available_service_roles(self, profile, role_list: List[str]) -> Result:
        result = Result()
        logger.info('set available service roles')
        self.config.save_available_service_roles(group_name=self.active_profile_group.name,
                                                 profile_name=profile,
                                                 role_list=role_list)
        result.set_success()
        return result

    @staticmethod
    def run_script(profile_group: ProfileGroup) -> Result:
        result = Result()
        if not profile_group or not profile_group.script:
            result.set_success()
            return result

        logger.info('run script')
        if not files.file_exists(profile_group.script):
            result.error(f'{profile_group.script} not found')
            return result

        shell_output = shell.run(profile_group.script)
        if not shell_output:
            result.error('script failed')
            return result

        logger.info(f'script output:\n{shell_output}')
        result.set_success()
        return result

    @staticmethod
    def _ensure_session(access_key: str, mfa_token: Optional[str]) -> Result:
        result = Result()

        session_check_result = credentials.check_session(access_key=access_key)
        if not session_check_result.was_success and not mfa_token:
            return session_check_result
        if not session_check_result.was_success and mfa_token:
            session_fetch_result = credentials.fetch_session_token(access_key=access_key, mfa_token=mfa_token)
            if not session_fetch_result.was_success:
                return session_fetch_result

        result.set_success()
        return result

    @staticmethod
    def _handle_support_files(profile_group: ProfileGroup):
        logger.info('handle support files')
        files.write_active_group_file(profile_group.name)

    @staticmethod
    def set_access_key(key_name: str, key_id: str, key_secret: str) -> Result:
        return credentials.set_access_key(key_name=key_name, key_id=key_id, key_secret=key_secret)

    @staticmethod
    def get_access_key_list() -> list:
        return credentials.get_access_key_list()

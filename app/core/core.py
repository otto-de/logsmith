import logging
from typing import Optional, List

from app.aws import credentials, iam
from app.core import files
from app.core.config import Config, ProfileGroup
from app.core.result import Result
from app.core.toggles import Toggles
from app.gcp import login, config
from app.shell import shell

logger = logging.getLogger('logsmith')


class Core:
    def __init__(self):
        self.config: Config = Config()
        self.config.initialize()
        self.toggles: Toggles = Toggles()
        self.toggles.initialize()

        self.active_profile_group: ProfileGroup = None
        self.empty_profile_group: ProfileGroup = ProfileGroup('logout', {}, '', '', '')
        self.region_override: str = None
    
    ########################
    # ACCESS KEY LOGIN
    def login_with_key(self, profile_group: ProfileGroup, mfa_token: Optional[str]) -> Result:
        result = Result()
        logger.info(f'start key login {profile_group.name} with token {mfa_token}')
        self.active_profile_group = profile_group

        cleanup_resul = credentials.cleanup()
        if not cleanup_resul.was_success:
            return cleanup_resul

        access_key = profile_group.get_access_key()
        access_key_result = credentials.check_access_key(access_key=access_key)
        if not access_key_result.was_success:
            return access_key_result

        session_result = self._ensure_session(access_key=access_key, mfa_token=mfa_token)
        if not session_result.was_success:
            return session_result

        user_name = credentials.get_user_name(access_key=access_key)
        role_result = credentials.fetch_key_credentials(user_name, profile_group)
        if not role_result.was_success:
            return role_result

        if profile_group.service_profile is not None:
            service_profile_result = credentials.fetch_key_service_profile(profile_group)
            if not service_profile_result.was_success:
                return service_profile_result
        
        set_region_result = self.set_region(self.region_override)
        if not set_region_result.was_success:
            return set_region_result

        logger.info('key login success')
        self._handle_support_files(profile_group)

        if self.toggles.run_script:
            run_script_result = self.run_script(profile_group)
            if not run_script_result.was_success:
                return run_script_result

        result.set_success()
        return result
    
    ########################
    # SSO LOGIN
    def login_with_sso(self, profile_group: ProfileGroup) -> Result:
        result = Result()
        logger.info(f'start sso login {profile_group.name}')
        self.active_profile_group = profile_group
        
        cleanup_resul = credentials.cleanup()
        if not cleanup_resul.was_success:
            return cleanup_resul
 
        sso_result = credentials.fetch_sso_credentials(profile_group)
        if not sso_result.was_success:
            return sso_result
        
        if profile_group.service_profile is not None:
            service_profile_result = credentials.fetch_sso_service_profile(profile_group)
            if not service_profile_result.was_success:
                return service_profile_result

        set_region_result = self.set_region(self.region_override)
        if not set_region_result.was_success:
            return set_region_result

        logger.info('sso login success')
        self._handle_support_files(profile_group)

        if self.toggles.run_script:
            run_script_result = self.run_script(profile_group)
            if not run_script_result.was_success:
                return run_script_result

        result.set_success()
        return result
    
    ########################
    # GCP
    def login_gcp(self, profile_group: ProfileGroup) -> Result:
        result = Result()
        self.active_profile_group = profile_group
        logger.info('gcp login detected')

        # first login
        user_login_result = login.gcloud_auth_login()
        if not user_login_result.was_success:
            return user_login_result

        # second login for application default credentials
        adc_login_result = login.gcloud_auth_application_login()
        if not adc_login_result.was_success:
            return adc_login_result

        # set project
        set_project_result = config.set_default_project(project=profile_group.name)
        if not set_project_result.was_success:
            return set_project_result

        # set region
        config_region_result = config.set_default_region(region=profile_group.region)
        if not config_region_result.was_success:
            return config_region_result
        
        # set quota-project
        config_region_result = config.set_default_quota_project(project=profile_group.name)
        if not config_region_result.was_success:
            return config_region_result

        logger.info('login success')
        self._handle_support_files(profile_group)

        run_script_result = self.run_script(profile_group)
        if not run_script_result.was_success:
            return run_script_result

        result.set_success()
        return result

    ########################
    # LOGOUT
    def logout(self) -> Result:
        result = Result()
        logger.info(f'start logout')
        self.active_profile_group = None

        cleanup_result = credentials.cleanup()
        if not cleanup_result.was_success:
            return cleanup_result
        
        
        sso_logout_result = credentials.sso_logout()
        if not sso_logout_result.was_success:
            return sso_logout_result

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

    def run_script(self, profile_group: ProfileGroup) -> Result:
        result = Result()
        if not profile_group or not profile_group.script:
            result.set_success()
            return result

        script_path = profile_group.script
        script_path = files.replace_home_variable(script_path)

        logger.info(f'run script: {script_path}')
        if not files.file_exists(script_path):
            result.error(f'{script_path} not found')
            return result

        script_result = shell.run(command=script_path, timeout=60)
        if not script_result.was_success:
            return script_result
        
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
    def set_sso_session(sso_name: str, sso_url: str, sso_region: str, sso_scopes: str) -> Result:
        return credentials.set_sso_session(sso_name=sso_name, sso_url=sso_url, sso_region=sso_region, sso_scopes=sso_scopes)

    @staticmethod
    def get_access_key_list() -> list:
        return credentials.get_access_key_list()
    
    @staticmethod
    def get_sso_sessions_list() -> list:
        return credentials.get_sso_sessions_list()

    @staticmethod
    def check_name(prefix: str, name: str) -> Result:
        result = Result()
        if not name.startswith(prefix):
            result.error(f"'{name}' must start with {prefix}")
            return result
        if ' ' in name:
            result.error(f"'{name}' must not contain spaces")
            return result
        result.set_success()
        return result
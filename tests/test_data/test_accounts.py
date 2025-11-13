from app.core.profile_group import ProfileGroup


def get_default_test_accounts() -> dict:
    return {
        'development': {
            'color': '#388E3C',
            'team': 'awesome-team',
            'region': 'us-east-1',
            'profiles': [
                {
                    'profile': 'developer',
                    'account': '123495678901',
                    'role': 'developer',
                    'default': 'true',
                },
                {
                    'profile': 'readonly',
                    'account': '012349567890',
                    'role': 'readonly',
                }
            ]
        },
        'live': {
            'color': '#388E3C',
            'team': 'awesome-team',
            'region': 'us-east-1',
            'access_key': 'access-key-123',
            'script': './some-script.sh',
            'profiles': [
                {
                    'profile': 'admin',
                    'account': '9876543210',
                    'role': 'admin',
                    'default': 'true',
                },
                {
                    'profile': 'readonly',
                    'account': '0000000000',
                    'role': 'readonly',
                }
            ]
        },
        'gcp-project-dev': {
            'color': '#FF0000',
            'team': 'another-team',
            'region': 'europe-west1',
            'type': 'gcp',
            'profiles': [],  # this will be automatically added
        }
    }
    
def get_test_accounts__mixed_auth_modes() -> dict:
    return {
        'development': {
            'color': '#388E3C',
            'team': 'awesome-team',
            'region': 'us-east-1',
            'auth_mode': 'key',
            'access_key': 'access-key-123',
            'profiles': [
                {
                    'profile': 'developer',
                    'account': '123495678901',
                    'role': 'developer',
                    'default': 'true',
                },
                {
                    'profile': 'readonly',
                    'account': '012349567890',
                    'role': 'readonly',
                }
            ]
        },
        'live': {
            'color': '#388E3C',
            'team': 'awesome-team',
            'region': 'us-east-1',
            'auth_mode': 'sso',
            'sso_session': 'sso-123',
            'script': './some-script.sh',
            'profiles': [
                {
                    'profile': 'admin',
                    'account': '9876543210',
                    'role': 'admin',
                    'default': 'true',
                },
                {
                    'profile': 'readonly',
                    'account': '0000000000',
                    'role': 'readonly',
                }
            ]
        },
        'gcp-project-dev': {
            'color': '#FF0000',
            'team': 'another-team',
            'region': 'europe-west1',
            'type': 'gcp',
            'profiles': [],  # this will be automatically added
        }
    }


def get_test_accounts__minimal() -> dict:
    return {
        'development': {
            'color': '#388E3C',
            'team': 'awesome-team',
            'region': 'us-east-1',
            'profiles': [
                {
                    'profile': 'developer',
                    'account': '123495678901',
                    'role': 'developer',
                    'default': 'true',
                },
            ]
        }
    }


def get_test_group():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'script': './some-script.sh',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
                'default': 'true',
            }
        ]
    }
    
def get_test_group__with_sso():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'auth_mode': 'sso',
        'sso_session': 'specific-sso-session',
        'script': './some-script.sh',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
                'default': 'true',
            }
        ]
    }
    
def get_test_group__with_sso__no_default():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'auth_mode': 'sso',
        'sso_session': 'specific-sso-session',
        'script': './some-script.sh',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
            }
        ]
    }    
    
def get_test_group__with_sso__chain_assume():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'auth_mode': 'sso',
        'sso_session': 'specific-sso-session',
        'script': './some-script.sh',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'pipeline',
                'account': '012345678901',
                'role': 'pipeline',
                'source': 'developer'
            }
        ]
    }
    

def get_test_group__with_key():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'auth_mode': 'key',
        'access_key': 'specific-access-key',
        'script': './some-script.sh',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
                'default': 'true',
            }
        ]
    }


def get_test_group_with_specific_access_key():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'access_key': 'specific-access-key',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
                'default': 'true',
            }
        ]
    }
    
def get_test_group_with_specific_sso_session():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'sso_session': 'specific-sso-session',
        'auth_mode': 'sso',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly',
                'default': 'true',
            }
        ]
    }


def get_test_group_no_default():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'readonly',
                'account': '012345678901',
                'role': 'readonly'
            }
        ]
    }


def get_test_group_chain_assume():
    return {
        'color': '#388E3C',
        'team': 'awesome-team',
        'region': 'us-east-1',
        'profiles': [
            {
                'profile': 'developer',
                'account': '123456789012',
                'role': 'developer',
            },
            {
                'profile': 'service',
                'account': '012345678901',
                'role': 'service',
                'source': 'developer'
            }
        ]
    }


def get_test_profile():
    return {
        'profile': 'readonly',
        'account': '123456789012',
        'role': 'readonly-role',
        'default': 'true',
    }


def get_test_profile_no_default():
    return {
        'profile': 'readonly',
        'account': '123456789012',
        'role': 'readonly-role',
    }


def get_test_profile_with_source():
    return {
        'profile': 'readonly',
        'account': '123456789012',
        'role': 'readonly-role',
        'source': 'some-source'
    }


def get_test_profile_group(include_service_role=False) -> ProfileGroup:
    profile_group = ProfileGroup('test', get_test_group(), 'some-access-key', 'some-sso-session')
    if include_service_role:
        profile_group.set_service_role_profile('developer', 'dummy')
    return profile_group

def get_test_profile_group_key(include_service_role=False) -> ProfileGroup:
    profile_group =  ProfileGroup('test', get_test_group__with_key(), 'some-access-key', 'some-sso-session')
    if include_service_role:
        profile_group.set_service_role_profile('developer', 'dummy')
    return profile_group

def get_test_profile_group_sso(include_service_role=False) -> ProfileGroup:
    profile_group =  ProfileGroup('test', get_test_group__with_sso(), 'some-access-key', 'some-sso-session')
    if include_service_role:
        profile_group.set_service_role_profile('developer', 'dummy')
    return profile_group

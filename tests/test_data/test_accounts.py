def get_test_accounts() -> dict:
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
            'profiles': [
                {
                    'profile': 'developer',
                    'account': '123456789012',
                    'role': 'developer',
                    'default': 'true',
                },
                {
                    'profile': 'readonly',
                    'account': '012345678901',
                    'role': 'readonly',
                }
            ]
        },
        'gcp-project-dev': {
            'color': '#FF0000',
            'team': 'another-team',
            'region': 'europe-west1',
            'type': 'gcp',
        }
    }


def get_test_group():
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

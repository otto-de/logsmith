from app.core.profile import Profile


def generate_session_name(key_name: str) -> str:
    return f'session-token-{key_name}'

def is_positive_int(value) -> bool:
    try:
        s = str(value).strip()
        return s.isdigit() and int(s) >= 0
    except Exception:
        return False


def use_as_default(profile: Profile, override: str | None):
    if override and profile.profile == override:
        return True
    if not override and profile.default:
        return True
    return False
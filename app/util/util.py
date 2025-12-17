def generate_session_name(key_name: str) -> str:
    return f'session-token-{key_name}'

def is_positive_int(value) -> bool:
    try:
        s = str(value).strip()
        return s.isdigit() and int(s) >= 0
    except Exception:
        return False

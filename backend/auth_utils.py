import bcrypt


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password[:72].encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def validate_password(password: str) -> tuple:
    """校验密码强度。返回 (is_valid, message)"""
    if len(password) < 6 or len(password) > 20:
        return False, "密码长度需为 6-20 位"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not has_letter or not has_digit:
        return False, "密码需要同时包含字母与数字"
    return True, ""

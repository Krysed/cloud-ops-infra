import bcrypt

from .cache import get_redis_client
from .db import get_user_by_email


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_user(email: str, password: str) -> int | None:
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode(), user["hashed_password"].encode()):
        return user["id"]
    return None

def logout_user(user_id: int) -> bool:
    redis = get_redis_client()
    session_key = f"session:{user_id}"
    if redis.exists(session_key):
        redis.delete(session_key)
        return True
    return False

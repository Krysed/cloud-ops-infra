import re

import bcrypt

from .cache import get_redis_client
from .db import get_user_by_email


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def is_password_valid(password: str) -> bool:
    if len(password) < 6:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

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

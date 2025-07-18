import re
import json
import secrets
from datetime import datetime, timedelta, timezone

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

def create_session(user_id: int) -> str:
    session_token = secrets.token_urlsafe(32)
    redis = get_redis_client()
    now = datetime.now(timezone.utc)
    session_data = {
        "user_id": user_id,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat()
    }
    redis.setex(f"session:{session_token}", 604800, json.dumps(session_data))
    return session_token

def get_session_user(session_token: str) -> dict | None:
    if not session_token:
        return None
    
    redis = get_redis_client()
    session_data = redis.get(f"session:{session_token}")
    if not session_data:
        return None
    
    try:
        session = json.loads(session_data)
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            redis.delete(f"session:{session_token}")
            return None
        return session
    except (json.JSONDecodeError, KeyError, ValueError):
        return None

def login_user(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode(), user["hashed_password"].encode()):
        session_token = create_session(user["id"])
        return {
            "user_id": user["id"],
            "email": user["email"],
            "session_token": session_token
        }
    return None

def logout_user(session_token: str) -> bool:
    if not session_token:
        return False
    
    redis = get_redis_client()
    session_key = f"session:{session_token}"
    if redis.exists(session_key):
        redis.delete(session_key)
        return True
    return False

from core import db, security
from fastapi import HTTPException


def register_user(name: str, email: str, password: str) -> int:
    if db.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = security.hash_password(password)
    return db.create_user(name, email, hashed_pw)

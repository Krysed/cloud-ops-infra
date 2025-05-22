from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from core.db import get_db_connection
from core.cache import get_redis_client
import json

router = APIRouter()
db = get_db_connection()
cache = get_redis_client()
cursor = db.cursor()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/users")
async def get_users():
    cursor.execute(" SELECT * FROM users")
    users = cursor.fetchall()
    return users

@router.post("/submit")
async def submit(name: str = Form(...), email: str = Form(...)):
    cursor.execute(f"INSERT INTO users (name, email) VALUES ({name}, {email}) RETURNING id")
    user_id = cursor.fetchone()["id"]
    db.commit()

    user_data = {"id": user_id, "name": name, "email": email}
    cache.set(f"user: {user_id}")
    
    return RedirectResponse(url="/users", status_code=303)

@router.get("/user/{user_id}")
async def get_user(user_id: int):
    cached = cache.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    if user:
        cache.set(f"user: user_id", json.dumps(user))
    return user or {"error": "User not found"}

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from core.db import get_db_connection
from core.cache import get_redis_client
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")
db = get_db_connection()
cache = get_redis_client()
cursor = db.cursor()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/submit")
async def submit(name: str = Form(...), email: str = Form(...)):
    cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id", (name, email))
    user_id = cursor.fetchone()["id"]
    db.commit()

    user_data = {"id": user_id, "name": name, "email": email}
    cache.set(f"user: {user_id}", json.dumps(user_data))
    
    return RedirectResponse(url="/users", status_code=303)

@router.get("/user/{user_id}")
async def get_user(user_id: int):
    cached = cache.get(f"user:{user_id}", json.dumps(user))
    if cached:
        return json.loads(cached)
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id))
    user = cursor.fetchone()
    if user:
        cache.set(f"user: user_id", json.dumps(user))
    return user or {"error": "User not found"}


@router.get("/users")
def get_users_html(request: Request):
    cursor.execute("SELECT * FROM users")
    db_users = cursor.fetchall()
    users = [
        {
            "id": user["id"],
            "username": user.get("name") or user.get("username"),
            "email": user["email"]
        }
        for user in db_users
    ]
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.post("/seed")
async def seed_users():
    users = [
        ("Anna Kowalska", "anna.kowalska@example.com"),
        ("Jan Nowak", "jan.nowak@example.com"),
        ("Maja Majecka", "maja.majecka@example.com"),
        ("Krzysztof Kononowicz", "krzysztof.kononowicz@example.com"),
        ("Test Temp", "test.temp@example.com")
    ]
    for name, email in users:
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    db.commit()
    return {"status": "seeded", "rows": len(users)}

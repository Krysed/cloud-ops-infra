from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from core.logger import logger
from core.security import hash_password
from core.cache import get_redis_client
from core.db import (
    get_db_connection, 
    get_user_by_email, 
    create_user, 
    update_user_in_db, 
    delete_user_from_db, 
    create_posting_in_db, 
    update_posting_in_db, 
    delete_posting_from_db
)
import json

router = APIRouter()
api_router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.post("/submit")
async def submit(name: str = Form(...), surname: str = Form(...), username: str = Form(...), email: str = Form(...)):
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = create_user(name, surname, username, email, hashed_password=hash_password("user_password")) #TODO: <- Change this - hash_password("user_password")

    user_data = {"id": user_id, "name": name, "email": email}
    get_redis_client().set(f"user:{user_id}", json.dumps(user_data))
    return RedirectResponse(url=f"/api/user/{user_id}", status_code=303)

@api_router.get("/user/{user_id}")
async def get_user(user_id: int):
    cache = get_redis_client()
    cached = cache.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                cache.set(f"user:{user_id}", json.dumps(user))
                return user
            else:
                raise HTTPException(status_code=404, detail="User not found")

@router.put("/user/{user_id}")
async def update_user(
    user_id: int,
    name: str = Form(None),
    surname: str = Form(None),
    username: str = Form(None),
    email: str = Form(None),
):
    success = update_user_in_db(user_id, name, surname, username, email)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content={"message": "User updated successfully"})

@router.delete("/user/{user_id}")
async def delete_user(user_id: int):
    success = delete_user_from_db(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content={"message": "User deleted successfully"})

@router.get("/login")
async def login():
    pass

@router.get("/logout")
async def logout():
    pass

@router.post("/create_posting")
async def create_posting(
    title: str = Form(...),
    post_description: str = Form(...),
    category: str = Form(...),
    user_id: int = Form(...)
):
    posting_id = create_posting_in_db(title, post_description, category, user_id)
    return JSONResponse(content={"message": "Posting created", "id": posting_id})

@router.put("/update_posting")
async def update_posting(
    posting_id: int = Form(...),
    title: str = Form(None),
    category: str = Form(None),
    post_description: str = Form(None),
    status: str = Form(None)
):
    success = update_posting_in_db(posting_id, title, category, post_description)
    if not success:
        raise HTTPException(status_code=404, detail="Posting not found")
    return JSONResponse(content={"message": "Posting updated successfully"})

@router.delete("/delete_posting")
async def delete_posting(posting_id: int = Form(...)):
    success = delete_posting_from_db(posting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Posting not found")
    return JSONResponse(content={"message": "Posting deleted successfully"})

@router.get("/apply")
async def apply():
    pass

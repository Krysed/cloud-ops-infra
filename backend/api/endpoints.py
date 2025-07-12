from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from core.logger import logger
from core.security import hash_password, login_user, logout_user
from core.cache import get_redis_client
from core.utility import json_serializer
from core.db import (
    get_db_connection, 
    get_user_by_email, 
    create_user, 
    update_user_in_db, 
    delete_user_from_db, 
    create_posting_in_db, 
    update_posting_in_db, 
    delete_posting_from_db,
    apply_to_posting,
    get_applications_by_user,
    get_applications_by_posting,
    get_all_postings,
    get_posting_by_id,
    get_postings_by_user
)
import json

router = APIRouter()
api_router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.post("/users")
async def submit(name: str = Form(...), surname: str = Form(...), username: str = Form(...), email: str = Form(...)):
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = create_user(name, surname, username, email, hashed_password=hash_password("user_password")) #TODO: <- Change this - hash_password("user_password")

    user_data = {"id": user_id, "name": name, "email": email}
    get_redis_client().set(f"user:{user_id}", json.dumps(user_data))
    return RedirectResponse(url=f"/api/user/{user_id}", status_code=303)

@api_router.get("/users/{user_id}")
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
                cache.set(f"user:{user_id}", json.dumps(user, default=json_serializer))
                return user
            else:
                raise HTTPException(status_code=404, detail="User not found")

@api_router.put("/users/{user_id}")
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

@api_router.delete("/user/{user_id}")
async def delete_user(user_id: int):
    success = delete_user_from_db(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content={"message": "User deleted successfully"})

@api_router.post("/postings")
async def create_posting(
    title: str = Form(...),
    post_description: str = Form(...),
    category: str = Form(...),
    user_id: int = Form(...)
):
    posting_id = create_posting_in_db(title, post_description, category, user_id)
    return JSONResponse(content={"message": "Posting created", "id": posting_id})

@api_router.put("/postings")
async def update_posting(
    posting_id: int = Form(...),
    title: str = Form(None),
    category: str = Form(None),
    post_description: str = Form(None),
    status: str = Form(None)
):
    success = update_posting_in_db(posting_id, title, category, post_description, status)
    if not success:
        raise HTTPException(status_code=404, detail="Posting not found")
    return JSONResponse(content={"message": "Posting updated successfully"})

@api_router.delete("/postings")
async def delete_posting(posting_id: int = Form(...)):
    success = delete_posting_from_db(posting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Posting not found")
    return JSONResponse(content={"message": "Posting deleted successfully"})

@api_router.get("/postings")
async def api_get_all_postings():
    return get_all_postings()

@api_router.get("/postings/{posting_id}")
async def api_get_posting(posting_id: int):
    posting = get_posting_by_id(posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    return posting

@api_router.get("/postings/by_user/{user_id}")
async def api_get_postings_by_user(user_id: int):
    return get_postings_by_user(user_id)

@api_router.post("/applications")
async def apply(user_id: int = Form(...), posting_id: int = Form(...)):
    success = apply_to_posting(user_id, posting_id)
    if not success:
        raise HTTPException(status_code=400, detail="Application failed (already applied or posting not found)")
    return {"message": "Application submitted successfully"}

@api_router.get("/applications/by_user/{user_id}")
async def api_get_applications_by_user(user_id: int):
    return get_applications_by_user(user_id)

@api_router.get("/applications/by_posting/{posting_id}")
async def api_get_applications_by_posting(posting_id: int):
    return get_applications_by_posting(posting_id)

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    logger.info(f"Login attempt: {email}")
    user_id = login_user(email, password)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.post("/logout")
async def logout(user_id: int = Form(...)):
    logger.info(f"Logout attempt for user_id: {user_id}")
    success = logout_user(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed or user not logged in")
    return JSONResponse(content={"message": "Logout successful"})

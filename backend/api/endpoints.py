import json

from core.cache import get_redis_client
from core.db import (
    apply_to_posting,
    create_posting_in_db,
    create_user,
    delete_posting_from_db,
    delete_user_from_db,
    get_all_postings,
    get_applications_by_posting,
    get_applications_by_user,
    get_application_details,
    get_posting_analytics,
    get_posting_by_id,
    get_posting_with_public_stats,
    get_postings_by_user,
    get_public_postings,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_user_posting_stats,
    track_posting_view,
    update_application_status,
    update_posting_in_db,
    update_user_in_db,
)
from core.logger import logger
from core.security import get_session_user, hash_password, login_user, logout_user
from core.utility import json_serializer
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter()
api_router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@api_router.post("/users")
async def create_user_account(name: str = Form(...), surname: str = Form(...), username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        # Check if username and email are the same
        if username.lower() == email.lower():
            logger.info(f"Registration failed: Username and email cannot be the same - {username}")
            return RedirectResponse(url="/register.html?error=username_email_same", status_code=303)
        
        # Check if email already exists
        if get_user_by_email(email):
            logger.info(f"Registration failed for {email}: Email already in use")
            return RedirectResponse(url="/register.html?error=email_taken", status_code=303)
        
        # Check if username already exists
        if get_user_by_username(username):
            logger.info(f"Registration failed for {username}: Username already taken")
            return RedirectResponse(url="/register.html?error=username_taken", status_code=303)
        
        user_id = create_user(name, surname, username, email, hashed_password=hash_password(password))
        
        user_data = {"id": user_id, "name": name, "email": email}
        get_redis_client().set(f"user:{user_id}", json.dumps(user_data))
        logger.info(f"Account created successfully for user: {email}")
        return RedirectResponse(url="/login.html?success=account_created", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account creation failed for {email}: {str(e)}")
        return RedirectResponse(url="/register.html?error=server_error", status_code=303)

@api_router.get("/users/{user_id}")
async def get_user(user_id: int):
    cache = get_redis_client()
    cached = cache.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    user = get_user_by_id(user_id)
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

@api_router.delete("/users/{user_id}")
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
async def apply(
    request: Request,
    posting_id: int = Form(...), 
    message: str = Form(None), 
    cover_letter: str = Form(None)
):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    success = apply_to_posting(user_id, posting_id, message, cover_letter)
    if not success:
        raise HTTPException(status_code=400, detail="Application failed (already applied or posting not found)")
    return {"message": "Application submitted successfully"}

@api_router.get("/applications/by_user/{user_id}")
async def api_get_applications_by_user(user_id: int):
    return get_applications_by_user(user_id)

@api_router.get("/applications/by_posting/{posting_id}")
async def api_get_applications_by_posting(posting_id: int):
    return get_applications_by_posting(posting_id)

@api_router.get("/postings/public")
async def get_public_postings_endpoint():
    """Get all active postings with limited public information"""
    return get_public_postings()

@api_router.get("/postings/{posting_id}/view")
async def view_posting(posting_id: int, request: Request):
    """View a posting and track the view"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    user_id = session_data["user_id"] if session_data else None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Track the view
    track_posting_view(posting_id, user_id, ip_address, user_agent, session_token)
    
    # Get posting with public stats
    posting = get_posting_with_public_stats(posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    
    return posting

@api_router.get("/postings/my-postings")
async def get_my_postings(request: Request):
    """Get current user's postings"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    return get_postings_by_user(user_id)

@api_router.get("/postings/{posting_id}/analytics")
async def get_posting_analytics_endpoint(posting_id: int, request: Request):
    """Get comprehensive analytics for a posting (owner only)"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    analytics = get_posting_analytics(posting_id, user_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Posting not found or access denied")
    
    return analytics

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics for current user"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    return get_user_posting_stats(user_id)

@api_router.get("/applications/my-applications")
async def get_my_applications(request: Request):
    """Get current user's applications"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    return get_applications_by_user(user_id)

@api_router.get("/applications/{application_id}")
async def get_application_details_endpoint(application_id: int, request: Request):
    """Get application details (for owner or applicant)"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    application = get_application_details(application_id, user_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found or access denied")
    
    return application

@api_router.post("/applications/{application_id}/review")
async def review_application(
    application_id: int,
    request: Request,
    status: str = Form(...),
    reviewer_notes: str = Form(None)
):
    """Review an application (posting owner only)"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    
    # Verify that the user owns the posting for this application
    application = get_application_details(application_id, user_id)
    if not application or application["posting_owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate status
    valid_statuses = ["pending", "reviewed", "accepted", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    success = update_application_status(application_id, status, reviewer_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application status updated successfully"}

@api_router.post("/contact")
async def contact_form(full_name: str = Form(..., alias="full-name"), email: str = Form(...), message: str = Form(...)):
    logger.info(f"Contact form submission from: {email}")
    return JSONResponse(content={"message": "Thank you for your message! We'll get back to you soon."})

@api_router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        # Check if user is already logged in
        session_token = request.cookies.get("session_token")
        if session_token and get_session_user(session_token):
            logger.info("User already logged in, redirecting to data view")
            return RedirectResponse(url="/data-view.html", status_code=303)
        
        logger.info(f"Login attempt: {email}")
        result = login_user(email, password)
        if result is None:
            logger.info(f"Login failed for {email}: Invalid credentials")
            return RedirectResponse(url="/login.html?error=invalid_credentials", status_code=303)
        
        response = RedirectResponse(url="/data-view.html", status_code=303)
        response.set_cookie(
            key="session_token",
            value=result["session_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=604800  # 7 days
        )
        logger.info(f"Login successful for {email}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {email}: {str(e)}")
        return RedirectResponse(url="/login.html?error=server_error", status_code=303)

@api_router.post("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session_token")
    logger.info(f"Logout attempt with session token: {session_token}")
    logout_user(session_token)
    
    response = RedirectResponse(url="/index.html?success=logged_out", status_code=303)
    response.delete_cookie("session_token")
    return response

@api_router.get("/auth/status")
async def auth_status(request: Request):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if session_data:
        return JSONResponse(content={
            "authenticated": True,
            "user_id": session_data["user_id"]
        })
    else:
        return JSONResponse(content={"authenticated": False})

@api_router.get("/auth/buttons")
async def auth_buttons(request: Request):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if session_data:
        return JSONResponse(content={
            "authenticated": True,
            "action": "logout",
            "method": "POST",
            "url": "/api/logout",
            "text": "Logout",
            "icon": "bi-box-arrow-right"
        })
    else:
        return JSONResponse(content={
            "authenticated": False,
            "action": "login",
            "method": "GET",
            "url": "/login.html",
            "text": "Login",
            "icon": "bi-box-arrow-in-right"
        })

# Authentication-aware redirects
@router.get("/")
async def root(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token and get_session_user(session_token):
        return RedirectResponse(url="/data-view.html", status_code=302)
    return RedirectResponse(url="/index.html", status_code=302)

@router.get("/login")
async def login_redirect(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token and get_session_user(session_token):
        return RedirectResponse(url="/data-view.html", status_code=302)
    return RedirectResponse(url="/login.html", status_code=302)

@router.get("/register")
async def register_redirect(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token and get_session_user(session_token):
        return RedirectResponse(url="/data-view.html", status_code=302)
    return RedirectResponse(url="/register.html", status_code=302)

@router.get("/data-view")
async def data_view_redirect(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or not get_session_user(session_token):
        return RedirectResponse(url="/login.html", status_code=302)
    return RedirectResponse(url="/data-view.html", status_code=302)

@router.get("/profile")
async def profile_redirect(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or not get_session_user(session_token):
        return RedirectResponse(url="/login.html", status_code=302)
    return RedirectResponse(url="/profile.html", status_code=302)

@router.get("/contact")
async def contact_redirect():
    return RedirectResponse(url="/contact.html", status_code=302)

@router.get("/password-reset")
async def password_reset_redirect():
    return RedirectResponse(url="/password-reset.html", status_code=302)

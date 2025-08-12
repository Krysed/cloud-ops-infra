import json
from contextlib import suppress

from core.cache import get_redis_client
from core.db import (
    apply_to_posting,
    check_user_application_exists,
    create_posting_in_db,
    create_user,
    delete_posting_from_db,
    delete_user_from_db,
    get_all_postings,
    get_application_details,
    get_applications_by_posting,
    get_applications_by_user,
    get_posting_analytics,
    get_posting_by_hash,
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
from fastapi.responses import JSONResponse, RedirectResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter()
api_router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for Mimir to scrape"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
    request: Request,
    title: str = Form(...),
    post_description: str = Form(...),
    category: str = Form(...)
):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        return RedirectResponse(url="/login.html?error=auth_required", status_code=303)
    
    user_id = session_data["user_id"]
    create_posting_in_db(title, post_description, category, user_id)
    return RedirectResponse(url="/my-postings.html?success=posting_created", status_code=303)

@api_router.post("/postings/update")
async def update_posting(
    request: Request,
    posting_id: int = Form(...),
    title: str = Form(...),
    category: str = Form(...),
    post_description: str = Form(...),
    status: str = Form(...)
):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        return RedirectResponse(url="/login.html?error=auth_required", status_code=303)
    
    try:
        # Check if user owns this posting before updating
        user_id = session_data["user_id"]
        posting = get_posting_by_id(posting_id)
        
        if not posting or posting["user_id"] != user_id:
            return RedirectResponse(url="/my-postings.html?error=access_denied", status_code=303)
        
        success = update_posting_in_db(posting_id, title, category, post_description, status)
        if not success:
            return RedirectResponse(url="/my-postings.html?error=update_failed", status_code=303)
        
        return RedirectResponse(url="/my-postings.html?success=posting_updated", status_code=303)
    except Exception:
        return RedirectResponse(url="/my-postings.html?error=update_failed", status_code=303)

@api_router.get("/posting/{posting_id}/manage")
async def get_posting_for_edit(posting_id: int, request: Request):
    """Get posting data for editing (API endpoint)"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    posting = get_posting_by_id(posting_id)
    
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    
    # Check if user owns this posting
    if posting["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return posting data as JSON for frontend to consume
    return JSONResponse(content={
        "posting": {
            "id": posting["id"],
            "title": posting["title"],
            "category": posting["category"],
            "description": posting["description"],
            "status": posting.get("status", "open")
        }
    })

@api_router.delete("/postings")
async def delete_posting(posting_id: int = Form(...)):
    success = delete_posting_from_db(posting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Posting not found")
    return JSONResponse(content={"message": "Posting deleted successfully"})

@api_router.get("/postings")
async def api_get_all_postings():
    return get_all_postings()

@api_router.get("/postings/public")
async def get_public_postings_endpoint():
    """Get all active postings with limited public information"""
    try:
        postings = get_public_postings()
        return postings
    except Exception as e:
        logger.error(f"Error fetching public postings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch postings") from e

@api_router.get("/postings/my-postings")
async def get_my_postings(request: Request):
    """Get current user's postings with pre-rendered HTML"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    try:
        postings = get_postings_by_user(user_id)
        
        # Add formatted data for each posting - data processing only
        for posting in postings:
            posting["status"] = posting.get("status", "active")  # Provide status value
            posting["formatted_date"] = posting["created_at"].strftime("%m/%d/%Y") if posting.get("created_at") else ""
        
        return postings
    except Exception as e:
        logger.error(f"Error fetching user postings for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch your postings") from e

@api_router.get("/postings/by_user/{user_id}")
async def api_get_postings_by_user(user_id: int):
    return get_postings_by_user(user_id)

@api_router.get("/postings/{posting_identifier}")
async def api_get_posting(posting_identifier: str):
    # Try to parse as integer first (for backward compatibility)
    try:
        posting_id = int(posting_identifier)
        posting = get_posting_by_id(posting_id)
    except ValueError:
        # If not an integer, treat as hash
        posting = get_posting_by_hash(posting_identifier)
    
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    return posting

@api_router.post("/applications")
async def apply(
    request: Request,
    posting_id: int = Form(...), 
    message: str = Form(None), 
    cover_letter: str = Form(None)
):
    logger.info(f"Application received for posting {posting_id}, message: {message[:50] if message else 'None'}")
    
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        logger.warning(f"Unauthenticated application attempt for posting {posting_id}")
        return RedirectResponse(url="/login.html?error=auth_required", status_code=303)
    
    user_id = session_data["user_id"]
    
    try:
        result = apply_to_posting(user_id, posting_id, message, cover_letter)
        
        # Get posting hash for proper redirect
        posting = get_posting_by_id(posting_id)
        if not posting:
            return RedirectResponse(url="/my-postings.html?error=posting_not_found", status_code=303)
        
        posting_hash = posting["hash"]
        
        if not result["success"]:
            error_param = result["error"] if result["error"] else "application_failed"
            logger.warning(f"Application failed for posting {posting_id}, user {user_id}: {result['error']}")
            return RedirectResponse(url=f"/posting-detail.html?hash={posting_hash}&error={error_param}", status_code=303)
        
        logger.info(f"Application successful for posting {posting_id}, user {user_id}")
        return RedirectResponse(url=f"/posting-detail.html?hash={posting_hash}&success=application_submitted", status_code=303)
        
    except Exception:
        # Log the error and redirect with generic error
        return RedirectResponse(url="/my-postings.html?error=application_failed", status_code=303)

@api_router.get("/applications/by_user/{user_id}")
async def api_get_applications_by_user(user_id: int):
    return get_applications_by_user(user_id)

@api_router.get("/applications/by_posting/{posting_id}")
async def api_get_applications_by_posting(posting_id: int):
    return get_applications_by_posting(posting_id)

@api_router.get("/postings/view/{posting_hash}")
async def view_posting(posting_hash: str, request: Request):
    """View a posting and track the view - return comprehensive data"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    # Get posting by hash first (fallback to treating as ID for compatibility)
    posting = None
    with suppress(Exception):
        # Try hash lookup first
        posting = get_posting_by_hash(posting_hash)
    
    if not posting:
        # Fallback to ID lookup for existing functionality
        try:
            posting_id = int(posting_hash)
            posting = get_posting_by_id(posting_id)
        except ValueError:
            pass
    
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    
    user_id = session_data["user_id"] if session_data else None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Track the view using posting ID
    track_posting_view(posting["id"], user_id, ip_address, user_agent, session_token)
    
    # Get posting with public stats
    posting_with_stats = get_posting_with_public_stats(posting["id"])
    if not posting_with_stats:
        posting_with_stats = posting
    
    # Add user context information
    is_authenticated = bool(session_data)
    is_owner = False
    can_apply = False
    has_applied = False
    
    if is_authenticated:
        is_owner = posting_with_stats["user_id"] == session_data["user_id"]
        if not is_owner:
            has_applied = check_user_application_exists(session_data["user_id"], posting_with_stats["id"])
            can_apply = not has_applied
    
    # Return enhanced data for frontend
    return {
        "posting": posting_with_stats,
        "is_authenticated": is_authenticated,
        "is_owner": is_owner,
        "can_apply": can_apply,
        "has_applied": has_applied,
        "user": session_data
    }

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

# HTML Page Routes with Server-Side Logic
@api_router.get("/data-view")
async def data_view_page(request: Request):
    """Serve data view page with server-side rendered postings"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    # Get all public postings
    postings = get_public_postings()
    
    # Mark which postings belong to current user
    current_user_id = session_data["user_id"] if session_data else None
    for posting in postings:
        posting["is_own"] = posting["user_id"] == current_user_id if current_user_id else False
        posting["can_apply"] = session_data and not posting["is_own"]
    
    # Return redirect to static page with data in session or query params
    # For now, redirect to static page - we'll enhance this
    return RedirectResponse(url="/data-view.html", status_code=302)

@api_router.get("/posting/{posting_id}")
async def view_posting_page(posting_id: int, request: Request):
    """Serve individual posting view page"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    # Track the view and get posting details
    user_id = session_data["user_id"] if session_data else None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Track the view
    track_posting_view(posting_id, user_id, ip_address, user_agent, session_token)
    
    # Get posting with stats
    posting = get_posting_with_public_stats(posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    
    # For now, redirect to a posting detail page with ID
    return RedirectResponse(url=f"/posting-detail.html?id={posting_id}", status_code=302)

@api_router.get("/posting/{posting_hash}/page")
async def posting_detail_page(posting_hash: str, request: Request):
    """Return posting data as JSON for frontend to render"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    # Get posting by hash
    posting = get_posting_by_hash(posting_hash)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    
    # Track the view
    user_id = session_data["user_id"] if session_data else None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    track_posting_view(posting["id"], user_id, ip_address, user_agent, session_token)
    
    # Get updated posting with stats
    posting_with_stats = get_posting_with_public_stats(posting["id"])
    if not posting_with_stats:
        posting_with_stats = posting
    
    # Determine user context and actions
    is_authenticated = bool(session_data)
    is_owner = False
    can_apply = False
    
    if is_authenticated:
        is_owner = posting_with_stats["user_id"] == session_data["user_id"]
        can_apply = not is_owner
    
    return {
        "posting": posting_with_stats,
        "is_authenticated": is_authenticated,
        "is_owner": is_owner,
        "can_apply": can_apply,
        "user": session_data
    }

@api_router.get("/posting-detail")
async def posting_detail_static():
    """Serve posting detail page"""
    return RedirectResponse(url="/posting-detail.html", status_code=302)

@api_router.get("/postings-data")
async def get_postings_data(request: Request):
    """API endpoint to get postings with user context"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    # Get all public postings
    postings = get_public_postings()
    
    # Add user context to each posting - business logic only
    current_user_id = session_data["user_id"] if session_data else None
    for posting in postings:
        posting["is_own"] = posting["user_id"] == current_user_id if current_user_id else False
        posting["can_apply"] = session_data and not posting["is_own"]
        posting["is_authenticated"] = bool(session_data)
    
    return {
        "postings": postings,
        "user": session_data,
        "is_authenticated": bool(session_data)
    }

@api_router.post("/contact")
async def contact_form(request: Request, full_name: str = Form(..., alias="full-name"), email: str = Form(...), message: str = Form(...)):
    logger.info(f"Contact form submission from: {email}")
    # In a real app, save to database or send email here
    return RedirectResponse(url="/contact.html?success=message_sent", status_code=303)

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
            "user": session_data
        })
    else:
        return JSONResponse(content={"authenticated": False})

@api_router.get("/profile/data")
async def get_profile_data(request: Request):
    """Get complete profile data with stats and activity"""
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = session_data["user_id"]
    
    # Get user details
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user postings and applications for stats
    postings = get_postings_by_user(user_id)
    applications = get_applications_by_user(user_id)
    
    # Calculate stats - business logic only
    total_postings = len(postings) if postings else 0
    total_applications = len(applications) if applications else 0
    
    # Provide structured data for frontend to render
    recent_postings = postings[:3] if postings else []
    recent_applications = applications[:3] if applications else []
    
    return {
        "user": user,
        "stats": {
            "total_postings": total_postings,
            "total_applications": total_applications,
            "member_since": user.get("created_at", "Jan 2024")
        },
        "recent_postings": recent_postings,
        "recent_applications": recent_applications
    }

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

@api_router.get("/navigation")
async def get_navigation(request: Request):
    session_token = request.cookies.get("session_token")
    session_data = get_session_user(session_token)
    
    if session_data:
        # Authenticated user navigation
        nav_items = [
            {"url": "/data-view.html", "text": "All Postings", "path_check": "/data-view"},
            {"url": "/create-posting.html", "text": "Create Posting", "path_check": "/create-posting"},
            {"url": "/my-postings.html", "text": "My Postings", "path_check": "/my-postings"},
            {"url": "/contact.html", "text": "Contact", "path_check": "/contact"},
            {"url": "/profile.html", "text": "Profile", "path_check": "/profile"}
        ]
    else:
        # Unauthenticated user navigation
        nav_items = [
            {"url": "/data-view.html", "text": "View Postings", "path_check": "/data-view"},
            {"url": "/login.html", "text": "Login", "path_check": "/login"},
            {"url": "/register.html", "text": "Register", "path_check": "/register"},
            {"url": "/contact.html", "text": "Contact", "path_check": "/contact"}
        ]
    
    return JSONResponse(content={
        "authenticated": bool(session_data),
        "nav_items": nav_items
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

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# backend/ uses bare module names ('from core.* import ...'), so add it to path
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import api.endpoints as ep  # noqa: E402

_app = FastAPI()
_app.include_router(ep.router)
_app.include_router(ep.api_router)

MOCK_SESSION = {"user_id": 1, "username": "testuser", "email": "test@example.com"}
MOCK_USER = {
    "id": 1,
    "name": "Test",
    "surname": "User",
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "Jan 2024",
}
MOCK_POSTING = {
    "id": 1,
    "user_id": 1,
    "title": "Test Job",
    "category": "IT",
    "description": "A test posting",
    "status": "open",
    "hash": "abc123",
    "created_at": None,
}
MOCK_APPLICATION = {
    "id": 1,
    "user_id": 2,
    "posting_id": 1,
    "posting_owner_id": 1,
    "message": "I am interested",
    "status": "pending",
}


@pytest.fixture
def client():
    return TestClient(_app, raise_server_exceptions=True)


@pytest.fixture
def no_session():
    with patch("api.endpoints.get_session_user", return_value=None):
        yield


@pytest.fixture
def with_session():
    with patch("api.endpoints.get_session_user", return_value=MOCK_SESSION):
        yield


# ── Health ──────────────────────────────────────────────────────────────────

def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_metrics_endpoint(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]


# ── Auth status / buttons / navigation ──────────────────────────────────────

def test_auth_status_unauthenticated(client, no_session):
    r = client.get("/api/auth/status")
    assert r.status_code == 200
    assert r.json() == {"authenticated": False}


def test_auth_status_authenticated(client, with_session):
    r = client.get("/api/auth/status", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["authenticated"] is True
    assert r.json()["user"] == MOCK_SESSION


def test_auth_buttons_unauthenticated(client, no_session):
    r = client.get("/api/auth/buttons")
    assert r.status_code == 200
    assert r.json()["authenticated"] is False
    assert r.json()["action"] == "login"


def test_auth_buttons_authenticated(client, with_session):
    r = client.get("/api/auth/buttons", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["authenticated"] is True
    assert r.json()["action"] == "logout"


def test_navigation_unauthenticated(client, no_session):
    r = client.get("/api/navigation")
    assert r.status_code == 200
    data = r.json()
    assert data["authenticated"] is False
    assert any(item["path_check"] == "/login" for item in data["nav_items"])


def test_navigation_authenticated(client, with_session):
    r = client.get("/api/navigation", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["authenticated"] is True
    assert any(item["path_check"] == "/my-postings" for item in data["nav_items"])


# ── Login / Logout ───────────────────────────────────────────────────────────

def test_login_success(client):
    mock_result = {"session_token": "tok123"}
    with patch("api.endpoints.get_session_user", return_value=None), \
         patch("api.endpoints.login_user", return_value=mock_result):
        r = client.post(
            "/api/login",
            data={"email": "user@example.com", "password": "secret"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert r.headers["location"] == "/data-view.html"
    assert "session_token" in r.cookies


def test_login_invalid_credentials(client):
    with patch("api.endpoints.get_session_user", return_value=None), \
         patch("api.endpoints.login_user", return_value=None):
        r = client.post(
            "/api/login",
            data={"email": "user@example.com", "password": "wrong"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "invalid_credentials" in r.headers["location"]


def test_login_already_authenticated(client, with_session):
    r = client.post(
        "/api/login",
        data={"email": "user@example.com", "password": "secret"},
        cookies={"session_token": "tok"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/data-view.html"


def test_logout(client, with_session):
    with patch("api.endpoints.logout_user") as mock_logout:
        r = client.post(
            "/api/logout",
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "logged_out" in r.headers["location"]
    mock_logout.assert_called_once_with("tok")


# ── Users ────────────────────────────────────────────────────────────────────

def test_get_user_from_cache(client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"id": 1, "name": "Test", "email": "t@t.com"}'
    with patch("api.endpoints.get_redis_client", return_value=mock_redis):
        r = client.get("/api/users/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_get_user_from_db(client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    with patch("api.endpoints.get_redis_client", return_value=mock_redis), \
         patch("api.endpoints.get_user_by_id", return_value=MOCK_USER):
        r = client.get("/api/users/1")
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


def test_get_user_not_found(client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    with patch("api.endpoints.get_redis_client", return_value=mock_redis), \
         patch("api.endpoints.get_user_by_id", return_value=None):
        r = client.get("/api/users/999")
    assert r.status_code == 404


def test_update_user_success(client):
    with patch("api.endpoints.update_user_in_db", return_value=True):
        r = client.put("/api/users/1", data={"name": "Updated"})
    assert r.status_code == 200
    assert r.json()["message"] == "User updated successfully"


def test_update_user_not_found(client):
    with patch("api.endpoints.update_user_in_db", return_value=False):
        r = client.put("/api/users/999", data={"name": "Ghost"})
    assert r.status_code == 404


def test_delete_user_success(client):
    with patch("api.endpoints.delete_user_from_db", return_value=True):
        r = client.delete("/api/users/1")
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"


def test_delete_user_not_found(client):
    with patch("api.endpoints.delete_user_from_db", return_value=False):
        r = client.delete("/api/users/999")
    assert r.status_code == 404


def test_create_user_success(client):
    mock_redis = MagicMock()
    with patch("api.endpoints.get_user_by_email", return_value=None), \
         patch("api.endpoints.get_user_by_username", return_value=None), \
         patch("api.endpoints.create_user", return_value=42), \
         patch("api.endpoints.hash_password", return_value="hashed"), \
         patch("api.endpoints.get_redis_client", return_value=mock_redis):
        r = client.post(
            "/api/users",
            data={
                "name": "New", "surname": "User", "username": "newuser",
                "email": "new@example.com", "password": "pass",
            },
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "account_created" in r.headers["location"]


def test_create_user_email_taken(client):
    with patch("api.endpoints.get_user_by_email", return_value=MOCK_USER):
        r = client.post(
            "/api/users",
            data={
                "name": "X", "surname": "Y", "username": "xy",
                "email": "existing@example.com", "password": "pass",
            },
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "email_taken" in r.headers["location"]


def test_create_user_username_taken(client):
    with patch("api.endpoints.get_user_by_email", return_value=None), \
         patch("api.endpoints.get_user_by_username", return_value=MOCK_USER):
        r = client.post(
            "/api/users",
            data={
                "name": "X", "surname": "Y", "username": "taken",
                "email": "x@example.com", "password": "pass",
            },
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "username_taken" in r.headers["location"]


def test_create_user_username_equals_email(client):
    r = client.post(
        "/api/users",
        data={
            "name": "X", "surname": "Y", "username": "same@example.com",
            "email": "same@example.com", "password": "pass",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "username_email_same" in r.headers["location"]


# ── Postings ─────────────────────────────────────────────────────────────────

def test_get_all_postings(client):
    with patch("api.endpoints.get_all_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/postings")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_public_postings(client):
    with patch("api.endpoints.get_public_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/postings/public")
    assert r.status_code == 200


def test_get_my_postings_unauthenticated(client, no_session):
    r = client.get("/api/postings/my-postings")
    assert r.status_code == 401


def test_get_my_postings_authenticated(client, with_session):
    posting = {**MOCK_POSTING, "created_at": None}
    with patch("api.endpoints.get_postings_by_user", return_value=[posting]):
        r = client.get("/api/postings/my-postings", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_posting_by_id(client):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING):
        r = client.get("/api/postings/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Test Job"


def test_get_posting_by_hash(client):
    with patch("api.endpoints.get_posting_by_id", side_effect=ValueError), \
         patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING):
        r = client.get("/api/postings/abc123")
    assert r.status_code == 200


def test_get_posting_not_found(client):
    with patch("api.endpoints.get_posting_by_id", return_value=None):
        r = client.get("/api/postings/999")
    assert r.status_code == 404


def test_create_posting_unauthenticated(client, no_session):
    r = client.post(
        "/api/postings",
        data={"title": "Job", "post_description": "Desc", "category": "IT"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "auth_required" in r.headers["location"]


def test_create_posting_authenticated(client, with_session):
    with patch("api.endpoints.create_posting_in_db"):
        r = client.post(
            "/api/postings",
            data={"title": "Job", "post_description": "Desc", "category": "IT"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "posting_created" in r.headers["location"]


def test_delete_posting_unauthenticated(client, no_session):
    r = client.delete("/api/postings/1")
    assert r.status_code == 401


def test_delete_posting_not_found(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=None):
        r = client.delete("/api/postings/1", cookies={"session_token": "tok"})
    assert r.status_code == 404


def test_delete_posting_access_denied(client, with_session):
    other_user_posting = {**MOCK_POSTING, "user_id": 99}
    with patch("api.endpoints.get_posting_by_id", return_value=other_user_posting):
        r = client.delete("/api/postings/1", cookies={"session_token": "tok"})
    assert r.status_code == 403


def test_delete_posting_success(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING), \
         patch("api.endpoints.delete_posting_from_db", return_value=True):
        r = client.delete("/api/postings/1", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["message"] == "Posting deleted successfully"


def test_get_posting_for_edit_unauthenticated(client, no_session):
    r = client.get("/api/posting/1/manage")
    assert r.status_code == 401


def test_get_posting_for_edit_not_found(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=None):
        r = client.get("/api/posting/1/manage", cookies={"session_token": "tok"})
    assert r.status_code == 404


def test_get_posting_for_edit_access_denied(client, with_session):
    other_user_posting = {**MOCK_POSTING, "user_id": 99}
    with patch("api.endpoints.get_posting_by_id", return_value=other_user_posting):
        r = client.get("/api/posting/1/manage", cookies={"session_token": "tok"})
    assert r.status_code == 403


def test_get_posting_for_edit_success(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING):
        r = client.get("/api/posting/1/manage", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["posting"]["title"] == "Test Job"


# ── Dashboard / Profile ──────────────────────────────────────────────────────

def test_dashboard_stats_unauthenticated(client, no_session):
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 401


def test_dashboard_stats_authenticated(client, with_session):
    stats = {"total_postings": 3, "total_applications": 5}
    with patch("api.endpoints.get_user_posting_stats", return_value=stats):
        r = client.get("/api/dashboard/stats", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["total_postings"] == 3


def test_profile_data_unauthenticated(client, no_session):
    r = client.get("/api/profile/data")
    assert r.status_code == 401


def test_profile_data_user_not_found(client, with_session):
    with patch("api.endpoints.get_user_by_id", return_value=None):
        r = client.get("/api/profile/data", cookies={"session_token": "tok"})
    assert r.status_code == 404


def test_profile_data_success(client, with_session):
    with patch("api.endpoints.get_user_by_id", return_value=MOCK_USER), \
         patch("api.endpoints.get_postings_by_user", return_value=[]), \
         patch("api.endpoints.get_applications_by_user", return_value=[]):
        r = client.get("/api/profile/data", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["username"] == "testuser"
    assert data["stats"]["total_postings"] == 0


# ── Applications ─────────────────────────────────────────────────────────────

def test_apply_unauthenticated(client, no_session):
    r = client.post(
        "/api/applications",
        data={"posting_id": "1", "message": "I want this job"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "auth_required" in r.headers["location"]


def test_apply_success(client, with_session):
    apply_result = {"success": True, "error": None}
    with patch("api.endpoints.apply_to_posting", return_value=apply_result), \
         patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING):
        r = client.post(
            "/api/applications",
            data={"posting_id": "1", "message": "Interested"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "application_submitted" in r.headers["location"]


def test_apply_already_applied(client, with_session):
    apply_result = {"success": False, "error": "already_applied"}
    with patch("api.endpoints.apply_to_posting", return_value=apply_result), \
         patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING):
        r = client.post(
            "/api/applications",
            data={"posting_id": "1"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "already_applied" in r.headers["location"]


def test_my_applications_unauthenticated(client, no_session):
    r = client.get("/api/applications/my-applications")
    assert r.status_code == 401


def test_my_applications_authenticated(client, with_session):
    with patch("api.endpoints.get_applications_by_user", return_value=[MOCK_APPLICATION]):
        r = client.get("/api/applications/my-applications", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_application_details_unauthenticated(client, no_session):
    r = client.get("/api/applications/1")
    assert r.status_code == 401


def test_get_application_details_not_found(client, with_session):
    with patch("api.endpoints.get_application_details", return_value=None):
        r = client.get("/api/applications/1", cookies={"session_token": "tok"})
    assert r.status_code == 404


def test_get_application_details_success(client, with_session):
    with patch("api.endpoints.get_application_details", return_value=MOCK_APPLICATION):
        r = client.get("/api/applications/1", cookies={"session_token": "tok"})
    assert r.status_code == 200


def test_review_application_unauthenticated(client, no_session):
    r = client.post("/api/applications/1/review", data={"status": "accepted"})
    assert r.status_code == 401


def test_review_application_access_denied(client, with_session):
    other_owner_app = {**MOCK_APPLICATION, "posting_owner_id": 99}
    with patch("api.endpoints.get_application_details", return_value=other_owner_app):
        r = client.post(
            "/api/applications/1/review",
            data={"status": "accepted"},
            cookies={"session_token": "tok"},
        )
    assert r.status_code == 403


def test_review_application_invalid_status(client, with_session):
    with patch("api.endpoints.get_application_details", return_value=MOCK_APPLICATION):
        r = client.post(
            "/api/applications/1/review",
            data={"status": "invalid_status"},
            cookies={"session_token": "tok"},
        )
    assert r.status_code == 400


def test_review_application_success(client, with_session):
    with patch("api.endpoints.get_application_details", return_value=MOCK_APPLICATION), \
         patch("api.endpoints.update_application_status", return_value=True):
        r = client.post(
            "/api/applications/1/review",
            data={"status": "accepted"},
            cookies={"session_token": "tok"},
        )
    assert r.status_code == 200
    assert "updated" in r.json()["message"]


# ── Page redirects ────────────────────────────────────────────────────────────

def test_root_unauthenticated(client, no_session):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/index.html"


def test_root_authenticated(client, with_session):
    r = client.get("/", cookies={"session_token": "tok"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


def test_login_redirect_unauthenticated(client, no_session):
    r = client.get("/login", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_login_redirect_authenticated(client, with_session):
    r = client.get("/login", cookies={"session_token": "tok"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


def test_data_view_redirect_unauthenticated(client, no_session):
    r = client.get("/data-view", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_data_view_redirect_authenticated(client, with_session):
    r = client.get("/data-view", cookies={"session_token": "tok"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


def test_profile_redirect_unauthenticated(client, no_session):
    r = client.get("/profile", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_contact_redirect(client):
    r = client.get("/contact", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/contact.html"


def test_register_redirect_unauthenticated(client, no_session):
    r = client.get("/register", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/register.html"


def test_register_redirect_authenticated(client, with_session):
    r = client.get("/register", cookies={"session_token": "tok"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


def test_profile_redirect_authenticated(client, with_session):
    r = client.get("/profile", cookies={"session_token": "tok"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/profile.html"


def test_password_reset_redirect(client):
    r = client.get("/password-reset", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/password-reset.html"


# ── update_posting ────────────────────────────────────────────────────────────

def test_update_posting_unauthenticated(client, no_session):
    r = client.post(
        "/api/postings/update",
        data={"posting_id": "1", "title": "T", "category": "IT",
              "post_description": "D", "status": "open"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "auth_required" in r.headers["location"]


def test_update_posting_access_denied_no_posting(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=None):
        r = client.post(
            "/api/postings/update",
            data={"posting_id": "1", "title": "T", "category": "IT",
                  "post_description": "D", "status": "open"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "access_denied" in r.headers["location"]


def test_update_posting_access_denied_wrong_owner(client, with_session):
    other = {**MOCK_POSTING, "user_id": 99}
    with patch("api.endpoints.get_posting_by_id", return_value=other):
        r = client.post(
            "/api/postings/update",
            data={"posting_id": "1", "title": "T", "category": "IT",
                  "post_description": "D", "status": "open"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "access_denied" in r.headers["location"]


def test_update_posting_db_failure(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING), \
         patch("api.endpoints.update_posting_in_db", return_value=False):
        r = client.post(
            "/api/postings/update",
            data={"posting_id": "1", "title": "T", "category": "IT",
                  "post_description": "D", "status": "open"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "update_failed" in r.headers["location"]


def test_update_posting_success(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING), \
         patch("api.endpoints.update_posting_in_db", return_value=True):
        r = client.post(
            "/api/postings/update",
            data={"posting_id": "1", "title": "T", "category": "IT",
                  "post_description": "D", "status": "open"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "posting_updated" in r.headers["location"]


def test_update_posting_exception(client, with_session):
    with patch("api.endpoints.get_posting_by_id", side_effect=RuntimeError("db down")):
        r = client.post(
            "/api/postings/update",
            data={"posting_id": "1", "title": "T", "category": "IT",
                  "post_description": "D", "status": "open"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "update_failed" in r.headers["location"]


# ── delete_posting db failure ────────────────────────────────────────────────

def test_delete_posting_db_failure(client, with_session):
    with patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING), \
         patch("api.endpoints.delete_posting_from_db", return_value=False):
        r = client.delete("/api/postings/1", cookies={"session_token": "tok"})
    assert r.status_code == 500


# ── get_public_postings exception ────────────────────────────────────────────

def test_get_public_postings_exception(client):
    with patch("api.endpoints.get_public_postings", side_effect=RuntimeError("db error")):
        r = client.get("/api/postings/public")
    assert r.status_code == 500


# ── get_my_postings exception ────────────────────────────────────────────────

def test_get_my_postings_exception(client, with_session):
    with patch("api.endpoints.get_postings_by_user", side_effect=RuntimeError("db error")):
        r = client.get("/api/postings/my-postings", cookies={"session_token": "tok"})
    assert r.status_code == 500


# ── postings/by_user and applications/by_* ──────────────────────────────────

def test_get_postings_by_user(client):
    with patch("api.endpoints.get_postings_by_user", return_value=[MOCK_POSTING]):
        r = client.get("/api/postings/by_user/1")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_applications_by_user(client):
    with patch("api.endpoints.get_applications_by_user", return_value=[MOCK_APPLICATION]):
        r = client.get("/api/applications/by_user/2")
    assert r.status_code == 200


def test_get_applications_by_posting(client):
    with patch("api.endpoints.get_applications_by_posting", return_value=[MOCK_APPLICATION]):
        r = client.get("/api/applications/by_posting/1")
    assert r.status_code == 200


# ── create_user server error ─────────────────────────────────────────────────

def test_create_user_server_error(client):
    with patch("api.endpoints.get_user_by_email", return_value=None), \
         patch("api.endpoints.get_user_by_username", return_value=None), \
         patch("api.endpoints.hash_password", return_value="hashed"), \
         patch("api.endpoints.create_user", side_effect=RuntimeError("db error")):
        r = client.post(
            "/api/users",
            data={"name": "X", "surname": "Y", "username": "u",
                  "email": "x@x.com", "password": "p"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "server_error" in r.headers["location"]


def test_create_user_http_exception_propagates(client):
    from fastapi import HTTPException as FastAPIHTTPException
    with patch("api.endpoints.get_user_by_email", return_value=None), \
         patch("api.endpoints.get_user_by_username", return_value=None), \
         patch("api.endpoints.hash_password", return_value="hashed"), \
         patch("api.endpoints.create_user",
               side_effect=FastAPIHTTPException(status_code=409, detail="conflict")):
        r = client.post(
            "/api/users",
            data={"name": "X", "surname": "Y", "username": "u",
                  "email": "x@x.com", "password": "p"},
            follow_redirects=False,
        )
    assert r.status_code == 409


# ── apply edge cases ─────────────────────────────────────────────────────────

def test_apply_posting_not_found_after_apply(client, with_session):
    apply_result = {"success": True, "error": None}
    with patch("api.endpoints.apply_to_posting", return_value=apply_result), \
         patch("api.endpoints.get_posting_by_id", return_value=None):
        r = client.post(
            "/api/applications",
            data={"posting_id": "1"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "posting_not_found" in r.headers["location"]


def test_apply_exception(client, with_session):
    with patch("api.endpoints.apply_to_posting", side_effect=RuntimeError("db error")):
        r = client.post(
            "/api/applications",
            data={"posting_id": "1"},
            cookies={"session_token": "tok"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "application_failed" in r.headers["location"]


# ── review_application update failure ───────────────────────────────────────

def test_review_application_update_fails(client, with_session):
    with patch("api.endpoints.get_application_details", return_value=MOCK_APPLICATION), \
         patch("api.endpoints.update_application_status", return_value=False):
        r = client.post(
            "/api/applications/1/review",
            data={"status": "accepted"},
            cookies={"session_token": "tok"},
        )
    assert r.status_code == 404


# ── analytics ────────────────────────────────────────────────────────────────

def test_analytics_unauthenticated(client, no_session):
    r = client.get("/api/postings/1/analytics")
    assert r.status_code == 401


def test_analytics_not_found(client, with_session):
    with patch("api.endpoints.get_posting_analytics", return_value=None):
        r = client.get("/api/postings/1/analytics", cookies={"session_token": "tok"})
    assert r.status_code == 404


def test_analytics_success(client, with_session):
    analytics = {"views": 10, "applications": 3}
    with patch("api.endpoints.get_posting_analytics", return_value=analytics):
        r = client.get("/api/postings/1/analytics", cookies={"session_token": "tok"})
    assert r.status_code == 200
    assert r.json()["views"] == 10


# ── view_posting (/api/postings/view/{hash}) ─────────────────────────────────

def test_view_posting_by_hash_unauthenticated(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/postings/view/abc123")
    assert r.status_code == 200
    data = r.json()
    assert data["is_authenticated"] is False
    assert data["is_owner"] is False


def test_view_posting_authenticated_owner(client, with_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/postings/view/abc123", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_authenticated"] is True
    assert data["is_owner"] is True


def test_view_posting_authenticated_non_owner(client, with_session):
    other_posting = {**MOCK_POSTING, "user_id": 99}
    with patch("api.endpoints.get_posting_by_hash", return_value=other_posting), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=other_posting), \
         patch("api.endpoints.check_user_application_exists", return_value=False):
        r = client.get("/api/postings/view/abc123", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_owner"] is False
    assert data["can_apply"] is True


def test_view_posting_authenticated_already_applied(client, with_session):
    other_posting = {**MOCK_POSTING, "user_id": 99}
    with patch("api.endpoints.get_posting_by_hash", return_value=other_posting), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=other_posting), \
         patch("api.endpoints.check_user_application_exists", return_value=True):
        r = client.get("/api/postings/view/abc123", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["has_applied"] is True
    assert data["can_apply"] is False


def test_view_posting_stats_fallback(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=None):
        r = client.get("/api/postings/view/abc123")
    assert r.status_code == 200


def test_view_posting_hash_not_found_id_fallback(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=None), \
         patch("api.endpoints.get_posting_by_id", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/postings/view/1")
    assert r.status_code == 200


def test_view_posting_not_found(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=None):
        r = client.get("/api/postings/view/nonexistent")
    assert r.status_code == 404


# ── data_view_page (/api/data-view) ──────────────────────────────────────────

def test_data_view_page_unauthenticated(client, no_session):
    with patch("api.endpoints.get_public_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/data-view", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


def test_data_view_page_authenticated(client, with_session):
    with patch("api.endpoints.get_public_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/data-view", cookies={"session_token": "tok"},
                       follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/data-view.html"


# ── view_posting_page (/api/posting/{id}) ────────────────────────────────────

def test_view_posting_page_success(client, no_session):
    with patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/posting/1", follow_redirects=False)
    assert r.status_code == 302
    assert "posting-detail.html" in r.headers["location"]


def test_view_posting_page_not_found(client, no_session):
    with patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=None):
        r = client.get("/api/posting/999")
    assert r.status_code == 404


# ── posting_detail_page (/api/posting/{hash}/page) ───────────────────────────

def test_posting_detail_page_not_found(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=None):
        r = client.get("/api/posting/badhash/page")
    assert r.status_code == 404


def test_posting_detail_page_unauthenticated(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/posting/abc123/page")
    assert r.status_code == 200
    data = r.json()
    assert data["is_authenticated"] is False


def test_posting_detail_page_authenticated_owner(client, with_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=MOCK_POSTING):
        r = client.get("/api/posting/abc123/page", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_owner"] is True
    assert data["can_apply"] is False


def test_posting_detail_page_stats_fallback(client, no_session):
    with patch("api.endpoints.get_posting_by_hash", return_value=MOCK_POSTING), \
         patch("api.endpoints.track_posting_view"), \
         patch("api.endpoints.get_posting_with_public_stats", return_value=None):
        r = client.get("/api/posting/abc123/page")
    assert r.status_code == 200


# ── posting_detail_static (/api/posting-detail) ──────────────────────────────

def test_posting_detail_static(client):
    r = client.get("/api/posting-detail", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/posting-detail.html"


# ── get_postings_data (/api/postings-data) ───────────────────────────────────

def test_get_postings_data_unauthenticated(client, no_session):
    with patch("api.endpoints.get_public_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/postings-data")
    assert r.status_code == 200
    data = r.json()
    assert data["is_authenticated"] is False
    assert len(data["postings"]) == 1


def test_get_postings_data_authenticated(client, with_session):
    with patch("api.endpoints.get_public_postings", return_value=[MOCK_POSTING]):
        r = client.get("/api/postings-data", cookies={"session_token": "tok"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_authenticated"] is True


# ── contact form ─────────────────────────────────────────────────────────────

def test_contact_form(client):
    r = client.post(
        "/api/contact",
        data={"full-name": "Jan Kowalski", "email": "jan@example.com",
              "message": "Hello!"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "message_sent" in r.headers["location"]


# ── login exception ──────────────────────────────────────────────────────────

def test_login_server_error(client):
    with patch("api.endpoints.get_session_user", return_value=None), \
         patch("api.endpoints.login_user", side_effect=RuntimeError("db error")):
        r = client.post(
            "/api/login",
            data={"email": "u@u.com", "password": "p"},
            follow_redirects=False,
        )
    assert r.status_code == 303
    assert "server_error" in r.headers["location"]


def test_login_http_exception_propagates(client):
    from fastapi import HTTPException as FastAPIHTTPException
    with patch("api.endpoints.get_session_user", return_value=None), \
         patch("api.endpoints.login_user",
               side_effect=FastAPIHTTPException(status_code=429, detail="rate limited")):
        r = client.post(
            "/api/login",
            data={"email": "u@u.com", "password": "p"},
            follow_redirects=False,
        )
    assert r.status_code == 429


# ── cache.py ─────────────────────────────────────────────────────────────────

def test_get_redis_client():
    from core.cache import get_redis_client
    with patch("core.cache.redis.Redis") as mock_redis_cls:
        get_redis_client()
        mock_redis_cls.assert_called_once()

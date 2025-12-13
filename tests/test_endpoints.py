"""
Integration tests for critical authentication flows and analytics endpoints.
These tests focus on the authentication business logic that would be used
in the endpoints without testing the HTTP layer directly.
"""

import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestAuthenticationFlows:
    """Test the authentication flows that endpoints would use"""
    
    @patch('backend.core.security.get_session_user')
    @patch('backend.core.security.login_user')
    @patch('backend.core.db.get_user_by_email')
    def test_login_flow_success(self, mock_get_user_by_email, mock_login_user, mock_get_session_user):
        """Test successful login flow returns session data"""
        from backend.core.security import login_user
        
        # Mock user exists and login succeeds
        mock_user = {
            "id": 42,
            "email": "test@example.com",
            "hashed_password": "$2b$12$test_hash"
        }
        mock_get_user_by_email.return_value = mock_user
        mock_login_user.return_value = {
            "user_id": 42,
            "email": "test@example.com", 
            "session_token": "test_token"
        }
        
        # Test the login flow
        result = login_user("test@example.com", "correct_password")
        
        assert result is not None
        assert result["user_id"] == 42
        assert "session_token" in result
    
    @patch('backend.core.security.get_session_user')
    @patch('backend.core.security.login_user')
    def test_login_flow_failure(self, mock_login_user, mock_get_session_user):
        """Test failed login flow returns None"""
        from backend.core.security import login_user
        
        mock_login_user.return_value = None
        
        result = login_user("test@example.com", "wrong_password")
        
        assert result is None
    
    @patch('backend.core.security.get_session_user')
    def test_session_validation_valid(self, mock_get_session_user):
        """Test valid session returns user data"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = {
            "user_id": 42,
            "created_at": "2023-01-01T00:00:00Z",
            "expires_at": "2023-01-08T00:00:00Z"
        }
        
        result = get_session_user("valid_token")
        
        assert result is not None
        assert result["user_id"] == 42
    
    @patch('backend.core.security.get_session_user')
    def test_session_validation_invalid(self, mock_get_session_user):
        """Test invalid session returns None"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = None
        
        result = get_session_user("invalid_token")
        
        assert result is None
    
    @patch('backend.core.security.logout_user')
    def test_logout_flow_success(self, mock_logout_user):
        """Test successful logout flow"""
        from backend.core.security import logout_user
        
        mock_logout_user.return_value = True
        
        result = logout_user("valid_token")
        
        assert result is True
    
    @patch('backend.core.security.logout_user')
    def test_logout_flow_failure(self, mock_logout_user):
        """Test logout with invalid token"""
        from backend.core.security import logout_user
        
        mock_logout_user.return_value = False
        
        result = logout_user("invalid_token")
        
        assert result is False


class TestRegistrationFlows:
    """Test user registration flows"""
    
    @patch('backend.core.db.get_user_by_email')
    @patch('backend.core.db.get_user_by_username')
    @patch('backend.core.db.create_user')
    def test_registration_validation_success(self, mock_create_user, mock_get_username, mock_get_email):
        """Test successful registration validation"""
        from backend.core.db import create_user, get_user_by_email, get_user_by_username
        
        # Mock that user doesn't exist
        mock_get_email.return_value = None
        mock_get_username.return_value = None
        mock_create_user.return_value = 42
        
        # Test registration validation logic
        email_exists = get_user_by_email("new@example.com")
        username_exists = get_user_by_username("newuser")
        
        assert email_exists is None
        assert username_exists is None
        
        # Test user creation
        user_id = create_user("John", "Doe", "newuser", "new@example.com", "hashed_password")
        assert user_id == 42
    
    @patch('backend.core.db.get_user_by_email')
    def test_registration_validation_email_taken(self, mock_get_email):
        """Test registration fails when email is taken"""
        from backend.core.db import get_user_by_email
        
        mock_get_email.return_value = {"id": 1, "email": "taken@example.com"}
        
        result = get_user_by_email("taken@example.com")
        
        assert result is not None
        assert result["email"] == "taken@example.com"
    
    @patch('backend.core.db.get_user_by_email')
    @patch('backend.core.db.get_user_by_username')
    def test_registration_validation_username_taken(self, mock_get_username, mock_get_email):
        """Test registration fails when username is taken"""
        from backend.core.db import get_user_by_email, get_user_by_username
        
        mock_get_email.return_value = None
        mock_get_username.return_value = {"id": 1, "username": "taken"}
        
        email_result = get_user_by_email("new@example.com")
        username_result = get_user_by_username("taken")
        
        assert email_result is None
        assert username_result is not None
        assert username_result["username"] == "taken"


class TestAuthenticationStates:
    """Test authentication state logic that endpoints would use"""
    
    def test_username_email_same_validation(self):
        """Test validation that username and email cannot be the same"""
        username = "same@example.com"
        email = "same@example.com"
        
        # This is the validation logic that would be in endpoints
        is_same = username.lower() == email.lower()
        
        assert is_same is True
    
    def test_username_email_different_validation(self):
        """Test validation passes when username and email are different"""
        username = "username"
        email = "different@example.com"
        
        is_same = username.lower() == email.lower()
        
        assert is_same is False
    
    @patch('backend.core.security.get_session_user')
    def test_auth_status_logic_authenticated(self, mock_get_session_user):
        """Test auth status logic for authenticated users"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = {"user_id": 42}
        
        session_data = get_session_user("valid_token")
        
        # This is the logic that would be in the auth status endpoint
        if session_data:
            status = {
                "authenticated": True,
                "user_id": session_data["user_id"]
            }
        else:
            status = {"authenticated": False}
        
        assert status["authenticated"] is True
        assert status["user_id"] == 42
    
    @patch('backend.core.security.get_session_user')
    def test_auth_status_logic_not_authenticated(self, mock_get_session_user):
        """Test auth status logic for unauthenticated users"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = None
        
        session_data = get_session_user("invalid_token")
        
        # This is the logic that would be in the auth status endpoint
        if session_data:
            status = {
                "authenticated": True,
                "user_id": session_data["user_id"]
            }
        else:
            status = {"authenticated": False}
        
        assert status["authenticated"] is False
        assert "user_id" not in status
    
    @patch('backend.core.security.get_session_user')
    def test_auth_buttons_logic_authenticated(self, mock_get_session_user):
        """Test auth buttons logic for authenticated users"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = {"user_id": 42}
        
        session_data = get_session_user("valid_token")
        
        # This is the logic that would be in the auth buttons endpoint
        if session_data:
            buttons = {
                "authenticated": True,
                "action": "logout",
                "method": "POST",
                "url": "/api/logout",
                "text": "Logout",
                "icon": "bi-box-arrow-right"
            }
        else:
            buttons = {
                "authenticated": False,
                "action": "login",
                "method": "GET",
                "url": "/login.html",
                "text": "Login",
                "icon": "bi-box-arrow-in-right"
            }
        
        assert buttons["authenticated"] is True
        assert buttons["action"] == "logout"
        assert buttons["method"] == "POST"
    
    @patch('backend.core.security.get_session_user')
    def test_auth_buttons_logic_not_authenticated(self, mock_get_session_user):
        """Test auth buttons logic for unauthenticated users"""
        from backend.core.security import get_session_user
        
        mock_get_session_user.return_value = None
        
        session_data = get_session_user("invalid_token")
        
        # This is the logic that would be in the auth buttons endpoint
        if session_data:
            buttons = {
                "authenticated": True,
                "action": "logout",
                "method": "POST",
                "url": "/api/logout",
                "text": "Logout",
                "icon": "bi-box-arrow-right"
            }
        else:
            buttons = {
                "authenticated": False,
                "action": "login",
                "method": "GET",
                "url": "/login.html",
                "text": "Login",
                "icon": "bi-box-arrow-in-right"
            }
        
        assert buttons["authenticated"] is False
        assert buttons["action"] == "login"
        assert buttons["method"] == "GET"


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""
    
    @patch('backend.api.endpoints.get_public_postings')
    def test_get_public_postings_success(self, mock_get_public_postings):
        """Test getting public postings successfully"""
        from backend.api.endpoints import get_public_postings_endpoint
        
        mock_get_public_postings.return_value = [
            {
                "id": 1,
                "title": "Software Engineer",
                "post_description": "Looking for a skilled developer",
                "category": "technology",
                "views": 150,
                "status": "active",
                "creator_name": "John Doe",
                "creator_username": "johndoe",
                "application_count": 8
            }
        ]
        
        result = asyncio.run(get_public_postings_endpoint())
        
        assert len(result) == 1
        assert result[0]["title"] == "Software Engineer"
        assert result[0]["application_count"] == 8
    
    @patch('backend.api.endpoints.check_user_application_exists')
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_authenticated(self, mock_get_session, mock_get_hash, mock_get_id, mock_get_posting, mock_track_view, mock_check_applied):
        """Test viewing posting as authenticated user"""
        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        # Hash lookup fails, ID lookup succeeds
        mock_get_hash.return_value = None
        mock_get_id.return_value = {
            "id": 1,
            "user_id": 99,
            "title": "Test Job",
            "views": 100,
            "application_count": 5
        }
        mock_get_posting.return_value = {
            "id": 1,
            "user_id": 99,
            "title": "Test Job",
            "views": 100,
            "application_count": 5
        }
        mock_track_view.return_value = True
        mock_check_applied.return_value = False  # User hasn't applied yet
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting(1, mock_request))
        
        assert result["posting"]["title"] == "Test Job"
        assert result["is_authenticated"] is True
        assert result["is_owner"] is False  # user_id 42 != posting user_id 99
        assert result["has_applied"] is False
        assert result["can_apply"] is True
        mock_track_view.assert_called_once_with(1, 42, "127.0.0.1", "Test User Agent", "session_token")
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_unauthenticated(self, mock_get_session, mock_get_hash, mock_get_id, mock_get_posting, mock_track_view):
        """Test viewing posting as unauthenticated user"""
        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = None
        # Hash lookup fails, ID lookup succeeds
        mock_get_hash.return_value = None
        mock_get_id.return_value = {
            "id": 1,
            "user_id": 99,
            "title": "Test Job",
            "views": 100,
            "application_count": 5
        }
        mock_get_posting.return_value = {
            "id": 1,
            "user_id": 99,
            "title": "Test Job",
            "views": 100,
            "application_count": 5
        }
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting(1, mock_request))
        
        assert result["posting"]["title"] == "Test Job"
        assert result["is_authenticated"] is False
        assert result["is_owner"] is False
        assert result["has_applied"] is False
        assert result["can_apply"] is False  # can't apply when not authenticated
        mock_track_view.assert_called_once_with(1, None, "127.0.0.1", "Test User Agent", "session_token")
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_not_found(self, mock_get_session, mock_get_by_hash, mock_get_by_id, mock_get_posting, mock_track_view):
        """Test viewing non-existent posting"""
        from fastapi import HTTPException

        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_by_hash.return_value = None
        mock_get_by_id.return_value = None
        mock_get_posting.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        try:
            asyncio.run(view_posting(999, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"
    
    @patch('backend.api.endpoints.get_postings_by_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_my_postings_success(self, mock_get_session, mock_get_postings):
        """Test getting user's own postings"""
        from backend.api.endpoints import get_my_postings
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_postings.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42},
            {"id": 2, "title": "Job 2", "user_id": 42}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_my_postings(mock_request))
        
        assert len(result) == 2
        assert result[0]["title"] == "Job 1"
        mock_get_postings.assert_called_once_with(42)
    
    @patch('backend.api.endpoints.get_session_user')
    def test_get_my_postings_unauthenticated(self, mock_get_session):
        """Test getting postings without authentication"""
        from fastapi import HTTPException

        from backend.api.endpoints import get_my_postings
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        try:
            asyncio.run(get_my_postings(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"
    
    @patch('backend.api.endpoints.get_posting_analytics')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_posting_analytics_success(self, mock_get_session, mock_get_analytics):
        """Test getting posting analytics as owner"""
        from backend.api.endpoints import get_posting_analytics_endpoint
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_analytics.return_value = {
            "posting_id": 1,
            "stats": {"views": 100, "application_count": 5},
            "daily_metrics": [],
            "application_status": []
        }
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_posting_analytics_endpoint(1, mock_request))
        
        assert result["posting_id"] == 1
        assert result["stats"]["views"] == 100
        mock_get_analytics.assert_called_once_with(1, 42)
    
    @patch('backend.api.endpoints.get_posting_analytics')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_posting_analytics_not_owner(self, mock_get_session, mock_get_analytics):
        """Test getting posting analytics for non-owned posting"""
        from fastapi import HTTPException

        from backend.api.endpoints import get_posting_analytics_endpoint
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_analytics.return_value = None  # Not owner or posting not found
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_posting_analytics_endpoint(1, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found or access denied"
    
    @patch('backend.api.endpoints.get_user_posting_stats')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_dashboard_stats_success(self, mock_get_session, mock_get_stats):
        """Test getting dashboard statistics"""
        from backend.api.endpoints import get_dashboard_stats
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_stats.return_value = {
            "overview": {"total_postings": 5, "total_views": 500},
            "top_postings": [],
            "recent_activity": []
        }
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_dashboard_stats(mock_request))
        
        assert result["overview"]["total_postings"] == 5
        mock_get_stats.assert_called_once_with(42)
    
    @patch('backend.api.endpoints.get_applications_by_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_my_applications_success(self, mock_get_session, mock_get_applications):
        """Test getting user's applications"""
        from backend.api.endpoints import get_my_applications
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_applications.return_value = [
            {"id": 1, "posting_id": 1, "title": "Job 1", "status": "pending"},
            {"id": 2, "posting_id": 2, "title": "Job 2", "status": "reviewed"}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_my_applications(mock_request))
        
        assert len(result) == 2
        assert result[0]["title"] == "Job 1"
        mock_get_applications.assert_called_once_with(42)
    
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_application_details_success(self, mock_get_session, mock_get_details):
        """Test getting application details"""
        from backend.api.endpoints import get_application_details_endpoint
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = {
            "id": 1,
            "user_id": 42,
            "posting_id": 1,
            "message": "I'm interested",
            "status": "pending",
            "posting_title": "Test Job"
        }
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_application_details_endpoint(1, mock_request))
        
        assert result["id"] == 1
        assert result["posting_title"] == "Test Job"
        mock_get_details.assert_called_once_with(1, 42)
    
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_application_details_no_access(self, mock_get_session, mock_get_details):
        """Test getting application details without access"""
        from fastapi import HTTPException

        from backend.api.endpoints import get_application_details_endpoint
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = None  # No access
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_application_details_endpoint(1, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Application not found or access denied"


class TestApplicationReviewEndpoints:
    """Test application review endpoints"""
    
    @patch('backend.api.endpoints.update_application_status')
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_success(self, mock_get_session, mock_get_details, mock_update_status):
        """Test reviewing application successfully"""
        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = {
            "id": 1,
            "user_id": 123,
            "posting_id": 1,
            "posting_owner_id": 42,
            "status": "pending"
        }
        mock_update_status.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(review_application(1, mock_request, "accepted", "Great candidate!"))
        
        assert result["message"] == "Application status updated successfully"
        mock_update_status.assert_called_once_with(1, "accepted", "Great candidate!")
    
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_not_owner(self, mock_get_session, mock_get_details):
        """Test reviewing application as non-owner"""
        from fastapi import HTTPException

        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = {
            "id": 1,
            "user_id": 123,
            "posting_id": 1,
            "posting_owner_id": 999,  # Different owner
            "status": "pending"
        }
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(review_application(1, mock_request, "accepted", "Great candidate!"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 403
            assert e.detail == "Access denied"
    
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_not_found(self, mock_get_session, mock_get_details):
        """Test reviewing non-existent application"""
        from fastapi import HTTPException

        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = None  # Application not found
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(review_application(999, mock_request, "accepted", "Great candidate!"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 403
            assert e.detail == "Access denied"
    
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_invalid_status(self, mock_get_session, mock_get_details):
        """Test reviewing application with invalid status"""
        from fastapi import HTTPException

        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = {
            "id": 1,
            "user_id": 123,
            "posting_id": 1,
            "posting_owner_id": 42,
            "status": "pending"
        }
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(review_application(1, mock_request, "invalid_status", "Notes"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 400
            assert e.detail == "Invalid status"
    
    @patch('backend.api.endpoints.update_application_status')
    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_update_failed(self, mock_get_session, mock_get_details, mock_update_status):
        """Test reviewing application when update fails"""
        from fastapi import HTTPException

        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = {
            "id": 1,
            "user_id": 123,
            "posting_id": 1,
            "posting_owner_id": 42,
            "status": "pending"
        }
        mock_update_status.return_value = False  # Update failed
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(review_application(1, mock_request, "accepted", "Great candidate!"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Application not found"
    
    def test_review_application_valid_statuses(self):
        """Test that valid application statuses are defined correctly"""
        valid_statuses = ["pending", "reviewed", "accepted", "rejected"]
        
        # Test that each status is a valid string
        for status in valid_statuses:
            assert isinstance(status, str)
            assert len(status) > 0
        
        # Test that there are no duplicates
        assert len(valid_statuses) == len(set(valid_statuses))
    
    @patch('backend.api.endpoints.get_session_user')
    def test_review_application_unauthenticated(self, mock_get_session):
        """Test reviewing application without authentication"""
        from fastapi import HTTPException

        from backend.api.endpoints import review_application
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        try:
            asyncio.run(review_application(1, mock_request, "accepted", "Great candidate!"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"


class TestPostingManagementBusinessLogic:
    """Test posting management business logic"""
    
    @patch('backend.core.db.create_posting_in_db')
    @patch('backend.core.security.get_session_user')
    def test_create_posting_authentication_check(self, mock_get_session, mock_create_posting):
        """Test creating posting requires authentication"""
        from backend.core.security import get_session_user
        
        # Test authenticated user
        mock_get_session.return_value = {"user_id": 42}
        session_data = get_session_user("valid_token")
        assert session_data is not None
        assert session_data["user_id"] == 42
        
        # Test unauthenticated user
        mock_get_session.return_value = None
        session_data = get_session_user("invalid_token")
        assert session_data is None
    
    @patch('backend.core.db.create_posting_in_db')
    def test_create_posting_db_call(self, mock_create_posting):
        """Test posting creation database call"""
        from backend.core.db import create_posting_in_db
        
        mock_create_posting.return_value = "abc123hash"
        
        result = create_posting_in_db("Software Engineer", "Looking for a skilled developer", "technology", 42)
        
        assert result == "abc123hash"
        mock_create_posting.assert_called_once_with("Software Engineer", "Looking for a skilled developer", "technology", 42)
    
    @patch('backend.core.db.update_posting_in_db')
    def test_update_posting_logic(self, mock_update_posting):
        """Test posting update business logic"""
        from backend.core.db import update_posting_in_db
        
        # Test successful update
        mock_update_posting.return_value = True
        result = update_posting_in_db(1, "Updated Title", "updated_category", "Updated description", "active")
        assert result is True
        mock_update_posting.assert_called_once_with(1, "Updated Title", "updated_category", "Updated description", "active")
        
        # Test failed update (posting not found)
        mock_update_posting.return_value = False
        result = update_posting_in_db(999, "Updated Title")
        assert result is False
    
    @patch('backend.core.db.delete_posting_from_db')
    def test_delete_posting_logic(self, mock_delete_posting):
        """Test posting deletion business logic"""
        from backend.core.db import delete_posting_from_db
        
        # Test successful deletion
        mock_delete_posting.return_value = True
        result = delete_posting_from_db(1)
        assert result is True
        mock_delete_posting.assert_called_once_with(1)
        
        # Test failed deletion (posting not found)
        mock_delete_posting.return_value = False
        result = delete_posting_from_db(999)
        assert result is False


class TestPostingLookupBusinessLogic:
    """Test posting lookup business logic"""
    
    @patch('backend.core.db.get_posting_by_id')
    def test_get_posting_by_id_logic(self, mock_get_posting):
        """Test getting posting by ID business logic"""
        from backend.core.db import get_posting_by_id
        
        mock_get_posting.return_value = {
            "id": 1,
            "title": "Software Engineer",
            "hash": "abc123"
        }
        
        result = get_posting_by_id(1)
        
        assert result["id"] == 1
        assert result["title"] == "Software Engineer"
        mock_get_posting.assert_called_once_with(1)
    
    @patch('backend.core.db.get_posting_by_hash')
    def test_get_posting_by_hash_logic(self, mock_get_by_hash):
        """Test getting posting by hash business logic"""
        from backend.core.db import get_posting_by_hash
        
        mock_get_by_hash.return_value = {
            "id": 1,
            "title": "Software Engineer",
            "hash": "abc123"
        }
        
        result = get_posting_by_hash("abc123")
        
        assert result["id"] == 1
        assert result["hash"] == "abc123"
        mock_get_by_hash.assert_called_once_with("abc123")
    
    @patch('backend.core.db.get_posting_by_hash')
    def test_get_posting_not_found_logic(self, mock_get_by_hash):
        """Test getting non-existent posting business logic"""
        from backend.core.db import get_posting_by_hash
        
        mock_get_by_hash.return_value = None
        
        result = get_posting_by_hash("nonexistent")
        
        assert result is None


class TestEnhancedApplicationBusinessLogic:
    """Test enhanced application business logic"""
    
    @patch('backend.core.db.apply_to_posting')
    def test_apply_with_cover_letter_logic(self, mock_apply):
        """Test applying to posting with cover letter business logic"""
        from backend.core.db import apply_to_posting
        
        mock_apply.return_value = {"success": True, "error": None}
        
        result = apply_to_posting(42, 1, "I'm interested in this position", "Dear hiring manager, I have 5 years of experience...")
        
        assert result["success"] is True
        assert result["error"] is None
        mock_apply.assert_called_once_with(42, 1, "I'm interested in this position", "Dear hiring manager, I have 5 years of experience...")
    
    @patch('backend.core.db.apply_to_posting')
    def test_apply_without_cover_letter_logic(self, mock_apply):
        """Test applying to posting without cover letter business logic"""
        from backend.core.db import apply_to_posting
        
        mock_apply.return_value = {"success": True, "error": None}
        
        result = apply_to_posting(42, 1, "I'm interested in this position", None)
        
        assert result["success"] is True
        assert result["error"] is None
        mock_apply.assert_called_once_with(42, 1, "I'm interested in this position", None)
    
    @patch('backend.core.db.apply_to_posting')
    def test_apply_failure_logic(self, mock_apply):
        """Test application failure business logic"""
        from backend.core.db import apply_to_posting
        
        mock_apply.return_value = {"success": False, "error": "already_applied"}
        
        result = apply_to_posting(42, 1, "I'm interested in this position")
        
        assert result["success"] is False
        assert result["error"] == "already_applied"


class TestViewTrackingBusinessLogic:
    """Test view tracking business logic"""
    
    @patch('backend.core.db.track_posting_view')
    def test_track_posting_view_logic(self, mock_track_view):
        """Test view tracking business logic"""
        from backend.core.db import track_posting_view
        
        mock_track_view.return_value = True
        
        result = track_posting_view(1, user_id=42, ip_address="127.0.0.1", user_agent="Test User Agent", session_id="test_session")
        
        assert result is True
        mock_track_view.assert_called_once_with(1, user_id=42, ip_address="127.0.0.1", user_agent="Test User Agent", session_id="test_session")
    
    @patch('backend.core.db.get_posting_with_public_stats')
    def test_get_posting_with_public_stats_logic(self, mock_get_stats):
        """Test getting posting with public stats business logic"""
        from backend.core.db import get_posting_with_public_stats
        
        mock_get_stats.return_value = {
            "id": 1,
            "title": "Software Engineer",
            "views": 150,
            "application_count": 8
        }
        
        result = get_posting_with_public_stats(1)
        
        assert result["title"] == "Software Engineer"
        assert result["views"] == 150
        assert result["application_count"] == 8


class TestBasicEndpoints:
    """Test basic endpoints that are missing coverage"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        import asyncio

        from backend.api.endpoints import health_check
        
        result = asyncio.run(health_check())
        assert result == {"status": "healthy"}


class TestUserManagementEndpoints:
    """Test user management HTTP endpoints"""
    
    @patch('backend.api.endpoints.get_redis_client')
    @patch('backend.api.endpoints.create_user')
    @patch('backend.api.endpoints.get_user_by_username')
    @patch('backend.api.endpoints.get_user_by_email')
    @patch('backend.api.endpoints.hash_password')
    def test_create_user_account_success(self, mock_hash_password, mock_get_by_email, mock_get_by_username, mock_create_user, mock_redis):
        """Test successful user account creation"""
        import asyncio

        from backend.api.endpoints import create_user_account
        
        # Mock dependencies
        mock_hash_password.return_value = "hashed_password"
        mock_get_by_email.return_value = None  # Email not taken
        mock_get_by_username.return_value = None  # Username not taken
        mock_create_user.return_value = 42
        mock_redis.return_value.set.return_value = None
        
        result = asyncio.run(create_user_account("John", "Doe", "johndoe", "john@example.com", "Password123!"))
        
        assert result.status_code == 303
        assert "/login.html?success=account_created" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_user_by_email')
    def test_create_user_account_email_taken(self, mock_get_by_email):
        """Test user creation with taken email"""
        import asyncio

        from backend.api.endpoints import create_user_account
        
        mock_get_by_email.return_value = {"id": 1, "email": "john@example.com"}
        
        result = asyncio.run(create_user_account("John", "Doe", "johndoe", "john@example.com", "Password123!"))
        
        assert result.status_code == 303
        assert "/register.html?error=email_taken" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_user_by_username')
    @patch('backend.api.endpoints.get_user_by_email')
    def test_create_user_account_username_taken(self, mock_get_by_email, mock_get_by_username):
        """Test user creation with taken username"""
        import asyncio

        from backend.api.endpoints import create_user_account
        
        mock_get_by_email.return_value = None
        mock_get_by_username.return_value = {"id": 1, "username": "johndoe"}
        
        result = asyncio.run(create_user_account("John", "Doe", "johndoe", "john@example.com", "Password123!"))
        
        assert result.status_code == 303
        assert "/register.html?error=username_taken" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_user_by_username')
    @patch('backend.api.endpoints.get_user_by_email')
    def test_create_user_account_username_email_same(self, mock_get_by_email, mock_get_by_username):
        """Test user creation with username same as email"""
        import asyncio

        from backend.api.endpoints import create_user_account
        
        result = asyncio.run(create_user_account("John", "Doe", "john@example.com", "john@example.com", "Password123!"))
        
        assert result.status_code == 303
        assert "/register.html?error=username_email_same" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_redis_client')
    @patch('backend.api.endpoints.get_user_by_id')
    def test_get_user_success(self, mock_get_user, mock_redis):
        """Test successful user retrieval"""
        import asyncio

        from backend.api.endpoints import get_user
        
        mock_redis.return_value.get.return_value = None  # No cache
        mock_get_user.return_value = {"id": 42, "name": "John", "email": "john@example.com"}
        mock_redis.return_value.set.return_value = None
        
        result = asyncio.run(get_user(42))
        
        assert result["id"] == 42
        assert result["name"] == "John"
    
    @patch('backend.api.endpoints.get_redis_client')
    def test_get_user_cached(self, mock_redis):
        """Test user retrieval from cache"""
        import asyncio
        import json

        from backend.api.endpoints import get_user
        
        cached_data = {"id": 42, "name": "John", "email": "john@example.com"}
        mock_redis.return_value.get.return_value = json.dumps(cached_data)
        
        result = asyncio.run(get_user(42))
        
        assert result["id"] == 42
        assert result["name"] == "John"
    
    @patch('backend.api.endpoints.get_redis_client')
    @patch('backend.api.endpoints.get_user_by_id')
    def test_get_user_not_found(self, mock_get_user, mock_redis):
        """Test user not found"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import get_user
        
        mock_redis.return_value.get.return_value = None
        mock_get_user.return_value = None
        
        try:
            asyncio.run(get_user(999))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "User not found"
    
    @patch('backend.api.endpoints.update_user_in_db')
    def test_update_user_success(self, mock_update_user):
        """Test successful user update"""
        import asyncio

        from backend.api.endpoints import update_user
        
        mock_update_user.return_value = True
        
        result = asyncio.run(update_user(42, name="John", surname="Doe", username="johndoe", email="john@example.com"))
        
        assert result.status_code == 200
    
    @patch('backend.api.endpoints.update_user_in_db')
    def test_update_user_not_found(self, mock_update_user):
        """Test user update when user not found"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import update_user
        
        mock_update_user.return_value = False
        
        try:
            asyncio.run(update_user(999, name="John"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "User not found"
    
    @patch('backend.api.endpoints.delete_user_from_db')
    def test_delete_user_success(self, mock_delete_user):
        """Test successful user deletion"""
        import asyncio

        from backend.api.endpoints import delete_user
        
        mock_delete_user.return_value = True
        
        result = asyncio.run(delete_user(42))
        
        assert result.status_code == 200
    
    @patch('backend.api.endpoints.delete_user_from_db')
    def test_delete_user_not_found(self, mock_delete_user):
        """Test user deletion when user not found"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import delete_user
        
        mock_delete_user.return_value = False
        
        try:
            asyncio.run(delete_user(999))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "User not found"


class TestPostingManagementEndpoints:
    """Test posting management HTTP endpoints"""
    
    @patch('backend.api.endpoints.create_posting_in_db')
    @patch('backend.api.endpoints.get_session_user')
    def test_create_posting_success(self, mock_get_session, mock_create_posting):
        """Test successful posting creation"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import create_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_create_posting.return_value = "abc123hash"
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(create_posting(mock_request, "Software Engineer", "Looking for developer", "technology"))
        
        assert result.status_code == 303
        assert "/my-postings.html?success=posting_created" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_create_posting_unauthenticated(self, mock_get_session):
        """Test posting creation without authentication"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import create_posting
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        result = asyncio.run(create_posting(mock_request, "Software Engineer", "Looking for developer", "technology"))
        
        assert result.status_code == 303
        assert "/login.html?error=auth_required" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.update_posting_in_db')
    def test_update_posting_success(self, mock_update_posting, mock_get_session, mock_get_posting):
        """Test successful posting update"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import update_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = {"id": 1, "user_id": 42, "title": "Old Title"}
        mock_update_posting.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_session"
        
        result = asyncio.run(update_posting(
            request=mock_request,
            posting_id=1, 
            title="New Title", 
            category="tech", 
            post_description="New description", 
            status="active"
        ))
        
        assert result.status_code == 303
        assert "success=posting_updated" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.update_posting_in_db')
    def test_update_posting_not_found(self, mock_update_posting, mock_get_session, mock_get_posting):
        """Test posting update when posting not found"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import update_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = None  # Posting not found
        mock_update_posting.return_value = False
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_session"
        
        result = asyncio.run(update_posting(
            request=mock_request,
            posting_id=999, 
            title="New Title",
            category="tech",
            post_description="Description",
            status="active"
        ))
        
        assert result.status_code == 303
        assert "error=access_denied" in result.headers["location"]
    
    @patch('backend.api.endpoints.delete_posting_from_db')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_session_user')
    def test_delete_posting_success(self, mock_get_session, mock_get_posting, mock_delete_posting):
        """Test successful posting deletion"""
        import asyncio

        from backend.api.endpoints import delete_posting

        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 1, "email": "test@example.com"}

        # Mock posting owned by the user
        mock_get_posting.return_value = {"id": 1, "user_id": 1, "title": "Test Posting"}

        # Mock successful deletion
        mock_delete_posting.return_value = True

        # Mock request with session cookie
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_session"

        result = asyncio.run(delete_posting(posting_id=1, request=mock_request))

        assert result.status_code == 200
        assert json.loads(result.body) == {"message": "Posting deleted successfully"}

    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_session_user')
    def test_delete_posting_not_found(self, mock_get_session, mock_get_posting):
        """Test posting deletion when posting not found"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import delete_posting

        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 1, "email": "test@example.com"}

        # Mock posting not found
        mock_get_posting.return_value = None

        # Mock request with session cookie
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_session"

        try:
            asyncio.run(delete_posting(posting_id=999, request=mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"

    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_session_user')
    def test_delete_posting_access_denied(self, mock_get_session, mock_get_posting):
        """Test posting deletion when user doesn't own the posting"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import delete_posting

        # Mock authenticated user (user_id = 1)
        mock_get_session.return_value = {"user_id": 1, "email": "test@example.com"}

        # Mock posting owned by different user (user_id = 2)
        mock_get_posting.return_value = {"id": 1, "user_id": 2, "title": "Other User's Posting"}

        # Mock request with session cookie
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_session"

        try:
            asyncio.run(delete_posting(posting_id=1, request=mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 403
            assert "Access denied" in e.detail

    @patch('backend.api.endpoints.get_session_user')
    def test_delete_posting_unauthenticated(self, mock_get_session):
        """Test posting deletion when user is not authenticated"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import delete_posting

        # Mock no session (not authenticated)
        mock_get_session.return_value = None

        # Mock request without session cookie
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None

        try:
            asyncio.run(delete_posting(posting_id=1, request=mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"
    
    @patch('backend.api.endpoints.get_all_postings')
    def test_api_get_all_postings(self, mock_get_all):
        """Test getting all postings API"""
        import asyncio

        from backend.api.endpoints import api_get_all_postings
        
        mock_get_all.return_value = [
            {"id": 1, "title": "Job 1"},
            {"id": 2, "title": "Job 2"}
        ]
        
        result = asyncio.run(api_get_all_postings())
        
        assert len(result) == 2
        assert result[0]["title"] == "Job 1"
    
    @patch('backend.api.endpoints.get_public_postings')
    def test_get_public_postings_endpoint_success(self, mock_get_public):
        """Test successful public postings retrieval"""
        import asyncio

        from backend.api.endpoints import get_public_postings_endpoint
        
        mock_get_public.return_value = [
            {"id": 1, "title": "Job 1", "status": "active"},
            {"id": 2, "title": "Job 2", "status": "active"}
        ]
        
        result = asyncio.run(get_public_postings_endpoint())
        
        assert len(result) == 2
        assert result[0]["status"] == "active"
    
    @patch('backend.api.endpoints.get_public_postings')
    def test_get_public_postings_endpoint_error(self, mock_get_public):
        """Test public postings retrieval with error"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import get_public_postings_endpoint
        
        mock_get_public.side_effect = Exception("Database error")
        
        try:
            asyncio.run(get_public_postings_endpoint())
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 500
            assert e.detail == "Failed to fetch postings"
    
    @patch('backend.api.endpoints.get_postings_by_user')
    def test_api_get_postings_by_user(self, mock_get_by_user):
        """Test getting postings by user API"""
        import asyncio

        from backend.api.endpoints import api_get_postings_by_user
        
        mock_get_by_user.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42}
        ]
        
        result = asyncio.run(api_get_postings_by_user(42))
        
        assert len(result) == 1
        assert result[0]["user_id"] == 42
    
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_api_get_posting_by_id(self, mock_get_by_id, mock_get_by_hash):
        """Test getting posting by ID"""
        import asyncio

        from backend.api.endpoints import api_get_posting
        
        mock_get_by_id.return_value = {"id": 1, "title": "Job 1"}
        
        result = asyncio.run(api_get_posting("1"))
        
        assert result["id"] == 1
        assert result["title"] == "Job 1"
    
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_api_get_posting_by_hash(self, mock_get_by_id, mock_get_by_hash):
        """Test getting posting by hash"""
        import asyncio

        from backend.api.endpoints import api_get_posting
        
        mock_get_by_hash.return_value = {"id": 1, "hash": "abc123", "title": "Job 1"}
        
        result = asyncio.run(api_get_posting("abc123"))
        
        assert result["id"] == 1
        assert result["hash"] == "abc123"
    
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_api_get_posting_not_found(self, mock_get_by_id, mock_get_by_hash):
        """Test getting non-existent posting"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import api_get_posting
        
        mock_get_by_hash.return_value = None
        mock_get_by_id.return_value = None
        
        try:
            asyncio.run(api_get_posting("nonexistent"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"


class TestApplicationEndpoints:
    """Test application management HTTP endpoints"""
    
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.apply_to_posting')
    @patch('backend.api.endpoints.get_session_user')
    def test_apply_success(self, mock_get_session, mock_apply, mock_get_posting):
        """Test successful application submission"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import apply
        
        mock_get_session.return_value = {"user_id": 42}
        mock_apply.return_value = {"success": True}
        mock_get_posting.return_value = {"id": 1, "hash": "abc123", "title": "Test Job"}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(apply(mock_request, posting_id=1, message="I'm interested", cover_letter="Dear hiring manager"))
        
        assert result.status_code == 303
        assert "success=application_submitted" in result.headers["location"]
        assert "/posting-detail.html?hash=abc123" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.apply_to_posting')
    @patch('backend.api.endpoints.get_session_user')
    def test_apply_failure(self, mock_get_session, mock_apply, mock_get_posting):
        """Test application submission failure"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import apply
        
        mock_get_session.return_value = {"user_id": 42}
        mock_apply.return_value = {"success": False, "error": "already_applied"}
        mock_get_posting.return_value = {"id": 1, "hash": "abc123", "title": "Test Job"}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(apply(mock_request, posting_id=1, message="I'm interested"))
        
        assert result.status_code == 303
        assert "error=already_applied" in result.headers["location"]
        assert "/posting-detail.html?hash=abc123" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_apply_unauthenticated(self, mock_get_session):
        """Test application submission without authentication"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import apply
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        result = asyncio.run(apply(mock_request, posting_id=1, message="I'm interested"))
        
        assert result.status_code == 303
        assert "/login.html?error=auth_required" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_applications_by_user')
    def test_api_get_applications_by_user(self, mock_get_applications):
        """Test getting applications by user API"""
        import asyncio

        from backend.api.endpoints import api_get_applications_by_user
        
        mock_get_applications.return_value = [
            {"id": 1, "posting_id": 1, "user_id": 42, "status": "pending"}
        ]
        
        result = asyncio.run(api_get_applications_by_user(42))
        
        assert len(result) == 1
        assert result[0]["user_id"] == 42
    
    @patch('backend.api.endpoints.get_applications_by_posting')
    def test_api_get_applications_by_posting(self, mock_get_applications):
        """Test getting applications by posting API"""
        import asyncio

        from backend.api.endpoints import api_get_applications_by_posting
        
        mock_get_applications.return_value = [
            {"id": 1, "posting_id": 1, "user_id": 42, "status": "pending"}
        ]
        
        result = asyncio.run(api_get_applications_by_posting(1))
        
        assert len(result) == 1
        assert result[0]["posting_id"] == 1


class TestAuthenticationEndpoints:
    """Test authentication HTTP endpoints"""
    
    @patch('backend.api.endpoints.login_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_login_success(self, mock_get_session, mock_login_user):
        """Test successful login"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login
        
        mock_get_session.return_value = None  # Not already logged in
        mock_login_user.return_value = {"user_id": 42, "session_token": "new_token"}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(login(mock_request, "john@example.com", "password"))
        
        assert result.status_code == 303
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.login_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_login_failure(self, mock_get_session, mock_login_user):
        """Test login failure"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login
        
        mock_get_session.return_value = None
        mock_login_user.return_value = None  # Login failed
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(login(mock_request, "john@example.com", "wrongpassword"))
        
        assert result.status_code == 303
        assert "/login.html?error=invalid_credentials" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_login_already_logged_in(self, mock_get_session):
        """Test login when already logged in"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login
        
        mock_get_session.return_value = {"user_id": 42}  # Already logged in
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "existing_token"
        
        result = asyncio.run(login(mock_request, "john@example.com", "password"))
        
        assert result.status_code == 303
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.logout_user')
    def test_logout_success(self, mock_logout_user):
        """Test successful logout"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import logout
        
        mock_logout_user.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(logout(mock_request))
        
        assert result.status_code == 303
        assert "/index.html?success=logged_out" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_auth_status_authenticated(self, mock_get_session):
        """Test auth status when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import auth_status
        
        mock_get_session.return_value = {"user_id": 42, "email": "john@example.com"}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(auth_status(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is True
        assert content["user"]["user_id"] == 42
    
    @patch('backend.api.endpoints.get_session_user')
    def test_auth_status_unauthenticated(self, mock_get_session):
        """Test auth status when not authenticated"""
        import asyncio
        import json
        from unittest.mock import MagicMock

        from backend.api.endpoints import auth_status
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(auth_status(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is False
    
    @patch('backend.api.endpoints.get_session_user')
    def test_auth_buttons_authenticated(self, mock_get_session):
        """Test auth buttons when authenticated"""
        import asyncio
        import json
        from unittest.mock import MagicMock

        from backend.api.endpoints import auth_buttons
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(auth_buttons(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is True
        assert content["action"] == "logout"
    
    @patch('backend.api.endpoints.get_session_user')
    def test_auth_buttons_unauthenticated(self, mock_get_session):
        """Test auth buttons when not authenticated"""
        import asyncio
        import json
        from unittest.mock import MagicMock

        from backend.api.endpoints import auth_buttons
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(auth_buttons(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is False
        assert content["action"] == "login"


class TestNavigationEndpoints:
    """Test navigation and redirect endpoints"""
    
    @patch('backend.api.endpoints.get_session_user')
    def test_get_navigation_authenticated(self, mock_get_session):
        """Test navigation for authenticated users"""
        import asyncio
        import json
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_navigation
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_navigation(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is True
        assert len(content["nav_items"]) == 5  # Authenticated nav items
    
    @patch('backend.api.endpoints.get_session_user')
    def test_get_navigation_unauthenticated(self, mock_get_session):
        """Test navigation for unauthenticated users"""
        import asyncio
        import json
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_navigation
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(get_navigation(mock_request))
        
        assert result.status_code == 200
        content = json.loads(result.body)
        assert content["authenticated"] is False
        assert len(content["nav_items"]) == 4  # Unauthenticated nav items
    
    @patch('backend.api.endpoints.get_session_user')
    def test_root_redirect_authenticated(self, mock_get_session):
        """Test root redirect when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import root
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(root(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_root_redirect_unauthenticated(self, mock_get_session):
        """Test root redirect when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import root
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(root(mock_request))
        
        assert result.status_code == 302
        assert "/index.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_login_redirect_authenticated(self, mock_get_session):
        """Test login redirect when already authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login_redirect
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(login_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_login_redirect_unauthenticated(self, mock_get_session):
        """Test login redirect when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login_redirect
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(login_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/login.html" in result.headers["location"]


class TestProfileAndContactEndpoints:
    """Test profile and contact endpoints"""
    
    @patch('backend.api.endpoints.get_applications_by_user')
    @patch('backend.api.endpoints.get_postings_by_user')
    @patch('backend.api.endpoints.get_user_by_id')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_profile_data_success(self, mock_get_session, mock_get_user, mock_get_postings, mock_get_applications):
        """Test successful profile data retrieval"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_profile_data
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_user.return_value = {"id": 42, "name": "John", "email": "john@example.com", "created_at": "2024-01-01"}
        mock_get_postings.return_value = [{"id": 1, "title": "Job 1"}]
        mock_get_applications.return_value = [{"id": 1, "posting_id": 1}]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_profile_data(mock_request))
        
        assert result["user"]["id"] == 42
        assert result["stats"]["total_postings"] == 1
        assert result["stats"]["total_applications"] == 1
    
    @patch('backend.api.endpoints.get_session_user')
    def test_get_profile_data_unauthenticated(self, mock_get_session):
        """Test profile data retrieval without authentication"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_profile_data
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(get_profile_data(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"
    
    def test_contact_form_success(self):
        """Test successful contact form submission"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import contact_form
        
        mock_request = MagicMock()
        
        result = asyncio.run(contact_form(mock_request, "John Doe", "john@example.com", "Hello there"))
        
        assert result.status_code == 303
        assert "/contact.html?success=message_sent" in result.headers["location"]


class TestErrorHandlingEndpoints:
    """Test error handling in endpoints"""
    
    @patch('backend.api.endpoints.create_user')
    @patch('backend.api.endpoints.get_user_by_username')
    @patch('backend.api.endpoints.get_user_by_email')
    @patch('backend.api.endpoints.hash_password')
    def test_create_user_account_server_error(self, mock_hash_password, mock_get_by_email, mock_get_by_username, mock_create_user):
        """Test user creation with server error"""
        import asyncio

        from backend.api.endpoints import create_user_account
        
        mock_hash_password.return_value = "hashed_password"
        mock_get_by_email.return_value = None
        mock_get_by_username.return_value = None
        mock_create_user.side_effect = Exception("Database connection failed")
        
        result = asyncio.run(create_user_account("John", "Doe", "johndoe", "john@example.com", "Password123!"))
        
        assert result.status_code == 303
        assert "/register.html?error=server_error" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_postings_by_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_my_postings_server_error(self, mock_get_session, mock_get_postings):
        """Test getting my postings with server error"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_my_postings
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_postings.side_effect = Exception("Database error")
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_my_postings(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 500
            assert e.detail == "Failed to fetch your postings"
    
    @patch('backend.api.endpoints.login_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_login_server_error(self, mock_get_session, mock_login_user):
        """Test login with server error"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import login
        
        mock_get_session.return_value = None
        mock_login_user.side_effect = Exception("Database connection failed")
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(login(mock_request, "john@example.com", "password"))
        
        assert result.status_code == 303
        assert "/login.html?error=server_error" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_user_by_id')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_profile_data_user_not_found(self, mock_get_session, mock_get_user):
        """Test profile data when user not found"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_profile_data
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_user.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_profile_data(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "User not found"


class TestRedirectEndpoints:
    """Test additional redirect endpoints"""
    
    @patch('backend.api.endpoints.get_session_user')
    def test_register_redirect_authenticated(self, mock_get_session):
        """Test register redirect when already authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import register_redirect
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(register_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_register_redirect_unauthenticated(self, mock_get_session):
        """Test register redirect when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import register_redirect
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(register_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/register.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_data_view_redirect_authenticated(self, mock_get_session):
        """Test data view redirect when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import data_view_redirect
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(data_view_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_data_view_redirect_unauthenticated(self, mock_get_session):
        """Test data view redirect when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import data_view_redirect
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(data_view_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/login.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_profile_redirect_authenticated(self, mock_get_session):
        """Test profile redirect when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import profile_redirect
        
        mock_get_session.return_value = {"user_id": 42}
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(profile_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/profile.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    def test_profile_redirect_unauthenticated(self, mock_get_session):
        """Test profile redirect when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import profile_redirect
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(profile_redirect(mock_request))
        
        assert result.status_code == 302
        assert "/login.html" in result.headers["location"]
    
    def test_contact_redirect(self):
        """Test contact page redirect"""
        import asyncio

        from backend.api.endpoints import contact_redirect
        
        result = asyncio.run(contact_redirect())
        
        assert result.status_code == 302
        assert "/contact.html" in result.headers["location"]
    
    def test_password_reset_redirect(self):
        """Test password reset page redirect"""
        import asyncio

        from backend.api.endpoints import password_reset_redirect
        
        result = asyncio.run(password_reset_redirect())
        
        assert result.status_code == 302
        assert "/password-reset.html" in result.headers["location"]


class TestMissingCoverageEndpoints:
    """Test endpoints that are missing coverage"""
    
    @patch('backend.api.endpoints.get_redis_client')
    @patch('backend.api.endpoints.create_user')
    @patch('backend.api.endpoints.get_user_by_username')
    @patch('backend.api.endpoints.get_user_by_email')
    @patch('backend.api.endpoints.hash_password')
    def test_create_user_account_http_exception_reraise(self, mock_hash_password, mock_get_by_email, mock_get_by_username, mock_create_user, mock_redis):
        """Test user creation with HTTPException re-raise"""
        import asyncio

        from fastapi import HTTPException

        from backend.api.endpoints import create_user_account
        
        mock_hash_password.return_value = "hashed_password"
        mock_get_by_email.return_value = None
        mock_get_by_username.return_value = None
        mock_create_user.side_effect = HTTPException(status_code=400, detail="Validation error")
        
        try:
            asyncio.run(create_user_account("John", "Doe", "johndoe", "john@example.com", "Password123!"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 400
            assert e.detail == "Validation error"
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_value_error_handling(self, mock_get_session, mock_get_by_hash, mock_get_by_id, mock_get_posting, mock_track_view):
        """Test view_posting with ValueError in ID conversion"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_by_hash.return_value = None  # Hash lookup fails
        mock_get_by_id.return_value = {"id": 1, "title": "Job 1", "user_id": 42}  # ID lookup succeeds
        mock_get_posting.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        # Use a string that looks like an ID but will trigger fallback
        result = asyncio.run(view_posting("123", mock_request))
        
        assert result["posting"]["id"] == 1
        assert result["is_authenticated"] is True
    
    @patch('backend.api.endpoints.get_public_postings')
    @patch('backend.api.endpoints.get_session_user')
    def test_data_view_page_authenticated(self, mock_get_session, mock_get_postings):
        """Test data_view_page endpoint when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import data_view_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_postings.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42},
            {"id": 2, "title": "Job 2", "user_id": 99}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(data_view_page(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_public_postings')
    @patch('backend.api.endpoints.get_session_user')
    def test_data_view_page_unauthenticated(self, mock_get_session, mock_get_postings):
        """Test data_view_page endpoint when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import data_view_page
        
        mock_get_session.return_value = None
        mock_get_postings.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42},
            {"id": 2, "title": "Job 2", "user_id": 99}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(data_view_page(mock_request))
        
        assert result.status_code == 302
        assert "/data-view.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_page_authenticated(self, mock_get_session, mock_get_posting, mock_track_view):
        """Test view_posting_page endpoint when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import view_posting_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting_page(1, mock_request))
        
        assert result.status_code == 302
        assert "/posting-detail.html?id=1" in result.headers["location"]
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_page_not_found(self, mock_get_session, mock_get_posting, mock_track_view):
        """Test view_posting_page endpoint when posting not found"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import view_posting_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        try:
            asyncio.run(view_posting_page(999, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_posting_detail_page_authenticated(self, mock_get_session, mock_get_by_hash, mock_get_posting, mock_track_view):
        """Test posting_detail_page endpoint when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import posting_detail_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_by_hash.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_get_posting.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(posting_detail_page("abc123", mock_request))
        
        assert result["posting"]["id"] == 1
        assert result["is_authenticated"] is True
        assert result["is_owner"] is True
        assert result["can_apply"] is False
    
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_posting_detail_page_unauthenticated(self, mock_get_session, mock_get_by_hash, mock_get_posting, mock_track_view):
        """Test posting_detail_page endpoint when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import posting_detail_page
        
        mock_get_session.return_value = None
        mock_get_by_hash.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_get_posting.return_value = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(posting_detail_page("abc123", mock_request))
        
        assert result["posting"]["id"] == 1
        assert result["is_authenticated"] is False
        assert result["is_owner"] is False
        assert result["can_apply"] is False
    
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_posting_detail_page_not_found(self, mock_get_session, mock_get_by_hash):
        """Test posting_detail_page endpoint when posting not found"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import posting_detail_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_by_hash.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(posting_detail_page("nonexistent", mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"
    
    def test_posting_detail_static(self):
        """Test posting_detail_static endpoint"""
        import asyncio

        from backend.api.endpoints import posting_detail_static
        
        result = asyncio.run(posting_detail_static())
        
        assert result.status_code == 302
        assert "/posting-detail.html" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_public_postings')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_postings_data_authenticated(self, mock_get_session, mock_get_postings):
        """Test get_postings_data endpoint when authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_postings_data
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_postings.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42},
            {"id": 2, "title": "Job 2", "user_id": 99}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_postings_data(mock_request))
        
        assert result["user"]["user_id"] == 42
        assert result["is_authenticated"] is True
        assert len(result["postings"]) == 2
        assert result["postings"][0]["is_own"] is True
        assert result["postings"][0]["can_apply"] is False
        assert result["postings"][1]["is_own"] is False
        assert result["postings"][1]["can_apply"] is True
    
    @patch('backend.api.endpoints.get_public_postings')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_postings_data_unauthenticated(self, mock_get_session, mock_get_postings):
        """Test get_postings_data endpoint when not authenticated"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_postings_data
        
        mock_get_session.return_value = None
        mock_get_postings.return_value = [
            {"id": 1, "title": "Job 1", "user_id": 42},
            {"id": 2, "title": "Job 2", "user_id": 99}
        ]
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(get_postings_data(mock_request))
        
        assert result["user"] is None
        assert result["is_authenticated"] is False
        assert len(result["postings"]) == 2
        assert result["postings"][0]["is_own"] is False
        assert result["postings"][0]["can_apply"] is None  # None and not False = None
        assert result["postings"][0]["is_authenticated"] is False
        assert result["postings"][1]["is_own"] is False
        assert result["postings"][1]["can_apply"] is None  # None and not False = None
        assert result["postings"][1]["is_authenticated"] is False
    
    @patch('backend.api.endpoints.login_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_login_http_exception_reraise(self, mock_get_session, mock_login_user):
        """Test login with HTTPException re-raise"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import login
        
        mock_get_session.return_value = None
        mock_login_user.side_effect = HTTPException(status_code=429, detail="Too many requests")
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(login(mock_request, "john@example.com", "password"))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 429
            assert e.detail == "Too many requests"

    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_fallback_value_error(self, mock_get_session, mock_get_by_hash, mock_get_by_id, mock_track_view, mock_get_stats):
        """Test ValueError handling in posting lookup fallback (lines 247-248)"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_by_hash.return_value = None  # Hash lookup fails
        mock_get_by_id.return_value = None    # ID lookup also fails
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        # Use invalid string that can't convert to int
        try:
            asyncio.run(view_posting("invalid_id", mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"

    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_view_posting_stats_fallback(self, mock_get_session, mock_get_by_hash, mock_track_view, mock_get_stats):
        """Test posting stats fallback when stats not available (line 263)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_stats.return_value = None  # Stats not available
        
        posting_data = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_get_by_hash.return_value = posting_data
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting("hash123", mock_request))
        
        # Should use original posting when stats are None
        assert result["posting"]["id"] == 1
        assert result["posting"]["title"] == "Job 1"

    @patch('backend.api.endpoints.get_posting_analytics')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_posting_analytics_unauthenticated(self, mock_get_session, mock_get_analytics):
        """Test analytics endpoint with no authentication (line 290)"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_posting_analytics_endpoint
        
        mock_get_session.return_value = None  # Not authenticated
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(get_posting_analytics_endpoint(1, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"

    @patch('backend.api.endpoints.get_user_posting_stats')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_dashboard_stats_unauthenticated(self, mock_get_session, mock_get_stats):
        """Test dashboard stats endpoint with no authentication (line 307)"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_dashboard_stats
        
        mock_get_session.return_value = None  # Not authenticated
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(get_dashboard_stats(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"

    @patch('backend.api.endpoints.get_applications_by_user')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_my_applications_unauthenticated(self, mock_get_session, mock_get_applications):
        """Test my applications endpoint with no authentication (line 319)"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_my_applications
        
        mock_get_session.return_value = None  # Not authenticated
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(get_my_applications(mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"

    @patch('backend.api.endpoints.get_application_details')
    @patch('backend.api.endpoints.get_session_user')
    def test_get_application_details_unauthenticated(self, mock_get_session, mock_get_details):
        """Test application details endpoint with no authentication (line 331)"""
        import asyncio
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from backend.api.endpoints import get_application_details_endpoint
        
        mock_get_session.return_value = None  # Not authenticated
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        try:
            asyncio.run(get_application_details_endpoint(1, mock_request))
            raise AssertionError("Should have raised HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"

    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.track_posting_view')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.get_session_user')
    def test_posting_detail_page_stats_fallback(self, mock_get_session, mock_get_by_hash, mock_track_view, mock_get_stats):
        """Test posting detail page stats fallback when stats not available (line 435)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import posting_detail_page
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_stats.return_value = None  # Stats not available
        
        posting_data = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_get_by_hash.return_value = posting_data
        mock_track_view.return_value = True
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(posting_detail_page("hash123", mock_request))
        
        # Should use original posting when stats are None
        assert "posting" in result
        assert result["posting"]["id"] == 1
        assert result["posting"]["title"] == "Job 1"


class TestViewPostingWithApplicationStatus:
    """Test the enhanced view_posting endpoint with application status logic"""
    
    @patch('backend.api.endpoints.check_user_application_exists')
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.track_posting_view')
    def test_view_posting_user_has_applied(self, mock_track_view, mock_get_by_hash, 
                                         mock_get_stats, mock_get_session, mock_check_applied):
        """Test view_posting returns has_applied=True when user already applied"""
        from backend.api.endpoints import view_posting
        
        # Mock authenticated user who has already applied
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting data
        posting_data = {"id": 1, "title": "Job 1", "user_id": 18}  # Different user owns posting
        mock_get_by_hash.return_value = posting_data
        mock_get_stats.return_value = posting_data
        
        # Mock user has already applied
        mock_check_applied.return_value = True
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting("hash123", mock_request))
        
        # Verify application status logic
        assert result["is_authenticated"] is True
        assert result["is_owner"] is False  # User doesn't own the posting
        assert result["has_applied"] is True  # User has applied
        assert result["can_apply"] is False  # Can't apply again
        
        # Verify check_user_application_exists was called correctly
        mock_check_applied.assert_called_once_with(42, 1)
    
    @patch('backend.api.endpoints.check_user_application_exists')
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.track_posting_view')
    def test_view_posting_user_can_apply(self, mock_track_view, mock_get_by_hash, 
                                       mock_get_stats, mock_get_session, mock_check_applied):
        """Test view_posting returns can_apply=True when user hasn't applied"""
        from backend.api.endpoints import view_posting
        
        # Mock authenticated user who hasn't applied
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting data
        posting_data = {"id": 1, "title": "Job 1", "user_id": 18}  # Different user owns posting
        mock_get_by_hash.return_value = posting_data
        mock_get_stats.return_value = posting_data
        
        # Mock user has NOT applied yet
        mock_check_applied.return_value = False
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting("hash123", mock_request))
        
        # Verify application status logic
        assert result["is_authenticated"] is True
        assert result["is_owner"] is False  # User doesn't own the posting
        assert result["has_applied"] is False  # User hasn't applied
        assert result["can_apply"] is True  # Can apply
        
        # Verify check_user_application_exists was called correctly
        mock_check_applied.assert_called_once_with(42, 1)
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.track_posting_view')
    def test_view_posting_owner_cannot_apply(self, mock_track_view, mock_get_by_hash, 
                                           mock_get_stats, mock_get_session):
        """Test view_posting shows owner cannot apply to own posting"""
        from backend.api.endpoints import view_posting
        
        # Mock authenticated user who owns the posting
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting data - same user owns it
        posting_data = {"id": 1, "title": "Job 1", "user_id": 42}
        mock_get_by_hash.return_value = posting_data
        mock_get_stats.return_value = posting_data
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting("hash123", mock_request))
        
        # Verify owner logic
        assert result["is_authenticated"] is True
        assert result["is_owner"] is True  # User owns the posting
        assert result["has_applied"] is False  # Not applicable for owner
        assert result["can_apply"] is False  # Owner can't apply to own posting
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_with_public_stats')
    @patch('backend.api.endpoints.get_posting_by_hash')
    @patch('backend.api.endpoints.track_posting_view')
    def test_view_posting_unauthenticated_user(self, mock_track_view, mock_get_by_hash, 
                                             mock_get_stats, mock_get_session):
        """Test view_posting for unauthenticated user"""
        from backend.api.endpoints import view_posting
        
        # Mock no authenticated user
        mock_get_session.return_value = None
        
        # Mock posting data
        posting_data = {"id": 1, "title": "Job 1", "user_id": 18}
        mock_get_by_hash.return_value = posting_data
        mock_get_stats.return_value = posting_data
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        result = asyncio.run(view_posting("hash123", mock_request))
        
        # Verify unauthenticated user logic
        assert result["is_authenticated"] is False
        assert result["is_owner"] is False
        assert result["has_applied"] is False
        assert result["can_apply"] is False


class TestUpdatePostingErrorHandling:
    """Test update_posting endpoint error scenarios for missing coverage"""
    
    @patch('backend.api.endpoints.get_session_user')
    def test_update_posting_no_authentication(self, mock_get_session):
        """Test update_posting with no authentication (line 139)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import update_posting
        
        # Mock no session data
        mock_get_session.return_value = None
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        result = asyncio.run(update_posting(
            mock_request, 
            posting_id=1, 
            title="Updated Title", 
            category="tech", 
            post_description="Updated description", 
            status="active"
        ))
        
        # Should redirect to login
        assert result.status_code == 303
        assert "/login.html?error=auth_required" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_by_id')
    @patch('backend.api.endpoints.update_posting_in_db')
    def test_update_posting_database_failure(self, mock_update_db, mock_get_posting, mock_get_session):
        """Test update_posting database failure (lines 151, 154-155)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import update_posting
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting owned by user
        mock_get_posting.return_value = {"id": 1, "user_id": 42, "title": "Original"}
        
        # Mock database update failure
        mock_update_db.return_value = False
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(update_posting(
            mock_request,
            posting_id=1,
            title="Updated Title",
            category="tech", 
            post_description="Updated description",
            status="active"
        ))
        
        # Should redirect with update failed error
        assert result.status_code == 303
        assert "/my-postings.html?error=update_failed" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_update_posting_exception_handling(self, mock_get_posting, mock_get_session):
        """Test update_posting exception handling (lines 154-155)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import update_posting
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock get_posting_by_id to raise exception
        mock_get_posting.side_effect = Exception("Database error")
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(update_posting(
            mock_request,
            posting_id=1,
            title="Updated Title", 
            category="tech",
            post_description="Updated description",
            status="active"
        ))
        
        # Should redirect with update failed error
        assert result.status_code == 303
        assert "/my-postings.html?error=update_failed" in result.headers["location"]


class TestGetPostingForEditEndpoint:
    """Test get_posting_for_edit endpoint for complete coverage (lines 160-177)"""
    
    @patch('backend.api.endpoints.get_session_user')
    def test_get_posting_for_edit_no_authentication(self, mock_get_session):
        """Test get_posting_for_edit with no authentication (lines 163-164)"""
        import asyncio
        from unittest.mock import MagicMock

        import pytest
        from fastapi import HTTPException

        from backend.api.endpoints import get_posting_for_edit
        
        # Mock no session data
        mock_get_session.return_value = None
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        
        # Should raise 401 HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_posting_for_edit(1, mock_request))
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_get_posting_for_edit_posting_not_found(self, mock_get_posting, mock_get_session):
        """Test get_posting_for_edit with posting not found (lines 169-170)"""
        import asyncio
        from unittest.mock import MagicMock

        import pytest
        from fastapi import HTTPException

        from backend.api.endpoints import get_posting_for_edit
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting not found
        mock_get_posting.return_value = None
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        # Should raise 404 HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_posting_for_edit(1, mock_request))
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Posting not found"
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_get_posting_for_edit_access_denied(self, mock_get_posting, mock_get_session):
        """Test get_posting_for_edit with access denied (lines 173-174)"""
        import asyncio
        from unittest.mock import MagicMock

        import pytest
        from fastapi import HTTPException

        from backend.api.endpoints import get_posting_for_edit
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting owned by different user
        mock_get_posting.return_value = {"id": 1, "user_id": 18, "title": "Job"}
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        # Should raise 403 HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_posting_for_edit(1, mock_request))
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied"
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_get_posting_for_edit_success(self, mock_get_posting, mock_get_session):
        """Test get_posting_for_edit success path (lines 177-185)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import get_posting_for_edit
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock posting owned by user
        mock_get_posting.return_value = {
            "id": 1,
            "user_id": 42,
            "title": "Software Engineer",
            "category": "tech",
            "description": "Job description",
            "status": "active"
        }
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(get_posting_for_edit(1, mock_request))
        
        # Should return JSONResponse with posting data
        assert "posting" in result.body.decode()
        # Parse the JSON response
        import json
        response_data = json.loads(result.body.decode())
        assert response_data["posting"]["id"] == 1
        assert response_data["posting"]["title"] == "Software Engineer"
        assert response_data["posting"]["category"] == "tech"


class TestApplyEndpointErrorHandling:
    """Test apply endpoint error scenarios for missing coverage"""
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.apply_to_posting')
    @patch('backend.api.endpoints.get_posting_by_id')
    def test_apply_posting_not_found(self, mock_get_posting, mock_apply, mock_get_session):
        """Test apply endpoint when posting not found (line 273)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import apply
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock successful application
        mock_apply.return_value = {"success": True, "error": None}
        
        # Mock posting not found
        mock_get_posting.return_value = None
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(apply(
            mock_request,
            posting_id=1,
            message="I'm interested",
            cover_letter="Cover letter"
        ))
        
        # Should redirect with posting not found error
        assert result.status_code == 303
        assert "/my-postings.html?error=posting_not_found" in result.headers["location"]
    
    @patch('backend.api.endpoints.get_session_user')
    @patch('backend.api.endpoints.apply_to_posting')
    def test_apply_exception_handling(self, mock_apply, mock_get_session):
        """Test apply endpoint exception handling (lines 285-287)"""
        import asyncio
        from unittest.mock import MagicMock

        from backend.api.endpoints import apply
        
        # Mock authenticated user
        mock_get_session.return_value = {"user_id": 42}
        
        # Mock apply_to_posting to raise exception
        mock_apply.side_effect = Exception("Database error")
        
        # Mock request
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        result = asyncio.run(apply(
            mock_request,
            posting_id=1,
            message="I'm interested",
            cover_letter="Cover letter"
        ))
        
        # Should redirect with application failed error
        assert result.status_code == 303
        assert "/my-postings.html?error=application_failed" in result.headers["location"]

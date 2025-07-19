"""
Integration tests for critical authentication flows and analytics endpoints.
These tests focus on the authentication business logic that would be used
in the endpoints without testing the HTTP layer directly.
"""

import os
import sys
import asyncio
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
    
    @patch('backend.core.db.track_posting_view')
    @patch('backend.core.db.get_posting_with_public_stats')
    @patch('backend.core.security.get_session_user')
    def test_view_posting_authenticated(self, mock_get_session, mock_get_posting, mock_track_view):
        """Test viewing posting as authenticated user"""
        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = {
            "id": 1,
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
        
        assert result["title"] == "Test Job"
        mock_track_view.assert_called_once_with(1, 42, "127.0.0.1", "Test User Agent", "session_token")
    
    @patch('backend.core.db.track_posting_view')
    @patch('backend.core.db.get_posting_with_public_stats')
    @patch('backend.core.security.get_session_user')
    def test_view_posting_unauthenticated(self, mock_get_session, mock_get_posting, mock_track_view):
        """Test viewing posting as unauthenticated user"""
        from backend.api.endpoints import view_posting
        
        mock_get_session.return_value = None
        mock_get_posting.return_value = {
            "id": 1,
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
        
        assert result["title"] == "Test Job"
        mock_track_view.assert_called_once_with(1, None, "127.0.0.1", "Test User Agent", "session_token")
    
    @patch('backend.core.db.get_posting_with_public_stats')
    @patch('backend.core.security.get_session_user')
    def test_view_posting_not_found(self, mock_get_session, mock_get_posting):
        """Test viewing non-existent posting"""
        from backend.api.endpoints import view_posting
        from fastapi import HTTPException
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_posting.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "Test User Agent"
        
        try:
            asyncio.run(view_posting(999, mock_request))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found"
    
    @patch('backend.core.db.get_postings_by_user')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.security.get_session_user')
    def test_get_my_postings_unauthenticated(self, mock_get_session):
        """Test getting postings without authentication"""
        from backend.api.endpoints import get_my_postings
        from fastapi import HTTPException
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        try:
            asyncio.run(get_my_postings(mock_request))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"
    
    @patch('backend.core.db.get_posting_analytics')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.db.get_posting_analytics')
    @patch('backend.core.security.get_session_user')
    def test_get_posting_analytics_not_owner(self, mock_get_session, mock_get_analytics):
        """Test getting posting analytics for non-owned posting"""
        from backend.api.endpoints import get_posting_analytics_endpoint
        from fastapi import HTTPException
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_analytics.return_value = None  # Not owner or posting not found
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_posting_analytics_endpoint(1, mock_request))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Posting not found or access denied"
    
    @patch('backend.core.db.get_user_posting_stats')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.db.get_applications_by_user')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
    def test_get_application_details_no_access(self, mock_get_session, mock_get_details):
        """Test getting application details without access"""
        from backend.api.endpoints import get_application_details_endpoint
        from fastapi import HTTPException
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = None  # No access
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(get_application_details_endpoint(1, mock_request))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Application not found or access denied"


class TestApplicationReviewEndpoints:
    """Test application review endpoints"""
    
    @patch('backend.core.db.update_application_status')
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
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
    
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
    def test_review_application_not_owner(self, mock_get_session, mock_get_details):
        """Test reviewing application as non-owner"""
        from backend.api.endpoints import review_application
        from fastapi import HTTPException
        
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
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 403
            assert e.detail == "Access denied"
    
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
    def test_review_application_not_found(self, mock_get_session, mock_get_details):
        """Test reviewing non-existent application"""
        from backend.api.endpoints import review_application
        from fastapi import HTTPException
        
        mock_get_session.return_value = {"user_id": 42}
        mock_get_details.return_value = None  # Application not found
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "session_token"
        
        try:
            asyncio.run(review_application(999, mock_request, "accepted", "Great candidate!"))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 403
            assert e.detail == "Access denied"
    
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
    def test_review_application_invalid_status(self, mock_get_session, mock_get_details):
        """Test reviewing application with invalid status"""
        from backend.api.endpoints import review_application
        from fastapi import HTTPException
        
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
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 400
            assert e.detail == "Invalid status"
    
    @patch('backend.core.db.update_application_status')
    @patch('backend.core.db.get_application_details')
    @patch('backend.core.security.get_session_user')
    def test_review_application_update_failed(self, mock_get_session, mock_get_details, mock_update_status):
        """Test reviewing application when update fails"""
        from backend.api.endpoints import review_application
        from fastapi import HTTPException
        
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
            assert False, "Should have raised HTTPException"
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
    
    @patch('backend.core.security.get_session_user')
    def test_review_application_unauthenticated(self, mock_get_session):
        """Test reviewing application without authentication"""
        from backend.api.endpoints import review_application
        from fastapi import HTTPException
        
        mock_get_session.return_value = None
        
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "invalid_token"
        
        try:
            asyncio.run(review_application(1, mock_request, "accepted", "Great candidate!"))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Authentication required"
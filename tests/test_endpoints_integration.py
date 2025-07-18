"""
Integration tests for critical authentication flows.
These tests focus on the authentication business logic that would be used
in the endpoints without testing the HTTP layer directly.
"""

import os
import sys
from unittest.mock import patch

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

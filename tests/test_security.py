import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import pytest

from backend.core import security


def test_hash_and_verify_password():
    password = "Test123!"
    hashed = security.hash_password(password)

    assert isinstance(hashed, str)
    assert bcrypt.checkpw(password.encode(), hashed.encode())
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong", hashed) is False


@pytest.mark.parametrize("password,expected", [
    ("Aa1!", False),            # Too short
    ("aaaaaa", False),          # No uppercase, number, or special
    ("AAAAAA", False),          # No number or special
    ("Aaaaaa", False),          # No number or special
    ("Aaaaa1", False),          # No special
    ("Aaaaa!", False),          # No number
    ("Aaaa1!", True),           # Valid
    ("Password1!", True),       # Valid
])
def test_is_password_valid(password, expected):
    assert security.is_password_valid(password) is expected


def test_create_session():
    mock_redis = MagicMock()
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        session_token = security.create_session(42)
        
        assert isinstance(session_token, str)
        assert len(session_token) > 0
        mock_redis.setex.assert_called_once()
        
        # Check that the session data contains required fields
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("session:")
        assert call_args[0][1] == 604800  # 7 days in seconds
        session_data = json.loads(call_args[0][2])
        assert session_data["user_id"] == 42
        assert "created_at" in session_data
        assert "expires_at" in session_data


def test_get_session_user_valid():
    mock_redis = MagicMock()
    now = datetime.now(UTC)
    session_data = {
        "user_id": 42,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat()
    }
    mock_redis.get.return_value = json.dumps(session_data)
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.get_session_user("valid_token")
        
        assert result == session_data
        mock_redis.get.assert_called_once_with("session:valid_token")


def test_get_session_user_expired():
    mock_redis = MagicMock()
    now = datetime.now(UTC)
    session_data = {
        "user_id": 42,
        "created_at": now.isoformat(),
        "expires_at": (now - timedelta(days=1)).isoformat()  # Expired
    }
    mock_redis.get.return_value = json.dumps(session_data)
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.get_session_user("expired_token")
        
        assert result is None
        mock_redis.delete.assert_called_once_with("session:expired_token")


def test_get_session_user_invalid_token():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.get_session_user("invalid_token")
        
        assert result is None
        mock_redis.get.assert_called_once_with("session:invalid_token")


def test_get_session_user_no_token():
    result = security.get_session_user(None)
    assert result is None
    
    result = security.get_session_user("")
    assert result is None


def test_get_session_user_malformed_json():
    mock_redis = MagicMock()
    mock_redis.get.return_value = "invalid json"
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.get_session_user("malformed_token")
        
        assert result is None


def test_login_user_success(monkeypatch):
    mock_user = {
        "id": 42,
        "email": "test@example.com",
        "hashed_password": bcrypt.hashpw(b"Correct1!", bcrypt.gensalt()).decode()
    }
    mock_redis = MagicMock()

    monkeypatch.setattr(security, "get_user_by_email", lambda email: mock_user)
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.login_user("test@example.com", "Correct1!")
        
        assert result is not None
        assert result["user_id"] == 42
        assert result["email"] == "test@example.com"
        assert "session_token" in result
        assert isinstance(result["session_token"], str)


def test_login_user_fail(monkeypatch):
    monkeypatch.setattr(security, "get_user_by_email", lambda email: None)
    result = security.login_user("missing@example.com", "any")
    assert result is None

    mock_user = {
        "id": 99,
        "email": "test@example.com",
        "hashed_password": bcrypt.hashpw(b"RightPass1!", bcrypt.gensalt()).decode()
    }
    monkeypatch.setattr(security, "get_user_by_email", lambda email: mock_user)
    result = security.login_user("test@example.com", "WrongPass")
    assert result is None


def test_logout_user_success():
    mock_redis = MagicMock()
    mock_redis.exists.return_value = True
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.logout_user("valid_token")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("session:valid_token")
        mock_redis.delete.assert_called_once_with("session:valid_token")


def test_logout_user_fail():
    mock_redis = MagicMock()
    mock_redis.exists.return_value = False
    
    with patch('backend.core.security.get_redis_client', return_value=mock_redis):
        result = security.logout_user("invalid_token")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("session:invalid_token")
        mock_redis.delete.assert_not_called()


def test_logout_user_no_token():
    result = security.logout_user(None)
    assert result is False
    
    result = security.logout_user("")
    assert result is False

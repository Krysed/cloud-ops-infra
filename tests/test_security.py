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


def test_login_user_success(monkeypatch):
    mock_user = {
        "id": 42,
        "hashed_password": bcrypt.hashpw(b"Correct1!", bcrypt.gensalt()).decode()
    }

    monkeypatch.setattr(security, "get_user_by_email", lambda email: mock_user)
    result = security.login_user("test@example.com", "Correct1!")
    assert result == 42

def test_login_user_fail(monkeypatch):
    monkeypatch.setattr(security, "get_user_by_email", lambda email: None)
    assert security.login_user("missing@example.com", "any") is None

    mock_user = {
        "id": 99,
        "hashed_password": bcrypt.hashpw(b"RightPass1!", bcrypt.gensalt()).decode()
    }
    monkeypatch.setattr(security, "get_user_by_email", lambda email: mock_user)
    assert security.login_user("test@example.com", "WrongPass") is None


def test_logout_user(monkeypatch):
    deleted_keys = []

    class MockRedis:
        def exists(self, key):
            return key == "session:1"
        def delete(self, key):
            deleted_keys.append(key)
            return True

    monkeypatch.setattr(security, "get_redis_client", lambda: MockRedis())

    assert security.logout_user(1) is True
    assert "session:1" in deleted_keys
    assert security.logout_user(2) is False

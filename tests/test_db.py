from unittest.mock import MagicMock, patch

import pytest

from backend.core import db


def test_create_user(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = {"id": 42}
    user_id = db.create_user("John", "Doe", "johndoe", "john@example.com", "hashed_pwd")

    assert user_id == 42
    mock_cursor.execute.assert_called_once_with(
        """
            INSERT INTO users (name, surname, username, email, user_type, hashed_password)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """,
        ("John", "Doe", "johndoe", "john@example.com", "regular", "hashed_pwd")
    )
    patch_psycopg2_connect.return_value.commit.assert_called_once()

def test_get_user_by_id(patch_psycopg2_connect, mock_cursor):
    expected_user = {"id": 1, "email": "user@example.com"}
    mock_cursor.fetchone.return_value = expected_user

    user = db.get_user_by_id(1)

    assert user == expected_user
    mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))

def test_update_user_in_db_success(patch_psycopg2_connect, mock_cursor, mock_redis):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None, None, None, None]
    result = db.update_user_in_db(1, name="NewName", surname="NewSurname", username="NewUsername", email="new@example.com")

    assert result is True
    assert mock_cursor.execute.call_count >= 3
    patch_psycopg2_connect.return_value.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with("user:1")


def test_update_user_in_db_not_found(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = None
    result = db.update_user_in_db(999, name="NoUser")

    assert result is False
    patch_psycopg2_connect.return_value.commit.assert_not_called()


def test_delete_user_from_db_success(patch_psycopg2_connect, mock_cursor, mock_redis):
    mock_cursor.rowcount = 1
    result = db.delete_user_from_db(1)

    assert result is True
    patch_psycopg2_connect.return_value.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with("user:1")


def test_delete_user_from_db_fail(patch_psycopg2_connect, mock_cursor):
    mock_cursor.rowcount = 0
    result = db.delete_user_from_db(999)

    assert result is False
    mock_cursor.execute.assert_called_once()
    patch_psycopg2_connect.return_value.commit.assert_not_called()


@patch('backend.core.db.generate_unique_hash')
def test_create_posting_in_db_success(mock_generate_hash, patch_psycopg2_connect, mock_cursor):
    mock_generate_hash.return_value = "abc123hash"
    mock_cursor.fetchone.return_value = {"hash": "abc123hash"}
    posting_hash = db.create_posting_in_db("Title", "Desc", "Cat", 1)

    assert posting_hash == "abc123hash"
    patch_psycopg2_connect.return_value.commit.assert_called_once()


@patch('backend.core.db.generate_unique_hash')
def test_create_posting_in_db_no_id_raises(mock_generate_hash, patch_psycopg2_connect, mock_cursor):
    mock_generate_hash.return_value = "abc123hash"
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError):
        db.create_posting_in_db("Title", "Desc", "Cat", 1)

def test_update_posting_in_db_success(patch_psycopg2_connect, mock_cursor, mock_redis):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]
    result = db.update_posting_in_db(1, title="New Title", category="NewCategory", post_description="brand new post description", status="active")

    assert result is True
    patch_psycopg2_connect.return_value.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with("posting id:1")


def test_update_posting_in_db_not_found(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = None
    result = db.update_posting_in_db(999, title="No Title")

    assert result is False
    patch_psycopg2_connect.return_value.commit.assert_not_called()

def test_delete_posting_from_db_success(patch_psycopg2_connect, mock_cursor, mock_redis):
    mock_cursor.rowcount = 1
    result = db.delete_posting_from_db(1)

    assert result is True
    patch_psycopg2_connect.return_value.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with("posting id:1")


def test_delete_posting_from_db_fail(patch_psycopg2_connect, mock_cursor):
    mock_cursor.rowcount = 0
    result = db.delete_posting_from_db(999)

    assert result is False
    mock_cursor.execute.assert_called_once()
    patch_psycopg2_connect.return_value.commit.assert_not_called()

def test_get_all_postings(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
    result = db.get_all_postings()

    assert isinstance(result, list)
    assert len(result) == 2
    mock_cursor.execute.assert_called_once_with("SELECT * FROM postings ORDER BY id DESC")

def test_get_posting_by_id(patch_psycopg2_connect, mock_cursor):
    expected = {"id": 1, "title": "Test"}
    mock_cursor.fetchone.return_value = expected
    result = db.get_posting_by_id(1)

    assert result == expected
    mock_cursor.execute.assert_called_once_with("SELECT * FROM postings WHERE id = %s", (1,))

def test_get_postings_by_user(patch_psycopg2_connect, mock_cursor):
    expected = [{"id": 1, "applications_count": 3}, {"id": 2, "applications_count": 1}]
    mock_cursor.fetchall.return_value = expected
    result = db.get_postings_by_user(1)

    assert result == expected
    # Just check that the query was called with the correct user_id
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args
    assert call_args[0][1] == (1,)  # Check the parameters

def test_get_applications_by_user(patch_psycopg2_connect, mock_cursor):
    expected = [{"application_id": 1, "title": "Posting"}]
    mock_cursor.fetchall.return_value = expected
    result = db.get_applications_by_user(1)

    assert result == expected
    mock_cursor.execute.assert_called_once()

def test_get_applications_by_posting(patch_psycopg2_connect, mock_cursor):
    expected = [{"application_id": 1, "name": "User", "email": "user@example.com"}]
    mock_cursor.fetchall.return_value = expected
    result = db.get_applications_by_posting(1)

    assert result == expected
    mock_cursor.execute.assert_called_once()

def test_update_user_rowcount_zero(patch_psycopg2_connect, mock_cursor, mock_redis):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]
    def fake_execute(*args, **kwargs):
        mock_cursor.rowcount = 0

    mock_cursor.execute.side_effect = fake_execute
    result = db.update_user_in_db(1, name="ShouldFail")
    assert result is True

def test_get_user_by_email(patch_psycopg2_connect, mock_cursor):
    expected_user = {"id": 1, "email": "john@example.com", "username": "johndoe"}
    mock_cursor.fetchone.return_value = expected_user

    result = db.get_user_by_email("john@example.com")

    assert result == expected_user
    mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE email = %s", ("john@example.com",))

def test_get_user_by_username(patch_psycopg2_connect, mock_cursor):
    expected_user = {"id": 1, "email": "john@example.com", "username": "johndoe"}
    mock_cursor.fetchone.return_value = expected_user

    result = db.get_user_by_username("johndoe")

    assert result == expected_user
    mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE username = %s", ("johndoe",))

def test_get_user_by_username_not_found(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = None

    result = db.get_user_by_username("nonexistent")

    assert result is None
    mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE username = %s", ("nonexistent",))


# Analytics and Enhanced Posting Tests

@patch('backend.core.db.get_db_connection')
def test_track_posting_view_unique_user(mock_get_db):
    """Test tracking unique view by user"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock no previous view (unique)
    mock_cursor.fetchone.return_value = None
    
    result = db.track_posting_view(1, user_id=42, ip_address="127.0.0.1", user_agent="Test")
    
    assert result is True
    assert mock_cursor.execute.call_count == 4  # check unique, insert view, update posting, update metrics


@patch('backend.core.db.get_db_connection')
def test_track_posting_view_non_unique_user(mock_get_db):
    """Test tracking non-unique view by same user"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock previous view exists (not unique)
    mock_cursor.fetchone.return_value = {"id": 1}
    
    result = db.track_posting_view(1, user_id=42, ip_address="127.0.0.1", user_agent="Test")
    
    assert result is False
    assert mock_cursor.execute.call_count == 4  # check unique, insert view, update posting, update metrics


@patch('backend.core.db.get_db_connection')
def test_track_posting_view_session_based(mock_get_db):
    """Test tracking view by session when no user"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock no previous view by session
    mock_cursor.fetchone.return_value = None
    
    result = db.track_posting_view(1, user_id=None, session_id="session123")
    
    assert result is True
    assert mock_cursor.execute.call_count == 4


@patch('backend.core.db.get_db_connection')
def test_get_posting_analytics_owner(mock_get_db):
    """Test getting posting analytics for owner"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting owned by user
    mock_cursor.fetchone.side_effect = [
        {"user_id": 42},  # ownership check
        {"views": 100, "application_count": 5, "total_views": 150, "unique_views": 120}  # stats
    ]
    mock_cursor.fetchall.side_effect = [
        [{"date": "2023-01-01", "views_count": 10, "unique_views_count": 8, "applications_count": 1}],  # daily metrics
        [{"status": "pending", "count": 3}, {"status": "reviewed", "count": 2}]  # application status
    ]
    
    result = db.get_posting_analytics(1, 42)
    
    assert result is not None
    assert result["posting_id"] == 1
    assert "stats" in result
    assert "daily_metrics" in result
    assert "application_status" in result


@patch('backend.core.db.get_db_connection')
def test_get_posting_analytics_not_owner(mock_get_db):
    """Test getting posting analytics for non-owner"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting not owned by user
    mock_cursor.fetchone.return_value = {"user_id": 123}  # different user
    
    result = db.get_posting_analytics(1, 42)
    
    assert result == {}


@patch('backend.core.db.get_db_connection')
def test_get_posting_analytics_not_found(mock_get_db):
    """Test getting analytics for non-existent posting"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting not found
    mock_cursor.fetchone.return_value = None
    
    result = db.get_posting_analytics(999, 42)
    
    assert result == {}


@patch('backend.core.db.get_db_connection')
def test_get_user_posting_stats(mock_get_db):
    """Test getting user posting statistics"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "total_postings": 5,
        "active_postings": 3,
        "total_views": 500,
        "total_applications": 25,
        "avg_views_per_posting": 100
    }
    mock_cursor.fetchall.side_effect = [
        [{"id": 1, "title": "Test Job", "views": 200, "application_count": 10}],  # top postings
        [{"date": "2023-01-01", "daily_views": 50, "daily_unique_views": 40, "daily_applications": 3}]  # recent activity
    ]
    
    result = db.get_user_posting_stats(42)
    
    assert result is not None
    assert "overview" in result
    assert "top_postings" in result
    assert "recent_activity" in result
    assert result["overview"]["total_postings"] == 5


@patch('backend.core.db.get_db_connection')
def test_get_posting_with_public_stats(mock_get_db):
    """Test getting posting with public statistics"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "title": "Test Job",
        "post_description": "Test description",
        "views": 100,
        "application_count": 5,
        "creator_name": "John Doe",
        "creator_username": "johndoe"
    }
    
    result = db.get_posting_with_public_stats(1)
    
    assert result is not None
    assert result["title"] == "Test Job"
    assert result["application_count"] == 5


@patch('backend.core.db.get_db_connection')
def test_update_application_status_success(mock_get_db):
    """Test updating application status successfully"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.rowcount = 1
    
    result = db.update_application_status(1, "accepted", "Great candidate")
    
    assert result is True
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_db_connection')
def test_update_application_status_not_found(mock_get_db):
    """Test updating non-existent application status"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.rowcount = 0
    
    result = db.update_application_status(999, "accepted", "Great candidate")
    
    assert result is False


@patch('backend.core.db.get_db_connection')
def test_get_application_details_owner(mock_get_db):
    """Test getting application details as posting owner"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_id": 123,
        "posting_id": 1,
        "message": "I'm interested",
        "status": "pending",
        "applicant_name": "Jane Doe",
        "applicant_email": "jane@example.com",
        "posting_title": "Test Job",
        "posting_owner_id": 42
    }
    
    result = db.get_application_details(1, 42)  # user 42 is posting owner
    
    assert result is not None
    assert result["posting_title"] == "Test Job"
    assert result["applicant_name"] == "Jane Doe"


@patch('backend.core.db.get_db_connection')
def test_get_application_details_applicant(mock_get_db):
    """Test getting application details as applicant"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_id": 123,
        "posting_id": 1,
        "message": "I'm interested",
        "status": "pending",
        "applicant_name": "Jane Doe",
        "applicant_email": "jane@example.com",
        "posting_title": "Test Job",
        "posting_owner_id": 42
    }
    
    result = db.get_application_details(1, 123)  # user 123 is applicant
    
    assert result is not None
    assert result["user_id"] == 123


@patch('backend.core.db.get_db_connection')
def test_get_application_details_no_access(mock_get_db):
    """Test getting application details with no access"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = None
    
    result = db.get_application_details(1, 999)  # user 999 has no access
    
    assert result is None


@patch('backend.core.db.get_db_connection')
def test_get_posting_with_public_stats_active(mock_get_db):
    """Test getting active posting with public stats"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
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
    
    result = db.get_posting_with_public_stats(1)
    
    assert result is not None
    assert result["title"] == "Software Engineer"
    assert result["application_count"] == 8
    assert result["status"] == "active"


@patch('backend.core.db.get_db_connection')
def test_get_posting_with_public_stats_inactive(mock_get_db):
    """Test getting inactive posting returns None"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = None  # No active posting found
    
    result = db.get_posting_with_public_stats(1)
    
    assert result is None


@patch('backend.core.db.get_db_connection')
def test_get_public_postings(mock_get_db):
    """Test getting all public postings"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchall.return_value = [
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
        },
        {
            "id": 2,
            "title": "Designer",
            "post_description": "Creative UI/UX designer needed",
            "category": "design",
            "views": 75,
            "status": "active",
            "creator_name": "Jane Smith",
            "creator_username": "janesmith",
            "application_count": 3
        }
    ]
    
    result = db.get_public_postings()
    
    assert result is not None
    assert len(result) == 2
    assert result[0]["title"] == "Software Engineer"
    assert result[0]["application_count"] == 8
    assert result[1]["title"] == "Designer"
    assert result[1]["application_count"] == 3


# New Enhanced Posting Management Tests

@patch('backend.core.db.get_db_connection')
@patch('backend.core.db.generate_unique_hash')
def test_create_posting_returns_hash(mock_generate_hash, mock_get_db):
    """Test that create_posting_in_db returns hash instead of ID"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_generate_hash.return_value = "abc123hash"
    mock_cursor.fetchone.return_value = {"hash": "abc123hash"}
    
    result = db.create_posting_in_db("Software Engineer", "Job description", "technology", 42)
    
    assert result == "abc123hash"
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_db_connection')
def test_get_posting_by_hash_success(mock_get_db):
    """Test getting posting by hash"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "title": "Software Engineer",
        "hash": "abc123",
        "user_id": 42
    }
    
    result = db.get_posting_by_hash("abc123")
    
    assert result is not None
    assert result["hash"] == "abc123"
    assert result["title"] == "Software Engineer"
    mock_cursor.execute.assert_called_once_with("SELECT * FROM postings WHERE hash = %s", ("abc123",))


@patch('backend.core.db.get_db_connection')
def test_get_posting_by_hash_not_found(mock_get_db):
    """Test getting posting by non-existent hash"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = None
    
    result = db.get_posting_by_hash("nonexistent")
    
    assert result is None


@patch('backend.core.db.get_db_connection')
def test_apply_to_posting_with_enhanced_fields(mock_get_db):
    """Test applying to posting with enhanced message and cover_letter fields"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting exists and user hasn't applied
    mock_cursor.fetchone.side_effect = [
        {"id": 1, "user_id": 99},  # posting exists, owned by user 99
        None  # user hasn't applied
    ]
    
    result = db.apply_to_posting(42, 1, "I'm very interested", "Dear hiring manager, I have 5 years experience...")
    
    assert result["success"] is True
    assert "error" not in result  # No error key on success
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_db_connection')
def test_apply_to_posting_already_applied_enhanced(mock_get_db):
    """Test applying to posting when already applied (enhanced return format)"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting exists but user has already applied
    mock_cursor.fetchone.side_effect = [
        {"id": 1, "user_id": 99},  # posting exists, owned by user 99
        {"id": 1}   # user has already applied
    ]
    
    result = db.apply_to_posting(42, 1, "I'm interested", "Cover letter")
    
    assert result["success"] is False
    assert result["error"] == "already_applied"
    mock_conn.commit.assert_not_called()


@patch('backend.core.db.get_db_connection')
def test_apply_to_posting_own_posting_enhanced(mock_get_db):
    """Test user trying to apply to their own posting (enhanced return format)"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting exists and is owned by the same user trying to apply
    mock_cursor.fetchone.return_value = {"id": 1, "user_id": 42}  # same user_id as applicant
    
    result = db.apply_to_posting(42, 1, "I'm interested", "Cover letter")
    
    assert result["success"] is False
    assert result["error"] == "cannot_apply_own_posting"
    mock_conn.commit.assert_not_called()


@patch('backend.core.db.get_db_connection')
def test_apply_to_posting_not_found_enhanced(mock_get_db):
    """Test applying to non-existent posting (enhanced return format)"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting doesn't exist
    mock_cursor.fetchone.return_value = None
    
    result = db.apply_to_posting(42, 999, "I'm interested", "Cover letter")
    
    assert result["success"] is False
    assert result["error"] == "posting_not_found"
    mock_conn.commit.assert_not_called()


@patch('backend.core.db.get_db_connection')
def test_generate_unique_hash(mock_get_db):
    """Test hash generation creates unique strings"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock that hash doesn't exist in database
    mock_cursor.fetchone.return_value = None
    
    hash1 = db.generate_unique_hash()
    hash2 = db.generate_unique_hash()
    
    assert isinstance(hash1, str)
    assert isinstance(hash2, str)
    assert len(hash1) == 12  # Default length is 12
    assert len(hash2) == 12
    assert hash1 != hash2  # Should be unique


@patch('backend.core.db.get_db_connection')
@patch('backend.core.db.datetime')
def test_track_posting_view_anonymous_user(mock_datetime, mock_get_db):
    """Test tracking view for anonymous user by IP"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock datetime for metrics
    mock_datetime.now.return_value.date.return_value = "2023-01-01"
    
    result = db.track_posting_view(1, user_id=None, ip_address="192.168.1.1", user_agent="Browser")
    
    assert result is True
    # When no user_id or session_id provided, function should insert view record and update metrics
    # Check that INSERT INTO posting_views was called
    insert_calls = [call for call in mock_cursor.execute.call_args_list 
                   if call[0][0].strip().startswith('INSERT INTO posting_views')]
    assert len(insert_calls) > 0
    
    # Check that posting views count was updated
    update_calls = [call for call in mock_cursor.execute.call_args_list 
                   if 'UPDATE postings SET views' in call[0][0]]
    assert len(update_calls) > 0

@patch('backend.core.db.get_db_connection')
def test_get_application_details_with_enhanced_fields(mock_get_db):
    """Test getting application details with enhanced cover_letter and reviewer_notes"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "user_id": 42,
        "posting_id": 1,
        "message": "I'm interested",
        "cover_letter": "Dear hiring manager, I have extensive experience...",
        "status": "pending",
        "reviewer_notes": None,
        "reviewed_at": None,
        "posting_title": "Software Engineer",
        "posting_owner_id": 99
    }
    
    result = db.get_application_details(1, 42)  # User 42 is the applicant
    
    assert result is not None
    assert result["cover_letter"] == "Dear hiring manager, I have extensive experience..."
    assert result["reviewer_notes"] is None
    assert result["status"] == "pending"


@patch('backend.core.db.get_db_connection')
def test_update_application_status_with_notes(mock_get_db):
    """Test updating application status with reviewer notes"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.rowcount = 1
    
    result = db.update_application_status(1, "accepted", "Excellent candidate with strong technical skills")
    
    assert result is True
    # Should update status, reviewer_notes, and reviewed_at
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args[0]
    assert "reviewer_notes" in call_args[0]
    assert "reviewed_at" in call_args[0]
    assert call_args[1] == ("accepted", "Excellent candidate with strong technical skills", 1)


@patch('backend.core.db.get_db_connection')
def test_update_application_status_without_notes(mock_get_db):
    """Test updating application status without reviewer notes"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.rowcount = 1
    
    result = db.update_application_status(1, "reviewed", None)
    
    assert result is True
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_redis_client')
@patch('backend.core.db.get_db_connection')
def test_posting_status_updates(mock_get_db, mock_redis):
    """Test posting status field updates"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock existing posting
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]
    
    result = db.update_posting_in_db(1, title=None, category=None, post_description=None, status="inactive")
    
    assert result is True
    # Should only update the status field since others are None
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_db_connection')
def test_get_postings_by_user_with_status(mock_get_db):
    """Test getting user postings includes status field"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchall.return_value = [
        {"id": 1, "title": "Job 1", "status": "active", "views": 100},
        {"id": 2, "title": "Job 2", "status": "inactive", "views": 50}
    ]
    
    result = db.get_postings_by_user(42)
    
    assert result is not None
    assert len(result) == 2
    assert result[0]["status"] == "active"
    assert result[1]["status"] == "inactive"


@patch('backend.core.db.get_db_connection')
def test_view_tracking_with_session_data(mock_get_db):
    """Test view tracking with session data for anonymous users"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock no previous view
    mock_cursor.fetchone.return_value = None
    
    result = db.track_posting_view(
        posting_id=1,
        user_id=None,
        ip_address="127.0.0.1",
        user_agent="Test Browser",
        session_id="session123"
    )
    
    assert result is True
    # Should record session_id for anonymous users
    insert_call = None
    for call in mock_cursor.execute.call_args_list:
        if "INSERT INTO posting_views" in call[0][0]:
            insert_call = call
            break
    
    assert insert_call is not None
    assert "session123" in str(insert_call)


@patch('backend.core.db.get_db_connection')
def test_check_user_application_exists_true(mock_get_db):
    """Test check_user_application_exists returns True when application exists"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock application exists
    mock_cursor.fetchone.return_value = {"id": 1}
    
    result = db.check_user_application_exists(user_id=42, posting_id=1)
    
    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "SELECT 1 FROM applications WHERE user_id = %s AND posting_id = %s",
        (42, 1)
    )


@patch('backend.core.db.get_db_connection')
def test_check_user_application_exists_false(mock_get_db):
    """Test check_user_application_exists returns False when no application exists"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock no application exists
    mock_cursor.fetchone.return_value = None
    
    result = db.check_user_application_exists(user_id=42, posting_id=1)
    
    assert result is False
    mock_cursor.execute.assert_called_once_with(
        "SELECT 1 FROM applications WHERE user_id = %s AND posting_id = %s",
        (42, 1)
    )


@patch('backend.core.db.get_db_connection')
def test_get_applications_by_user_with_details(mock_get_db):
    """Test enhanced get_applications_by_user returns detailed application info"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock detailed application data
    expected_applications = [
        {
            "id": 1,
            "user_id": 42,
            "posting_id": 1,
            "message": "I'm interested",
            "applied_at": "2025-01-21 10:00:00",
            "status": "pending",
            "cover_letter": "Dear employer...",
            "title": "Software Developer",
            "post_description": "Great opportunity",
            "category": "Tech",
            "posting_created_at": "2025-01-20 09:00:00",
            "posting_hash": "abc123",
            "posting_creator_name": "John Employer"
        }
    ]
    mock_cursor.fetchall.return_value = expected_applications
    
    result = db.get_applications_by_user(user_id=42)
    
    assert result == expected_applications
    mock_cursor.execute.assert_called_once()
    
    # Verify the SQL includes all the new fields
    sql_call = mock_cursor.execute.call_args[0][0]
    assert "applications.*" in sql_call
    assert "postings.title" in sql_call
    assert "postings.post_description" in sql_call
    assert "postings.category" in sql_call
    assert "postings.created_at as posting_created_at" in sql_call
    assert "postings.hash as posting_hash" in sql_call
    assert "users.name as posting_creator_name" in sql_call
    assert "ORDER BY applications.applied_at DESC" in sql_call

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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


def test_create_posting_in_db_success(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = {"id": 123}
    posting_id = db.create_posting_in_db("Title", "Desc", "Cat", 1)

    assert posting_id == 123
    patch_psycopg2_connect.return_value.commit.assert_called_once()


def test_create_posting_in_db_no_id_raises(patch_psycopg2_connect, mock_cursor):
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
    expected = [{"id": 1}, {"id": 2}]
    mock_cursor.fetchall.return_value = expected
    result = db.get_postings_by_user(1)

    assert result == expected
    mock_cursor.execute.assert_called_once_with("SELECT * FROM postings WHERE user_id = %s", (1,))

def test_apply_to_posting_success(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]

    result = db.apply_to_posting(1, 1)

    assert result is True
    patch_psycopg2_connect.return_value.commit.assert_called_once()

def test_apply_to_posting_already_applied(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.side_effect = [{"id": 1}, {"exists": True}]

    result = db.apply_to_posting(1, 1)

    assert result is False
    patch_psycopg2_connect.return_value.commit.assert_not_called()

def test_apply_to_posting_posting_not_found(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.return_value = None

    result = db.apply_to_posting(1, 999)

    assert result is False
    patch_psycopg2_connect.return_value.commit.assert_not_called()

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

def test_update_user_rowcount_zero(patch_psycopg2_connect, mock_cursor, mock_redis_client):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]
    def fake_execute(*args, **kwargs):
        mock_cursor.rowcount = 0

    mock_cursor.execute.side_effect = fake_execute
    result = db.update_user_in_db(1, name="ShouldFail")
    assert result is True

def test_apply_to_posting_triggers_commit(patch_psycopg2_connect, mock_cursor):
    mock_cursor.fetchone.side_effect = [{"id": 1}, None]
    mock_cursor.rowcount = 1  # Ensures conn.commit() will be triggered

    result = db.apply_to_posting(1, 1)

    assert result is True
    patch_psycopg2_connect.return_value.commit.assert_called_once()

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
    
    assert result is None


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
    
    assert result is None


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
@patch('backend.core.db.datetime')
def test_apply_to_posting_with_analytics(mock_datetime, mock_get_db):
    """Test applying to posting updates metrics"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting exists and user hasn't applied
    mock_cursor.fetchone.side_effect = [
        {"id": 1},  # posting exists
        None  # user hasn't applied
    ]
    
    mock_datetime.now.return_value.date.return_value = "2023-01-01"
    
    result = db.apply_to_posting(42, 1, "I'm interested", "My cover letter")
    
    assert result is True
    assert mock_cursor.execute.call_count == 4  # check posting, check applied, insert application, update metrics
    mock_conn.commit.assert_called_once()


@patch('backend.core.db.get_db_connection')
def test_apply_to_posting_optional_fields(mock_get_db):
    """Test applying to posting with optional message and cover letter"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock posting exists and user hasn't applied
    mock_cursor.fetchone.side_effect = [
        {"id": 1},  # posting exists
        None  # user hasn't applied
    ]
    
    # Test with no message or cover letter
    result = db.apply_to_posting(42, 1)
    
    assert result is True
    # Check that None values were passed for message and cover_letter
    insert_call = mock_cursor.execute.call_args_list[2]  # Third call is the insert
    assert insert_call[0][1] == (42, 1, None, None)


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

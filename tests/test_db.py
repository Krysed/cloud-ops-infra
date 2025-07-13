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

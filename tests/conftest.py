import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def temp_db_config(tmp_path, monkeypatch):
    # Create fake config content
    fake_config = {
        "REDIS": {
            "host": "localhost",
            "port": 6379,
            "password": None,
            "db": 0
        },
        "POSTGRES": {
            "dbname": "testdb",
            "user": "testuser",
            "password": "testpass",
            "host": "localhost",
            "port": 5432
        }
    }
    # Create temp file and write JSON
    config_file = tmp_path / "db_config.json"
    config_file.write_text(json.dumps(fake_config))

    # Patch environment variable to point to this temp file
    monkeypatch.setenv("DB_CONFIG_PATH", str(config_file))

    # Also make sure ENV is not 'production', so fallback is triggered
    monkeypatch.delenv("ENV", raising=False)

    # Return path for reference if needed
    return config_file

@pytest.fixture
def mock_cursor():
    """Mock cursor DB with execute, fetchone, fetchall methods"""
    cursor = MagicMock()
    cursor.execute = MagicMock()
    cursor.fetchone = MagicMock()
    cursor.fetchall = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None
    return cursor

@pytest.fixture
def mock_conn(mock_cursor):
    """Mock DB connection returning mock_cursor"""
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = mock_cursor
    conn.close = MagicMock()
    return conn

@pytest.fixture
def patch_psycopg2_connect(mock_conn):
    """Patch psycopg2.connect to return mock_connect."""
    with patch("backend.core.db.psycopg2.connect", return_value=mock_conn) as mock_connect:
        yield mock_connect

@pytest.fixture
def mock_redis():
    """Mock redis client"""
    mock_redis_client = MagicMock()
    with patch("backend.core.db.get_redis_client", return_value=mock_redis_client):
        yield mock_redis_client

@pytest.fixture
def mock_redis_client(monkeypatch):
    """Mock redis client"""
    mock_redis = MagicMock()
    monkeypatch.setattr("backend.core.db.get_redis_client", lambda: mock_redis)
    return mock_redis
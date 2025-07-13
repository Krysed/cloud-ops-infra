from unittest.mock import MagicMock, patch

import pytest

from backend.core import cache


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    fake_redis_config = {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
    }
    fake_postgres_config = {
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass",
        "host": "localhost",
        "port": 5432,
    }

    monkeypatch.setattr("backend.core.config.REDIS_CONFIG", fake_redis_config)
    monkeypatch.setattr("backend.core.config.POSTGRES_CONFIG", fake_postgres_config)

def test_get_redis_client_calls_redis_with_config():
    fake_redis_instance = MagicMock()
    with patch("backend.core.cache.redis.Redis", return_value=fake_redis_instance) as mock_redis:
        client = cache.get_redis_client()
        
        mock_redis.assert_called_once_with(
            host=cache.REDIS_CONFIG["host"],
            port=cache.REDIS_CONFIG["port"],
            password=cache.REDIS_CONFIG.get("password"),
            db=cache.REDIS_CONFIG["db"],
        )
        
        assert client == fake_redis_instance

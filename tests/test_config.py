import sys
from unittest.mock import MagicMock, patch

from backend.core import cache, config


def test_get_redis_client_calls_redis_with_config():
    fake_redis_instance = MagicMock()
    with patch("backend.core.cache.redis.Redis", return_value=fake_redis_instance) as mock_redis:
        client = cache.get_redis_client()

        mock_redis.assert_called_once_with(
            host=config.REDIS_CONFIG["host"],
            port=config.REDIS_CONFIG["port"],
            password=config.REDIS_CONFIG.get("password"),
            db=config.REDIS_CONFIG["db"],
        )
        assert client == fake_redis_instance

def test_redis_config_from_env(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("REDIS_PASSWORD", "testpass")
    monkeypatch.setenv("REDIS_HOST", "redis-host")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS_DB", "2")

    if "backend.core.config" in sys.modules:
        del sys.modules["backend.core.config"]

    # Importujemy config ponownie
    import backend.core.config as config

    assert config.REDIS_CONFIG["password"] == "testpass"
    assert config.REDIS_CONFIG["host"] == "redis-host"
    assert config.REDIS_CONFIG["port"] == 6380
    assert config.REDIS_CONFIG["db"] == 2

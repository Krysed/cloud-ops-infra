from unittest.mock import MagicMock, patch

from backend.core import cache


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

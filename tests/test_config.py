import sys


def test_redis_config_from_env(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("REDIS_PASSWORD", "testpass")
    monkeypatch.setenv("REDIS_HOST", "redis-host")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS_DB", "2")

    # Remove and reload the config module to pick up new env vars
    if "backend.core.config" in sys.modules:
        del sys.modules["backend.core.config"]

    # Import the module fresh
    import backend.core.config as config
    
    assert config.REDIS_CONFIG["password"] == "testpass"
    assert config.REDIS_CONFIG["host"] == "redis-host"
    assert config.REDIS_CONFIG["port"] == 6380
    assert config.REDIS_CONFIG["db"] == 2

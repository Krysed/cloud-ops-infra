import redis
from .config import REDIS_CONFIG

def get_redis_client():
    return redis.Redis(
        host=REDIS_CONFIG["host"],
        port=REDIS_CONFIG["port"],
        password=REDIS_CONFIG.get("password"),
        db=REDIS_CONFIG["db"]
    )

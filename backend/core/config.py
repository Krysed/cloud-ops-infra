import json
import os
from pathlib import Path

if os.getenv("ENV") == "production":
    REDIS_CONFIG = {
        "password": os.getenv("REDIS_PASSWORD"),
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0))
    }

    POSTGRES_CONFIG = {
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432))
    }

else:
    PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    DB_CONFIG_PATH = os.getenv("DB_CONFIG_PATH", os.path.join(PROJECT_ROOT_DIR, "secrets", "db_config.json"))

    with open(DB_CONFIG_PATH) as f:
        config = json.load(f)
    REDIS_CONFIG = config["REDIS"]
    POSTGRES_CONFIG = config["POSTGRES"]

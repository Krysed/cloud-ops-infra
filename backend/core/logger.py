import logging
import os
from logging_loki import LokiHandler

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Loki handler for centralized logging
loki_url = os.getenv('LOKI_URL', 'http://loki:3100/loki/api/v1/push')
loki_handler = LokiHandler(
    url=loki_url,
    tags={"job": "fastapi-backend", "service": "backend"},
    version="1",
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        console_handler,
        loki_handler
    ]
)

logger = logging.getLogger("fastapi-backend")

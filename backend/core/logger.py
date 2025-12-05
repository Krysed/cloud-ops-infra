import logging

# Create console handler with structured logging format
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)

# Configure logging to stdout (Promtail will collect these logs)
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)

logger = logging.getLogger("fastapi-backend")

import psycopg2
import psycopg2.extras
from .config import POSTGRES_CONFIG

def get_db_connection():
    connection = psycopg2.connect(
        host=POSTGRES_CONFIG["host"],
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        port=POSTGRES_CONFIG["port"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return connection

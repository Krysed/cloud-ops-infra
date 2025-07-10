import psycopg2
import psycopg2.extras
from .config import POSTGRES_CONFIG
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        host=POSTGRES_CONFIG["host"],
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        port=POSTGRES_CONFIG["port"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()

def get_user_by_email(email: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cursor.fetchone()

def create_user(name: str, surname: str, username: str, email: str, hashed_password: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, surname, username, email, user_type, hashed_password)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, surname, username, email, "regular", hashed_password))
            user = cursor.fetchone()
            conn.commit()
            return user["id"]

def get_user_by_id(user_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()

def update_user_in_db(user_id: int, name: str = None, surname: str = None, username: str = None, email: str = None) -> bool:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return False

            if name:
                cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
            if surname:
                cursor.execute("UPDATE users SET surname = %s WHERE id = %s", (surname, user_id))
            if username:
                cursor.execute("UPDATE users SET username = %s WHERE id = %s", (username, user_id))    
            if email:
                cursor.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))
            conn.commit()
            return True

def delete_user_from_db(user_id: int) -> bool:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            if cursor.rowcount == 0:
                return False

            conn.commit()
            return True

def create_posting_in_db(title: str, description: str, category: str, user_id: int) -> int:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO postings (title, description, category, user_id)
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (title, description, category, user_id)
            )
            posting_id = cursor.fetchone()[0]
            conn.commit()
            return posting_id

def update_posting_in_db(posting_id: int, title: str = None, category: str = None, post_description: str = None, status: str = None) -> bool:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM postings WHERE id = %s", (posting_id,))
            if not cursor.fetchone():
                return False

            if title:
                cursor.execute("UPDATE postings SET title = %s WHERE id = %s", (title, posting_id))
            if category:
                cursor.execute("UPDATE postings SET category = %s WHERE id = %s", (category, posting_id))
            if post_description:
                cursor.execute("UPDATE postings SET post_description = %s WHERE id = %s", (post_description, posting_id))
            if status:
                cursor.execute("UPDATE postings SET status = %s WHERE id = %s", (status, posting_id))

            conn.commit()
            return True

def delete_posting_from_db(posting_id: int) -> bool:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM postings WHERE id = %s", (posting_id,))
            if cursor.rowcount == 0:
                return False

            conn.commit()
            return True

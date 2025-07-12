from contextlib import contextmanager
from datetime import UTC, datetime

import psycopg2
import psycopg2.extras

from .cache import get_redis_client
from .config import POSTGRES_CONFIG


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
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()

def create_user(name: str, surname: str, username: str, email: str, hashed_password: str):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (name, surname, username, email, user_type, hashed_password)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, surname, username, email, "regular", hashed_password))
        user = cursor.fetchone()
        conn.commit()
        return user["id"]

def get_user_by_id(user_id: int):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()

def update_user_in_db(user_id: int, name: str = None, surname: str = None, username: str = None, email: str = None) -> bool:
    with get_db_connection() as conn, conn.cursor() as cursor:
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
        get_redis_client().delete(f"user:{user_id}")
        return True

def delete_user_from_db(user_id: int) -> bool:
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if cursor.rowcount == 0:
            return False

        conn.commit()
        get_redis_client().delete(f"user:{user_id}")
        return True

def create_posting_in_db(title: str, post_description: str, category: str, user_id: int) -> int:
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO postings (title, post_description, category, user_id)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (title, post_description, category, user_id)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Insert failed: no ID returned from insert statement.")
        conn.commit()
        return row["id"] # posting id

def update_posting_in_db(posting_id: int, title: str = None, category: str = None, post_description: str = None, status: str = None) -> bool:
    with get_db_connection() as conn, conn.cursor() as cursor:
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
        cursor.execute("UPDATE postings SET updated_at = %s WHERE id = %s", (datetime.now(UTC), posting_id))
            
        conn.commit()
        get_redis_client().delete(f"posting id:{posting_id}")
        return True

def delete_posting_from_db(posting_id: int) -> bool:
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM postings WHERE id = %s", (posting_id,))
        if cursor.rowcount == 0:
            return False
        conn.commit()
        get_redis_client().delete(f"posting id:{posting_id}")
        return True

def get_all_postings():
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM postings ORDER BY id DESC")
        return cursor.fetchall()

def get_posting_by_id(posting_id):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM postings WHERE id = %s", (posting_id,))
        return cursor.fetchone()

def get_postings_by_user(user_id):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM postings WHERE user_id = %s", (user_id,))
        return cursor.fetchall()

def apply_to_posting(user_id: int, posting_id: int) -> bool:
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT id FROM postings WHERE id = %s", (posting_id,))
        if not cursor.fetchone():
            return False

        # check if applied already
        cursor.execute(
            "SELECT 1 FROM applications WHERE user_id = %s AND posting_id = %s",
            (user_id, posting_id)
        )

        if cursor.fetchone():
            return False

        cursor.execute(
            "INSERT INTO applications (user_id, posting_id) VALUES (%s, %s)",
            (user_id, posting_id)
        )
        conn.commit()
        return True

def get_applications_by_user(user_id):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT applications.*, postings.title 
            FROM applications 
            JOIN postings ON applications.posting_id = postings.id 
            WHERE applications.user_id = %s
        """, (user_id,))
        return cursor.fetchall()

def get_applications_by_posting(posting_id):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT applications.*, users.name, users.email 
            FROM applications 
            JOIN users ON applications.user_id = users.id 
            WHERE applications.posting_id = %s
        """, (posting_id,))
        return cursor.fetchall()

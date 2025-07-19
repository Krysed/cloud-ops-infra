from contextlib import contextmanager
from datetime import UTC, datetime
import secrets
import string

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

def generate_unique_hash(length: int = 12) -> str:
    """Generate a unique hash for posting URLs"""
    alphabet = string.ascii_lowercase + string.digits
    while True:
        hash_value = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Check if hash already exists
        with get_db_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM postings WHERE hash = %s", (hash_value,))
            if cursor.fetchone() is None:
                return hash_value

def get_user_by_email(email: str):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()

def get_user_by_username(username: str):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
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

def create_posting_in_db(title: str, post_description: str, category: str, user_id: int) -> str:
    """Create a posting and return its hash"""
    hash_value = generate_unique_hash()
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO postings (title, post_description, category, user_id, hash)
            VALUES (%s, %s, %s, %s, %s) RETURNING hash
            """,
            (title, post_description, category, user_id, hash_value)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Insert failed: no hash returned from insert statement.")
        conn.commit()
        return row["hash"] # posting hash

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

def get_posting_by_hash(posting_hash: str):
    """Get posting by hash instead of ID"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM postings WHERE hash = %s", (posting_hash,))
        return cursor.fetchone()

def get_postings_by_user(user_id):
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.id,
                p.user_id,
                p.hash,
                p.title,
                p.post_description,
                p.category,
                p.views,
                p.created_at,
                p.updated_at,
                p.status,
                COUNT(DISTINCT a.id) as applications_count
            FROM postings p
            LEFT JOIN applications a ON p.id = a.posting_id
            WHERE p.user_id = %s
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """, (user_id,))
        return cursor.fetchall()

def apply_to_posting(user_id: int, posting_id: int, message: str = None, cover_letter: str = None) -> dict:
    with get_db_connection() as conn, conn.cursor() as cursor:
        # Check if posting exists and get the posting owner
        cursor.execute("SELECT id, user_id FROM postings WHERE id = %s", (posting_id,))
        posting_data = cursor.fetchone()
        if not posting_data:
            return {"success": False, "error": "posting_not_found"}
        
        # Prevent posting creators from applying to their own posts
        if posting_data['user_id'] == user_id:
            return {"success": False, "error": "cannot_apply_own_posting"}

        # check if applied already
        cursor.execute(
            "SELECT 1 FROM applications WHERE user_id = %s AND posting_id = %s",
            (user_id, posting_id)
        )

        if cursor.fetchone():
            return {"success": False, "error": "already_applied"}

        cursor.execute(
            "INSERT INTO applications (user_id, posting_id, message, cover_letter) VALUES (%s, %s, %s, %s)",
            (user_id, posting_id, message, cover_letter)
        )
        
        # Update daily metrics for applications
        today = datetime.now(UTC).date()
        cursor.execute("""
            INSERT INTO posting_metrics (posting_id, date, applications_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (posting_id, date) 
            DO UPDATE SET 
                applications_count = posting_metrics.applications_count + 1,
                updated_at = NOW()
        """, (posting_id, today))
        
        conn.commit()
        return {"success": True}

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

# Analytics and View Tracking Functions

def track_posting_view(posting_id: int, user_id: int = None, ip_address: str = None, user_agent: str = None, session_id: str = None) -> bool:
    """Track a view of a posting and determine if it's unique"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        # Check if this is a unique view (same user/session within 24 hours)
        is_unique = True
        if user_id:
            cursor.execute("""
                SELECT 1 FROM posting_views 
                WHERE posting_id = %s AND user_id = %s 
                AND viewed_at > NOW() - INTERVAL '24 hours'
            """, (posting_id, user_id))
            is_unique = cursor.fetchone() is None
        elif session_id:
            cursor.execute("""
                SELECT 1 FROM posting_views 
                WHERE posting_id = %s AND session_id = %s 
                AND viewed_at > NOW() - INTERVAL '24 hours'
            """, (posting_id, session_id))
            is_unique = cursor.fetchone() is None
        
        # Record the view
        cursor.execute("""
            INSERT INTO posting_views (posting_id, user_id, ip_address, user_agent, session_id, is_unique_view)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (posting_id, user_id, ip_address, user_agent, session_id, is_unique))
        
        # Update posting view count
        cursor.execute("""
            UPDATE postings SET views = views + 1 WHERE id = %s
        """, (posting_id,))
        
        # Update daily metrics
        today = datetime.now(UTC).date()
        cursor.execute("""
            INSERT INTO posting_metrics (posting_id, date, views_count, unique_views_count)
            VALUES (%s, %s, 1, %s)
            ON CONFLICT (posting_id, date) 
            DO UPDATE SET 
                views_count = posting_metrics.views_count + 1,
                unique_views_count = posting_metrics.unique_views_count + %s,
                updated_at = NOW()
        """, (posting_id, today, 1 if is_unique else 0, 1 if is_unique else 0))
        
        conn.commit()
        return is_unique

def get_posting_analytics(posting_id: int, user_id: int) -> dict:
    """Get comprehensive analytics for a posting (only for posting owner)"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        # Verify ownership
        cursor.execute("SELECT user_id FROM postings WHERE id = %s", (posting_id,))
        posting = cursor.fetchone()
        if not posting or posting["user_id"] != user_id:
            return None
        
        # Get basic posting stats
        cursor.execute("""
            SELECT 
                p.views,
                p.created_at,
                p.status,
                COUNT(DISTINCT a.id) as application_count,
                COUNT(DISTINCT pv.id) as total_views,
                COUNT(DISTINCT CASE WHEN pv.is_unique_view THEN pv.id END) as unique_views
            FROM postings p
            LEFT JOIN applications a ON p.id = a.posting_id
            LEFT JOIN posting_views pv ON p.id = pv.posting_id
            WHERE p.id = %s
            GROUP BY p.id, p.views, p.created_at, p.status
        """, (posting_id,))
        stats = cursor.fetchone()
        
        # Get daily metrics for the last 30 days
        cursor.execute("""
            SELECT date, views_count, unique_views_count, applications_count
            FROM posting_metrics
            WHERE posting_id = %s AND date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date DESC
        """, (posting_id,))
        daily_metrics = cursor.fetchall()
        
        # Get application status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM applications
            WHERE posting_id = %s
            GROUP BY status
        """, (posting_id,))
        application_status = cursor.fetchall()
        
        return {
            "posting_id": posting_id,
            "stats": stats,
            "daily_metrics": daily_metrics,
            "application_status": application_status
        }

def get_user_posting_stats(user_id: int) -> dict:
    """Get overview statistics for all user's postings"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        # Get overview stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.id) as total_postings,
                COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.id END) as active_postings,
                SUM(p.views) as total_views,
                COUNT(DISTINCT a.id) as total_applications,
                AVG(p.views) as avg_views_per_posting
            FROM postings p
            LEFT JOIN applications a ON p.id = a.posting_id
            WHERE p.user_id = %s
        """, (user_id,))
        overview = cursor.fetchone()
        
        # Get top performing postings
        cursor.execute("""
            SELECT 
                p.id,
                p.title,
                p.views,
                p.created_at,
                COUNT(DISTINCT a.id) as application_count
            FROM postings p
            LEFT JOIN applications a ON p.id = a.posting_id
            WHERE p.user_id = %s
            GROUP BY p.id, p.title, p.views, p.created_at
            ORDER BY p.views DESC
            LIMIT 5
        """, (user_id,))
        top_postings = cursor.fetchall()
        
        # Get recent activity (last 7 days)
        cursor.execute("""
            SELECT 
                date,
                SUM(views_count) as daily_views,
                SUM(unique_views_count) as daily_unique_views,
                SUM(applications_count) as daily_applications
            FROM posting_metrics pm
            JOIN postings p ON pm.posting_id = p.id
            WHERE p.user_id = %s AND date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY date
            ORDER BY date DESC
        """, (user_id,))
        recent_activity = cursor.fetchall()
        
        return {
            "overview": overview,
            "top_postings": top_postings,
            "recent_activity": recent_activity
        }

def get_posting_with_public_stats(posting_id: int) -> dict:
    """Get posting with limited public statistics"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.*,
                u.name as creator_name,
                u.username as creator_username,
                COUNT(DISTINCT a.id) as application_count
            FROM postings p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN applications a ON p.id = a.posting_id
            WHERE p.id = %s AND p.status = 'active'
            GROUP BY p.id, u.name, u.username
        """, (posting_id,))
        return cursor.fetchone()

def update_application_status(application_id: int, status: str, reviewer_notes: str = None) -> bool:
    """Update application status (for posting owners)"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            UPDATE applications 
            SET status = %s, reviewer_notes = %s, reviewed_at = NOW()
            WHERE id = %s
        """, (status, reviewer_notes, application_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False

def get_application_details(application_id: int, user_id: int) -> dict:
    """Get application details (for posting owner or applicant)"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.*,
                u.name as applicant_name,
                u.email as applicant_email,
                p.title as posting_title,
                p.user_id as posting_owner_id
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN postings p ON a.posting_id = p.id
            WHERE a.id = %s AND (a.user_id = %s OR p.user_id = %s)
        """, (application_id, user_id, user_id))
        return cursor.fetchone()

def get_public_postings():
    """Get all active postings with limited public information"""
    with get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.id,
                p.user_id,
                p.hash,
                p.title,
                p.post_description,
                p.category,
                p.views,
                p.created_at,
                p.status,
                u.name as creator_name,
                u.username as creator_username,
                COUNT(DISTINCT a.id) as applications_count
            FROM postings p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN applications a ON p.id = a.posting_id
            WHERE p.status = 'active'
            GROUP BY p.id, p.user_id, u.name, u.username
            ORDER BY p.created_at DESC
        """)
        return cursor.fetchall()

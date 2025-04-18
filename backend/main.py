from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import redis
import psycopg2
import psycopg2.extras
import json
import os

BASE_DIR = Path(__file__).parent
db_json = os.getenv("DB_CONFIG_PATH", str(BASE_DIR.parent / "secrets" / "db_config.json"))

with open(db_json, "r") as f:
    config = json.load(f)

app = FastAPI()
template_env = Environment(loader=FileSystemLoader(str(BASE_DIR / "template")))
static_dir = str(BASE_DIR / "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

redis_config = config["REDIS"]
postgres_config = config["POSTGRES"]
REDIS_HOST = os.getenv("REDIS_HOST", config["REDIS"]["host"])  
POSTGRES_HOST = os.getenv("POSTGRES_HOST", config["POSTGRES"]["host"])

cache = redis.Redis(
    host=REDIS_HOST,
    port=redis_config["port"],
    password=redis_config.get("password"),
    decode_responses=True
)

db_connection = psycopg2.connect(
    host=POSTGRES_HOST,
    dbname=postgres_config["dbname"],
    user=postgres_config["user"],
    password=postgres_config["password"],
    port=postgres_config["port"],
    cursor_factory=psycopg2.extras.RealDictCursor
)
cursor = db_connection.cursor()

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML page."""
    template = template_env.get_template("index.html")
    return template.render()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open(os.path.join(BASE_DIR, "template", "login.html")) as f:
        return HTMLResponse(content=f.read())

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    with open(os.path.join(BASE_DIR, "template", "register.html")) as f:
        return HTMLResponse(content=f.read())

@app.get("/password-reset", response_class=HTMLResponse)
async def password_reset_page():
    with open(os.path.join(BASE_DIR, "template", "password-reset.html")) as f:
        return HTMLResponse(content=f.read())

@app.get("/contact", response_class=HTMLResponse)
async def contact_page():
    with open(os.path.join(BASE_DIR, "template", "contact.html")) as f:
        return HTMLResponse(content=f.read())

@app.get("/404", response_class=HTMLResponse)
async def not_found_page():
    with open(os.path.join(BASE_DIR, "template", "404.html")) as f:
        return HTMLResponse(content=f.read())

#TODO
@app.get("/users", response_class=HTMLResponse)
async def get_users():
    """List users from PostgreSQL."""
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    template = template_env.get_template("users.html")
    return HTMLResponse(content=template_env.render(users=users), status_code=200)

#TODO
@app.post("/submit")
async def submit(name: str = Form(...), email: str = Form(...)):
    """Handle form submission and store in DB & cache."""
    if not name or not email:
        return {"error": "Missing data"}

    # Store in PostgreSQL
    cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id", (name, email))
    user_id = cursor.fetchone()["id"]
    db_connection.commit()

    # Cache data in Redis
    cache.set(f"user:{user_id}", json.dumps({"id": user_id, "name": name, "email": email}))

    return RedirectResponse(url="/users", status_code=303)

#TODO
@app.get("/user/{user_id}")
async def get_user(user_id: int):
    """Fetch user from cache or DB."""
    cached_user = cache.get(f"user:{user_id}")
    if cached_user:
        return json.loads(cached_user)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        cache.set(f"user:{user_id}", json.dumps(user))  # Store in cache
    return user or {"error": "User not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

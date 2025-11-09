import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env (for local dev)
load_dotenv()

class Config:
    # -------------------------------
    # 🔐 Security & Core Settings
    # -------------------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_dev_key')

    # -------------------------------
    # 💾 Database
    # -------------------------------
    # If DATABASE_URL is provided (Render/Postgres), use that. Otherwise, use local SQLite.
   # -------------------------------
# 💾 Database (PostgreSQL on Render)
# -------------------------------
# -------------------------------
# 💾 Database Configuration (Render Safe)
# -------------------------------
    import urllib.parse

    uri = os.getenv("DATABASE_URL", "sqlite:///database.db")

# Render still sometimes provides old postgres:// URIs
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

# ✅ Enforce SSL for PostgreSQL to fix "bad record mac" errors
    if "postgresql" in uri:
        if "?" in uri:
            if "sslmode" not in uri:
                uri += "&sslmode=require"
        else:
            uri += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # -------------------------------
    # 🧩 Session Settings
    # -------------------------------
    SESSION_COOKIE_SECURE = True               # required for Render HTTPS
    SESSION_COOKIE_SAMESITE = "None"           # allow cross-site cookies
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days

    # -------------------------------
    # 🧠 Debug
    # -------------------------------
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']

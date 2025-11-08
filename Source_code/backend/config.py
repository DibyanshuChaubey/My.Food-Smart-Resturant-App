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
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///database.db'  # local fallback
    ).replace("postgres://", "postgresql://")  # Render’s fix for SQLAlchemy

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------
    # 📧 Mail Settings (Gmail SMTP)
    # -------------------------------
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (
        os.getenv('MAIL_SENDER_NAME', 'Restaurant App'),
        os.getenv('MAIL_USERNAME')
    )

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

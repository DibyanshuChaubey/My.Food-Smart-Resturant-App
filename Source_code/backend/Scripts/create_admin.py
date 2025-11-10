# Source_code/backend/Scripts/create_admin.py
import os
import sys
from werkzeug.security import generate_password_hash
from flask import Flask

# ✅ Fix import paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from models import db, User
from config import Config

def make_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

if __name__ == "__main__":
    app = make_app()
    with app.app_context():
        email = input("Admin email (existing or new): ").strip()
        existing = User.query.filter_by(email=email).first()
        if existing:
            existing.role = 'admin'
            db.session.commit()
            print(f"✅ Updated existing user {email} -> admin")
        else:
            name = input("Name for new admin: ").strip() or "Admin"
            pwd = input("Password for new admin: ").strip() or "admin123"
            user = User(name=name, email=email, password=generate_password_hash(pwd), role='admin')
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created new admin user: {email}")

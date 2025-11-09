from flask import Flask, render_template
from flask_cors import CORS
from flask_mail import Mail
from config import Config
from models import db
from auth import auth_bp, mail as auth_mail
from customer import customer_bp
from admin import admin_bp

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    # ✅ Enable CORS globally (important for Render)
    CORS(app, supports_credentials=True)

    # ✅ Initialize extensions
    db.init_app(app)
    auth_mail.init_app(app)

    # ✅ Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    # ✅ Create all tables safely
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return render_template('index.html')

    return app

app = create_app()

@app.context_processor
def inject_auth_state():
    from flask import session
    return {
        "is_authenticated": bool(session.get("user_id")),
        "user_email": session.get("email")
    }

import os
print("🧩 DEBUG ENV TEST:")
print("MAIL USER:", os.getenv("MAIL_USERNAME"))
print("DB URL:", os.getenv("DATABASE_URL"))

@app.route("/db-check")
def db_check():
    try:
        from models import User
        count = User.query.count()
        return f"✅ Database Connected! Found {count} users."
    except Exception as e:
        return f"❌ DB Error: {e}"

from flask import g
from sqlalchemy import text
import time

@app.before_request
def db_health_check():
    """Optional: lightweight DB connection check (every request)"""
    try:
        start = time.time()
        db.session.execute(text("SELECT 1"))
        g.db_latency = round((time.time() - start) * 1000, 2)
    except Exception as e:
        print("❌ Database connection issue detected:", e)

@app.after_request
def log_db_status(response):
    """Logs request + DB health details to Render logs"""
    if hasattr(g, "db_latency"):
        print(f"✅ DB OK | Query latency: {g.db_latency} ms | Path: {request.path}")
    else:
        print(f"⚠️ DB check skipped | Path: {request.path}")
    return response



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

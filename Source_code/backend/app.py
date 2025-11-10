from flask import Flask, render_template, request, g
from flask_cors import CORS
from flask_mail import Mail
from config import Config
from models import db
from auth import auth_bp, mail as auth_mail
from customer import customer_bp
from admin import admin_bp
from sqlalchemy import text
import os
import time

# =====================================================
# 🧩 App Factory
# =====================================================
def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config)

    # ✅ Enable CORS globally
    CORS(app, supports_credentials=True)

    # ✅ Initialize extensions
    db.init_app(app)
    auth_mail.init_app(app)

    # ✅ Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    # ✅ Create tables safely
    with app.app_context():
        db.create_all()

    # ✅ Define main route
    @app.route('/')
    def home():
        dishes = [
        {"id":1,"name": "Truffle Risotto", "price": 18.99, "category": "startters",
         "description": "Vegitable Salad with fresh ingredients.",
         "image": "/static/images/vegitable_salad.jpg"},
        {"id":2,"name": "Grilled Salmon", "price": 22.49, "category": "main-course",
         "description": "Delicious Crispy Sweet Corn butter sauce.",
         "image": "/static/images/Sweet_Corn.jpg"},
        {"id":3,"name": "Tiramisu", "price": 8.99, "category": "desserts",
         "description": "Classic Italian dessert with mascarpone and cocoa.",
         "image": "/static/images/tiramisu.jpg"}
        ]
        return render_template('index.html', dishes=dishes)


    return app


# =====================================================
# 🚀 App Instance
# =====================================================
app = create_app()


# =====================================================
# 🌐 Template Context (For Navbar)
# =====================================================
@app.context_processor
def inject_auth_state():
    from flask import session
    return {
        "is_authenticated": bool(session.get("user_id")),
        "user_email": session.get("email"),
        "user_role": session.get("role")
    }


# =====================================================
# 🧠 DB Health Monitoring Middleware
# =====================================================
@app.before_request
def db_health_check():
    """Check DB connection (only when DEBUG=True)."""
    if os.getenv("DEBUG", "False").lower() not in ["true", "1", "t"]:
        return
    try:
        start = time.time()
        db.session.execute(text("SELECT 1"))
        g.db_latency = round((time.time() - start) * 1000, 2)
    except Exception as e:
        print("❌ Database connection issue detected:", e)
        g.db_latency = None


@app.after_request
def log_db_status(response):
    """Log DB connection health (only when DEBUG=True)."""
    if os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]:
        if hasattr(g, "db_latency") and g.db_latency is not None:
            print(f"✅ DB OK | Query latency: {g.db_latency} ms | Path: {request.path}")
        else:
            print(f"⚠️ DB check skipped or failed | Path: {request.path}")
    return response


# =====================================================
# 🧩 Manual DB Check Route
# =====================================================
@app.route("/db-check")
def db_check():
    """Manual DB connectivity test."""
    try:
        from models import User
        count = User.query.count()
        return f"✅ Database Connected! Found {count} users."
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return f"❌ DB Error: {e}"


# =====================================================
# 🧩 Environment Debug (Print Once)
# =====================================================
if os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]:
    print("///////////////////////////////////////////////////////////")
    print("🧩 DEBUG ENV TEST:")
    print("MAIL USER:", os.getenv("MAIL_USERNAME"))
    print("DB URL:", os.getenv("DATABASE_URL"))
    print("///////////////////////////////////////////////////////////")


# =====================================================
# 🚀 Run Server
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

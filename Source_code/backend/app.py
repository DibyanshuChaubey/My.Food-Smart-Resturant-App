# backend/app.py
from flask import Flask, render_template
from flask_mail import Mail
from flask_cors import CORS
from config import Config
from models import db
from auth import auth_bp, mail as auth_mail
from customer import customer_bp
from admin import admin_bp


# -----------------------------
#  Application Factory
# -----------------------------
def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    # Enable CORS (optional)
    CORS(app)

    # ✅ Initialize extensions
    db.init_app(app)
    auth_mail.init_app(app)

    # ✅ Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    # ✅ Create tables only if they don't exist
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():  # Only run if no tables
            print("🔧 Creating database tables for the first time...")
            db.create_all()


    # ✅ Inject session variables (for login-based nav)
    @app.context_processor
    def inject_auth_state():
        from flask import session
        return {
            "is_authenticated": bool(session.get("user_id")),
            "user_email": session.get("email")
        }

    # ✅ Create tables automatically (safe)
    # with app.app_context():
    #     db.create_all()

    # ✅ Define routes
    @app.route('/')
    def home():
        return render_template('index.html')

    return app


# -----------------------------
#  Global Flask App for Gunicorn
# -----------------------------
app = create_app()


# -----------------------------
#  Run Locally
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


# backend/app.py
from flask import Flask, render_template
from flask_mail import Mail
from flask_cors import CORS
from backend.config import Config
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

    # Enable CORS
    CORS(app)

    # Initialize extensions
    db.init_app(app)
    auth_mail.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    # 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # Inject session data globally (used for navbar login status)
    @app.context_processor
    def inject_auth_state():
        from flask import session
        return {
            "is_authenticated": bool(session.get("user_id")),
            "user_email": session.get("email")
        }

    return app


# -----------------------------
#  Run the Application
# -----------------------------
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

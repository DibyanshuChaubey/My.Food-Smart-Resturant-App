from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

def setup_database():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if admin exists
        admin_email = "admin@example.com"
        existing_admin = User.query.filter_by(email=admin_email).first()

        if not existing_admin:
            admin = User(
                name="Administrator",
                email=admin_email,
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin@example.com / admin123")
        else:
            print("ℹ️ Admin user already exists.")

if __name__ == "__main__":
    setup_database()

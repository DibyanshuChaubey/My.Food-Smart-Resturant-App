import os
import sys
from werkzeug.security import generate_password_hash
from flask import Flask

# ✅ Fix import paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from models import db, User
from config import Config
from app import app

def list_admins():
    """Display all current admins"""
    admins = User.query.filter_by(role='admin').all()
    if not admins:
        print("⚠️ No admins found in database.")
        return False
    print("\n📋 Current Admins:")
    print("-" * 50)
    for a in admins:
        print(f"👤 {a.id} | {a.name} | {a.email} | Created: {a.created_at}")
    print("-" * 50)
    return True

is_end=True
while is_end:
    with app.app_context():
        print("\n====== 🧑‍💼 ADMIN MANAGEMENT TOOL ======")
        print("1️⃣ List all admins")
        print("2️⃣ Edit an admin")
        print("3️⃣ Delete an admin")
        print("4️⃣ Exit")
        print("=========================================")

        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            list_admins()

        elif choice == "2":
            is_admin=list_admins()
            if is_admin:
                email = input("Enter admin email to edit: ").strip()
                admin = User.query.filter_by(email=email, role='admin').first()
                print(f"Editing admin: {admin.name} ({admin.email})")
                new_name = input(f"New name (press Enter to keep '{admin.name}'): ").strip()
                new_email = input(f"New email (press Enter to keep '{admin.email}'): ").strip()
                new_password = input("New password (press Enter to keep current): ").strip()

                if new_name:
                    admin.name = new_name
                if new_email:
                    admin.email = new_email
                if new_password:
                    admin.password = generate_password_hash(new_password)

                db.session.commit()
                print(f"✅ Admin '{admin.email}' updated successfully!")

        elif choice == "3":
            list_admins()
            email = input("Enter admin email to delete: ").strip()
            admin = User.query.filter_by(email=email, role='admin').first()

            if not admin:
                print(f"⚠️ No admin found with email: {email}")
            else:
                confirm = input(f"⚠️ Are you sure you want to delete admin '{email}'? (yes/no): ").lower()
                if confirm == "yes":
                    db.session.delete(admin)
                    db.session.commit()
                    print(f"🗑️ Admin '{email}' deleted successfully.")
                else:
                    print("❌ Operation cancelled.")

        elif choice == "4":
            is_end=False
            print("👋 Exiting...")
        else:
            print("❌ Invalid choice. Please enter a number 1–4.")

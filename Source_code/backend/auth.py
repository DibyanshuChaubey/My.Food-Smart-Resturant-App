from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
import requests  # External HTTP library for Brevo API
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from flask_mail import Mail
import random
import string
import os

# ====================================================
# 🔧 Setup
# ====================================================
auth_bp = Blueprint('auth', __name__)
mail = Mail()

# Temporary in-memory OTP store (for production use Redis or DB)
otp_store = {}

# ====================================================
# 🔹 USER REGISTRATION
# ====================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template('register.html', error="Email already registered.")

        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("🎉 Registration successful! Please login.")
        return redirect(url_for('auth.otp_login'))

    return render_template('register.html')

# ====================================================
# 🔹 PASSWORD + OTP LOGIN
# ====================================================
@auth_bp.route('/otp_login', methods=['GET', 'POST'])
def otp_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email

            next_url = session.pop('post_login_next', None)
            return redirect(next_url or url_for('customer.customer_panel'))

        return render_template('otp_login.html', error="Invalid credentials. Please try again.")

    # Handle ?next= param
    next_url = request.args.get('next')
    if next_url:
        session['post_login_next'] = next_url

    return render_template('otp_login.html')

# ====================================================
# 🔹 SEND OTP (Using Brevo API)
# ====================================================
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'success': False, 'message': '❌ Email not registered. Please register first.'}), 400

    # ✅ Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[email] = otp

    # ✅ Brevo API setup
    api_key = os.getenv("BREVO_API_KEY")
    sender = os.getenv("MAIL_USERNAME")
    sender_name = os.getenv("MAIL_SENDER_NAME", "Restaurant App")

    data = {
        "sender": {"name": sender_name, "email": sender},
        "to": [{"email": email}],
        "subject": "Your OTP Code - Restaurant App 🍽️",
        "htmlContent": f"""
        <div style='font-family: Arial, sans-serif; padding: 15px; background-color: #fff8e1; color: #444; border-radius: 10px;'>
            <h2 style='color: #d97706;'>Welcome to Restaurant App!</h2>
            <p>Your one-time password (OTP) is:</p>
            <h1 style='color:#b45309; letter-spacing: 3px;'>{otp}</h1>
            <p>This code will expire in <b>5 minutes</b>. Do not share it with anyone.</p>
            <hr>
            <p style='font-size: 12px; color: #888;'>Restaurant App Team</p>
        </div>
        """
    }

    try:
        res = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key
            },
            json=data
        )

        if res.status_code == 201:
            print(f"✅ OTP email sent successfully to {email}")
            return jsonify({'success': True, 'message': '✅ OTP sent successfully! Please check your email.'})
        else:
            print(f"⚠️ Brevo API error {res.status_code}: {res.text}")
            return jsonify({'success': False, 'message': '⚠️ Failed to send OTP email. Check Render logs.'})
    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
        return jsonify({'success': False, 'message': f'❌ Network error: {e}'})

# ====================================================
# 🔹 VERIFY OTP (with smart redirect)
# ====================================================
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp = request.form.get('otp')

    user = User.query.filter_by(email=email).first()
    valid = user and otp_store.get(email) == otp

    if valid:
        session['user_id'] = user.id
        session['email'] = user.email
        otp_store.pop(email, None)

        next_url = session.pop('post_login_next', None) or session.pop('redirectAfterLogin', None)
        redirect_url = next_url or url_for('customer.customer_panel')

        flash(f"Welcome back, {user.name}! 🎉")

        # For AJAX requests
        if (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.is_json
            or request.accept_mimetypes.best == 'application/json'
        ):
            return jsonify({
                'success': True,
                'message': '✅ OTP verified successfully!',
                'redirect': redirect_url
            }), 200

        return redirect(redirect_url)

    # ❌ Invalid OTP
    flash("❌ Invalid or expired OTP. Please try again.")
    if (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.is_json
        or request.accept_mimetypes.best == 'application/json'
    ):
        return jsonify({'success': False, 'message': '❌ Invalid or expired OTP.'}), 400

    return redirect(url_for('auth.otp_login'))

# ====================================================
# 🔹 LOGOUT
# ====================================================
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for('home'))  # Redirect to index.html

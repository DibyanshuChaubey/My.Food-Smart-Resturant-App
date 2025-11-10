from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from flask_mail import Mail
import random
import string
import os

auth_bp = Blueprint('auth', __name__)
mail = Mail()

# Temporary in-memory OTP store (replace with Redis or DB in production)
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

        # Check for existing user
        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template('register.html', error="Email already registered.")

        # Create new user
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("✅ Registration successful! Please login to continue.")
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

        # ✅ Password login
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email
            session['role'] = user.role

            flash(f"Welcome back, {user.name}! 🎉")

            # ✅ Redirect based on role or pending URL
            next_url = session.pop('post_login_next', None)
            if next_url:
                return redirect(next_url)
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.customer_dashboard'))

        # ❌ Invalid credentials
        return render_template('otp_login.html', error="Invalid credentials. Please try again.")

    # 🧭 Handle ?next param for redirect after login
    next_url = request.args.get('next')
    if next_url:
        session['post_login_next'] = next_url

    return render_template('otp_login.html')


# ====================================================
# 🔹 SEND OTP (via Brevo)
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
    sender_email = os.getenv("MAIL_USERNAME", "dibyanshuchaubey727@gmail.com")
    sender_name = os.getenv("MAIL_SENDER_NAME", "Soviare Restaurant")

    data = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": email}],
        "subject": "Your OTP Code - Soviare Restaurant",
        "htmlContent": f"""
            <div style='font-family: Arial, sans-serif; padding: 15px;'>
                <h2>🔐 Your OTP Code</h2>
                <p>Hello {user.name if user else 'Customer'},</p>
                <p>Your one-time password is:</p>
                <h1 style='color:#ff6600;'>{otp}</h1>
                <p>This code is valid for 5 minutes.</p>
                <hr>
                <p>🍽️ Soviare — Bringing taste to your doorstep!</p>
            </div>
        """
    }

    try:
        # ✅ Send email via Brevo API
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
            return jsonify({'success': True, 'message': '✅ OTP sent successfully! Please check your email.'}), 200
        else:
            print(f"⚠️ Brevo API error {res.status_code}: {res.text}")
            print(f"🔄 Fallback OTP for {email}: {otp}")
            return jsonify({'success': True, 'message': '⚠️ Email failed, OTP logged in Render logs.'}), 200

    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
        print(f"🔄 Fallback OTP for {email}: {otp}")
        return jsonify({'success': True, 'message': '⚠️ Network issue — OTP logged in Render logs.'}), 200


# ====================================================
# 🔹 VERIFY OTP (with role-based smart redirect)
# ====================================================
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp = request.form.get('otp')

    user = User.query.filter_by(email=email).first()
    valid = user and otp_store.get(email) == otp

    if valid:
        # ✅ OTP success — setup session
        session['user_id'] = user.id
        session['email'] = user.email
        session['role'] = user.role
        otp_store.pop(email, None)

        flash(f"Welcome back, {user.name}! 🎉")

        # ✅ Role-based redirect
        redirect_url = url_for('admin.dashboard') if user.role == 'admin' else url_for('customer.customer_dashboard')

        # ✅ JSON / AJAX Response Support
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
    return redirect(url_for('home'))

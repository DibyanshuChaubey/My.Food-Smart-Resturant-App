# backend/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from models import db, User
import random
import string

auth_bp = Blueprint('auth', __name__)
mail = Mail()

# Temporary in-memory OTP store (for production, replace with Redis or DB)
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
        flash("Registration successful! Please login.")
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

            # Redirect user to pending page (if any)
            next_url = session.pop('post_login_next', None)
            return redirect(next_url or url_for('customer.customer_panel'))

        # ❌ Invalid credentials
        return render_template('otp_login.html', error="Invalid credentials. Please try again.")

    # 🧭 Handle ?next param for redirect after login
    next_url = request.args.get('next')
    if next_url:
        session['post_login_next'] = next_url

    return render_template('otp_login.html')


# ====================================================
# 🔹 SEND OTP (Render-safe)
# ====================================================
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            'success': False,
            'message': '❌ Email not registered. Please register first.'
        }), 400

    # Generate and store OTP
    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[email] = otp

    # ✅ Log OTP for Render (no SMTP needed)
    print(f"✅ OTP for {email}: {otp}")

    # Optional: send via Gmail if SMTP creds exist
    try:
        if mail:
            msg = Message(
                subject="Your OTP Code - Restaurant App",
                recipients=[email],
                body=f"Your OTP code is {otp}. It will expire soon.",
                sender=("Restaurant App", "noreply@restaurant-app.com")
            )
            mail.send(msg)
    except Exception as e:
        print("⚠️ Email send skipped:", e)

    return jsonify({
        'success': True,
        'message': f"✅ OTP generated successfully for {email}. (Check Render Logs)"
    }), 200


# ====================================================
# 🔹 VERIFY OTP (with smart redirect)
# ====================================================
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp = request.form.get('otp')

    # ✅ Validate OTP
    if otp_store.get(email) == otp:
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            session['email'] = user.email
            otp_store.pop(email, None)

            # Smart redirect after OTP login
            next_url = session.pop('post_login_next', None) or session.pop('redirectAfterLogin', None)
            pending_data = (
                session.pop('pendingOrder', None)
                or session.pop('pendingBooking', None)
                or session.pop('pendingEvent', None)
            )

            flash(f"Welcome back, {user.name}! 🎉")

            # Handle AJAX (fetch) or normal redirect
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'redirect': next_url or url_for('customer.customer_panel'),
                    'pending_data': pending_data
                })

            return redirect(next_url or url_for('customer.customer_panel'))

    # ❌ Invalid OTP
    flash("Invalid or expired OTP. Please try again.")
    return redirect(url_for('auth.otp_login'))


# ====================================================
# 🔹 LOGOUT
# ====================================================
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for('home'))  # Redirect to index.html

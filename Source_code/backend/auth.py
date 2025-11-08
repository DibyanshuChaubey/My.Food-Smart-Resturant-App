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
    try:
        email = request.form.get('email')

        if not email:
            return jsonify({'success': False, 'message': '⚠️ Email is required.'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': '❌ Email not registered. Please register first.'}), 400

        # ✅ Generate and store OTP
        otp = ''.join(random.choices(string.digits, k=6))
        otp_store[email] = otp

        # ✅ Log OTP (since SMTP may not work on Render free tier)
        print(f"✅ OTP for {email}: {otp}")

        # 🔒 Try email sending only if SMTP is configured
        try:
            msg = Message(
                subject="Your OTP Code - Restaurant App",
                recipients=[email],
                body=f"Your OTP code is {otp}.",
                sender=("Restaurant App", "noreply@restaurant-app.com")
            )
            mail.send(msg)
        except Exception as mail_err:
            print(f"⚠️ Mail sending skipped: {mail_err}")

        return jsonify({'success': True, 'message': '✅ OTP sent successfully! Check Render logs.'}), 200

    except Exception as e:
        print("❌ Error in /send-otp:", str(e))
        return jsonify({'success': False, 'message': f'❌ Server error: {str(e)}'}), 500



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
        # ✅ Save session
        session['user_id'] = user.id
        session['email'] = user.email
        otp_store.pop(email, None)

        # ✅ Smart redirect handling
        next_url = session.pop('post_login_next', None) or session.pop('redirectAfterLogin', None)
        redirect_url = next_url or url_for('customer.customer_panel')

        flash(f"Welcome back, {user.name}! 🎉")

        # ✅ Detect AJAX / fetch requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({
                'success': True,
                'message': '✅ OTP verified successfully!',
                'redirect': redirect_url
            }), 200

        # Normal browser form post fallback
        return redirect(redirect_url)

    # ❌ Invalid OTP
    flash("❌ Invalid or expired OTP. Please try again.")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
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

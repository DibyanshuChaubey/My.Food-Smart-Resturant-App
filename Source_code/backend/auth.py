# backend/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from models import db, User
import random
import string

auth_bp = Blueprint('auth', __name__)
mail = Mail()

# temporary memory storage (use Redis in production)
otp_store = {}

# 🔹 Registration
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
        flash("Registration successful! Please login.")
        return redirect(url_for('auth.otp_login'))
    return render_template('register.html')


# 🔹 OTP Login (GET + POST combined cleanly)
@auth_bp.route('/otp_login', methods=['GET', 'POST'])
def otp_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email

            # 🆕 After normal login, redirect to saved next page if available
            next_url = session.pop('post_login_next', None)
            if next_url:
                return redirect(next_url)
            return redirect(url_for('customer.customer_panel'))

        return render_template('otp_login.html', error="Invalid credentials.")

    # 🆕 Handle ?next= param in GET
    next_url = request.args.get('next')
    if next_url:
        session['post_login_next'] = next_url  # store for later use

    return render_template('otp_login.html')


# 🔹 Send OTP
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'error': 'Email not registered.'})

    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[email] = otp

    msg = Message(
        subject="Your OTP Code",
        recipients=[email],
        body=f"Your OTP code is {otp}.",
        sender=("Restaurant App", "dibyanshuchaubey727@gmail.com")
    )

    try:
        mail.send(msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# 🔹 Verify OTP (with redirect to saved page)
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp = request.form.get('otp')

    if otp_store.get(email) == otp:
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            session['email'] = user.email
            otp_store.pop(email, None)

            # 🆕 smart redirect after OTP login
            next_url = session.pop('post_login_next', None)
            if next_url:
                return redirect(next_url)
            return redirect(url_for('customer.customer_panel'))

    flash("Invalid or expired OTP. Please try again.")
    return redirect(url_for('auth.otp_login'))


# 🔹 Logout
# 🔹 Logout
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('home'))  # ✅ Redirects to index.html


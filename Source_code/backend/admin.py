# backend/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, Order, PrivateRoom, Event, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin_logged_in() -> bool:
    return bool(session.get('admin'))

# -------- Auth --------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, go to dashboard
    if is_admin_logged_in():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Look up admin user in DB
        admin_user = User.query.filter_by(email=email, role='admin').first()

        if admin_user and check_password_hash(admin_user.password, password):
            session['admin'] = True
            session['admin_email'] = admin_user.email
            flash('Logged in as admin.', 'success')
            return redirect(url_for('admin.dashboard'))

        # If no DB admin matches, fail silently
        return render_template('admin_login.html', error="Invalid admin credentials.")

    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('admin_email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

# -------- Dashboard --------
@admin_bp.route('/dashboard')
def dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    private_bookings = PrivateRoom.query.order_by(PrivateRoom.created_at.desc()).all()
    event_bookings = Event.query.order_by(Event.created_at.desc()).all()

    # admin.html expects SQLAlchemy objects (not tuples)
    return render_template(
        'admin.html',
        orders=orders,
        private_bookings=private_bookings,
        event_bookings=event_bookings
    )

# -------- Order Actions --------
@admin_bp.route('/order/<int:id>')
def order_detail(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))
    order = Order.query.get_or_404(id)
    return render_template('order_detail.html', order=order)

@admin_bp.route('/order/<int:id>/complete', methods=['POST'])
def complete_order(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))
    order = Order.query.get_or_404(id)
    order.status = 'Completed'
    db.session.commit()
    flash(f'Order #{id} marked as Completed.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/order/<int:id>/delete', methods=['POST'])
def delete_order(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash(f'Order #{id} deleted.', 'warning')
    return redirect(url_for('admin.dashboard'))

# -------- Private Room Details --------
@admin_bp.route('/private/<int:id>')
def private_detail(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))
    booking = PrivateRoom.query.get_or_404(id)
    return render_template('private_detail.html', booking=booking)

# -------- Event Details --------
@admin_bp.route('/event/<int:id>')
def event_detail(id):
    if not is_admin_logged_in():
        return redirect(url_for('admin.login'))
    event = Event.query.get_or_404(id)
    return render_template('event_detail.html', event=event)

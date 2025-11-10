# backend/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from functools import wraps
from models import db, User, Order, PrivateRoom, Event  # adjust import path if necessary
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')

def admin_required(f):
    """Decorator: require an authenticated user with role == 'admin'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id') or session.get('role') != 'admin':
            flash("Unauthorized: admin access required.", "danger")
            # send user to login with next param
            return redirect(url_for('auth.otp_login', next=request.path))
        return f(*args, **kwargs)
    return decorated

# ---- Admin dashboard ----
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # show quick counts
    users_count = User.query.count()
    orders_count = Order.query.count()
    rooms_count = PrivateRoom.query.count()
    events_count = Event.query.count()
    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           orders_count=orders_count,
                           rooms_count=rooms_count,
                           events_count=events_count)

# ---- Users list / manage ----
@admin_bp.route('/users')
@admin_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/promote/<int:user_id>', methods=['POST'])
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash(f"{user.email} promoted to admin.", "success")
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/demote/<int:user_id>', methods=['POST'])
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    # prevent demoting yourself accidentally
    if user.id == session.get('user_id'):
        flash("You cannot demote yourself.", "warning")
        return redirect(url_for('admin.users_list'))
    user.role = 'customer'
    db.session.commit()
    flash(f"{user.email} demoted to customer.", "success")
    return redirect(url_for('admin.users_list'))

# ---- Orders listing ----
@admin_bp.route('/orders')
@admin_required
def orders_list():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    # for each order we can show minimal info; template will iterate
    return render_template('admin/listing.html', title="Orders", items=orders, kind='orders')

# ---- Private rooms listing ----
@admin_bp.route('/rooms')
@admin_required
def rooms_list():
    rooms = PrivateRoom.query.order_by(PrivateRoom.created_at.desc()).all()
    return render_template('admin/listing.html', title="Private Rooms", items=rooms, kind='rooms')

# ---- Events listing ----
@admin_bp.route('/events')
@admin_required
def events_list():
    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template('admin/listing.html', title="Events", items=events, kind='events')

# ---- API helper to toggle order status (example) ----
@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def change_order_status(order_id):
    new_status = request.form.get('status')
    order = Order.query.get_or_404(order_id)
    order.status = new_status
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'status': new_status})
    flash("Order status updated.", "success")
    return redirect(url_for('admin.orders_list'))

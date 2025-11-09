# backend/customer.py
from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, flash
from models import db, Order, PrivateRoom, Event, User

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

# ----------------------------------------------------
# 1️⃣ Customer Panel (Welcome Page)
# ----------------------------------------------------
@customer_bp.route('/', methods=['GET'])
def customer_panel():
    if not session.get('user_id'):
        flash("Please login to continue.")
        return redirect(url_for('auth.otp_login'))

    email = session.get('email', 'customer@example.com')
    return render_template('customer_panel.html', email=email)


# ----------------------------------------------------
# 2️⃣ Customer Dashboard (Detailed View)
# ----------------------------------------------------
@customer_bp.route('/dashboard', methods=['GET'])
def customer_dashboard():
    if not session.get('user_id'):
        flash("Please login to access your dashboard.")
        return redirect(url_for('auth.otp_login'))

    email = session.get('email', 'customer@example.com')
    return render_template('customer.html', email=email)


# ----------------------------------------------------
# 3️⃣ Customer Data API for Dashboard
# ----------------------------------------------------
@customer_bp.route('/api/customer-data', methods=['GET'])
def get_customer_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    email = session.get('email', '')

    orders = Order.query.filter_by(customer_id=user_id).all()
    private_rooms = PrivateRoom.query.filter_by(customer_id=user_id).all()
    events = Event.query.filter_by(customer_id=user_id).all()

    print("DEBUG:", user_id, len(orders), len(private_rooms), len(events))  # 🧩 debug info

    def serialize(model_obj):
        return {col.name: getattr(model_obj, col.name) for col in model_obj.__table__.columns}

    return jsonify({
        'email': email,
        'orders': [serialize(o) for o in orders],
        'private_rooms': [serialize(r) for r in private_rooms],
        'events': [serialize(e) for e in events]
    })


# ----------------------------------------------------
# 4️⃣ Create New Order
# ----------------------------------------------------
@customer_bp.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    # Require login
    if not session.get('user_id'):
        return jsonify({'login_required': True, 'message': 'Please login to place an order.'}), 401

    try:
        new_order = Order(
            customer_id=session['user_id'],
            items=data.get('items', []),
            total=data.get('total', 0.0),
            method=data.get('delivery', {}).get('method', 'Pickup'),
            address=data.get('delivery', {}).get('address', ''),
            special_requests=data.get('delivery', {}).get('specialRequests', '')
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'success': True, 'order_id': new_order.id}), 201

    except Exception as e:
        print("Error creating order:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ----------------------------------------------------
# 5️⃣ Book Private Room
# ----------------------------------------------------
@customer_bp.route('/api/private-room', methods=['POST'])
def book_private_room():
    try:
        if not session.get('user_id'):
            return jsonify({'login_required': True, 'message': 'Please login to book a private room.'}), 401

        data = request.get_json()
        new_booking = PrivateRoom(
            customer_id=session['user_id'],
            name=data.get('name', 'Anonymous'),
            email=data.get('email', ''),
            date=data.get('date', ''),
            time=data.get('time', ''),
            message=data.get('specialRequests', '')
        )
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({'success': True, 'booking_id': new_booking.id}), 201

    except Exception as e:
        print("Error booking private room:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ----------------------------------------------------
# 6️⃣ Reserve Event
# ----------------------------------------------------
@customer_bp.route('/api/event-reservation', methods=['POST'])
def event_reservation():
    try:
        if not session.get('user_id'):
            return jsonify({'login_required': True, 'message': 'Please login to reserve an event.'}), 401

        data = request.get_json()
        new_event = Event(
            customer_id=session['user_id'],
            name=data.get('name', 'Anonymous'),
            email=data.get('email', ''),
            event_type=data.get('event_type', ''),
            guests=data.get('guests', 0),
            date=data.get('date', ''),
            message=data.get('message', '')
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'success': True, 'event_id': new_event.id}), 201

    except Exception as e:
        print("Error booking event:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ----------------------------------------------------
# 7️⃣ Debug Route (Optional)
# ----------------------------------------------------
@customer_bp.route('/debug-data', methods=['GET'])
def debug_customer_data():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized - Please log in first'}), 401

    user_id = session['user_id']
    email = session.get('email')

    orders = Order.query.filter_by(customer_id=user_id).all()
    rooms = PrivateRoom.query.filter_by(customer_id=user_id).all()
    events = Event.query.filter_by(customer_id=user_id).all()

    def serialize(obj):
        return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}

    return jsonify({
        'customer_id': user_id,
        'email': email,
        'orders': [serialize(o) for o in orders],
        'private_rooms': [serialize(r) for r in rooms],
        'events': [serialize(e) for e in events]
    })

# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # ✅ Only define, do not initialize with app here

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='customer')
    created_at = db.Column(db.DateTime, default=datetime.now)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20))
    address = db.Column(db.String(200))
    special_requests = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.now)

class PrivateRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ✅ Added link
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ✅ Added link
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    event_type = db.Column(db.String(50))
    guests = db.Column(db.Integer)
    date = db.Column(db.String(20))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

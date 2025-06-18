from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):  # Inherit from UserMixin
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    is_artisan = db.Column(db.Boolean, default=False)
    profile_pic = db.Column(db.String(200))
    messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return True  # Override to always return True; adjust if you add an active status field

class Artisan(db.Model):
    __tablename__ = 'artisan'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    skills = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', backref=db.backref('artisan', uselist=False))

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id', name='fk_message_parent_id'))

    # Replies in chronological order
    replies = db.relationship(
        'Message',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        order_by='Message.timestamp.asc()'
    )

    @classmethod
    def top_level_for_user(cls, user_id):
        """Return top-level (non-reply) messages received by a user, oldest first."""
        return cls.query.filter_by(recipient_id=user_id, parent_id=None).order_by(cls.timestamp.asc())

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisan.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # e.g., 1-5
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    customer = db.relationship('User', backref=db.backref('reviews_given', lazy='dynamic'))
    artisan = db.relationship('Artisan', backref=db.backref('reviews_received', lazy='dynamic'))
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
    job_posts = db.relationship('JobPost', back_populates='user', lazy='dynamic')
    favorites = db.relationship('Favorite', back_populates='user', lazy='dynamic')
    reviews_given = db.relationship('Review', back_populates='customer', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')

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
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    user = db.relationship('User', backref=db.backref('artisan', uselist=False))
    favorited_by = db.relationship('Favorite', back_populates='artisan', lazy='dynamic')
    reviews_received = db.relationship('Review', back_populates='artisan', lazy='dynamic')
    job_applications = db.relationship('JobApplication', back_populates='artisan', lazy='dynamic')

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
    customer = db.relationship('User', back_populates='reviews_given')
    artisan = db.relationship('Artisan', back_populates='reviews_received')

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'message', 'review', 'booking'
    message = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255))  # Optional: link to relevant page
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='notifications')

class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisan.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='favorites')
    artisan = db.relationship('Artisan', back_populates='favorited_by')

class JobPost(db.Model):
    __tablename__ = 'job_post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    budget = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='job_posts')
    applications = db.relationship('JobApplication', backref='job_post', lazy='dynamic')

class JobApplication(db.Model):
    __tablename__ = 'job_application'
    id = db.Column(db.Integer, primary_key=True)
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisan.id'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    artisan = db.relationship('Artisan', back_populates='job_applications')
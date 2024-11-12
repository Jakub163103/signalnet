from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)  # Store hashed password
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)  # Foreign key
    subscription = db.relationship('Subscription', backref='users')
    profile_picture = db.Column(db.String(150), nullable=True)  # New column for profile picture
    last_signal_reset = db.Column(db.DateTime, nullable=True)  # New column to track last reset time
    signals_used = db.Column(db.Integer, default=0)  # New column for signal count
    country = db.Column(db.String(2), nullable=False)  # ISO country code
    
    # Privacy settings fields
    allow_marketing_emails = db.Column(db.Boolean, default=False)
    share_data_with_partners = db.Column(db.Boolean, default=False)
    allow_profile_visibility = db.Column(db.Boolean, default=True)  # Default to public

    def __repr__(self):
        return f"<User {self.username}>"

# Define a Subscription model
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    stripe_price_id = db.Column(db.String(50), nullable=False, unique=True)  # New field for Stripe price ID
    features = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.name}>"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Recipient
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Sender
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy=True))
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_notifications', lazy=True))

    def __repr__(self):
        return f"<Notification {self.id} from User {self.sender_id} to User {self.user_id}>"
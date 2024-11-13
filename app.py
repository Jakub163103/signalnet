from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, abort, jsonify
from markupsafe import Markup  # Correct import for Markup
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from PIL import Image
import random
import websocket
import json
from threading import Thread
from utils import send_notification  # Add this import
from datetime import datetime, timedelta
from models_.trend_analysis import calculate_moving_averages, generate_signals
import pandas as pd
import stripe
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask_wtf.csrf import CSRFProtect, CSRFError
from forms import (
    LoginForm,
    SignupForm,
    SubscribeForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    UpdateProfileForm,
    AccountSettingsForm,
    PrivacySettingsForm,
    AdminNotificationForm
)
from sqlalchemy.exc import SQLAlchemyError
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_mail import Mail, Message  # For sending emails
from itsdangerous import URLSafeTimedSerializer
from flask_login import login_required, current_user, LoginManager, login_user, logout_user, UserMixin
from dotenv import load_dotenv

from models import db, User, Subscription, Notification  # Add this line

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()  # Loads variables from .env into environment variables

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'Dewgwr432423423')  # Default for development
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Adjust as needed
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
csrf = CSRFProtect(app)

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Ensure this is correct
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.yourmailserver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@domain.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
mail = Mail(app)

def allowed_file(filename):
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        return True
    return False

def validate_image(stream):
    try:
        img = Image.open(stream)
        img.verify()
        return True
    except Exception:
        return False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Mail
mail = Mail(app)

def generate_default_profile_picture(username):
    # Create a blank image with a random background color
    img = Image.new('RGB', (100, 100), color=random_color())

    # Save the image to a file
    filename = f"{username}_default.png"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img.save(file_path)

    return os.path.join('uploads', filename)

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

@app.route('/')
def home():
    subscriptions = Subscription.query.all()
    form = SubscribeForm()
    return render_template('index.html', subscriptions=subscriptions, form=form)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Handle form submission
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

@app.route('/services')
def services():
    if 'user_logged_in' not in session:
        flash('Please log in to access the services.', 'warning')
        return redirect(url_for('login'))
    
    services_list = [
        {
            'name': 'Quick Signal',
            'slug': 'quick-signal',
            'description': 'Our Quick Signal service provides real-time financial market signals to help you make informed decisions swiftly.'
        },
    ]
    return render_template('services.html', services=services_list)

@app.route('/services/<slug>')
def service_detail(slug):
    if 'user_logged_in' not in session:
        flash('Please log in to access the service details.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    # Check if the user has an active subscription
    if not user.subscription:
        flash('You need an active subscription to access this service.', 'warning')
        return redirect(url_for('subscribe'))

    service_details = {
        'quick-signal': {
            'name': 'Quick Signal',
            'description': 'Our Quick Signal service provides real-time financial market signals to help you make informed decisions swiftly.',
            'features': [
                'Real-time data access',
                'Customizable alerts',
                'Comprehensive market analysis'
            ]
        },
    }

    service = service_details.get(slug)
    if not service:
        return render_template('404.html'), 404

    # Define the pairs you want to track
    pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    prices = {}

    return render_template('services/quick_signal.html', service=service, pairs=prices)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    form = SubscribeForm()
    subscriptions = Subscription.query.all()
    stripe_public_key = os.getenv('STRIPE_PUBLIC_KEY')  # Retrieve the publishable key

    if form.validate_on_submit():
        subscription_name = form.subscription.data
        price_id_map = {
            'Basic': os.getenv('BASIC_PRICE_ID'),
            'Pro': os.getenv('PRO_PRICE_ID'),
            'Professional': os.getenv('PROFESSIONAL_PRICE_ID')
        }
        price_id = price_id_map.get(subscription_name)

        if not price_id:
            flash('Invalid subscription plan selected.', 'danger')
            return redirect(url_for('subscribe'))

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('payment_cancelled', _external=True),
                customer_email=current_user.email,
                client_reference_id=str(current_user.id)
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            flash(f'An error occurred while creating the checkout session: {str(e)}', 'danger')
            return redirect(url_for('subscribe'))

    return render_template('subscribe.html', subscriptions=subscriptions, form=form, stripe_public_key=stripe_public_key)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    form.country.choices = [(country['code'], country['name']) for country in country_data]

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        country_code = form.country.data.strip()

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please try again.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password, country=country_code)
        db.session.add(new_user)

        try:
            db.session.commit()
            print("New user committed to the database.")  # Debugging

            login_user(new_user)

            # Send a welcome message
            system_user = User.query.filter_by(username='System').first()
            if system_user:
                print(f"System user found: {system_user.id}")  # Debugging
                welcome_message = (
                    "Welcome to SignalNet! We're excited to have you on board. "
                    "Please take a moment to explore our features and let us know if you have any questions."
                )
                send_notification(new_user.id, system_user.id, welcome_message)
            else:
                print("System user not found.")  # Debugging

            flash('Your account has been created and you are now logged in!', 'success')
            return redirect(url_for('home'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while saving to the database.', 'danger')
            print(f"Database error: {str(e)}")

    elif form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('signup.html', form=form, countries=country_data)

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Use Flask-Login's logout_user
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/subscription')
def subscription():
    if 'user_logged_in' not in session:
        flash('Please log in to view subscription plans.', 'warning')
        return redirect(url_for('login'))
    return render_template('subscription.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)  # Populate form with current user data
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    return render_template('profile.html', form=form)

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    if user and not user.profile_picture:
        # Generate a default profile picture if none exists
        user.profile_picture = generate_default_profile_picture(user.username)
        db.session.commit()

    return dict(user=user)

@app.route('/quick_signal', methods=['GET', 'POST'])
def quick_signal():
    symbol = request.args.get('symbol', 'btcusdt').upper()
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    if user:
        # Reset signal count if a day has passed since the last reset
        if user.last_signal_reset is None or user.last_signal_reset < datetime.now() - timedelta(days=1):
            user.signals_used = 0
            user.last_signal_reset = datetime.now()
            db.session.commit()

        model_name = "Trend Analysis Model"  # Ensure model_name is always defined
        remaining_time_seconds = None  # Initialize as None

        if request.method == 'POST':
            # Check if the user has remaining signals
            if user.signals_used < 5:  # Assuming 5 signals per day for Basic Plan
                user.signals_used += 1
                db.session.commit()

                from models_.trend_analysis import calculate_moving_averages
                data = calculate_moving_averages(data)

                latest_signal = data.iloc[-1]['position'] if 'position' in data else 'N/A'
                remaining_time_seconds = (user.last_signal_reset + timedelta(days=1) - datetime.now()).total_seconds()
            else:
                flash('Signal limit reached for today.', 'warning')
                return redirect(url_for('subscribe'))
        else:
            latest_signal = 'N/A'

        return render_template(
            'services/quick_signal.html',
            selected_pair=symbol,
            signal_count=user.signals_used,
            remaining_time_seconds=remaining_time_seconds,
            latest_signal=latest_signal,
            model_name=model_name
        )

    flash('You need a subscription to access this feature.', 'warning')
    return redirect(url_for('subscribe'))


def on_message(ws, message):
    data = json.loads(message)
    price = data['p']

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")


@app.route('/success')
def success():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    if user:
        # Retrieve the subscription name from the session or request
        subscription_name = request.args.get('subscription_name')  # Ensure this is being passed correctly
        subscription = Subscription.query.filter_by(name=subscription_name).first()  # Check for exact match

        if subscription:
            # Assign the subscription to the user
            user.subscription_id = subscription.id
            db.session.commit()
            flash(f'Successfully subscribed to {subscription.name} plan.', 'success')
        else:
            flash('Subscription plan not found.', 'danger')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('profile'))

@app.route('/cancel')
def cancel():
    flash('Payment was canceled or failed. Please try again.', 'warning')
    return redirect(url_for('subscribe'))

@app.route('/cancel_subscription', methods=['POST'])
def cancel_subscription():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    if user and user.email:
        try:
            # Retrieve the customer's subscriptions
            subscriptions = stripe.Subscription.list(customer=user.email)

            if subscriptions.data:
                # Assume the first subscription is the one to cancel
                subscription_id = subscriptions.data[0].id

                # Cancel the subscription in Stripe
                stripe.Subscription.delete(subscription_id)

                # Update the user's subscription status in your database
                user.subscription_id = None
                db.session.commit()

                flash('Your subscription has been canceled.', 'success')
            else:
                flash('No active subscription found.', 'warning')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('User not found or no email associated.', 'warning')

    return redirect(url_for('profile'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'profile_picture' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # Update user's profile_picture in the database
        current_user.profile_picture = f'uploads/{filename}'
        db.session.commit()
        flash('File successfully uploaded and profile updated.', 'success')
    else:
        flash('Invalid file type. Please upload an image file (png, jpg, jpeg, gif).', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/create_subscription', methods=['POST'])
def create_subscription():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    if user:
        price_id = request.form.get('subscription')
        try:
            # Create a Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=url_for('profile', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('subscribe', _external=True),
            )
            return redirect(session.url, code=303)
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('profile'))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/cookie_policy')
def cookie_policy():
    return render_template('cookie_policy.html')

def get_user_country():
    ip_address = request.remote_addr
    response = requests.get(f"http://ip-api.com/json/{ip_address}")
    data = response.json()
    if data['status'] == 'success':
        return data['countryCode']  # Returns country code e.g., 'US', 'PL'
    return None

# Load country data from JSON file
def load_country_data():
    with open('static/data/countries.json', 'r') as file:
        return json.load(file)

country_data = load_country_data()

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send Message')

@app.route('/set-cookie')
def set_cookie():
    resp = make_response(render_template('some_template.html'))
    resp.set_cookie('user_preference', 'dark_mode', max_age=365*24*60*60, httponly=True, secure=True, samesite='Strict')
    return resp

@app.route('/get-cookie')
def get_cookie():
    user_preference = request.cookies.get('user_preference', 'light_mode')
    return render_template('some_template.html', preference=user_preference)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a password reset token (implement token generation as needed)
            token = generate_reset_token(user.id)  # You need to define this function
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            msg = Message('Password Reset Request',
                          sender='noreply@signalnet.com',
                          recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
{reset_link}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            
            flash('A password reset link has been sent to your email.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email address not found.', 'danger')
    return render_template('forgot_password.html', form=form)

def generate_reset_token(user_id, expires_sec=1800):
    s = URLSafeTimedSerializer(app.secret_key)
    return s.dumps(user_id, salt='password-reset-salt')

def verify_reset_token(token, expires_sec=1800):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
    except:
        return None
    return User.query.get(user_id)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

def authenticate_user(username, password):
    """
    Authenticate a user by their username and password.
    
    :param username: The username provided by the user.
    :param password: The plaintext password provided by the user.
    :return: The User object if authentication is successful; otherwise, None.
    """
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user
    return None

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('profile'))

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects unauthorized users to the login page
login_manager.login_message_category = 'info'  # Category for flashed messages

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    form = AccountSettingsForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        # Update other fields as necessary
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account_settings'))
    return render_template('account_settings.html', form=form)

@app.route('/privacy_settings', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    form = PrivacySettingsForm(obj=current_user)
    if form.validate_on_submit():
        # Update Notification Preferences
        current_user.email_notifications = form.email_notifications.data
        current_user.sms_notifications = form.sms_notifications.data
        current_user.in_app_notifications = form.in_app_notifications.data
        
        # Update Privacy Settings
        current_user.allow_marketing_emails = form.allow_marketing_emails.data
        current_user.share_data_with_partners = form.share_data_with_partners.data
        current_user.allow_profile_visibility = form.allow_profile_visibility.data
        
        try:
            db.session.commit()
            flash('Your notification and privacy preferences have been updated.', 'success')
            return redirect(url_for('notifications'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('An error occurred while updating your preferences.', 'danger')
    return render_template('privacy_settings.html', form=form)

@app.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    form = PrivacySettingsForm()
    return render_template('notifications.html', notifications=notifications, form=form)

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.read = True
    try:
        db.session.commit()
        flash('Notification marked as read.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    return redirect(url_for('notifications'))

@app.route('/delete_notification/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(notification)
        db.session.commit()
        flash('Notification deleted.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    return redirect(url_for('notifications'))

@app.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
        db.session.commit()
        flash('All notifications marked as read.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    return redirect(url_for('notifications'))

@app.route('/delete_all_notifications', methods=['POST'])
@login_required
def delete_all_notifications():
    try:
        Notification.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All notifications deleted.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    return redirect(url_for('notifications'))

@app.route('/help_center')
def help_center():
    # Logic to display help and support resources
    return render_template('help_center.html')

# Ensure to create the corresponding templates and forms for each route.

@app.before_request
def check_session_expiration():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        last_activity = getattr(current_user, 'last_activity', None)
        if last_activity:
            if now > last_activity + app.permanent_session_lifetime:
                logout_user()
                flash('Session expired, please log in again.', 'warning')
                return redirect(url_for('login'))
        current_user.last_activity = now
        db.session.commit()

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Session expired or invalid request. Please try again.', 'danger')
    return redirect(url_for('login'))

@app.route('/test_flash')
def test_flash():
    flash('This is a test flash message.', 'info')
    return redirect(url_for('home'))

@app.route('/some_action')
@login_required
def some_action():
    # Perform some action
    # ...

    # Send a notification to the current user
    send_notification(current_user.id, "You have completed an action!")

    flash("Action completed and notification sent!", "success")
    return redirect(url_for('dashboard'))

@app.route('/admin/send_notification', methods=['GET', 'POST'])
@login_required
def admin_send_notification():
    form = AdminNotificationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            topic = form.topic.data
            message = form.message.data
            if not message or not topic:
                flash('Both topic and message cannot be empty', 'danger')
                return redirect(url_for('admin_send_notification'))

            # Assuming you want to send the notification to all users
            users = User.query.all()
            for user in users:
                full_message = f"{topic}: {message}"
                send_notification(user.id, current_user.id, full_message)

            flash('Notifications sent successfully', 'success')
            return redirect(url_for('admin_send_notification'))
    return render_template('admin_send_notification.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    # Logic for the dashboard
    return render_template('dashboard.html')

@app.route('/check_system_user')
def check_system_user():
    system_user = User.query.filter_by(username='System').first()
    if system_user:
        return f"System user exists with ID: {system_user.id}"
    else:
        return "System user does not exist"

@app.context_processor
def inject_unread_notifications_count():
    if current_user.is_authenticated:
        unread_notifications_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    else:
        unread_notifications_count = 0
    return dict(unread_notifications_count=unread_notifications_count)

# Define the custom filter
def nl2br(value):
    return Markup(value.replace("\n", "<br>"))

# Register the filter with Jinja2
app.jinja_env.filters['nl2br'] = nl2br

@app.route('/payment_success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        flash('No session ID provided.', 'danger')
        return redirect(url_for('subscribe'))
    
    try:
        # Retrieve the checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Extract the subscription plan ID from the session
        subscription_plan_id = checkout_session.metadata.get('subscription_plan_id')
        
        if not subscription_plan_id:
            flash('Subscription plan ID not found.', 'danger')
            return redirect(url_for('subscribe'))
        
        # Update the user's subscription in the database
        current_user.subscription_id = subscription_plan_id
        db.session.commit()
        
        flash('Your subscription was successful!', 'success')
        return redirect(url_for('success'))  # Redirect to a dashboard or relevant page
    except Exception as e:
        flash(f'Error retrieving Stripe session: {str(e)}', 'danger')
        return redirect(url_for('subscribe'))

@app.route('/payment_cancelled')
@login_required
def payment_cancelled():
    flash('Your payment was cancelled.', 'info')
    return redirect(url_for('subscribe'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    data = request.get_json()
    selected_plan = data.get('subscription')
    
    # Map subscription names to IDs
    subscription_map = {
        'Basic': 1,
        'Pro': 2,
        'Professional': 3
    }
    
    subscription_plan_id = subscription_map.get(selected_plan)
    
    if not subscription_plan_id:
        return jsonify({'error': 'Invalid subscription plan selected.'}), 400
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': os.getenv(f'{selected_plan.upper()}_PRICE_ID'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment_cancelled', _external=True),
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            metadata={'subscription_plan_id': subscription_plan_id}  # Include the plan ID in metadata
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

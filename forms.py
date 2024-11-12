from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, HiddenField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from flask_login import current_user
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=150, message='Username must be between 3 and 150 characters.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=150, message='Username must be between 3 and 150 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    country = SelectField('Country', choices=[], validators=[DataRequired()])
    tos = BooleanField('I accept the Terms of Service', validators=[
        DataRequired(message="You must accept the Terms of Service.")
    ])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('That email is already in use. Please choose a different one.')

class SubscribeForm(FlaskForm):
    subscription = HiddenField('Subscription Plan', validators=[
        DataRequired(message="Please select a subscription plan.")
    ])
    submit = SubmitField('Subscribe')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update Password')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=150, message='Username must be between 3 and 150 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField('New Password (leave blank to keep current password)', validators=[
        Optional(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('password', message="Passwords must match."),
        Optional()
    ])
    submit = SubmitField('Update Profile')

class AccountSettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password (leave blank to keep current password)', validators=[
        Optional(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('password', message="Passwords must match."),
        Optional()
    ])
    submit = SubmitField('Update Account')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')

class PrivacySettingsForm(FlaskForm):
    # Notification Preferences
    email_notifications = BooleanField('Email Notifications')
    sms_notifications = BooleanField('SMS Notifications')
    in_app_notifications = BooleanField('In-App Notifications')
    
    # Privacy Settings
    allow_marketing_emails = BooleanField('Allow Marketing Emails')
    share_data_with_partners = BooleanField('Share Data with Partners')
    allow_profile_visibility = BooleanField('Allow Profile Visibility')
    
    submit = SubmitField('Save Preferences')

    def validate_email_notifications(self, field):
        pass

    def validate_sms_notifications(self, field):
        pass

    def validate_in_app_notifications(self, field):
        pass

    def validate_allow_marketing_emails(self, field):
        pass

    def validate_share_data_with_partners(self, field):
        pass

    def validate_allow_profile_visibility(self, field):
        pass

class AdminNotificationForm(FlaskForm):
    topic = StringField('Notification Topic', validators=[DataRequired(), Length(max=100)])
    message = TextAreaField('Notification Message', validators=[DataRequired()])
    submit = SubmitField('Send Notification')
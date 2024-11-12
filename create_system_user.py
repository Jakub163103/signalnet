from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_system_user():
    with app.app_context():
        # Check if the "System" user already exists
        system_user = User.query.filter_by(username='System').first()
        if not system_user:
            # Create the "System" user
            system_user = User(
                username='System',
                email='system@signalnet.com',
                password=generate_password_hash('securepassword', method='pbkdf2:sha256'),  # Use a secure password
                country='US'  # Provide a default country code, e.g., 'US' for the United States
            )
            db.session.add(system_user)
            try:
                db.session.commit()
                print("System user created successfully.")
            except Exception as e:
                db.session.rollback()
                print(f"Failed to create System user: {e}")
        else:
            print("System user already exists.")

if __name__ == '__main__':
    create_system_user() 
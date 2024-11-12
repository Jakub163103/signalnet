from app import app, db
from models import Subscription
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Define the subscription plans with features and stripe_price_id
plans = [
    {"name": "Basic", "price": 9.99, "stripe_price_id": os.getenv("BASIC_PRICE_ID"), "features": ["Up to 5 signals per day","Community forum access", "Basic trend analysis model"]},
    {"name": "Pro", "price": 19.99, "stripe_price_id": os.getenv("PRO_PRICE_ID"), "features": ["Up to 20 signals per day","Priority email support", "Intermediate pattern recognition model"]},
    {"name": "Professional", "price": 49.99, "stripe_price_id": os.getenv("PROFESSIONAL_PRICE_ID"), "features": ["Unlimited signals","24/7 dedicated support", "Machine learning-based predictive model"]}
]

# Use the application context to perform database operations
with app.app_context():
    try:
        # Add each plan to the database
        for plan in plans:
            subscription = Subscription(
                name=plan["name"],
                price=plan["price"],
                stripe_price_id=plan["stripe_price_id"],
                features=','.join(plan["features"])
            )
            db.session.add(subscription)

        # Commit the changes to the database
        db.session.commit()
        print("Subscription plans added successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

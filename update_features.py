from app import app, db, Subscription

# Define the features for each subscription plan
features_data = {
    "Basic": ["5 Signals/Day", "Community forum access", "Basic trend analysis model"],
    "Pro": ["20 Signals/Day", "Priority email support", "Intermediate pattern recognition model"],
    "Professional": ["Unlimited Signals", "24/7 dedicated support", "Machine learning-based predictive model"]
}

# Use the application context to perform database operations
with app.app_context():
    for plan_name, features in features_data.items():
        # Find the subscription by name
        subscription = Subscription.query.filter_by(name=plan_name).first()
        if subscription:
            # Update the features column
            subscription.features = ','.join(features)
            db.session.commit()
            print(f"Updated features for {plan_name} plan.")
        else:
            print(f"Subscription plan {plan_name} not found.") 
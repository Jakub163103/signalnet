from models import db, Notification

def send_notification(recipient_id, sender_id, message):
    print(f"Attempting to send notification from {sender_id} to {recipient_id}.")  # Debugging
    notification = Notification(user_id=recipient_id, sender_id=sender_id, message=message)
    db.session.add(notification)
    try:
        db.session.commit()
        print(f"Notification sent from user {sender_id} to user {recipient_id}: {message}")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to send notification: {e}") 
"""Populate the database with 10 dummy events for testing.

This script finds the first user in the `users` table and creates 10 events
hosted by that user. Run it from the project root with the active Python
environment where dependencies from `requirements.txt` are installed.

Example:
    python scripts/create_dummy_events.py
"""
from datetime import date, time, timedelta
import random
from app.database import SessionLocal, engine
from app.models.event import Event
from app.models.user import User
from sqlalchemy.orm import Session

# Create DB tables if they don't exist (safe no-op if already created)
try:
    from app.database import Base
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

CATEGORY_CHOICES = ["music", "sports", "tech", "food", "art"]

def make_time(hour: int = 18, minute: int = 0):
    return time(hour, minute)


def create_dummy_events():
    db: Session = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users found in the database. Create a user first.")
            return

        base_date = date.today()
        for i in range(10):
            evt = Event(
                event_photo=None,
                event_title=f"Test Event {i+1}",
                event_description=f"This is a dummy event number {i+1} for testing.",
                event_location="Test Location",
                pincode="000000",
                whatsapp_group_link=None,
                date=base_date + timedelta(days=i),
                time=make_time(18 + (i % 4)),
                max_attendees=random.randint(5, 50),
                category=random.choice(CATEGORY_CHOICES),
                host_id=user.id,
            )
            db.add(evt)
        db.commit()
        print("Inserted 10 dummy events for user:", user.username)
    finally:
        db.close()


if __name__ == "__main__":
    create_dummy_events()

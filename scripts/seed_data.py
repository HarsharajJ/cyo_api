"""Comprehensive seed data script to populate the database with realistic test data.

This script creates:
- 5 users with complete profile information
- 10 events with varied categories and details
- Random host assignments (any of the 5 users can host events)
- Random event participation (users join events randomly, not all users join all events)

All photo URLs use Unsplash for high-quality placeholder images.

Example:
    python scripts/seed_data.py
"""
from datetime import date, time, timedelta, datetime, timezone
import random
from app.database import SessionLocal, engine
from app.models.event import Event
from app.models.user import User
from app.models.event_participant import event_participants
from app.auth.utils import get_password_hash
from sqlalchemy.orm import Session

# Create DB tables if they don't exist (safe no-op if already created)
try:
    from app.database import Base
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

# Event categories
CATEGORY_CHOICES = ["music", "sports", "tech", "food", "art"]

# Sample data for users
USER_DATA = [
    {
        "email": "john.doe@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "pincode": "560001",
        "mobile_number": "+919876543210",
        "bio": "Tech enthusiast and coffee lover. Love to explore new places and meet new people!",
        "interests": ["technology", "music", "travel", "photography"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/johndoe",
        "twitter_url": "https://twitter.com/johndoe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
    },
    {
        "email": "sarah.smith@example.com",
        "username": "sarahsmith",
        "full_name": "Sarah Smith",
        "pincode": "400001",
        "mobile_number": "+919876543211",
        "bio": "Foodie and fitness freak. Always up for outdoor adventures and trying new cuisines.",
        "interests": ["food", "fitness", "yoga", "hiking"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/sarahsmith",
        "linkedin_url": "https://linkedin.com/in/sarahsmith",
    },
    {
        "email": "mike.wilson@example.com",
        "username": "mikewilson",
        "full_name": "Mike Wilson",
        "pincode": "110001",
        "mobile_number": "+919876543212",
        "bio": "Sports fanatic and music lover. Organizing events is my passion!",
        "interests": ["sports", "music", "events", "networking"],
        "relationship_status": "in relationship",
        "twitter_url": "https://twitter.com/mikewilson",
        "portfolio_url": "https://mikewilson.dev",
    },
    {
        "email": "emily.brown@example.com",
        "username": "emilybrown",
        "full_name": "Emily Brown",
        "pincode": "600001",
        "mobile_number": "+919876543213",
        "bio": "Artist and creative soul. Love painting, music, and connecting with fellow artists.",
        "interests": ["art", "music", "painting", "design"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/emilybrown",
        "portfolio_url": "https://emilybrownart.com",
    },
    {
        "email": "alex.taylor@example.com",
        "username": "alextaylor",
        "full_name": "Alex Taylor",
        "pincode": "700001",
        "mobile_number": "+919876543214",
        "bio": "Developer by day, DJ by night. Love tech meetups and electronic music festivals.",
        "interests": ["technology", "music", "djing", "coding"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/alextaylor",
        "twitter_url": "https://twitter.com/alextaylor",
        "linkedin_url": "https://linkedin.com/in/alextaylor",
    },
]

# Sample data for events
EVENT_DATA = [
    {
        "event_photo": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=800",
        "event_title": "Summer Music Festival 2025",
        "event_description": "Join us for an amazing evening of live music featuring local bands and artists. Enjoy food stalls, games, and great vibes!",
        "event_location": "Central Park, Bangalore",
        "pincode": "560001",
        "category": "music",
        "max_attendees": 100,
        "days_offset": 5,
        "hour": 18,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
        "event_title": "Marathon for Health",
        "event_description": "5K charity marathon to raise awareness about health and fitness. All fitness levels welcome!",
        "event_location": "Marine Drive, Mumbai",
        "pincode": "400001",
        "category": "sports",
        "max_attendees": 200,
        "days_offset": 10,
        "hour": 6,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
        "event_title": "Tech Innovators Meetup",
        "event_description": "Network with fellow tech enthusiasts, learn about AI/ML trends, and share your projects. Pizza and drinks included!",
        "event_location": "Tech Hub, Delhi",
        "pincode": "110001",
        "category": "tech",
        "max_attendees": 50,
        "days_offset": 7,
        "hour": 19,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
        "event_title": "Food Tasting Extravaganza",
        "event_description": "Experience cuisines from around the world! Top chefs will showcase their signature dishes. Vegetarian and vegan options available.",
        "event_location": "Hotel Grand Plaza, Chennai",
        "pincode": "600001",
        "category": "food",
        "max_attendees": 80,
        "days_offset": 12,
        "hour": 20,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800",
        "event_title": "Art Exhibition & Workshop",
        "event_description": "Explore contemporary art and participate in hands-on painting workshops. All materials provided!",
        "event_location": "City Art Gallery, Kolkata",
        "pincode": "700001",
        "category": "art",
        "max_attendees": 40,
        "days_offset": 15,
        "hour": 16,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
        "event_title": "Jazz Night Under the Stars",
        "event_description": "Romantic evening of smooth jazz music. Bring your partner or come solo and enjoy the vibe!",
        "event_location": "Rooftop Lounge, Bangalore",
        "pincode": "560001",
        "category": "music",
        "max_attendees": 60,
        "days_offset": 20,
        "hour": 21,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=800",
        "event_title": "Basketball Tournament",
        "event_description": "3v3 street basketball tournament. Form your team or join as a free agent. Prizes for winners!",
        "event_location": "Sports Complex, Mumbai",
        "pincode": "400001",
        "category": "sports",
        "max_attendees": 30,
        "days_offset": 14,
        "hour": 17,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=800",
        "event_title": "Startup Pitch Night",
        "event_description": "Watch innovative startups pitch their ideas to investors. Great networking opportunity for entrepreneurs!",
        "event_location": "Innovation Center, Delhi",
        "pincode": "110001",
        "category": "tech",
        "max_attendees": 100,
        "days_offset": 18,
        "hour": 18,
        "minute": 30,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1529417305485-480f579e1e2c?w=800",
        "event_title": "Cooking Masterclass",
        "event_description": "Learn to cook authentic Italian dishes from a professional chef. Limited seats, book now!",
        "event_location": "Culinary Institute, Chennai",
        "pincode": "600001",
        "category": "food",
        "max_attendees": 20,
        "days_offset": 22,
        "hour": 15,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?w=800",
        "event_title": "Photography Walk",
        "event_description": "Explore the city through your lens! Perfect for beginners and pros. Tips and tricks from professional photographers.",
        "event_location": "Heritage District, Kolkata",
        "pincode": "700001",
        "category": "art",
        "max_attendees": 25,
        "days_offset": 8,
        "hour": 10,
        "minute": 0,
    },
]


def create_users(db: Session):
    """Create 5 users with complete profile information."""
    users = []
    default_password = "password123"  # Default password for all test users
    hashed_password = get_password_hash(default_password)
    
    print("Creating users...")
    for user_data in USER_DATA:
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            full_name=user_data["full_name"],
            pincode=user_data["pincode"],
            mobile_number=user_data["mobile_number"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            profile_picture_url=None,  # No profile pictures as requested
            bio=user_data["bio"],
            instagram_url=user_data.get("instagram_url"),
            twitter_url=user_data.get("twitter_url"),
            linkedin_url=user_data.get("linkedin_url"),
            portfolio_url=user_data.get("portfolio_url"),
            interests=user_data["interests"],
            subscribed=random.choice([True, False]),
            relationship_status=user_data["relationship_status"],
            profile_visibility="public",
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    # Refresh to get IDs
    for user in users:
        db.refresh(user)
    
    print(f"✓ Created {len(users)} users")
    return users


def create_events(db: Session, users: list[User]):
    """Create 10 events with random hosts from the 5 users."""
    events = []
    base_date = date.today()
    
    print("Creating events...")
    for event_data in EVENT_DATA:
        # Randomly select a host from the 5 users
        host = random.choice(users)
        
        event = Event(
            event_photo=event_data["event_photo"],
            event_title=event_data["event_title"],
            event_description=event_data["event_description"],
            event_location=event_data["event_location"],
            pincode=event_data["pincode"],
            whatsapp_group_link=None,  # No WhatsApp links for test data
            date=base_date + timedelta(days=event_data["days_offset"]),
            time=time(event_data["hour"], event_data["minute"]),
            max_attendees=event_data["max_attendees"],
            category=event_data["category"],
            host_id=host.id,
        )
        db.add(event)
        events.append(event)
    
    db.commit()
    # Refresh to get IDs
    for event in events:
        db.refresh(event)
    
    print(f"✓ Created {len(events)} events")
    return events


def create_event_participants(db: Session, users: list[User], events: list[Event]):
    """Make users join events randomly (not all users join all events)."""
    print("Creating event participations...")
    participations = 0
    
    for event in events:
        # Random number of users will join each event (between 1 and 4 users)
        num_participants = random.randint(1, 4)
        
        # Randomly select users to join this event
        participants = random.sample(users, num_participants)
        
        for participant in participants:
            # Don't add host as participant (they're already the host)
            if participant.id == event.host_id:
                continue
            
            # Insert into association table
            stmt = event_participants.insert().values(
                event_id=event.id,
                user_id=participant.id,
                joined_at=datetime.now(timezone.utc)
            )
            db.execute(stmt)
            participations += 1
    
    db.commit()
    print(f"✓ Created {participations} event participations")


def seed_database():
    """Main function to seed the entire database."""
    db: Session = SessionLocal()
    try:
        print("\n" + "="*60)
        print("SEED DATA SCRIPT - Populating Database")
        print("="*60 + "\n")
        
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"⚠ Warning: Database already contains {existing_users} users")
            response = input("Do you want to continue and add more data? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return
        
        # Create all data
        users = create_users(db)
        events = create_events(db, users)
        create_event_participants(db, users, events)
        
        print("\n" + "="*60)
        print("SEED DATA COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  • {len(users)} users created")
        print(f"  • {len(events)} events created")
        print(f"  • Random host assignments")
        print(f"  • Random event participations")
        print(f"\nDefault password for all users: 'password123'")
        print(f"\nUsers created:")
        for user in users:
            print(f"  - {user.username} ({user.email})")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

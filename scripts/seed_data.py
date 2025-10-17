"""Comprehensive seed data script to populate the database with realistic test data.

This script creates:
- 20 users with complete profile information
- 40 events with varied categories and details
- Random host assignments (any of the 20 users can host events)
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
CATEGORY_CHOICES = [
    "Sports & Fitness",
    "Outdoor Adventures",
    "Hobbies & Interests",
    "Food & Drink",
    "Arts & Culture",
    "Gaming",
    "Social & Community",
    "Learning & Workshops",
    "Networking & Professional"
]

# Pincodes near the town
LOCAL_PINCODES = ["574105", "576103", "576108", "574118", "576104", "576101", "576105", "576102", "576106"]

# Sample data for users
USER_DATA = [
    {
        "email": "john.doe@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "pincode": random.choice(LOCAL_PINCODES),
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
        "pincode": random.choice(LOCAL_PINCODES),
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
        "pincode": random.choice(LOCAL_PINCODES),
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
        "pincode": random.choice(LOCAL_PINCODES),
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
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543214",
        "bio": "Developer by day, DJ by night. Love tech meetups and electronic music festivals.",
        "interests": ["technology", "music", "djing", "coding"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/alextaylor",
        "twitter_url": "https://twitter.com/alextaylor",
        "linkedin_url": "https://linkedin.com/in/alextaylor",
    },
    {
        "email": "rachel.green@example.com",
        "username": "rachelgreen",
        "full_name": "Rachel Green",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543215",
        "bio": "Yoga instructor and wellness enthusiast. Spreading positivity through mindfulness.",
        "interests": ["yoga", "wellness", "meditation", "fitness"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/rachelgreen",
        "linkedin_url": "https://linkedin.com/in/rachelgreen",
    },
    {
        "email": "david.kumar@example.com",
        "username": "davidkumar",
        "full_name": "David Kumar",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543216",
        "bio": "Adventure junkie! Trekking, camping, and exploring the great outdoors.",
        "interests": ["trekking", "camping", "adventure", "photography"],
        "relationship_status": "single",
        "twitter_url": "https://twitter.com/davidkumar",
        "portfolio_url": "https://davidkumar.com",
    },
    {
        "email": "priya.sharma@example.com",
        "username": "priyasharma",
        "full_name": "Priya Sharma",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543217",
        "bio": "Book lover and aspiring writer. Coffee, books, and deep conversations.",
        "interests": ["reading", "writing", "literature", "coffee"],
        "relationship_status": "in relationship",
        "instagram_url": "https://instagram.com/priyasharma",
        "twitter_url": "https://twitter.com/priyasharma",
    },
    {
        "email": "kevin.lee@example.com",
        "username": "kevinlee",
        "full_name": "Kevin Lee",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543218",
        "bio": "Gaming enthusiast and streamer. Let's play together!",
        "interests": ["gaming", "streaming", "esports", "technology"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/kevinlee",
        "twitter_url": "https://twitter.com/kevinlee",
    },
    {
        "email": "nina.patel@example.com",
        "username": "ninapatel",
        "full_name": "Nina Patel",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543219",
        "bio": "Social worker passionate about community service and making a difference.",
        "interests": ["volunteering", "community", "social work", "education"],
        "relationship_status": "single",
        "linkedin_url": "https://linkedin.com/in/ninapatel",
    },
    {
        "email": "ryan.dsouza@example.com",
        "username": "ryandsouza",
        "full_name": "Ryan D'Souza",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543220",
        "bio": "Professional chef experimenting with fusion cuisine. Food is art!",
        "interests": ["cooking", "food", "restaurants", "travel"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/ryandsouza",
        "portfolio_url": "https://ryandsouza.chef",
    },
    {
        "email": "lisa.chen@example.com",
        "username": "lisachen",
        "full_name": "Lisa Chen",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543221",
        "bio": "Digital marketer and content creator. Let's create something amazing!",
        "interests": ["marketing", "content creation", "social media", "photography"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/lisachen",
        "linkedin_url": "https://linkedin.com/in/lisachen",
    },
    {
        "email": "arjun.reddy@example.com",
        "username": "arjunreddy",
        "full_name": "Arjun Reddy",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543222",
        "bio": "Entrepreneur and startup mentor. Building the future one idea at a time.",
        "interests": ["startups", "business", "mentoring", "innovation"],
        "relationship_status": "in relationship",
        "linkedin_url": "https://linkedin.com/in/arjunreddy",
        "twitter_url": "https://twitter.com/arjunreddy",
    },
    {
        "email": "maya.gupta@example.com",
        "username": "mayagupta",
        "full_name": "Maya Gupta",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543223",
        "bio": "Dancer and choreographer. Life is better when you dance!",
        "interests": ["dance", "choreography", "music", "performing arts"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/mayagupta",
        "portfolio_url": "https://mayagupta.dance",
    },
    {
        "email": "tom.anderson@example.com",
        "username": "tomanderson",
        "full_name": "Tom Anderson",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543224",
        "bio": "Fitness coach helping people achieve their health goals.",
        "interests": ["fitness", "coaching", "nutrition", "sports"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/tomanderson",
        "linkedin_url": "https://linkedin.com/in/tomanderson",
    },
    {
        "email": "sophia.martinez@example.com",
        "username": "sophiamartinez",
        "full_name": "Sophia Martinez",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543225",
        "bio": "Graphic designer with a passion for creating beautiful visual experiences.",
        "interests": ["design", "art", "illustration", "creativity"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/sophiamartinez",
        "portfolio_url": "https://sophiamartinez.design",
    },
    {
        "email": "raj.malhotra@example.com",
        "username": "rajmalhotra",
        "full_name": "Raj Malhotra",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543226",
        "bio": "Film buff and aspiring filmmaker. Cinema is my passion!",
        "interests": ["films", "cinematography", "directing", "writing"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/rajmalhotra",
        "twitter_url": "https://twitter.com/rajmalhotra",
    },
    {
        "email": "olivia.brown@example.com",
        "username": "oliviabrown",
        "full_name": "Olivia Brown",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543227",
        "bio": "Environmental activist working towards a sustainable future.",
        "interests": ["environment", "sustainability", "activism", "nature"],
        "relationship_status": "in relationship",
        "instagram_url": "https://instagram.com/oliviabrown",
        "linkedin_url": "https://linkedin.com/in/oliviabrown",
    },
    {
        "email": "vikram.singh@example.com",
        "username": "vikramsingh",
        "full_name": "Vikram Singh",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543228",
        "bio": "Musician and music producer. Creating beats that move souls.",
        "interests": ["music", "production", "djing", "concerts"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/vikramsingh",
        "twitter_url": "https://twitter.com/vikramsingh",
    },
    {
        "email": "emma.wilson@example.com",
        "username": "emmawilson",
        "full_name": "Emma Wilson",
        "pincode": random.choice(LOCAL_PINCODES),
        "mobile_number": "+919876543229",
        "bio": "Travel blogger exploring hidden gems around the world.",
        "interests": ["travel", "blogging", "photography", "culture"],
        "relationship_status": "single",
        "instagram_url": "https://instagram.com/emmawilson",
        "portfolio_url": "https://emmawilson.travel",
    },
]

# Sample data for events
EVENT_DATA = [
    # Sports & Fitness (6 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
        "event_title": "Marathon for Health",
        "event_description": "5K charity marathon to raise awareness about health and fitness. All fitness levels welcome!",
        "event_location": "Marine Drive, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 200,
        "days_offset": 3,
        "hour": 6,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=800",
        "event_title": "Basketball Tournament",
        "event_description": "3v3 street basketball tournament. Form your team or join as a free agent. Prizes for winners!",
        "event_location": "Sports Complex, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 30,
        "days_offset": 7,
        "hour": 17,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800",
        "event_title": "Yoga & Meditation Session",
        "event_description": "Start your day with rejuvenating yoga and meditation. Suitable for all levels.",
        "event_location": "Botanical Garden, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 50,
        "days_offset": 2,
        "hour": 7,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800",
        "event_title": "Cycling Club Ride",
        "event_description": "Join our weekly cycling group for a scenic 20km ride. All bike types welcome!",
        "event_location": "Lake Park, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 40,
        "days_offset": 5,
        "hour": 6,
        "minute": 30,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1549060279-7e168fcee0c2?w=800",
        "event_title": "CrossFit Challenge",
        "event_description": "Test your strength and endurance in this exciting CrossFit competition. All levels welcome!",
        "event_location": "FitBox Gym, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 35,
        "days_offset": 12,
        "hour": 18,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800",
        "event_title": "Badminton Championship",
        "event_description": "Singles and doubles badminton tournament. Register as a team or individual player!",
        "event_location": "Indoor Stadium, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Sports & Fitness",
        "max_attendees": 60,
        "days_offset": 18,
        "hour": 16,
        "minute": 0,
    },
    
    # Outdoor Adventures (5 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=800",
        "event_title": "Weekend Trek to Nandi Hills",
        "event_description": "Experience breathtaking sunrise views and enjoy nature. Moderate difficulty level.",
        "event_location": "Nandi Hills Base, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Outdoor Adventures",
        "max_attendees": 45,
        "days_offset": 4,
        "hour": 5,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?w=800",
        "event_title": "Camping Under the Stars",
        "event_description": "Overnight camping experience with bonfire, music, and stargazing. Tents provided!",
        "event_location": "Pawna Lake, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Outdoor Adventures",
        "max_attendees": 50,
        "days_offset": 9,
        "hour": 15,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
        "event_title": "Mountain Hiking Expedition",
        "event_description": "Full day hiking adventure through scenic mountain trails. Experienced guides included.",
        "event_location": "Himalayan Foothills, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Outdoor Adventures",
        "max_attendees": 30,
        "days_offset": 15,
        "hour": 6,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800",
        "event_title": "Beach Kayaking Adventure",
        "event_description": "Explore the coastline by kayak! Equipment and safety gear provided. No experience needed.",
        "event_location": "Marina Beach, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Outdoor Adventures",
        "max_attendees": 25,
        "days_offset": 20,
        "hour": 8,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1501555088652-021faa106b9b?w=800",
        "event_title": "Rock Climbing Workshop",
        "event_description": "Learn rock climbing basics from certified instructors. All equipment included!",
        "event_location": "Adventure Park, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Outdoor Adventures",
        "max_attendees": 20,
        "days_offset": 25,
        "hour": 9,
        "minute": 0,
    },
    
    # Hobbies & Interests (5 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?w=800",
        "event_title": "Photography Walk",
        "event_description": "Explore the city through your lens! Perfect for beginners and pros. Tips and tricks from professional photographers.",
        "event_location": "Heritage District, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Hobbies & Interests",
        "max_attendees": 25,
        "days_offset": 6,
        "hour": 10,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
        "event_title": "Book Club Meetup",
        "event_description": "Discussion of this month's book selection. Coffee and snacks included!",
        "event_location": "Cafe Literati, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Hobbies & Interests",
        "max_attendees": 20,
        "days_offset": 8,
        "hour": 18,
        "minute": 30,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800",
        "event_title": "Painting Workshop",
        "event_description": "Learn watercolor painting techniques. All art supplies provided. Perfect for beginners!",
        "event_location": "Art Studio, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Hobbies & Interests",
        "max_attendees": 15,
        "days_offset": 11,
        "hour": 16,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800",
        "event_title": "Gardening Workshop",
        "event_description": "Learn urban gardening techniques and plant care. Take home your own potted plant!",
        "event_location": "Community Garden, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Hobbies & Interests",
        "max_attendees": 30,
        "days_offset": 14,
        "hour": 10,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1514866726862-0f081731e63f?w=800",
        "event_title": "Knitting Circle",
        "event_description": "Join our cozy knitting group. Beginners welcome! Bring your own supplies or borrow ours.",
        "event_location": "Craft Cafe, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Hobbies & Interests",
        "max_attendees": 15,
        "days_offset": 22,
        "hour": 15,
        "minute": 0,
    },
    
    # Food & Drink (6 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
        "event_title": "Food Tasting Extravaganza",
        "event_description": "Experience cuisines from around the world! Top chefs will showcase their signature dishes. Vegetarian and vegan options available.",
        "event_location": "Hotel Grand Plaza, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 80,
        "days_offset": 10,
        "hour": 20,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1529417305485-480f579e1e2c?w=800",
        "event_title": "Italian Cooking Masterclass",
        "event_description": "Learn to cook authentic Italian dishes from a professional chef. Limited seats, book now!",
        "event_location": "Culinary Institute, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 20,
        "days_offset": 16,
        "hour": 15,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=800",
        "event_title": "Wine Tasting Evening",
        "event_description": "Sample fine wines from around the world. Learn about wine pairing from a sommelier.",
        "event_location": "Wine Bar, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 40,
        "days_offset": 13,
        "hour": 19,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=800",
        "event_title": "Street Food Tour",
        "event_description": "Explore the best street food spots in the city. A culinary adventure awaits!",
        "event_location": "Old Delhi Market, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 25,
        "days_offset": 5,
        "hour": 17,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800",
        "event_title": "Baking Workshop",
        "event_description": "Learn to bake artisan bread and pastries. Take home your delicious creations!",
        "event_location": "Bakery School, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 18,
        "days_offset": 19,
        "hour": 14,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800",
        "event_title": "Coffee Brewing Workshop",
        "event_description": "Master the art of brewing perfect coffee. Learn about different beans and techniques.",
        "event_location": "Third Wave Coffee, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Food & Drink",
        "max_attendees": 15,
        "days_offset": 24,
        "hour": 11,
        "minute": 0,
    },
    
    # Arts & Culture (5 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800",
        "event_title": "Contemporary Art Exhibition",
        "event_description": "Explore contemporary art and participate in hands-on painting workshops. All materials provided!",
        "event_location": "City Art Gallery, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Arts & Culture",
        "max_attendees": 40,
        "days_offset": 7,
        "hour": 16,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1503095396549-807759245b35?w=800",
        "event_title": "Classical Dance Performance",
        "event_description": "Experience the beauty of traditional Indian classical dance. Followed by a Q&A with performers.",
        "event_location": "Cultural Center, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Arts & Culture",
        "max_attendees": 100,
        "days_offset": 17,
        "hour": 18,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800",
        "event_title": "Theater Play: Modern Tales",
        "event_description": "Contemporary theater production exploring modern relationships. Award-winning cast!",
        "event_location": "City Theater, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Arts & Culture",
        "max_attendees": 150,
        "days_offset": 21,
        "hour": 19,
        "minute": 30,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800",
        "event_title": "Poetry Open Mic Night",
        "event_description": "Share your poetry or enjoy performances from local poets. All welcome!",
        "event_location": "Cafe Poet's Corner, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Arts & Culture",
        "max_attendees": 35,
        "days_offset": 11,
        "hour": 20,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8?w=800",
        "event_title": "Heritage Walk",
        "event_description": "Discover the rich history and architecture of our city with expert guides.",
        "event_location": "Old Quarter, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Arts & Culture",
        "max_attendees": 30,
        "days_offset": 26,
        "hour": 9,
        "minute": 0,
    },
    
    # Gaming (4 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800",
        "event_title": "E-Sports Tournament",
        "event_description": "Competitive gaming tournament featuring popular titles. Big prizes for winners!",
        "event_location": "Gaming Arena, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Gaming",
        "max_attendees": 100,
        "days_offset": 8,
        "hour": 14,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800",
        "event_title": "Board Game Night",
        "event_description": "Enjoy classic and modern board games with fellow enthusiasts. Snacks provided!",
        "event_location": "Game Cafe, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Gaming",
        "max_attendees": 40,
        "days_offset": 4,
        "hour": 18,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1556438064-2d7646166914?w=800",
        "event_title": "VR Gaming Experience",
        "event_description": "Try the latest virtual reality games and experiences. All equipment provided!",
        "event_location": "VR Zone, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Gaming",
        "max_attendees": 25,
        "days_offset": 12,
        "hour": 16,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800",
        "event_title": "Chess Championship",
        "event_description": "Test your strategic skills in this classical chess tournament. All levels welcome!",
        "event_location": "Chess Club, Kolkata",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Gaming",
        "max_attendees": 32,
        "days_offset": 23,
        "hour": 15,
        "minute": 0,
    },
    
    # Social & Community (4 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800",
        "event_title": "Community Cleanup Drive",
        "event_description": "Join us in making our neighborhood cleaner and greener. Gloves and bags provided!",
        "event_location": "City Park, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Social & Community",
        "max_attendees": 80,
        "days_offset": 3,
        "hour": 8,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800",
        "event_title": "Speed Networking Event",
        "event_description": "Meet new people and expand your social circle. Fun icebreaker activities included!",
        "event_location": "Social Hub, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Social & Community",
        "max_attendees": 60,
        "days_offset": 9,
        "hour": 19,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800",
        "event_title": "Charity Fundraiser Gala",
        "event_description": "Support local charities while enjoying dinner, music, and auctions.",
        "event_location": "Grand Hotel, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Social & Community",
        "max_attendees": 120,
        "days_offset": 28,
        "hour": 19,
        "minute": 30,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800",
        "event_title": "Singles Mixer Party",
        "event_description": "Meet new people in a fun and relaxed atmosphere. Games, music, and refreshments!",
        "event_location": "Lounge Bar, Chennai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Social & Community",
        "max_attendees": 70,
        "days_offset": 15,
        "hour": 20,
        "minute": 0,
    },
    
    # Learning & Workshops (3 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800",
        "event_title": "Python Programming Workshop",
        "event_description": "Learn Python basics for beginners. Laptops required, bring your own!",
        "event_location": "Tech Academy, Bangalore",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Learning & Workshops",
        "max_attendees": 30,
        "days_offset": 6,
        "hour": 14,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800",
        "event_title": "Public Speaking Masterclass",
        "event_description": "Overcome your fear and become a confident speaker. Practical exercises included!",
        "event_location": "Training Center, Mumbai",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Learning & Workshops",
        "max_attendees": 25,
        "days_offset": 13,
        "hour": 18,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=800",
        "event_title": "Financial Planning Workshop",
        "event_description": "Learn investment basics and financial planning strategies from experts.",
        "event_location": "Business Center, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Learning & Workshops",
        "max_attendees": 40,
        "days_offset": 20,
        "hour": 17,
        "minute": 0,
    },
    
    # Networking & Professional (2 events)
    {
        "event_photo": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
        "event_title": "Tech Innovators Meetup",
        "event_description": "Network with fellow tech enthusiasts, learn about AI/ML trends, and share your projects. Pizza and drinks included!",
        "event_location": "Tech Hub, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Networking & Professional",
        "max_attendees": 50,
        "days_offset": 10,
        "hour": 19,
        "minute": 0,
    },
    {
        "event_photo": "https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=800",
        "event_title": "Startup Pitch Night",
        "event_description": "Watch innovative startups pitch their ideas to investors. Great networking opportunity for entrepreneurs!",
        "event_location": "Innovation Center, Delhi",
        "pincode": random.choice(LOCAL_PINCODES),
        "category": "Networking & Professional",
        "max_attendees": 100,
        "days_offset": 27,
        "hour": 18,
        "minute": 30,
    },
]


def create_users(db: Session):
    """Create 20 users with complete profile information."""
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
    """Create 40 events with random hosts from the 20 users."""
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

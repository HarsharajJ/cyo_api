from sqlalchemy import Integer, ForeignKey, DateTime, Column, Table
from datetime import datetime, timezone
from app.database import Base

# Association table for many-to-many relationship between events and participants
event_participants = Table(
    'event_participants',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.now(timezone.utc))
)
from sqlalchemy import String, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from .event import Event
    from .memory import Memory

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    pincode: Mapped[str] = mapped_column(String)
    mobile_number: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    # Profile fields
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interests: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    relationship_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile_visibility: Mapped[str] = mapped_column(String, default="public")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="host")
    joined_events: Mapped[list["Event"]] = relationship("Event", secondary="event_participants", back_populates="participants")
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="user")
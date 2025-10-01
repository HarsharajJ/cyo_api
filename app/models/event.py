from sqlalchemy import String, Integer, Text, ForeignKey, Date, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date as DateType, time as TimeType
from typing import Optional
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_photo: Mapped[str] = mapped_column(String)
    event_title: Mapped[str] = mapped_column(String)
    event_description: Mapped[str] = mapped_column(Text)
    event_location: Mapped[str] = mapped_column(String)
    pincode: Mapped[str] = mapped_column(String)
    whatsapp_group_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date: Mapped[DateType] = mapped_column(Date)
    time: Mapped[TimeType] = mapped_column(Time)
    max_attendees: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    host = relationship("User", back_populates="events")
    participants = relationship("User", secondary="event_participants", back_populates="joined_events")
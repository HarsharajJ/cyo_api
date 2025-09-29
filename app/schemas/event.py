from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class EventCreate(BaseModel):
    event_title: str
    event_description: str
    event_location: str
    pincode: str
    whatsapp_group_link: Optional[str] = None
    date: date
    time: time
    max_attendees: int
    category: str

class EventResponse(BaseModel):
    id: int
    event_photo: str
    event_title: str
    event_description: str
    event_location: str
    pincode: str
    whatsapp_group_link: Optional[str] = None
    date: date
    time: time
    max_attendees: int
    category: str
    host_id: int
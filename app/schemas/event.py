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
    event_photo: Optional[str] = None
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

class HostInfo(BaseModel):
    profile_picture_url: Optional[str] = None
    full_name: str
    username: str

class EventDetailResponse(BaseModel):
    event_photo: Optional[str] = None
    event_title: str
    event_description: str
    event_location: str
    pincode: str
    whatsapp_group_link: Optional[str] = None
    date: date
    time: time
    max_attendees: int
    category: str
    host: HostInfo

class JoinEventRequest(BaseModel):
    event_id: int

class JoinEventResponse(BaseModel):
    message: str
    event_id: int
    user_id: int
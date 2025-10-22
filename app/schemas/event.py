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
    participants_count: int = 0
    # Allow construction from ORM objects (SQLAlchemy models)
    model_config = {"from_attributes": True}

class HostInfo(BaseModel):
    profile_picture_url: Optional[str] = None
    full_name: str
    username: str
    model_config = {"from_attributes": True}


class ParticipantInfo(BaseModel):
    id: int
    profile_picture_url: Optional[str] = None
    full_name: str
    username: str
    model_config = {"from_attributes": True}

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
    participants: Optional[list[ParticipantInfo]] = None
    participants_count: Optional[int] = None
    model_config = {"from_attributes": True}

class JoinEventRequest(BaseModel):
    event_id: int

class JoinEventResponse(BaseModel):
    message: str
    event_id: int
    user_id: int

class LeaveEventRequest(BaseModel):
    event_id: int

class LeaveEventResponse(BaseModel):
    message: str
    event_id: int
    user_id: int

class PaginatedEventResponse(BaseModel):
    events: list[EventResponse]
    total_pages: int
    model_config = {"from_attributes": True}
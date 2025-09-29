from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/events", tags=["events"])

def save_image(file: UploadFile, path: str):
    # TODO: save the file to the path
    return path

@router.post("/create_event", response_model=EventResponse)
def create_event(
    event_photo: Optional[UploadFile] = File(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_location: str = Form(...),
    pincode: str = Form(...),
    whatsapp_group_link: Optional[str] = Form(None),
    date: str = Form(...),
    time: str = Form(...),
    max_attendees: int = Form(...),
    category: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create payload object for validation
    from datetime import date, time
    payload = EventCreate(
        event_title=event_title,
        event_description=event_description,
        event_location=event_location,
        pincode=pincode,
        whatsapp_group_link=whatsapp_group_link,
        date=date.fromisoformat(date),
        time=time.fromisoformat(time),
        max_attendees=max_attendees,
        category=category,
    )

    if payload.event_photo:
        filename = payload.event_photo.filename
        path = f"uploads/events/{current_user.id}_{payload.event_title.replace(' ', '_')}_{filename}"
        event_photo_path = save_image(payload.event_photo, path)
    else:
        event_photo_path = None

    event = Event(
        event_photo=event_photo_path,
        event_title=payload.event_title,
        event_description=payload.event_description,
        event_location=payload.event_location,
        pincode=payload.pincode,
        whatsapp_group_link=payload.whatsapp_group_link,
        date=payload.date,
        time=payload.time,
        max_attendees=payload.max_attendees,
        category=payload.category,
        host_id=current_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
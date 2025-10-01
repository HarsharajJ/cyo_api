from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse, JoinEventRequest, JoinEventResponse
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

@router.post("/join_event", response_model=JoinEventResponse)
def join_event(
    payload: JoinEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if event exists
    event = db.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is the host
    if event.host_id == current_user.id:
        raise HTTPException(status_code=400, detail="Host cannot join their own event")
    
    # Check if user already joined
    if current_user in event.participants:
        raise HTTPException(status_code=400, detail="User already joined this event")
    
    # Check max attendees
    if len(event.participants) >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Add user to participants
    event.participants.append(current_user)
    db.commit()
    
    return JoinEventResponse(
        message="Successfully joined the event",
        event_id=payload.event_id,
        user_id=current_user.id
    )

@router.get("/recommended_events", response_model=list[EventResponse])
def get_recommended_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.interests:
        return []
    
    # Query events where category is in user's interests
    events = db.query(Event).filter(Event.category.in_(current_user.interests)).all()
    return events

@router.get("/search_events", response_model=list[EventResponse])
def search_events(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fuzzy search by event title, exclude user's own hosted events
    events = db.query(Event).filter(
        Event.event_title.ilike(f"%{query}%"),
        Event.host_id != current_user.id
    ).all()
    return events

@router.get("/my_joined_events", response_model=list[EventResponse])
def get_my_joined_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get events the user has joined
    events = db.query(Event).filter(
        Event.participants.any(User.id == current_user.id)
    ).all()
    return events

@router.get("/my_hosted_events", response_model=list[EventResponse])
def get_my_hosted_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get events the user has hosted
    events = db.query(Event).filter(Event.host_id == current_user.id).all()
    return events

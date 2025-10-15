from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse, JoinEventRequest, JoinEventResponse, EventDetailResponse, HostInfo
from app.dependencies.auth import get_current_user
from app.models.user import User
from typing import Optional
from datetime import date, time
import time as _time
import uuid as _uuid
import re as _re
from app.utils.pincode_initializer import save_image

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/create_event", response_model=EventResponse)
def create_event(
    # Accept either an UploadFile or an empty string from Swagger UI. FastAPI will
    # supply a str when the multipart form field is present but empty. We accept
    # Optional[UploadFile] and handle the str case at runtime.
    event_photo: Optional[UploadFile] | Optional[str] = File(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_location: str = Form(...),
    pincode: str = Form(...),
    whatsapp_group_link: Optional[str] = Form(None),
    date: date = Form(...),
    time: time = Form(...),
    max_attendees: int = Form(...),
    category: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create payload object for validation (FastAPI will coerce form strings to date/time)
    payload = EventCreate(
        event_title=event_title,
        event_description=event_description,
        event_location=event_location,
        pincode=pincode,
        whatsapp_group_link=whatsapp_group_link,
        date=date,
        time=time,
        max_attendees=max_attendees,
        category=category,
    )
    # Save uploaded image (use the form parameter `event_photo` passed to the endpoint)
    if event_photo:
        # create a safe, unique filename (no spaces) with timestamp+uuid
        orig = event_photo.filename or "image"
        # split extension
        if "." in orig:
            base, ext = orig.rsplit(".", 1)
            ext = ext.lower()
        else:
            base, ext = orig, ""
        safe_base = _re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "img"
        title_slug = _re.sub(r"[^A-Za-z0-9]+", "-", payload.event_title).strip("-").lower() or "event"
        ts = int(_time.time() * 1000)
        short = _uuid.uuid4().hex[:8]
        safe_filename = f"{safe_base}_{ts}_{short}" + (f".{ext}" if ext else "")
        path = f"events/{current_user.id}_{title_slug}_{safe_filename}"
        try:
            event_photo_path = save_image(event_photo, path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save event image: {e}")
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

@router.get("/event/{event_id}", response_model=EventDetailResponse)
def get_event_details(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query event with host information
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create host info
    host_info = HostInfo(
        profile_picture_url=event.host.profile_picture_url,
        full_name=event.host.full_name,
        username=event.host.username
    )
    
    # Return event details with host info
    return EventDetailResponse(
        event_photo=event.event_photo,
        event_title=event.event_title,
        event_description=event.event_description,
        event_location=event.event_location,
        pincode=event.pincode,
        whatsapp_group_link=event.whatsapp_group_link,
        date=event.date,
        time=event.time,
        max_attendees=event.max_attendees,
        category=event.category,
        host=host_info
    )

@router.get("/search_events", response_model=list[EventResponse])
def search_events(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fuzzy search by event title
    events = db.query(Event).filter(
        Event.event_title.ilike(f"%{query}%"),
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

@router.get("/{category}", response_model=list[EventResponse])
def get_events_by_category(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all events matching the given category (case-insensitive)."""
    if not category:
        return []
    # Use case-insensitive matching
    events = db.query(Event).filter(Event.category.ilike(category)).all()
    return events

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse, JoinEventRequest, JoinEventResponse, EventDetailResponse, HostInfo, LeaveEventRequest, LeaveEventResponse, PaginatedEventResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from sqlalchemy import func
from app.models.pincode import Pincode
from typing import Optional
from datetime import date, time, datetime, timedelta
import time as _time
import uuid as _uuid
import re as _re
from app.utils.pincode_initializer import save_image
import math

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

    # Check if event is active
    if not getattr(event, 'is_active', True):
        raise HTTPException(status_code=400, detail="Cannot join a cancelled event")
    
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

@router.post("/leave_event", response_model=LeaveEventResponse)
def leave_event(
    payload: LeaveEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if event exists
    event = db.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is the host
    if event.host_id == current_user.id:
        raise HTTPException(status_code=400, detail="Host cannot leave their own event")
    
    # Check if user is joined
    if current_user not in event.participants:
        raise HTTPException(status_code=400, detail="User not joined this event")
    
    # Remove user from participants
    event.participants.remove(current_user)
    db.commit()
    
    return LeaveEventResponse(
        message="Successfully left the event",
        event_id=payload.event_id,
        user_id=current_user.id
    )

@router.get("/recommended_events", response_model=PaginatedEventResponse)
def get_recommended_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    # Validate pagination
    page = max(1, page)
    size = max(1, min(200, size))

    # If the user has no interests, return an empty paginated response
    if not current_user.interests:
        return PaginatedEventResponse(events=[], total_pages=0)

    # Use a bounding-box prefilter to limit candidate pincodes/events before
    # calculating exact distances. This avoids loading all matching events into
    # memory when a user's interests match many events.

    # DB query for events matching user's interests (do not .all() here)
    current_date = date.today()
    lowered_interests = [i.strip().lower() for i in (current_user.interests or [])]
    events_query = db.query(Event).filter(
        func.lower(Event.category).in_(lowered_interests),
        Event.host_id != current_user.id,
        Event.date > current_date,
        Event.is_active == True,
        ~Event.participants.any(User.id == current_user.id),
    )

    # Get user's location from their pincode
    user_pincode_data = db.query(Pincode).filter(Pincode.pincode == current_user.pincode).first()
    if not user_pincode_data:
        # Fallback: do DB-level pagination (no distance sorting possible)
        fallback_events = events_query.offset((page - 1) * size).limit(size).all()
        total = events_query.count()
        total_pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedEventResponse(events=fallback_events, total_pages=total_pages)

    user_lat, user_lon = user_pincode_data.latitude, user_pincode_data.longitude

    # Bounding-box approximation to prefilter nearby pincodes (in degrees)
    max_distance_km = 70.0
    # Approx: 1 deg latitude ~ 111 km
    lat_delta = max_distance_km / 111.0
    # Lon delta adjusted by latitude
    lon_delta = max_distance_km / (111.320 * max(0.000001, math.cos(math.radians(user_lat))))

    # Query pincodes within the bounding box
    nearby_pincodes_q = db.query(Pincode.pincode).filter(
        Pincode.latitude.between(user_lat - lat_delta, user_lat + lat_delta),
        Pincode.longitude.between(user_lon - lon_delta, user_lon + lon_delta),
    )
    nearby_pincodes = [r.pincode for r in nearby_pincodes_q.all()]

    if not nearby_pincodes:
        # Fallback: return paginated events without distance sorting
        fallback_events = events_query.offset((page - 1) * size).limit(size).all()
        total = events_query.count()
        total_pages = math.ceil(total / size) if total > 0 else 0
        return PaginatedEventResponse(events=fallback_events, total_pages=total_pages)

    # Fetch candidate events whose pincode is in the nearby pincodes set.
    # Cap the number of candidates to avoid memory spikes.
    CANDIDATE_LIMIT = 5000
    candidate_events = events_query.filter(Event.pincode.in_(nearby_pincodes)).limit(CANDIDATE_LIMIT).all()
    if not candidate_events:
        return PaginatedEventResponse(events=[], total_pages=0)

    total = len(candidate_events)
    total_pages = math.ceil(total / size)

    # Convert candidate events to DataFrame for distance calculation
    import pandas as pd
    events_data = []
    for event in candidate_events:
        events_data.append({
            'id': event.id,
            'pincode': str(event.pincode),
            'event_photo': event.event_photo,
            'event_title': event.event_title,
            'event_description': event.event_description,
            'event_location': event.event_location,
            'whatsapp_group_link': event.whatsapp_group_link,
            'date': event.date,
            'time': event.time,
            'max_attendees': event.max_attendees,
            'category': event.category,
            'host_id': event.host_id
        })

    events_df = pd.DataFrame(events_data)

    # Get pincode lat/lon for only the pincodes present in candidate events
    unique_pincodes = events_df['pincode'].unique().tolist()
    pincodes_data = db.query(Pincode).filter(Pincode.pincode.in_(unique_pincodes)).all()

    pincodes_list = []
    for pincode in pincodes_data:
        pincodes_list.append({'pincode': str(pincode.pincode), 'latitude': pincode.latitude, 'longitude': pincode.longitude})

    pincodes_df = pd.DataFrame(pincodes_list)

    # Sort events by distance using the utility function
    from app.utils.distance import sort_events_by_distance
    sorted_events_df = sort_events_by_distance(events_df, pincodes_df, user_lat, user_lon, max_distance_km)

    # Apply pagination to the sorted results
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_events_df = sorted_events_df.iloc[start_idx:end_idx]

    # Convert back to Event objects for response
    paginated_event_ids = paginated_events_df['id'].tolist()
    if not paginated_event_ids:
        return PaginatedEventResponse(events=[], total_pages=0)

    paginated_events = db.query(Event).filter(Event.id.in_(paginated_event_ids)).all()

    # Preserve DataFrame order when returning objects
    event_id_to_obj = {event.id: event for event in paginated_events}
    sorted_paginated_events = [event_id_to_obj[eid] for eid in paginated_event_ids if eid in event_id_to_obj]

    return PaginatedEventResponse(events=sorted_paginated_events, total_pages=total_pages)

@router.get("/event/{event_id}", response_model=EventDetailResponse)
def get_event_details(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query event with host information
    event = db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create host info
    host_info = HostInfo(
        profile_picture_url=event.host.profile_picture_url,
        full_name=event.host.full_name,
        username=event.host.username
    )
    
    # Build participants info
    participants = []
    for u in event.participants:
        participants.append({
            "id": u.id,
            "profile_picture_url": u.profile_picture_url,
            "full_name": u.full_name,
            "username": u.username,
        })

    # Return event details with host info and participants
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
        host=host_info,
        participants=participants,
    )

@router.get("/search_events", response_model=PaginatedEventResponse)
def search_events(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    # Fuzzy search by event title
    page = max(1, page)
    size = max(1, min(200, size))
    current_date = date.today()
    q = db.query(Event).filter(
        Event.event_title.ilike(f"%{query}%"),
        Event.date > current_date,
        Event.is_active == True,
        ~Event.participants.any(User.id == current_user.id),
    )
    total = q.count()
    total_pages = math.ceil(total / size)
    events = q.offset((page - 1) * size).limit(size).all()
    return PaginatedEventResponse(events=events, total_pages=total_pages)

@router.get("/my_joined_events", response_model=PaginatedEventResponse)
def get_my_joined_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    # Get events the user has joined
    page = max(1, page)
    size = max(1, min(200, size))
    q = db.query(Event).filter(
        Event.participants.any(User.id == current_user.id),
        Event.is_active == True,
    )
    total = q.count()
    total_pages = math.ceil(total / size)
    events = q.offset((page - 1) * size).limit(size).all()
    return PaginatedEventResponse(events=events, total_pages=total_pages)

@router.get("/my_hosted_events", response_model=PaginatedEventResponse)
def get_my_hosted_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    # Get events the user has hosted
    page = max(1, page)
    size = max(1, min(200, size))
    q = db.query(Event).filter(Event.host_id == current_user.id, Event.is_active == True)
    total = q.count()
    total_pages = math.ceil(total / size)
    events = q.offset((page - 1) * size).limit(size).all()
    return PaginatedEventResponse(events=events, total_pages=total_pages)


@router.put("/edit_event/{event_id}", response_model=EventResponse)
def edit_event(
    event_id: int,
    # Accept either an UploadFile or an empty string from Swagger UI
    event_photo: Optional[UploadFile] | Optional[str] = File(None),
    event_title: Optional[str] = Form(None),
    event_description: Optional[str] = Form(None),
    event_location: Optional[str] = Form(None),
    pincode: Optional[str] = Form(None),
    whatsapp_group_link: Optional[str] = Form(None),
    date: Optional[date] = Form(None),
    time: Optional[time] = Form(None),
    max_attendees: Optional[int] = Form(None),
    category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch event
    event = db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Only host can edit
    if event.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the host can edit this event")

    # Handle photo upload
    if event_photo:
        orig = getattr(event_photo, 'filename', None) or "image"
        if "." in orig:
            base, ext = orig.rsplit(".", 1)
            ext = ext.lower()
        else:
            base, ext = orig, ""
        safe_base = _re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "img"
        title_slug = _re.sub(r"[^A-Za-z0-9]+", "-", (event_title or event.event_title)).strip("-").lower() or "event"
        ts = int(_time.time() * 1000)
        short = _uuid.uuid4().hex[:8]
        safe_filename = f"{safe_base}_{ts}_{short}" + (f".{ext}" if ext else "")
        path = f"events/{current_user.id}_{title_slug}_{safe_filename}"
        try:
            event_photo_path = save_image(event_photo, path)
            event.event_photo = event_photo_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save event image: {e}")

    # Update fields if provided
    if event_title is not None:
        event.event_title = event_title
    if event_description is not None:
        event.event_description = event_description
    if event_location is not None:
        event.event_location = event_location
    if pincode is not None:
        event.pincode = pincode
    if whatsapp_group_link is not None:
        event.whatsapp_group_link = whatsapp_group_link
    if date is not None:
        event.date = date
    if time is not None:
        event.time = time
    if category is not None:
        event.category = category

    # max_attendees change: ensure we don't set it below current participants
    if max_attendees is not None:
        current_participants = len(event.participants) if event.participants is not None else 0
        if max_attendees < current_participants:
            raise HTTPException(status_code=400, detail="max_attendees cannot be less than current number of participants")
        event.max_attendees = max_attendees

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/cancel")
def cancel_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-cancel an event. Only the host can cancel. Cancellation is not
    allowed after the event has started or within 12 hours of the event start.
    """
    event = db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or already cancelled")

    # Only host can cancel
    if event.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the host can cancel this event")

    # Build event datetime
    try:
        event_dt = datetime.combine(event.date, event.time)
    except Exception:
        # If we can't combine date/time, disallow cancellation for safety
        raise HTTPException(status_code=400, detail="Invalid event date/time")

    now = datetime.now()
    # Can't cancel after event started
    if now >= event_dt:
        raise HTTPException(status_code=400, detail="Cannot cancel an event that has already started or passed")

    # Can't cancel within 12 hours of start
    if now >= (event_dt - timedelta(hours=12)):
        raise HTTPException(status_code=400, detail="Cannot cancel an event within 12 hours of its start time")

    # Soft-delete
    event.is_active = False
    db.add(event)
    db.commit()
    return {"message": "Event cancelled successfully", "event_id": event_id}

@router.get("/{category}", response_model=PaginatedEventResponse)
def get_events_by_category(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    """Return events matching the given category (case-insensitive).

    Special case: if `category` equals "all" (case-insensitive), return events
    from all categories paginated.
    """
    if not category:
        return PaginatedEventResponse(events=[], total_pages=0)

    page = max(1, page)
    size = max(1, min(200, size))
    current_date = date.today()

    if category.strip().lower() == "all":
        q = db.query(Event).filter(Event.date > current_date, Event.is_active == True, ~Event.participants.any(User.id == current_user.id),)
    else:
        # Case-insensitive equality match for the provided category
        q = db.query(Event).filter(func.lower(Event.category) == category.strip().lower(), Event.date > current_date, Event.is_active == True, ~Event.participants.any(User.id == current_user.id),)

    total = q.count()
    total_pages = math.ceil(total / size)
    events = q.offset((page - 1) * size).limit(size).all()
    return PaginatedEventResponse(events=events, total_pages=total_pages)

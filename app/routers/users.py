from app.schemas.user import UserResponse, InterestsUpdate, CompleteProfile, Location, UserProfileResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
from app.utils.pincode_initializer import save_image, get_location_from_pincode
from app.models.memory import Memory
from app.schemas.memory import MemoryListResponse
from app.schemas.event import PaginatedEventResponse
from datetime import date
import time as _time
import uuid as _uuid
import re as _re

router = APIRouter(prefix="/users", tags=["users"])


# using shared save_image from app.utils.pincode_initializer


def user_to_response(user: User) -> dict:
    """Convert User model to UserResponse dict with location."""
    location_data = get_location_from_pincode(user.pincode)
    if not location_data:
        location_data = {"district": "Unknown", "state_name": "Unknown"}
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "pincode": user.pincode,
        "location": Location(**location_data),
        "mobile_number": user.mobile_number,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "profile_picture_url": user.profile_picture_url,
        "bio": user.bio,
        "instagram_url": user.instagram_url,
        "twitter_url": user.twitter_url,
        "linkedin_url": user.linkedin_url,
        "portfolio_url": user.portfolio_url,
        "snapchat_url": user.snapchat_url,
        "interests": user.interests,
        "subscribed": user.subscribed,
        "relationship_status": user.relationship_status,
        "profile_visibility": user.profile_visibility,
    }


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)

@router.get("/pincode/{pincode}")
def lookup_pincode(pincode: str):
    """Return district/state for a pincode (used by client for immediate lookup)."""
    loc = get_location_from_pincode(pincode)
    if not loc:
        # return a 404 so caller knows it wasn't found
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pincode not found")
    return {"pincode": pincode, "location": loc}

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Public endpoint: return a user's public profile (basic details) by their numeric ID.

    This endpoint intentionally returns only user metadata (no memories, no events).
    Returns 404 if the user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.get("/memories/{user_id}", response_model=MemoryListResponse)
def list_user_memories(user_id: int, page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    """Return paginated memories for the given user id."""
    page = max(1, page)
    size = max(1, min(200, size))
    q = db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.created_at.desc())
    total = q.count()
    total_pages = (total + size - 1) // size if total > 0 else 0
    memories = q.offset((page - 1) * size).limit(size).all()
    memories_list = []
    for m in memories:
        memories_list.append({
            "id": m.id,
            "user_id": m.user_id,
            "caption": m.caption,
            "image_urls": m.image_urls,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        })
    return MemoryListResponse(memories=memories_list, total=total, page=page, size=size, total_pages=total_pages)


@router.get("/events/{user_id}", response_model=PaginatedEventResponse)
def list_user_joined_events(user_id: int, page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    """Return paginated events joined by the specified user."""
    page = max(1, page)
    size = max(1, min(200, size))
    q = db.query(User).join(User.joined_events).filter(User.id == user_id)
    # q here yields Event rows via the join; switch to querying Event instead for clarity
    from app.models.event import Event
    eq = db.query(Event).filter(Event.participants.any(User.id == user_id))
    total = eq.count()
    total_pages = (total + size - 1) // size if total > 0 else 0
    events = eq.offset((page - 1) * size).limit(size).all()
    return PaginatedEventResponse(events=events, total_pages=total_pages)


@router.post("/complete-profile", response_model=UserResponse)
def complete_profile(
    profile_picture: Optional[UploadFile] = File(None),
    username: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    instagram_url: Optional[str] = Form(None),
    twitter_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    snapchat_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create payload object for validation
    payload = CompleteProfile(
        profile_picture_url=profile_picture, 
        username=username,
        bio=bio,
        instagram_url=instagram_url,
        twitter_url=twitter_url,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
        snapchat_url=snapchat_url,
    )

    # If username provided, ensure it's unique (or it's the same as current)
    if payload.username:
        existing = db.query(User).filter(User.username == payload.username).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already taken")
        # set username if provided and not taken
        current_user.username = payload.username

    # Handle profile picture
    if profile_picture:
        orig = profile_picture.filename or "avatar"
        if "." in orig:
            base, ext = orig.rsplit(".", 1)
            ext = ext.lower()
        else:
            base, ext = orig, ""
        safe_base = _re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "img"
        ts = int(_time.time() * 1000)
        short = _uuid.uuid4().hex[:8]
        safe_filename = f"{safe_base}_{ts}_{short}" + (f".{ext}" if ext else "")
        path = f"users/{current_user.id}_{safe_filename}"
        try:
            new_path = save_image(profile_picture, path)
            current_user.profile_picture_url = new_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save profile picture: {e}")

    # Update other optional profile fields
    if payload.bio is not None:
        current_user.bio = payload.bio
    if payload.instagram_url is not None:
        current_user.instagram_url = payload.instagram_url
    if payload.twitter_url is not None:
        current_user.twitter_url = payload.twitter_url
    if payload.linkedin_url is not None:
        current_user.linkedin_url = payload.linkedin_url
    if payload.portfolio_url is not None:
        current_user.portfolio_url = payload.portfolio_url
    if payload.snapchat_url is not None:
        current_user.snapchat_url = payload.snapchat_url

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


@router.put("/interests", response_model=UserResponse)
def update_interests(
    payload: InterestsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.interests = payload.interests
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


@router.put("/edit_profile", response_model=UserResponse)
def edit_profile(
    # Accept either an UploadFile or an empty string from Swagger UI
    profile_picture: Optional[UploadFile | str] = File(None),
    email: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    pincode: Optional[str] = Form(None),
    mobile_number: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    interests: Optional[str] = Form(None),
    subscribed: Optional[bool] = Form(None),
    relationship_status: Optional[str] = Form(None),
    profile_visibility: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    instagram_url: Optional[str] = Form(None),
    twitter_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    snapchat_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile.

    All fields are optional. Username and password are NOT updatable here.
    `profile_picture` accepts an UploadFile or an empty string (swagger quirk).
    `interests` may be JSON array string (e.g. '["a","b"]') or comma-separated.
    """
    import json

    # Email uniqueness check
    if email and email != current_user.email:
        existing = db.query(User).filter(User.email == email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = email

    # Update simple scalar fields
    if full_name is not None:
        current_user.full_name = full_name
    if pincode is not None:
        current_user.pincode = pincode
    if mobile_number is not None:
        current_user.mobile_number = mobile_number
    if is_active is not None:
        current_user.is_active = is_active
    if subscribed is not None:
        current_user.subscribed = subscribed
    if relationship_status is not None:
        current_user.relationship_status = relationship_status
    if profile_visibility is not None:
        current_user.profile_visibility = profile_visibility

    # Update profile links / bio
    if bio is not None:
        current_user.bio = bio
    if instagram_url is not None:
        current_user.instagram_url = instagram_url
    if twitter_url is not None:
        current_user.twitter_url = twitter_url
    if linkedin_url is not None:
        current_user.linkedin_url = linkedin_url
    if portfolio_url is not None:
        current_user.portfolio_url = portfolio_url
    if snapchat_url is not None:
        current_user.snapchat_url = snapchat_url

    # Parse interests
    if interests is not None:
        parsed = None
        # try JSON first
        try:
            parsed = json.loads(interests)
        except Exception:
            # fallback to comma-separated
            parsed = [s.strip() for s in (interests or "").split(",") if s.strip()]
        # Ensure list type
        if isinstance(parsed, list):
            current_user.interests = parsed

    # Handle profile picture upload
    if profile_picture:
        # Swagger may send an empty string for file fields; treat str as no-op
        if isinstance(profile_picture, str):
            # ignore empty string or direct URL strings here (no upload)
            pass
        else:
            orig = getattr(profile_picture, 'filename', None) or "avatar"
            if "." in orig:
                base, ext = orig.rsplit(".", 1)
                ext = ext.lower()
            else:
                base, ext = orig, ""
            safe_base = _re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "img"
            ts = int(_time.time() * 1000)
            short = _uuid.uuid4().hex[:8]
            safe_filename = f"{safe_base}_{ts}_{short}" + (f".{ext}" if ext else "")
            path = f"users/{current_user.id}_{safe_filename}"
            try:
                new_path = save_image(profile_picture, path)
                current_user.profile_picture_url = new_path
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save profile picture: {e}")

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)
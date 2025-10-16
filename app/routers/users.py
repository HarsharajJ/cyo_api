from app.schemas.user import UserResponse, InterestsUpdate, CompleteProfile
from app.dependencies.auth import get_current_user
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
from app.utils.pincode_initializer import save_image
import time as _time
import uuid as _uuid
import re as _re

router = APIRouter(prefix="/users", tags=["users"])


# using shared save_image from app.utils.pincode_initializer


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Public endpoint: return a user's full profile by their numeric ID.

    Returns 404 if the user does not exist.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/complete-profile", response_model=UserResponse)
def complete_profile(
    profile_picture: Optional[UploadFile] = File(None),
    username: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    instagram_url: Optional[str] = Form(None),
    twitter_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
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

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


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
    return current_user


@router.put("/edit_profile", response_model=UserResponse)
def edit_profile(
    # Accept either an UploadFile or an empty string from Swagger UI
    profile_picture: Optional[UploadFile] = File(None),
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
    return current_user
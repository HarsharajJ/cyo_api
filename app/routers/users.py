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
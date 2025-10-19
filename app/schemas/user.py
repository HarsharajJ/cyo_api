from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from app.schemas.memory import MemoryResponse
from app.schemas.event import EventResponse

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password must be 8-72 characters")
    full_name: str = Field(..., min_length=3, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=6)
    mobile_number: str = Field(default="+91", description="Mobile number with country code")

class Location(BaseModel):
    district: str
    state_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    pincode: str
    location: Location
    mobile_number: str  
    is_active: bool
    created_at: datetime
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    snapchat_url: Optional[str] = None
    interests: Optional[list[str]] = None
    subscribed: bool = False
    relationship_status: Optional[str] = None
    profile_visibility: str = "public"

class UserProfileResponse(UserResponse):
    memories: Optional[list[MemoryResponse]] = None
    joined_events: Optional[list[EventResponse]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    mobile_number: Optional[str] = None
    is_active: Optional[bool] = None
    interests: Optional[list[str]] = None
    subscribed: Optional[bool] = None
    relationship_status: Optional[str] = None
    profile_visibility: Optional[str] = None


class InterestsUpdate(BaseModel):
    interests: list[str]


class CompleteProfile(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    snapchat_url: Optional[str] = None
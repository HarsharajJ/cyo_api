from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from fastapi import UploadFile

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password must be 8-72 characters")
    full_name: str = Field(..., min_length=3, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=6)
    mobile_number: str = Field(default="+91", description="Mobile number with country code")

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    pincode: str
    mobile_number: str  
    is_active: bool
    created_at: datetime
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    interests: Optional[list[str]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    mobile_number: Optional[str] = None
    is_active: Optional[bool] = None
    interests: Optional[list[str]] = None


class InterestsUpdate(BaseModel):
    interests: list[str]


class CompleteProfile(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
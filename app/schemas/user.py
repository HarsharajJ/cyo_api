from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    pincode: str
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

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    pincode: Optional[str] = None
    mobile_number: Optional[str] = None
    is_active: Optional[bool] = None
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MemoryCreate(BaseModel):
    caption: str
    images: List  # This will be handled as UploadFile list in the endpoint

class MemoryResponse(BaseModel):
    id: int
    user_id: int
    caption: str
    image_urls: List[str]
    created_at: datetime
    updated_at: datetime

class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int
    page: int
    size: int
    total_pages: int

class MemoryUpdate(BaseModel):
    caption: Optional[str] = None
    images: Optional[List] = None  
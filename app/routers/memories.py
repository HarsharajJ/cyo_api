from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryResponse, MemoryListResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from typing import Optional, List
import time as _time
import uuid as _uuid
import re as _re
from app.utils.pincode_initializer import save_images

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("/create_memories", response_model=MemoryResponse)
def create_memories(
    caption: str = Form(...),
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new memory with multiple images and a caption."""

    if not images or len(images) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required")

    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed per memory")

    # Create safe filename base for the memory
    caption_slug = _re.sub(r"[^A-Za-z0-9]+", "-", caption).strip("-").lower() or "memory"
    ts = int(_time.time() * 1000)
    short = _uuid.uuid4().hex[:8]
    base_path = f"memories/{current_user.id}_{caption_slug}_{ts}_{short}_{{i}}"

    try:
        # Save all images using the batch function
        image_urls = save_images(images, base_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save images: {e}")

    if not image_urls:
        raise HTTPException(status_code=500, detail="Failed to save any images")

    # Create the memory record
    memory = Memory(
        user_id=current_user.id,
        caption=caption,
        image_urls=image_urls,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


@router.get("/view_memories", response_model=MemoryListResponse)
def view_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    """View all memories for the current user with pagination."""

    page = max(1, page)
    size = max(1, min(50, size))  # Max 50 per page for memories

    query = db.query(Memory).filter(Memory.user_id == current_user.id)
    total = query.count()
    memories = query.order_by(Memory.created_at.desc()).offset((page - 1) * size).limit(size).all()

    # Convert SQLAlchemy objects to dictionaries for Pydantic
    memories_data = []
    for memory in memories:
        memories_data.append({
            "id": memory.id,
            "user_id": memory.user_id,
            "caption": memory.caption,
            "image_urls": memory.image_urls,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        })

    return MemoryListResponse(
        memories=memories_data,
        total=total,
        page=page,
        size=size
    )
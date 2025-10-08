from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.models.user import User
from app.schemas.user import UserResponse
from app.dependencies.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all users.

    Access control: allowed only when running in debug mode or when the current
    user's username is "admin". This is a conservative safety measure because
    there is no explicit admin flag on the User model in this project.
    """
    if not settings.debug :
        raise HTTPException(status_code=403, detail="Forbidden")
    users = db.query(User).all()
    return users


@router.post("/clear-db")
def clear_db(current_user: User = Depends(get_current_user)):
    """Delete all rows from every table in the database while preserving
    table definitions. This is a destructive operation and therefore access is
    restricted to debug mode or the 'admin' username by default.
    """
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Forbidden")

    conn = engine.connect()
    trans = conn.begin()
    try:
        # Use reversed order to respect FKs when deleting rows
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
    return {"message": "All table rows deleted (tables preserved)."}
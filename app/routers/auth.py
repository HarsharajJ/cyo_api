from datetime import timedelta, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.token import RefreshToken
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import TokenResponse, RefreshResponse
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.utils import verify_password, get_password_hash
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=TokenResponse)
def register(request: Request, user: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate unique username from full_name
    base_username = user.full_name.lower().replace(' ', '_').replace('-', '_')
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        username=username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        pincode=user.pincode,
        mobile_number=user.mobile_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Auto login
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    # Store refresh token
    db_refresh = RefreshToken(token=refresh_token, user_id=new_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days))
    db.add(db_refresh)
    db.commit()
    # Set refresh token as cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=not settings.debug, samesite="strict", max_age=settings.refresh_token_expire_days * 24 * 60 * 60)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check if username contains '@' to determine if it's email or username
    if '@' in form_data.username:
        user = db.query(User).filter(User.email == form_data.username).first()
    else:
        user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username/email or password")
    
    # Store refresh token
    
    # Check active refresh tokens for this user (not blacklisted and not expired)
    now = datetime.now(timezone.utc)
    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.is_blacklisted == False,
        RefreshToken.expires_at > now
    ).all()
    
    if len(active_tokens) >= 4:
        # Rotate: delete the oldest token
        oldest_token = min(active_tokens, key=lambda t: t.expires_at)
        db.delete(oldest_token)
        db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    # Store refresh token
    db_refresh = RefreshToken(token=refresh_token, user_id=user.id, expires_at=now + timedelta(days=settings.refresh_token_expire_days))
    db.add(db_refresh)
    db.commit()
    # Set refresh token as cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=not settings.debug, samesite="strict", max_age=settings.refresh_token_expire_days * 24 * 60 * 60)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=RefreshResponse)
def refresh(refresh_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    try:
        payload = verify_token(refresh_token, "refresh")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id: str = payload.get("sub")
    # Check if blacklisted
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token, RefreshToken.is_blacklisted == False).first()
    if not db_token or db_token.user_id != int(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token}

@router.post("/logout")
def logout(response: Response, refresh_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if refresh_token:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        if db_token:
            db_token.is_blacklisted = True
            db.commit()
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}
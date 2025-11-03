from datetime import timedelta, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.token import RefreshToken
from app.models.otp import OTP
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import TokenResponse, RefreshResponse
from app.schemas.otp import OTPRequest, OTPVerify, OTPResponse
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, ResetPasswordResponse
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.utils import verify_password, get_password_hash
from app.config import settings
from app.utils.email import generate_otp, send_otp_email

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
    
    # Distinct errors: user not found vs incorrect password
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
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


@router.post("/otp/generate", response_model=OTPResponse)
def generate_otp_endpoint(request: OTPRequest, db: Session = Depends(get_db)):
    """
    Generate and send OTP to the specified email address.
    Previous unverified OTPs for this email will be invalidated.
    """
    try:
        # Generate 6-digit OTP
        otp_code = generate_otp(6)
        
        # Invalidate all previous unverified OTPs for this email
        db.query(OTP).filter(
            OTP.email == request.email,
            OTP.is_verified == False
        ).delete()
        db.commit()
        
        # Create new OTP record
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
        new_otp = OTP(
            email=request.email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.add(new_otp)
        db.commit()
        
        # Send OTP via email
        email_sent = send_otp_email(request.email, otp_code)
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email. Please try again."
            )
        
        return {
            "message": f"OTP sent successfully to {request.email}",
            "email": request.email
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating OTP"
        )


@router.post("/otp/verify", response_model=OTPResponse)
def verify_otp_endpoint(request: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify the OTP code for the specified email address.
    OTP must be valid and not expired.
    """
    # Find the most recent OTP for this email
    otp_record = db.query(OTP).filter(
        OTP.email == request.email,
        OTP.otp_code == request.otp_code,
        OTP.is_verified == False
    ).order_by(OTP.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Check if OTP has expired
    now = datetime.now(timezone.utc)
    
    # Handle timezone-aware vs timezone-naive datetime comparison
    expires_at = otp_record.expires_at
    if expires_at.tzinfo is None:
        # Database stored naive datetime, compare with naive now
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )
    
    # Mark OTP as verified
    otp_record.is_verified = True
    db.commit()
    
    return {
        "message": "OTP verified successfully",
        "email": request.email
    }


@router.post("/forgot-password", response_model=OTPResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate a password reset by accepting an email or username (identifier).
    If the identifier doesn't correspond to any user, return an error.
    If user exists, generate and send an OTP to the user's registered email.
    """
    identifier = request.identifier
    # Find user by email or username
    if '@' in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    else:
        user = db.query(User).filter(User.username == identifier).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email/username does not exist")

    try:
        # Generate 6-digit OTP
        otp_code = generate_otp(6)

        # Invalidate previous unverified OTPs for this email
        db.query(OTP).filter(
            OTP.email == user.email,
            OTP.is_verified == False
        ).delete()
        db.commit()

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
        new_otp = OTP(
            email=user.email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.add(new_otp)
        db.commit()

        email_sent = send_otp_email(user.email, otp_code)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email. Please try again."
            )

        return {"message": f"OTP sent successfully to {user.email}", "email": user.email}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating OTP")


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password for a user after verifying that an OTP was successfully verified for their email.
    The request accepts an identifier (email or username) and the new password.
    """
    identifier = request.identifier
    if '@' in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    else:
        user = db.query(User).filter(User.username == identifier).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email/username does not exist")

    # Check for a verified OTP for this user's email
    otp_record = db.query(OTP).filter(
        OTP.email == user.email,
        OTP.is_verified == True
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not verified for this email/username")

    # Update user's password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    # Remove OTPs for this email so the same OTP cannot be reused
    db.query(OTP).filter(OTP.email == user.email).delete()
    db.commit()

    return {"message": "Password reset successful"}
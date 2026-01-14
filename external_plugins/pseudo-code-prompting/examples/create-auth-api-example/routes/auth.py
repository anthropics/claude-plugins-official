from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, Role, Session as SessionModel, FailedLoginAttempt, EmailVerification
from schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordResetVerify, RefreshTokenRequest, ErrorResponse
)
from database import get_db
from auth_utils import PasswordManager, TokenManager, TokenGenerator
from audit_logger import AuditLogger
from rate_limiter import rate_limit_manager
from email_service import EmailService
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

def get_remote_address(request: Request) -> str:
    return request.client.host

def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    ip_address = get_remote_address(request)
    user_agent = get_user_agent(request)

    # Rate limiting
    if rate_limit_manager.is_rate_limited(f"register:{ip_address}", settings.RATE_LIMIT_REGISTER):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Please try later.")

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Email or username already registered")

    # Create new user
    hashed_password = PasswordManager.hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )

    # Assign default user role
    user_role = db.query(Role).filter(Role.name == "user").first()
    if user_role:
        new_user.roles.append(user_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration
    AuditLogger.log_registration(db, new_user.id, ip_address, user_agent)

    # Send email verification
    verification_token = TokenGenerator.generate_email_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRY_HOURS)

    email_verification = EmailVerification(
        user_id=new_user.id,
        token=verification_token,
        expires_at=expires_at
    )
    db.add(email_verification)
    db.commit()

    # Send verification email
    try:
        EmailService.send_verification_email(user_data.email, verification_token)
    except Exception as e:
        print(f"Failed to send verification email: {e}")

    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login"""
    ip_address = get_remote_address(request)
    user_agent = get_user_agent(request)

    # Rate limiting
    if rate_limit_manager.is_rate_limited(f"login:{ip_address}", settings.RATE_LIMIT_LOGIN):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try later.")

    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not PasswordManager.verify_password(credentials.password, user.password_hash):
        # Log failed attempt
        AuditLogger.log_failed_login(db, credentials.username, ip_address, user_agent)

        # Track failed attempts for account lockout
        failed_attempt = FailedLoginAttempt(
            username=credentials.username,
            ip_address=ip_address
        )
        db.add(failed_attempt)
        db.commit()

        # Check if user should be locked
        if user:
            failed_count = db.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.username == credentials.username,
                FailedLoginAttempt.attempted_at >= datetime.now(timezone.utc) - timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            ).count()

            if failed_count >= settings.MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                db.commit()
                AuditLogger.log_account_lock(db, user.id, ip_address, user_agent)
                raise HTTPException(status_code=403, detail="Account locked due to multiple failed login attempts")

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if user is locked
    if user.is_locked:
        if user.locked_until and datetime.now(timezone.utc) > user.locked_until:
            user.is_locked = False
            user.locked_until = None
            db.commit()
        else:
            raise HTTPException(status_code=403, detail="Account is locked")

    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email to login.")

    # Create tokens
    access_token = TokenManager.create_access_token(str(user.id))
    refresh_token = TokenManager.create_refresh_token(str(user.id))

    # Store session
    session = SessionModel(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session)
    db.commit()

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Log login
    AuditLogger.log_login(db, user.id, ip_address, user_agent)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """User logout - revoke tokens"""
    user_id = TokenManager.verify_token(token, "access")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    ip_address = get_remote_address(request)
    user_agent = get_user_agent(request)

    # Revoke all sessions for this user
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.is_revoked == False
    ).all()

    for session in sessions:
        session.is_revoked = True

    db.commit()

    # Log logout
    AuditLogger.log_logout(db, user_id, ip_address, user_agent)

    return None

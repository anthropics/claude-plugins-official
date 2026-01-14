from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, PasswordReset
from schemas import PasswordResetRequest, PasswordResetVerify, ErrorResponse
from database import get_db
from auth_utils import PasswordManager, TokenGenerator
from audit_logger import AuditLogger
from rate_limiter import rate_limit_manager
from email_service import EmailService
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["password"])

def get_remote_address(request: Request) -> str:
    return request.client.host

def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")

@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    ip_address = get_remote_address(request)

    # Rate limiting
    if rate_limit_manager.is_rate_limited(f"password_reset:{ip_address}", settings.RATE_LIMIT_PASSWORD_RESET):
        raise HTTPException(status_code=429, detail="Too many password reset requests. Please try later.")

    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        # Return success even if user not found (security)
        return {"message": "If account exists, password reset email will be sent"}

    # Create password reset token
    reset_token = TokenGenerator.generate_password_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRY_MINUTES)

    password_reset = PasswordReset(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(password_reset)
    db.commit()

    # Send reset email
    try:
        EmailService.send_password_reset_email(data.email, reset_token)
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

    return {"message": "If account exists, password reset email will be sent"}

@router.post("/password-reset/verify", status_code=status.HTTP_200_OK)
async def verify_password_reset(
    data: PasswordResetVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify password reset token and update password"""
    ip_address = get_remote_address(request)
    user_agent = get_user_agent(request)

    # Find password reset request
    reset_request = db.query(PasswordReset).filter(
        PasswordReset.token == data.token,
        PasswordReset.is_used == False
    ).first()

    if not reset_request:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Check if token expired
    if datetime.now(timezone.utc) > reset_request.expires_at:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    # Get user
    user = db.query(User).filter(User.id == reset_request.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    # Update password
    user.password_hash = PasswordManager.hash_password(data.new_password)

    # Mark reset as used
    reset_request.is_used = True

    # Invalidate all existing sessions (force re-login)
    from models import Session as SessionModel
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user.id,
        SessionModel.is_revoked == False
    ).all()
    for session in sessions:
        session.is_revoked = True

    db.commit()

    # Log password reset
    AuditLogger.log_password_reset(db, user.id, ip_address, user_agent)

    return {"message": "Password reset successfully. Please login with your new password."}

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, EmailVerification
from schemas import EmailVerificationRequest, ResendEmailVerification
from database import get_db
from auth_utils import TokenGenerator
from rate_limiter import rate_limit_manager
from email_service import EmailService
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["email"])

def get_remote_address(request: Request) -> str:
    return request.client.host

@router.post("/email/verify", status_code=status.HTTP_200_OK)
async def verify_email(
    data: EmailVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify user email with token"""
    ip_address = get_remote_address(request)

    # Find email verification
    email_verification = db.query(EmailVerification).filter(
        EmailVerification.token == data.token,
        EmailVerification.is_used == False
    ).first()

    if not email_verification:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    # Check if token expired
    if datetime.now(timezone.utc) > email_verification.expires_at:
        raise HTTPException(status_code=400, detail="Verification token has expired")

    # Get user
    user = db.query(User).filter(User.id == email_verification.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Mark email as verified
    user.is_verified = True
    email_verification.is_used = True

    db.commit()

    return {"message": "Email verified successfully"}

@router.post("/email/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_email(
    data: ResendEmailVerification,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    ip_address = get_remote_address(request)

    # Rate limiting
    if rate_limit_manager.is_rate_limited(f"resend_verification:{ip_address}", "5/hour"):
        raise HTTPException(status_code=429, detail="Too many verification email requests. Please try later.")

    # Find user
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"message": "If account exists, verification email will be sent"}

    # Check if already verified
    if user.is_verified:
        return {"message": "Email is already verified"}

    # Generate new verification token
    verification_token = TokenGenerator.generate_email_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRY_HOURS)

    # Delete old verification tokens
    old_verifications = db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id,
        EmailVerification.is_used == False
    ).all()
    for old_verification in old_verifications:
        db.delete(old_verification)

    # Create new verification
    email_verification = EmailVerification(
        user_id=user.id,
        token=verification_token,
        expires_at=expires_at
    )
    db.add(email_verification)
    db.commit()

    # Send verification email
    try:
        EmailService.send_verification_email(data.email, verification_token)
    except Exception as e:
        print(f"Failed to send verification email: {e}")

    return {"message": "If account exists, verification email will be sent"}

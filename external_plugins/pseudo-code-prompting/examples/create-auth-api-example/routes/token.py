from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, Session as SessionModel, TokenBlacklist
from schemas import RefreshTokenRequest, TokenResponse
from database import get_db
from auth_utils import TokenManager
from audit_logger import AuditLogger
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["tokens"])

def get_remote_address(request: Request) -> str:
    return request.client.host

def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    ip_address = get_remote_address(request)
    user_agent = get_user_agent(request)

    # Verify refresh token
    user_id = TokenManager.verify_token(data.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if token is blacklisted
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == data.refresh_token
    ).first()
    if blacklisted:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check if account is locked
    if user.is_locked:
        if user.locked_until and datetime.now(timezone.utc) > user.locked_until:
            user.is_locked = False
            user.locked_until = None
            db.commit()
        else:
            raise HTTPException(status_code=403, detail="Account is locked")

    # Find existing session
    session = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.refresh_token == data.refresh_token,
        SessionModel.is_revoked == False
    ).first()

    if not session:
        raise HTTPException(status_code=401, detail="Session not found or revoked")

    # Invalidate old refresh token (add to blacklist)
    old_refresh_token_blacklist = TokenBlacklist(
        token=data.refresh_token,
        blacklisted_at=datetime.now(timezone.utc),
        expires_at=session.expires_at
    )
    db.add(old_refresh_token_blacklist)

    # Create new tokens
    new_access_token = TokenManager.create_access_token(str(user.id))
    new_refresh_token = TokenManager.create_refresh_token(str(user.id))

    # Update session with new tokens
    session.token = new_access_token
    session.refresh_token = new_refresh_token
    session.created_at = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    db.commit()

    # Log token refresh
    AuditLogger.log_token_refresh(db, user.id, ip_address, user_agent)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

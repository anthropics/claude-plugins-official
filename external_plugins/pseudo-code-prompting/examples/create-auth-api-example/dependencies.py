from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from models import User, Role
from auth_utils import TokenManager
from database import get_db

async def get_current_user(
    token: str = None,
    request: Request = None,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    if not token:
        # Try to extract from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        token = auth_header[7:]

    # Verify token
    user_id = TokenManager.verify_token(token, "access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

async def get_user_with_role(
    required_role: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they have required role"""
    user_roles = [role.name for role in current_user.roles]

    if required_role not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have required role: {required_role}"
        )

    return current_user

def get_admin_user(current_user: User = Depends(get_user_with_role("admin"))) -> User:
    """Dependency for admin-only endpoints"""
    return current_user

def get_moderator_user(current_user: User = Depends(get_user_with_role("moderator"))) -> User:
    """Dependency for moderator-only endpoints"""
    return current_user

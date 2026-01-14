from sqlalchemy.orm import Session
from models import AuditLog
from typing import Optional
import uuid
from datetime import datetime

class AuditLogger:
    EVENT_LOGIN = "login"
    EVENT_REGISTER = "register"
    EVENT_LOGOUT = "logout"
    EVENT_PASSWORD_RESET = "password_reset"
    EVENT_FAILED_LOGIN = "failed_attempts"
    EVENT_ACCOUNT_LOCK = "account_lock"
    EVENT_SESSION_INVALIDATION = "session_invalidation"
    EVENT_TOKEN_REFRESH = "token_refresh"

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        ip_address: str,
        user_id: Optional[uuid.UUID] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Log an authentication event"""
        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def log_login(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log successful login"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="User logged in successfully"
        )

    @staticmethod
    def log_failed_login(db: Session, username: str, ip_address: str, user_agent: Optional[str] = None):
        """Log failed login attempt"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_FAILED_LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"Failed login attempt for username: {username}"
        )

    @staticmethod
    def log_registration(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log user registration"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_REGISTER,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="User registered successfully"
        )

    @staticmethod
    def log_password_reset(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log password reset"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_PASSWORD_RESET,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Password reset successfully"
        )

    @staticmethod
    def log_logout(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log logout"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_LOGOUT,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="User logged out"
        )

    @staticmethod
    def log_account_lock(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log account lock"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_ACCOUNT_LOCK,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Account locked due to multiple failed login attempts"
        )

    @staticmethod
    def log_session_invalidation(db: Session, user_id: uuid.UUID, ip_address: str, reason: str):
        """Log session invalidation"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_SESSION_INVALIDATION,
            user_id=user_id,
            ip_address=ip_address,
            details=f"Session invalidated: {reason}"
        )

    @staticmethod
    def log_token_refresh(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str] = None):
        """Log token refresh"""
        return AuditLogger.log_event(
            db=db,
            event_type=AuditLogger.EVENT_TOKEN_REFRESH,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details="Token refreshed successfully"
        )

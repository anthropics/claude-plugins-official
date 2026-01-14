from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API
    API_VERSION: str = "v1"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/auth_db"
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    DB_POOL_TIMEOUT: int = 30

    # JWT Token
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_NUMBERS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True

    # Email
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 24
    PASSWORD_RESET_EXPIRY_MINUTES: int = 30
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@app.com"

    # Account Protection
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CONNECTION_TIMEOUT: int = 5

    # Rate Limiting
    RATE_LIMIT_PER_USER: str = "10/minute"
    RATE_LIMIT_PER_IP: str = "50/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_PASSWORD_RESET: str = "3/hour"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Encryption
    ENCRYPTION_ALGORITHM: str = "AES-256"

    # Audit Logging
    AUDIT_LOG_RETENTION_DAYS: int = 90

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

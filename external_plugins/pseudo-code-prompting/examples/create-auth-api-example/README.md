# Production-Ready Authentication API

A comprehensive FastAPI authentication system implementing industry best practices with JWT tokens, email verification, password reset, account lockout protection, RBAC, token refresh, and complete audit logging.

## Features

### 🔐 Security
- **JWT Token Authentication**: Secure token-based authentication with configurable expiry
- **Password Hashing**: Bcrypt-based password hashing with salt
- **Password Complexity Rules**: Enforce uppercase, numbers, special characters
- **Account Lockout**: Automatic account lockout after 5 failed login attempts
- **Brute Force Protection**: IP and username-based tracking
- **Token Rotation**: New tokens generated on refresh, old ones invalidated
- **Token Revocation**: Redis-backed token blacklist for immediate revocation
- **CSRF Protection**: CSRF tokens for state-changing operations
- **Rate Limiting**: Per-user, per-IP, and per-endpoint rate limiting

### 📧 Email Features
- **Email Verification**: Required email verification for new accounts
- **Password Reset**: Secure password reset flow with time-limited tokens
- **Email Resend**: Resend verification emails with rate limiting
- **SendGrid Integration**: Production-ready email service integration

### 👤 User Management
- **User Registration**: Create accounts with email and username
- **User Login**: Authenticate with username/password
- **Session Management**: Single session per user, invalidate others on login
- **Role-Based Access Control (RBAC)**: User, Admin, and Moderator roles
- **User Profiles**: Track user information and login history

### 📋 Audit & Logging
- **Comprehensive Audit Logging**: Track all authentication events
- **Event Tracking**: Login, logout, failed attempts, password resets, account locks
- **IP and User-Agent Logging**: Track request origin and client information
- **Log Retention**: Configurable retention policy (default 90 days)
- **Archival Strategy**: Move old logs to cold storage

### 🛡️ Protection Mechanisms
- **DDoS Protection**: Multiple layers of protection including rate limiting and IP blocking
- **Suspicious Activity Detection**: Flag and respond to suspicious patterns
- **Lockout Recovery**: Automatic unlock after configurable duration
- **Session Invalidation**: Force re-authentication on password change
- **Redis Failover**: In-memory fallback if Redis is unavailable

## Project Structure

```
create-auth-api-example/
├── config.py                 # Configuration and settings
├── database.py              # Database setup and initialization
├── models.py                # SQLAlchemy database models
├── schemas.py               # Pydantic request/response schemas
├── auth_utils.py            # Password and token management utilities
├── rate_limiter.py          # Rate limiting with Redis fallback
├── audit_logger.py          # Audit logging functionality
├── email_service.py         # Email sending service (SendGrid)
├── dependencies.py          # FastAPI dependency injection
├── main.py                  # FastAPI application entry point
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Registration, login, logout endpoints
│   ├── password.py         # Password reset endpoints
│   ├── token.py            # Token refresh endpoint
│   └── email.py            # Email verification endpoints
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md               # This file
```

## Database Schema

### Users Table
- `id` (UUID): Primary key
- `email` (String, unique): User email
- `username` (String, unique): Username for login
- `password_hash` (String): Bcrypt hashed password
- `is_verified` (Boolean): Email verification status
- `is_locked` (Boolean): Account lock status
- `locked_until` (DateTime): When account lock expires
- `created_at` (DateTime): Account creation timestamp
- `last_login` (DateTime): Last successful login timestamp

### Additional Tables
- **Roles**: Define user roles (user, admin, moderator)
- **Sessions**: Store active sessions with tokens
- **TokenBlacklist**: Revoked tokens
- **EmailVerification**: Email verification tokens
- **PasswordReset**: Password reset tokens
- **FailedLoginAttempt**: Track failed login attempts
- **AuditLog**: Complete audit trail of events

## Setup & Installation

### 1. Create Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Database Setup
```bash
# Create PostgreSQL database
createdb auth_db

# Run migrations (if using Alembic)
alembic upgrade head
```

### 5. Run Application
```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/logout` - Logout and revoke tokens

### Token Management
- `POST /api/v1/auth/refresh` - Refresh access token

### Password Management
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/verify` - Verify reset token and update password

### Email Verification
- `POST /api/v1/auth/email/verify` - Verify email with token
- `POST /api/v1/auth/email/resend-verification` - Resend verification email

## Configuration

Key configuration options in `config.py`:

```python
# Token expiry
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password policy
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

# Account protection
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Rate limiting
RATE_LIMIT_PER_USER = "10/minute"
RATE_LIMIT_PER_IP = "50/minute"
RATE_LIMIT_LOGIN = "5/minute"
RATE_LIMIT_REGISTER = "3/minute"
RATE_LIMIT_PASSWORD_RESET = "3/hour"
```

## Security Considerations

### Production Deployment
1. **HTTPS Only**: Enable HTTPS in production
2. **Secret Key**: Change SECRET_KEY to a strong, random value
3. **Database**: Use strong passwords and restrict access
4. **Redis**: Secure Redis instance with authentication
5. **Email Service**: Use SendGrid or similar service
6. **CORS**: Restrict allowed origins to your frontend domains
7. **Rate Limiting**: Adjust rates based on your traffic patterns
8. **Monitoring**: Set up alerts for suspicious activities

### Secrets Management
- Use environment variables for sensitive data
- Never commit `.env` file
- Rotate secrets regularly
- Use secure secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.)

## Testing

### Manual Testing with cURL

```bash
# Register user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'

# Refresh token
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token-here"
  }'
```

## Performance

- **Database Pooling**: Configured with min 5, max 20 connections
- **Token Caching**: RBAC roles cached for 5 minutes
- **Redis Failover**: In-memory cache if Redis unavailable
- **Rate Limiting**: Prevent abuse without blocking legitimate traffic
- **Audit Log Archival**: Old logs moved to cold storage after 90 days

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Invalid input
- `401`: Unauthorized
- `403`: Forbidden
- `409`: Conflict (duplicate email/username)
- `429`: Rate limit exceeded
- `500`: Internal server error

## Dependencies

- **fastapi**: Web framework
- **sqlalchemy**: ORM
- **psycopg2**: PostgreSQL driver
- **python-jose**: JWT handling
- **passlib**: Password hashing
- **redis**: Cache and token blacklist
- **slowapi**: Rate limiting
- **pydantic**: Data validation
- **python-multipart**: Form data parsing
- **cryptography**: Encryption

## License

MIT

## Support

For issues, feature requests, or questions, please open an issue or contact the development team.

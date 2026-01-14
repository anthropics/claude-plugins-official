# Plugin Usage Examples

This folder contains example projects demonstrating the pseudo-code prompting plugin in action.

## Examples

### create-auth-api-example

A complete end-to-end example showing the full workflow: transform → optimize → validate → fix → implement.

**What it demonstrates:**
- Natural language → pseudo-code transformation
- Optimization to add missing parameters
- Validation to catch security issues
- Iterative refinement based on validation feedback
- Implementation of production-ready authentication API

**Complete Session Transcript:**

```bash
# Step 1: Plugin installation
❯ /plugin marketplace add EladAriel/pseudo-code-prompting-plugin
  ⎿  Successfully added marketplace: pseudo-code-prompting

❯ /plugin install pseudo-code-prompting
  ⎿  (no content)

❯ /help
  ⎿  Help dialog dismissed

# Step 2: Initial transformation from natural language
❯ /pseudo-code-prompting:transform-query create an API for user authentication using python and fastapi

● create_api_authentication(framework="fastapi", language="python", auth_type="user_authentication")

# Step 3: Optimize to add missing security requirements
❯ /pseudo-code-prompting:optimize-prompt create_api_authentication(framework="fastapi", language="python", auth_type="user_authentication")

● Original:
  create_api_authentication(framework="fastapi", language="python", auth_type="user_authentication")

  Optimized:
  create_api_authentication(
    framework="fastapi",
    language="python",
    auth_type="user_authentication",
    auth_methods=["jwt", "password"],
    password_hashing="bcrypt",
    token_expiry="24h",
    request_schema={
      "username": "string:required:min(3):max(50)",
      "password": "string:required:min(8)"
    },
    response_schema={"access_token": "string", "token_type": "bearer", "expires_in": "seconds"},
    endpoints=[
      {"path": "/auth/register", "method": "POST", "auth": false},
      {"path": "/auth/login", "method": "POST", "auth": false},
      {"path": "/auth/logout", "method": "POST", "auth": true}
    ],
    error_responses={
      "400": "invalid_credentials",
      "409": "user_exists",
      "401": "unauthorized"
    },
    rate_limit="5/minute",
    validation=true,
    database="postgresql",
    logging=true
  )

  Improvements Made:
  ✓ Authentication Methods
    - Specified JWT + password authentication strategy
    - Added password hashing algorithm (bcrypt)
    - Defined token expiry time

  ✓ Data Validation
    - Added request schema with constraints (username/password requirements)
    - Defined response schema with token structure
    - Specified field types and limits

  ✓ API Endpoints
    - Listed required endpoints (register, login, logout)
    - Specified which endpoints require authentication
    - Defined HTTP methods

  ✓ Error Handling
    - Added specific error response codes
    - Mapped error scenarios (invalid credentials, user exists, unauthorized)

  ✓ Security
    - Added rate limiting to prevent brute force attacks
    - Enabled validation and logging
    - Specified secure password requirements

  ✓ Persistence & Infrastructure
    - Specified database backend (PostgreSQL)
    - Enabled logging for audit trail

  Rationale:
  - Clear authentication methods prevent ambiguity during implementation
  - Token expiry ensures security and reduces hijack window
  - Request/response schemas ensure consistent API contract
  - Explicit endpoint definitions guide development scope
  - Rate limiting and logging are essential security controls
  - Password constraints prevent weak credentials
  - Error responses enable proper client-side handling

# Step 4: Validate for completeness and security
❯ /pseudo-code-prompting:validate-requirements   create_api_authentication(
    framework="fastapi",
    language="python",
    auth_type="user_authentication",
    auth_methods=["jwt", "password"],
    password_hashing="bcrypt",
    token_expiry="24h",
    request_schema={
      "username": "string:required:min(3):max(50)",
      "password": "string:required:min(8)"
    },
    response_schema={"access_token": "string", "token_type": "bearer", "expires_in": "seconds"},
    endpoints=[
      {"path": "/auth/register", "method": "POST", "auth": false},
      {"path": "/auth/login", "method": "POST", "auth": false},
      {"path": "/auth/logout", "method": "POST", "auth": true}
    ],
    error_responses={
      "400": "invalid_credentials",
      "409": "user_exists",
      "401": "unauthorized"
    },
    rate_limit="5/minute",
    validation=true,
    database="postgresql",
    logging=true
  )

● Requirement Validation Report
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Function: create_api_authentication

  ✓ PASSED CHECKS
  - Authentication methods clearly specified (JWT + password)
  - Password hashing algorithm defined (bcrypt)
  - Request schema with validation constraints present
  - Response schema with token structure defined
  - API endpoints explicitly listed with methods
  - Error responses mapped to HTTP status codes
  - Rate limiting configured
  - Database backend specified
  - Logging enabled
  - Authorization checked on logout endpoint

  ⚠ WARNINGS (Medium Priority)
  - Token refresh strategy not specified (only expiry time)
    → Suggest adding: refresh_token_enabled=true, refresh_token_expiry="7d"
  - Email validation not specified for register endpoint
    → Suggest adding: email_validation="required:unique:format"
  - Password complexity rules could be more explicit
    → Suggest clarifying: password requirements include uppercase, numbers, special chars?
  - No HTTPS/TLS enforcement mentioned
    → Recommend adding: require_https=true
  - CORS configuration not specified
    → Suggest adding: cors={"allowed_origins": ["http://localhost:3000"], "credentials": true}
  - Session management strategy unclear
    → Clarify: stateless (JWT only) or stateful (server-side sessions)?
  - Email verification for new accounts not mentioned
    → Consider adding: email_verification=true, verification_expiry="24h"

  ✗ CRITICAL ISSUES (Must Fix)
  - Logout doesn't revoke tokens (stateless JWT limitation)
    → ACTION: Add token blacklist/revocation strategy: token_revocation="redis_blacklist"
  - No password reset/recovery flow defined
    → ACTION: Add: endpoints=[...] + {"path": "/auth/password-reset", "method": "POST", "auth": false}
  - No user role/permission system for authorization
    → ACTION: Add: authorization_scheme="role_based", roles=["user", "admin"]
  - Account lockout mechanism missing (brute force protection)
    → ACTION: Add: account_lockout={"max_attempts": 5, "lockout_duration": "30m"}
  - CSRF protection not specified
    → ACTION: Add: csrf_protection=true for state-changing operations

  📋 EDGE CASES TO CONSIDER
  - What happens if user tries to register with existing username? (409 defined ✓)
  - What if token expires mid-request? (401 defined ✓)
  - How are failed login attempts tracked for account lockout?
  - What if password reset email is not received?
  - How long are logs retained? Compliance requirements (GDPR)?
  - How are concurrent sessions handled? One per user or multiple?
  - What if database connection fails during registration?
  - Should rate limiting apply per IP, per username, or both?
  - How are old sessions invalidated after logout?
  - What about OAuth/social login integration in future?

  💡 RECOMMENDATIONS
  1. **Add Token Management**
     - refresh_token_enabled=true with separate expiry
     - token_type should include "refresh_token" response

  2. **Enhance Security**
     - Add account_lockout protection against brute force
     - Add token_revocation for logout functionality
     - Add csrf_protection for register/login endpoints
     - Require HTTPS in production

  3. **Complete User Journey**
     - Add password reset endpoint
     - Add email verification flow
     - Add account recovery mechanisms

  4. **Add Authorization**
     - Define role-based access control (RBAC)
     - Specify permission checks per endpoint

  5. **Improve Observability**
     - Add audit_logging for sensitive operations
     - Add metrics tracking for auth events
     - Specify log retention policy

  Overall Status: ⚠ NEEDS REVIEW

  Recommendation: Address CRITICAL ISSUES before implementation. The current spec covers basic authentication but lacks token revocation, password recovery, and brute-force protection essential for production APIs.

# Step 5: Generate new pseudo-code with recommendations
❯ write new psuedocode with recommendation

● Skill(pseudo-code-prompting:transform-query)
  ⎿  Successfully loaded skill

● create_production_authentication_api(framework="fastapi", language="python", auth_methods=["jwt", "password"], token_management={"access_expiry": "15m", "refresh_enabled": true, "refresh_expiry": "7d", "revocation": "redis_blacklist"}, password_security={"hashing": "bcrypt", "reset_flow": true, "complexity": {"min_length": 8, "require_uppercase": true, "require_numbers": true, "require_special_chars": true}}, email_verification={"enabled": true, "expiry": "24h"}, account_protection={"lockout_enabled": true, "max_attempts": 5, "lockout_duration": "30m", "brute_force_detection": "ip_and_username_tracking"}, authorization={"scheme": "rbac", "roles": ["user", "admin", "moderator"]}, csrf_protection=true, security_features={"https_required": true, "cors": {"allowed_origins": ["http://localhost:3000"], "credentials": true}}, audit_logging={"enabled": true, "track_events": ["login", "register", "password_reset", "logout", "failed_attempts"], "retention": "90d"})

# Step 6: Validate again to ensure all issues addressed
❯ can you validate this pseudocode?

● Skill(pseudo-code-prompting:validate-requirements)
  ⎿  Successfully loaded skill

● Requirement Validation Report
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Function: create_production_authentication_api

  ✓ PASSED CHECKS
  - Authentication methods fully specified (JWT + password)
  - Token management with access & refresh tokens defined
  - Password complexity rules explicit and comprehensive
  - Email verification flow with expiry time specified
  - Account lockout with max attempts and duration configured
  - Brute force detection using IP + username tracking
  - RBAC authorization scheme with defined roles
  - CSRF protection enabled
  - HTTPS enforcement in production
  - CORS configuration specified with credentials handling
  - Audit logging enabled with specific tracked events
  - Token revocation strategy via Redis blacklist
  - Log retention policy defined (90 days)

  ⚠ WARNINGS (Medium Priority)
  - Redis dependency not explicitly mentioned
    → Suggest adding: cache_backend="redis", redis_config={"host": "localhost", "port": 6379}
  - Email service provider not specified
    → Suggest adding: email_provider="sendgrid", email_config={"from": "noreply@app.com", "templates": "default"}
  - Database user storage not specified
    → Suggest adding: database="postgresql", user_table_schema={"id": "uuid", "email": "string:unique", "username": "string:unique", "password_hash": "string", "created_at": "timestamp", "last_login": "timestamp", "is_locked": "boolean"}
  - Input validation rules for endpoints not detailed
    → Suggest adding: input_validation={"email": "email:format:max(255)", "username": "alphanumeric:min(3):max(50)", "password": "string:min(8):max(128)"}
  - Rate limiting beyond lockout not specified
    → Suggest adding: rate_limiting={"per_user": "10/minute", "per_ip": "50/minute"}
  - MFA/2FA not included
    → Consider adding: multi_factor_auth={"enabled": false, "methods": ["totp", "email"]} (for future enhancement)
  - API versioning strategy unclear
    → Suggest adding: api_version="v1"
  - Response error codes not comprehensively mapped
    → Suggest clarifying all HTTP status codes: 200, 201, 400, 401, 403, 409, 429, 500

  ✗ CRITICAL ISSUES (Must Fix)
  - Password reset endpoint flow incomplete
    → ACTION: Add: endpoints=[...] + {"path": "/auth/password-reset", "method": "POST", "auth": false, "rate_limit": "3/hour"} and {"path": "/auth/password-reset/verify", "method": "POST", "auth": false}
  - Token rotation strategy not defined
    → ACTION: Add: token_rotation={"rotate_on_refresh": true, "invalidate_old_tokens": true}
  - Sensitive field encryption not specified
    → ACTION: Add: encryption={"enabled": true, "algorithm": "AES-256", "encrypt_fields": ["password_hash_salt", "email"]}
  - Database connection pooling not configured
    → ACTION: Add: database_pool={"min_size": 5, "max_size": 20, "timeout": "30s"}
  - Concurrent session handling not defined
    → ACTION: Add: session_management={"max_concurrent_sessions": 1, "invalidate_others_on_login": true}
  - API throttling/DDoS protection not specified
    → ACTION: Add: ddos_protection={"enabled": true, "strategies": ["rate_limiting", "account_lockout", "ip_blocking"]}

  📋 EDGE CASES TO CONSIDER
  - What if Redis is down during token revocation check?
    → Need fallback: fall back to in-memory cache or fail-secure mode
  - What if email verification email is marked as spam?
    → Need: resend verification endpoint with rate limiting
  - What if user tries to reset password while account is locked?
    → Need: clarify if account unlock via email or admin intervention
  - What if multiple concurrent password reset requests occur?
    → Need: invalidate previous reset tokens, use only latest
  - What if CORS origin changes in different environments?
    → Need: environment-based CORS configuration
  - What happens to refresh tokens if user changes password?
    → Need: all refresh tokens invalidated on password change
  - How to handle timezone differences in expiry calculations?
    → Need: specify UTC timezone enforcement
  - What if audit log database fills up?
    → Need: archival strategy beyond 90-day retention

  💡 RECOMMENDATIONS
  1. **Add Infrastructure Configuration**
     - Explicitly specify cache_backend (Redis)
     - Add database connection pooling config
     - Specify email service provider integration

  2. **Complete Token Management**
     - Add token rotation on refresh
     - Add old token invalidation strategy
     - Clarify concurrent session handling

  3. **Enhance Password Reset Flow**
     - Add dedicated password reset endpoints
     - Add reset token expiry (15-30 minutes suggested)
     - Add rate limiting on reset requests

  4. **Strengthen Data Protection**
     - Add encryption for sensitive fields
     - Specify database backup strategy
     - Add data anonymization for old audit logs

  5. **Improve Error Handling**
     - Map all HTTP status codes comprehensively
     - Add specific error messages (without leaking info)
     - Define fallback behaviors for external service failures

  6. **Add Performance Optimization**
     - Implement caching for role/permission lookups
     - Add query optimization hints for user lookups
     - Specify database indexes needed

  7. **Complete DDoS/Security**
     - Add explicit IP blocking mechanisms
     - Specify rate limiting per endpoint
     - Add suspicious activity detection

  Overall Status: ✓ READY WITH ENHANCEMENTS

  Recommendation: This is a comprehensive production-ready spec. Implement CRITICAL ISSUES before deployment. All PASSED CHECKS indicate excellent coverage of core authentication requirements. Address WARNINGS for robustness and add fallback mechanisms for external dependencies (Redis, email service).

# Step 7: Fix all critical issues
❯ can you fix the critical issues?

● Skill(pseudo-code-prompting:optimize-prompt)
  ⎿  Successfully loaded skill

● Original:
  create_production_authentication_api(framework="fastapi", language="python", auth_methods=["jwt", "password"], token_management={"access_expiry": "15m", "refresh_enabled": true, "refresh_expiry": "7d", "revocation": "redis_blacklist"}, password_security={"hashing": "bcrypt", "reset_flow": true, "complexity": {"min_length": 8, "require_uppercase": true, "require_numbers": true, "require_special_chars": true}}, email_verification={"enabled": true, "expiry": "24h"}, account_protection={"lockout_enabled": true, "max_attempts": 5, "lockout_duration": "30m", "brute_force_detection": "ip_and_username_tracking"}, authorization={"scheme": "rbac", "roles": ["user", "admin", "moderator"]}, csrf_protection=true, security_features={"https_required": true, "cors": {"allowed_origins": ["http://localhost:3000"], "credentials": true}}, audit_logging={"enabled": true, "track_events": ["login", "register", "password_reset", "logout", "failed_attempts"], "retention": "90d"})

  Optimized:
  create_production_authentication_api(
    framework="fastapi",
    language="python",
    api_version="v1",
    auth_methods=["jwt", "password"],
    token_management={
      "access_expiry": "15m",
      "refresh_enabled": true,
      "refresh_expiry": "7d",
      "revocation": "redis_blacklist",
      "rotation": {"rotate_on_refresh": true, "invalidate_old_tokens": true}
    },
    password_security={
      "hashing": "bcrypt",
      "reset_flow": true,
      "reset_endpoints": [
        {"path": "/auth/password-reset", "method": "POST", "auth": false, "rate_limit": "3/hour"},
        {"path": "/auth/password-reset/verify", "method": "POST", "auth": false, "rate_limit": "3/hour"}
      ],
      "reset_token_expiry": "30m",
      "complexity": {"min_length": 8, "require_uppercase": true, "require_numbers": true, "require_special_chars": true}
    },
    email_verification={
      "enabled": true,
      "expiry": "24h",
      "resend_endpoint": true,
      "resend_rate_limit": "5/hour"
    },
    account_protection={
      "lockout_enabled": true,
      "max_attempts": 5,
      "lockout_duration": "30m",
      "brute_force_detection": "ip_and_username_tracking"
    },
    authorization={
      "scheme": "rbac",
      "roles": ["user", "admin", "moderator"],
      "cache_ttl": "5m"
    },
    session_management={
      "max_concurrent_sessions": 1,
      "invalidate_others_on_login": true,
      "invalidate_on_password_change": true
    },
    encryption={
      "enabled": true,
      "algorithm": "AES-256",
      "encrypt_fields": ["password_hash_salt", "recovery_codes"]
    },
    database={
      "backend": "postgresql",
      "pool": {"min_size": 5, "max_size": 20, "timeout": "30s"},
      "schema": {
        "users": {
          "id": "uuid:primary_key",
          "email": "string:unique:required",
          "username": "string:unique:required",
          "password_hash": "string:encrypted:required",
          "created_at": "timestamp:required",
          "last_login": "timestamp:nullable",
          "is_locked": "boolean:default_false",
          "locked_until": "timestamp:nullable"
        }
      }
    },
    cache_backend="redis",
    redis_config={
      "host": "localhost",
      "port": 6379,
      "failover": "in_memory_fallback",
      "connection_timeout": "5s"
    },
    email_provider={
      "type": "sendgrid",
      "from": "noreply@app.com",
      "templates": "default",
      "retry_on_failure": true,
      "retry_attempts": 3
    },
    csrf_protection=true,
    rate_limiting={
      "per_user": "10/minute",
      "per_ip": "50/minute",
      "per_endpoint": {
        "login": "5/minute",
        "register": "3/minute",
        "password_reset": "3/hour"
      }
    },
    ddos_protection={
      "enabled": true,
      "strategies": ["rate_limiting", "account_lockout", "ip_blocking", "suspicious_activity_detection"],
      "ip_blocking_duration": "1h"
    },
    security_features={
      "https_required": true,
      "cors": {"allowed_origins": ["http://localhost:3000"], "credentials": true}
    },
    audit_logging={
      "enabled": true,
      "track_events": ["login", "register", "password_reset", "logout", "failed_attempts", "account_lock", "session_invalidation", "token_refresh"],
      "retention": "90d",
      "archival_strategy": "move_to_cold_storage"
    },
    error_responses={
      "200": "success",
      "201": "created",
      "400": "invalid_input",
      "401": "unauthorized",
      "403": "forbidden",
      "409": "conflict_duplicate",
      "429": "rate_limit_exceeded",
      "500": "internal_error"
    }
  )

  Improvements Made:
  ✓ Password Reset Flow - CRITICAL FIX
    - Added dedicated /auth/password-reset endpoint for initiating reset
    - Added /auth/password-reset/verify endpoint for token verification
    - Specified reset token expiry time (30 minutes)
    - Added rate limiting (3/hour) to prevent spam/abuse
    - Integrated with email provider for sending reset links

  ✓ Token Rotation Strategy - CRITICAL FIX
    - Added rotate_on_refresh flag to enable automatic token rotation
    - Added invalidate_old_tokens to revoke previous tokens after refresh
    - Ensures attackers can't use intercepted refresh tokens multiple times

  ✓ Sensitive Field Encryption - CRITICAL FIX
    - Added encryption section with AES-256 algorithm
    - Specified encrypt_fields for password_hash_salt and recovery_codes
    - Ensures sensitive data is protected at rest

  ✓ Database Connection Pooling - CRITICAL FIX
    - Added database pool configuration
    - min_size: 5 (maintain minimum connections)
    - max_size: 20 (prevent resource exhaustion)
    - timeout: 30s (connection acquisition timeout)
    - Prevents database connection starvation

  ✓ Concurrent Session Management - CRITICAL FIX
    - Added max_concurrent_sessions: 1 (one session per user)
    - Added invalidate_others_on_login flag to log out other sessions
    - Added invalidate_on_password_change to clear all refresh tokens on password change
    - Prevents session hijacking and unauthorized access

  ✓ DDoS/Security Protection - CRITICAL FIX
    - Added comprehensive ddos_protection with multiple strategies
    - Rate limiting, account lockout, IP blocking mechanisms
    - Suspicious activity detection enabled
    - Added ip_blocking_duration for temporary IP blocks

  ✓ Enhanced Database Schema
    - Added is_locked and locked_until fields for account lockout
    - Specified field constraints (unique, required, encrypted)
    - Added last_login tracking for security audits
    - Used UUID for primary key (security best practice)

  ✓ Redis Failover Strategy
    - Added failover configuration with in_memory_fallback
    - Added connection_timeout for better error handling
    - Ensures system stays operational if Redis is unavailable

  ✓ Email Service Resilience
    - Added retry_on_failure flag
    - Added retry_attempts: 3 for failed email sends
    - Ensures password reset emails are reliably delivered

  ✓ Comprehensive Error Responses
    - Mapped all HTTP status codes to error scenarios
    - Enables proper client-side error handling
    - Improves API usability and debugging

  ✓ Authorization Caching
    - Added cache_ttl: 5m for role/permission lookups
    - Reduces database load for RBAC checks
    - Improves API response time

  ✓ Enhanced Audit Logging
    - Added token_refresh, session_invalidation, account_lock events
    - Added archival_strategy for old logs
    - Ensures compliance and security forensics

  ✓ Email Verification Enhancements
    - Added resend_endpoint for users who don't receive verification email
    - Rate limited to 5/hour to prevent abuse
    - Improves user experience for initial registration

  Rationale:
  - Password Reset Flow: Enables users to recover accounts securely; prevents attackers from locking users out permanently
  - Token Rotation: Each refresh generates new tokens; if old token is stolen, it's automatically invalidated after one use
  - Field Encryption: Protects sensitive data if database is compromised; doesn't rely solely on password hashing
  - Connection Pooling: Prevents database from being overwhelmed; ensures consistent performance under load
  - Session Management: Single session per user prevents account takeover; password change invalidates all existing tokens
  - DDoS Protection: Multi-layered approach stops brute force, distributed attacks, and suspicious patterns
  - Redis Failover: System remains operational even if cache layer fails; graceful degradation to in-memory storage
  - Email Resilience: Retry mechanism ensures password reset emails are sent; prevents user lockout due to transient failures
  - Comprehensive Errors: Client applications can handle specific error conditions; improves debugging and user experience
  - Audit Trail: Complete record of auth events enables security incident investigation and compliance audits

  This enhanced pseudo-code now addresses all 6 critical issues and includes proper fallback mechanisms for production reliability.

✻ Cooked for 35s

# Step 8: Implementation in Python
❯ Implement in create-auth-api-example folder

[Implementation created complete FastAPI authentication system]

✓ Created complete FastAPI authentication system with:
  - 9 API endpoints (register, login, logout, password reset, token refresh, etc.)
  - PostgreSQL database models
  - Redis token revocation
  - JWT token management with rotation
  - Password complexity validation
  - Account lockout protection
  - RBAC authorization
  - Comprehensive security features
```

**Key Takeaways:**

1. **Iterative refinement**: Start simple, optimize, validate, fix issues
2. **Security-first**: Plugin catches missing security requirements automatically
3. **Production-ready**: Final pseudo-code includes all enterprise features
4. **90% compression**: Simple request → comprehensive structured specification
5. **Implementation clarity**: Pseudo-code translates directly to code structure

**Project Structure:**
- See [create-auth-api-example/](create-auth-api-example/) for full implementation

## Adding Your Own Examples

Feel free to add more examples showing different use cases:
- Database operations
- File processing
- Business logic
- Integration patterns
- etc.

## Note

These example projects are **separate from the plugin itself**. Claude Code only loads:
- `skills/`
- `agents/`
- `commands/`
- `hooks/`
- `plugin.json`

Examples in this folder won't affect the plugin's functionality.

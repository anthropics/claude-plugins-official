# API Exploration Template

Use this template to systematically document and test APIs during the Prepare phase.
Complete documentation here enables faster implementation in the Code phase.

---

## API Overview

```markdown
# API: [Service Name]

## Basic Information
| Property | Value |
|----------|-------|
| Provider | [Company/Organization] |
| Documentation | [URL] |
| Version | [API version] |
| Status | [Production/Beta/Deprecated] |
| Last Updated | [Date checked] |

## Base URLs
| Environment | URL |
|-------------|-----|
| Production | `https://api.example.com/v1` |
| Sandbox | `https://sandbox.api.example.com/v1` |
| Local Mock | `http://localhost:3001` |
```

---

## Authentication

### Authentication Method

```markdown
## Authentication Type: [Bearer Token / API Key / OAuth 2.0 / Basic Auth]

### Obtaining Credentials
1. [Step to get credentials]
2. [Step to configure]
3. [Step to test]

### Credential Storage
- Development: `.env` file (in `.gitignore`)
- Production: [Secrets manager / Environment variables]
```

### Authentication Examples

**Bearer Token:**
```bash
curl -X GET "https://api.example.com/v1/resource" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**API Key in Header:**
```bash
curl -X GET "https://api.example.com/v1/resource" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**OAuth 2.0 Token Exchange:**
```bash
curl -X POST "https://auth.example.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"
```

### Authentication Test Results

```markdown
## Auth Testing: [Date]

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Valid token | 200 OK | 200 OK | PASS |
| Expired token | 401 Unauthorized | 401 Unauthorized | PASS |
| Invalid token | 401 Unauthorized | 401 Unauthorized | PASS |
| Missing token | 401 Unauthorized | 403 Forbidden | INVESTIGATE |
```

---

## Rate Limits and Quotas

```markdown
## Rate Limiting

| Limit Type | Value | Window | Scope |
|------------|-------|--------|-------|
| Requests | 100 | Per minute | Per API key |
| Requests | 10,000 | Per day | Per account |
| Burst | 20 | Per second | Per API key |

### Rate Limit Headers
| Header | Description |
|--------|-------------|
| X-RateLimit-Limit | Max requests in window |
| X-RateLimit-Remaining | Remaining requests |
| X-RateLimit-Reset | Unix timestamp when limit resets |
| Retry-After | Seconds to wait (when rate limited) |

### Handling Rate Limits
```javascript
async function apiCallWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers['retry-after'] || 60;
        await sleep(retryAfter * 1000);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```
```

---

## Endpoints Documentation

### Endpoint Template

```markdown
## Endpoint: [Name]

**Purpose**: [What this endpoint does]

### Request
| Property | Value |
|----------|-------|
| Method | GET / POST / PUT / DELETE |
| Path | `/resource/{id}` |
| Auth Required | Yes / No |

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource identifier |

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| limit | integer | No | 20 | Items per page |
| sort | string | No | created_at | Sort field |

### Request Body (for POST/PUT)
```json
{
  "name": "string, required, max 100 chars",
  "email": "string, required, valid email",
  "metadata": {
    "key": "value, optional"
  }
}
```

### Response
**Success (200):**
```json
{
  "data": {
    "id": "abc123",
    "name": "Example",
    "email": "example@test.com",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "meta": {
    "request_id": "req_xyz"
  }
}
```

**Error (400):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "field": "email"
  }
}
```

### Example Request
```bash
curl -X POST "https://api.example.com/v1/users" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'
```

### Notes
- [Any special considerations]
- [Edge cases discovered]
```

---

## Endpoint Inventory

```markdown
## All Endpoints

### Users
| Method | Path | Purpose | Auth | Tested |
|--------|------|---------|------|--------|
| GET | /users | List users | Yes | Yes |
| GET | /users/:id | Get user | Yes | Yes |
| POST | /users | Create user | Yes | Yes |
| PUT | /users/:id | Update user | Yes | No |
| DELETE | /users/:id | Delete user | Yes | No |

### Orders
| Method | Path | Purpose | Auth | Tested |
|--------|------|---------|------|--------|
| GET | /orders | List orders | Yes | No |
| POST | /orders | Create order | Yes | No |

### Webhooks
| Event | Payload | Retry Policy |
|-------|---------|--------------|
| user.created | User object | 3x with backoff |
| order.completed | Order object | 3x with backoff |
```

---

## Error Handling

```markdown
## Error Response Format

### Standard Error Structure
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [
      {
        "field": "email",
        "message": "Invalid format"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

### Error Codes
| HTTP Status | Error Code | Description | Handling |
|-------------|------------|-------------|----------|
| 400 | VALIDATION_ERROR | Invalid input | Show field errors |
| 401 | UNAUTHORIZED | Invalid/expired auth | Refresh token or re-auth |
| 403 | FORBIDDEN | Insufficient permissions | Check user role |
| 404 | NOT_FOUND | Resource doesn't exist | Show not found UI |
| 409 | CONFLICT | Duplicate resource | Handle uniqueness |
| 422 | UNPROCESSABLE | Business rule violation | Show specific error |
| 429 | RATE_LIMITED | Too many requests | Implement backoff |
| 500 | INTERNAL_ERROR | Server error | Retry with backoff |
| 503 | SERVICE_UNAVAILABLE | Maintenance/overload | Retry with backoff |
```

---

## SDK and Libraries

```markdown
## Official SDKs
| Language | Package | Version | Docs |
|----------|---------|---------|------|
| JavaScript | @example/sdk | 2.1.0 | [Link] |
| Python | example-sdk | 2.1.0 | [Link] |

## SDK Installation
```bash
# JavaScript/Node.js
npm install @example/sdk

# Python
pip install example-sdk
```

## SDK Usage Example
```javascript
import { ExampleClient } from '@example/sdk';

const client = new ExampleClient({
  apiKey: process.env.EXAMPLE_API_KEY,
  environment: 'production'
});

const user = await client.users.get('user_123');
```
```

---

## Testing Notes

```markdown
## API Testing Results

### Test Date: [YYYY-MM-DD]
### Tested By: [Name]

## Environment
- Sandbox: https://sandbox.api.example.com/v1
- Test Account: [how to access]

## Test Results

### Happy Path Tests
| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Create user | 201, user object | 201, user object | PASS |
| Get user | 200, user object | 200, user object | PASS |
| List users | 200, array | 200, array | PASS |

### Error Path Tests
| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Invalid email | 400, validation error | 400, validation error | PASS |
| Duplicate email | 409, conflict | 422, unprocessable | INVESTIGATE |
| Unauthorized | 401 | 401 | PASS |

### Edge Cases
| Scenario | Expected | Actual | Notes |
|----------|----------|--------|-------|
| Empty name | 400 | 400 | Min length = 1 |
| Unicode name | 200 | 200 | Supports UTF-8 |
| Very long name | 400 | 200 (truncated) | Max length not enforced? |

### Discovered Issues
1. **Issue**: Duplicate email returns 422 instead of 409
   - **Impact**: Minor - error code differs from docs
   - **Workaround**: Handle both 409 and 422 for duplicates

2. **Issue**: Name field doesn't enforce max length
   - **Impact**: Low - could cause display issues
   - **Recommendation**: Enforce max length client-side
```

---

## Integration Checklist

```markdown
## Pre-Integration Checklist

### Credentials
- [ ] API credentials obtained
- [ ] Credentials stored in `.env` (added to `.gitignore`)
- [ ] Separate credentials for dev/staging/production

### Documentation
- [ ] All required endpoints documented
- [ ] Error codes and handling documented
- [ ] Rate limits understood and handling planned
- [ ] Authentication flow tested

### Architecture
- [ ] Backend proxy pattern planned (no credentials in frontend)
- [ ] Error handling strategy defined
- [ ] Retry/backoff strategy defined
- [ ] Logging and monitoring planned

### Testing
- [ ] Sandbox/test environment available
- [ ] Happy path tests passing
- [ ] Error path tests passing
- [ ] Rate limit handling tested

### Security
- [ ] HTTPS enforced
- [ ] API keys rotatable
- [ ] Webhook signatures verified
- [ ] Sensitive data handling reviewed
```

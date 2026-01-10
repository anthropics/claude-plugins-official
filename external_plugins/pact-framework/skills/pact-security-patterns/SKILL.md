---
name: pact-security-patterns
description: |
  Security best practices and threat mitigation patterns for PACT framework development.
  Use when: implementing authentication or authorization, handling API credentials,
  integrating external APIs, processing sensitive data (PII, financial, health),
  reviewing code for vulnerabilities, or enforcing SACROSANCT security rules.
  Triggers on: security audit, credential handling, OWASP, auth flows, encryption,
  data protection, backend proxy pattern, frontend credential exposure.
---

# PACT Security Patterns

Security guidance for PACT development phases. This skill provides essential security
patterns and links to detailed references for comprehensive implementation.

## SACROSANCT Rules (Non-Negotiable)

These rules are ABSOLUTE and must NEVER be violated.

### Rule 1: Credential Protection

**NEVER ALLOW in version control:**
- Actual API keys, tokens, passwords, or secrets
- Credentials in frontend code (VITE_, REACT_APP_, NEXT_PUBLIC_ prefixes)
- Real credential values in documentation or code examples
- Hardcoded secrets in any file committed to git

**ONLY acceptable locations for actual credentials:**

| Location | Example | Security Level |
|----------|---------|----------------|
| `.env` files in `.gitignore` | `API_KEY=sk-xxx` | Development |
| Server-side `process.env` | `process.env.API_KEY` | Runtime |
| Deployment platform secrets | Railway, Vercel, AWS | Production |
| Secrets managers | Vault, AWS Secrets Manager | Enterprise |

**In Documentation - Always Use Placeholders:**
```markdown
# Configuration
Set your API key in `.env`:
API_KEY=your_api_key_here
```

### Rule 2: Backend Proxy Pattern

```
WRONG:  Frontend --> External API (credentials in frontend)
CORRECT: Frontend --> Backend Proxy --> External API
```

**Architecture Requirements:**
- Frontend MUST NEVER have direct access to API credentials
- ALL API credentials MUST exist exclusively on server-side
- Frontend calls backend endpoints (`/api/resource`) without credentials
- Backend handles ALL authentication with external APIs
- Backend validates and sanitizes ALL requests from frontend

**Verification Checklist:**
```bash
# Build the application
npm run build

# Search for exposed credentials in bundle
grep -r "sk-" dist/assets/*.js
grep -r "api_key" dist/assets/*.js
grep -r "VITE_" dist/assets/*.js
# All above should return NO results
```

## Quick Security Reference

### Input Validation

**Always validate on the server side:**

```javascript
// Express.js example
const { body, validationResult } = require('express-validator');

app.post('/api/user',
  body('email').isEmail().normalizeEmail(),
  body('name').trim().escape().isLength({ min: 1, max: 100 }),
  body('age').isInt({ min: 0, max: 150 }),
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    // Process validated input
  }
);
```

### Output Encoding

**Prevent XSS by encoding output:**

```javascript
// React (automatic encoding)
return <div>{userInput}</div>; // Safe - React escapes

// Dangerous - avoid unless absolutely necessary
return <div dangerouslySetInnerHTML={{__html: userInput}} />; // UNSAFE

// Node.js HTML response
const escapeHtml = (str) => str
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#039;');
```

### SQL Injection Prevention

**Always use parameterized queries:**

```javascript
// WRONG - SQL Injection vulnerable
const query = `SELECT * FROM users WHERE id = ${userId}`;

// CORRECT - Parameterized query
const query = 'SELECT * FROM users WHERE id = $1';
const result = await db.query(query, [userId]);

// ORM example (Prisma)
const user = await prisma.user.findUnique({
  where: { id: userId }  // Safe - Prisma handles escaping
});
```

### Authentication Security

**Password Storage:**
```javascript
const bcrypt = require('bcrypt');

// Hashing password
const saltRounds = 12;  // Minimum recommended
const hashedPassword = await bcrypt.hash(password, saltRounds);

// Verifying password
const isValid = await bcrypt.compare(password, hashedPassword);
```

**Session Configuration:**
```javascript
app.use(session({
  secret: process.env.SESSION_SECRET,  // Strong, random secret
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,       // HTTPS only
    httpOnly: true,     // No JavaScript access
    sameSite: 'strict', // CSRF protection
    maxAge: 3600000     // 1 hour
  }
}));
```

## Security Headers

**Essential HTTP headers:**

```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"]
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true
  }
}));
```

## Rate Limiting

**Protect against abuse:**

```javascript
const rateLimit = require('express-rate-limit');

// General API rate limit
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  message: { error: 'Too many requests, please try again later' }
});

// Stricter limit for auth endpoints
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 5,
  message: { error: 'Too many login attempts' }
});

app.use('/api/', apiLimiter);
app.use('/api/auth/', authLimiter);
```

## Security Checklist

Before any commit or deployment, verify:

### Credential Protection
- [ ] No credentials in staged files (`git diff --staged | grep -i "key\|secret\|password"`)
- [ ] `.env` files listed in `.gitignore`
- [ ] Placeholders used in all documentation
- [ ] No hardcoded API keys in source code

### Architecture
- [ ] Frontend makes NO direct external API calls with credentials
- [ ] Backend proxy pattern implemented for all external integrations
- [ ] All credentials loaded from environment variables

### Input/Output
- [ ] All user inputs validated server-side
- [ ] SQL queries use parameterized statements
- [ ] HTML output properly encoded
- [ ] File uploads validated for type and size

### Authentication
- [ ] Passwords hashed with bcrypt (12+ rounds)
- [ ] Sessions configured with secure flags
- [ ] Authentication endpoints rate-limited
- [ ] JWT tokens have short expiration

### Headers and Transport
- [ ] Security headers configured (use Helmet.js or equivalent)
- [ ] HTTPS enforced in production
- [ ] CORS configured restrictively

## Detailed References

For comprehensive security guidance, see:

- **OWASP Top 10 Mitigations**: [references/owasp-top-10.md](references/owasp-top-10.md)
  - Detailed vulnerability descriptions
  - Code examples for each mitigation
  - Testing approaches

- **Authentication Patterns**: [references/authentication-patterns.md](references/authentication-patterns.md)
  - JWT implementation
  - Session management
  - OAuth 2.0 flows
  - Multi-factor authentication

- **Data Protection**: [references/data-protection.md](references/data-protection.md)
  - Encryption at rest and in transit
  - PII handling requirements
  - GDPR compliance patterns
  - Key management

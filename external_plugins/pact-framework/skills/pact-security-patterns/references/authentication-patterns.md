# Authentication Patterns

Comprehensive guide to implementing secure authentication in web applications.
Covers JWT, sessions, OAuth 2.0, and multi-factor authentication patterns.

## Overview

| Pattern | Use Case | Stateless | Scalability |
|---------|----------|-----------|-------------|
| JWT | APIs, SPAs, Mobile | Yes | Excellent |
| Sessions | Traditional web apps | No | Good with Redis |
| OAuth 2.0 | Third-party auth | Varies | Excellent |
| API Keys | Service-to-service | Yes | Excellent |

---

## JWT (JSON Web Tokens)

### Token Structure

```
Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.  (Header)
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6I.  (Payload)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  (Signature)
```

### Secure JWT Implementation

```javascript
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

class JWTService {
  constructor() {
    // Use RS256 for production (asymmetric)
    // HS256 acceptable for simpler setups with proper key management
    this.algorithm = 'RS256';
    this.privateKey = process.env.JWT_PRIVATE_KEY;
    this.publicKey = process.env.JWT_PUBLIC_KEY;

    // Token lifetimes
    this.accessTokenExpiry = '15m';   // Short-lived
    this.refreshTokenExpiry = '7d';   // Longer-lived
  }

  generateAccessToken(user) {
    return jwt.sign(
      {
        sub: user.id,
        email: user.email,
        roles: user.roles,
        type: 'access'
      },
      this.privateKey,
      {
        algorithm: this.algorithm,
        expiresIn: this.accessTokenExpiry,
        issuer: 'myapp.com',
        audience: 'myapp.com'
      }
    );
  }

  generateRefreshToken(user) {
    const tokenId = crypto.randomUUID();

    const token = jwt.sign(
      {
        sub: user.id,
        jti: tokenId,  // Unique token ID for revocation
        type: 'refresh'
      },
      this.privateKey,
      {
        algorithm: this.algorithm,
        expiresIn: this.refreshTokenExpiry,
        issuer: 'myapp.com'
      }
    );

    // Store token ID for revocation capability
    this.storeRefreshTokenId(user.id, tokenId);

    return token;
  }

  verifyToken(token) {
    try {
      return jwt.verify(token, this.publicKey, {
        algorithms: [this.algorithm],
        issuer: 'myapp.com',
        audience: 'myapp.com'
      });
    } catch (error) {
      if (error.name === 'TokenExpiredError') {
        throw new Error('Token expired');
      }
      if (error.name === 'JsonWebTokenError') {
        throw new Error('Invalid token');
      }
      throw error;
    }
  }

  async revokeRefreshToken(tokenId) {
    // Add to blacklist or remove from whitelist
    await this.db.revokedTokens.create({
      tokenId,
      revokedAt: new Date()
    });
  }

  async isTokenRevoked(tokenId) {
    const revoked = await this.db.revokedTokens.findUnique({
      where: { tokenId }
    });
    return !!revoked;
  }
}
```

### JWT Middleware

```javascript
const authenticateJWT = async (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.split(' ')[1];

  try {
    const payload = jwtService.verifyToken(token);

    // Check token type
    if (payload.type !== 'access') {
      return res.status(401).json({ error: 'Invalid token type' });
    }

    // Optionally verify user still exists/active
    const user = await userService.findById(payload.sub);
    if (!user || !user.isActive) {
      return res.status(401).json({ error: 'User not found or inactive' });
    }

    req.user = {
      id: payload.sub,
      email: payload.email,
      roles: payload.roles
    };

    next();
  } catch (error) {
    return res.status(401).json({ error: error.message });
  }
};
```

### Token Refresh Flow

```javascript
app.post('/api/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    return res.status(400).json({ error: 'Refresh token required' });
  }

  try {
    const payload = jwtService.verifyToken(refreshToken);

    if (payload.type !== 'refresh') {
      return res.status(401).json({ error: 'Invalid token type' });
    }

    // Check if token is revoked
    if (await jwtService.isTokenRevoked(payload.jti)) {
      return res.status(401).json({ error: 'Token revoked' });
    }

    const user = await userService.findById(payload.sub);
    if (!user || !user.isActive) {
      return res.status(401).json({ error: 'User not found' });
    }

    // Rotate refresh token (invalidate old, issue new)
    await jwtService.revokeRefreshToken(payload.jti);

    const newAccessToken = jwtService.generateAccessToken(user);
    const newRefreshToken = jwtService.generateRefreshToken(user);

    res.json({
      accessToken: newAccessToken,
      refreshToken: newRefreshToken
    });
  } catch (error) {
    return res.status(401).json({ error: 'Invalid refresh token' });
  }
});
```

---

## Session-Based Authentication

### Secure Session Configuration

```javascript
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { createClient } = require('redis');

// Redis client for session storage
const redisClient = createClient({
  url: process.env.REDIS_URL
});
redisClient.connect();

app.use(session({
  store: new RedisStore({ client: redisClient }),

  // Strong, unique secret from environment
  secret: process.env.SESSION_SECRET,

  // Security settings
  name: 'sessionId',  // Custom name (not default 'connect.sid')
  resave: false,
  saveUninitialized: false,

  cookie: {
    secure: process.env.NODE_ENV === 'production',  // HTTPS only in prod
    httpOnly: true,   // No JavaScript access
    sameSite: 'strict',  // CSRF protection
    maxAge: 1000 * 60 * 60,  // 1 hour
    domain: '.example.com'  // Restrict to domain
  },

  // Regenerate session ID on auth state changes
  genid: () => crypto.randomUUID()
}));
```

### Session Authentication Flow

```javascript
// Login
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;

  const user = await userService.findByEmail(email);
  if (!user) {
    // Use same message to prevent enumeration
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const isValid = await bcrypt.compare(password, user.passwordHash);
  if (!isValid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Regenerate session to prevent fixation
  req.session.regenerate((err) => {
    if (err) {
      return res.status(500).json({ error: 'Session error' });
    }

    req.session.userId = user.id;
    req.session.createdAt = Date.now();

    res.json({ message: 'Login successful' });
  });
});

// Logout
app.post('/api/auth/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Logout failed' });
    }
    res.clearCookie('sessionId');
    res.json({ message: 'Logged out' });
  });
});

// Session middleware
const requireSession = (req, res, next) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  // Optional: Check session age for re-authentication
  const sessionAge = Date.now() - req.session.createdAt;
  const maxAge = 1000 * 60 * 60 * 24;  // 24 hours

  if (sessionAge > maxAge) {
    req.session.destroy();
    return res.status(401).json({ error: 'Session expired' });
  }

  next();
};
```

---

## OAuth 2.0 / OpenID Connect

### OAuth 2.0 Authorization Code Flow

```javascript
const { Issuer, generators } = require('openid-client');

class OAuthService {
  async initialize() {
    // Discover provider configuration
    const issuer = await Issuer.discover('https://accounts.google.com');

    this.client = new issuer.Client({
      client_id: process.env.GOOGLE_CLIENT_ID,
      client_secret: process.env.GOOGLE_CLIENT_SECRET,
      redirect_uris: ['https://myapp.com/api/auth/callback'],
      response_types: ['code']
    });
  }

  getAuthorizationUrl(state, nonce) {
    return this.client.authorizationUrl({
      scope: 'openid email profile',
      state,
      nonce,
      // PKCE for additional security
      code_challenge: generators.codeChallenge(this.codeVerifier),
      code_challenge_method: 'S256'
    });
  }

  async handleCallback(code, codeVerifier) {
    const tokenSet = await this.client.callback(
      'https://myapp.com/api/auth/callback',
      { code },
      { code_verifier: codeVerifier }
    );

    // Verify ID token claims
    const claims = tokenSet.claims();

    return {
      accessToken: tokenSet.access_token,
      idToken: tokenSet.id_token,
      email: claims.email,
      name: claims.name,
      sub: claims.sub  // Provider's unique user ID
    };
  }
}
```

### OAuth Routes

```javascript
// Initiate OAuth flow
app.get('/api/auth/google', (req, res) => {
  const state = crypto.randomUUID();
  const nonce = crypto.randomUUID();
  const codeVerifier = generators.codeVerifier();

  // Store in session for verification
  req.session.oauthState = state;
  req.session.oauthNonce = nonce;
  req.session.codeVerifier = codeVerifier;

  const authUrl = oauthService.getAuthorizationUrl(state, nonce);
  res.redirect(authUrl);
});

// Handle OAuth callback
app.get('/api/auth/callback', async (req, res) => {
  const { code, state, error } = req.query;

  // Check for errors
  if (error) {
    return res.redirect('/login?error=oauth_error');
  }

  // Verify state to prevent CSRF
  if (state !== req.session.oauthState) {
    return res.redirect('/login?error=invalid_state');
  }

  try {
    const tokenData = await oauthService.handleCallback(
      code,
      req.session.codeVerifier
    );

    // Find or create user
    let user = await userService.findByOAuthId('google', tokenData.sub);

    if (!user) {
      user = await userService.createFromOAuth({
        provider: 'google',
        providerId: tokenData.sub,
        email: tokenData.email,
        name: tokenData.name
      });
    }

    // Clear OAuth session data
    delete req.session.oauthState;
    delete req.session.oauthNonce;
    delete req.session.codeVerifier;

    // Create session
    req.session.regenerate((err) => {
      req.session.userId = user.id;
      res.redirect('/dashboard');
    });
  } catch (error) {
    console.error('OAuth error:', error);
    res.redirect('/login?error=callback_failed');
  }
});
```

---

## Multi-Factor Authentication (MFA)

### TOTP Implementation

```javascript
const speakeasy = require('speakeasy');
const qrcode = require('qrcode');

class MFAService {
  generateSecret(userEmail) {
    const secret = speakeasy.generateSecret({
      name: `MyApp (${userEmail})`,
      issuer: 'MyApp',
      length: 32
    });

    return {
      secret: secret.base32,
      otpauthUrl: secret.otpauth_url
    };
  }

  async generateQRCode(otpauthUrl) {
    return qrcode.toDataURL(otpauthUrl);
  }

  verifyToken(secret, token) {
    return speakeasy.totp.verify({
      secret,
      encoding: 'base32',
      token,
      window: 1  // Allow 1 step before/after for clock drift
    });
  }
}

// Enable MFA
app.post('/api/auth/mfa/enable', authenticate, async (req, res) => {
  const { secret, otpauthUrl } = mfaService.generateSecret(req.user.email);

  // Store secret temporarily (not yet verified)
  await userService.setMFAPending(req.user.id, secret);

  const qrCode = await mfaService.generateQRCode(otpauthUrl);

  res.json({
    qrCode,
    secret  // Also provide for manual entry
  });
});

// Verify MFA setup
app.post('/api/auth/mfa/verify', authenticate, async (req, res) => {
  const { token } = req.body;

  const pendingSecret = await userService.getMFAPending(req.user.id);
  if (!pendingSecret) {
    return res.status(400).json({ error: 'No MFA setup in progress' });
  }

  if (!mfaService.verifyToken(pendingSecret, token)) {
    return res.status(400).json({ error: 'Invalid token' });
  }

  // Generate backup codes
  const backupCodes = Array(10).fill(null)
    .map(() => crypto.randomBytes(4).toString('hex'));

  await userService.enableMFA(req.user.id, pendingSecret, backupCodes);

  res.json({
    message: 'MFA enabled',
    backupCodes  // Show once, user must save
  });
});

// Login with MFA
app.post('/api/auth/login', async (req, res) => {
  const { email, password, mfaToken } = req.body;

  const user = await userService.findByEmail(email);
  if (!user || !await bcrypt.compare(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Check if MFA is required
  if (user.mfaEnabled) {
    if (!mfaToken) {
      return res.status(200).json({
        requiresMFA: true,
        message: 'MFA token required'
      });
    }

    if (!mfaService.verifyToken(user.mfaSecret, mfaToken)) {
      // Check backup codes
      const isBackupCode = await userService.useBackupCode(user.id, mfaToken);
      if (!isBackupCode) {
        return res.status(401).json({ error: 'Invalid MFA token' });
      }
    }
  }

  // Create session/token
  req.session.userId = user.id;
  res.json({ message: 'Login successful' });
});
```

---

## Password Security

### Password Requirements

```javascript
const Joi = require('joi');
const hibp = require('hibp');

const passwordSchema = Joi.string()
  .min(12)
  .max(128)
  .pattern(/[A-Z]/, 'uppercase')
  .pattern(/[a-z]/, 'lowercase')
  .pattern(/[0-9]/, 'number')
  .pattern(/[^A-Za-z0-9]/, 'special')
  .required()
  .messages({
    'string.min': 'Password must be at least 12 characters',
    'string.pattern.name': 'Password must contain at least one {#name} character'
  });

async function validatePassword(password, email) {
  // Basic validation
  const { error } = passwordSchema.validate(password);
  if (error) {
    throw new Error(error.message);
  }

  // Check for email in password
  if (password.toLowerCase().includes(email.split('@')[0].toLowerCase())) {
    throw new Error('Password cannot contain your email');
  }

  // Check against breached passwords
  const breachCount = await hibp.pwnedPassword(password);
  if (breachCount > 0) {
    throw new Error('This password has been found in data breaches. Please choose a different password.');
  }

  return true;
}
```

### Password Hashing

```javascript
const bcrypt = require('bcrypt');

const SALT_ROUNDS = 12;  // Minimum recommended

async function hashPassword(password) {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password, hash) {
  return bcrypt.compare(password, hash);
}

// Password reset with secure token
async function initiatePasswordReset(email) {
  const user = await userService.findByEmail(email);

  // Always return success (prevent enumeration)
  if (!user) return;

  const token = crypto.randomBytes(32).toString('hex');
  const hashedToken = crypto.createHash('sha256').update(token).digest('hex');

  await userService.setPasswordResetToken(user.id, hashedToken, Date.now() + 3600000);

  // Send email with unhashed token
  await emailService.sendPasswordReset(email, token);
}

async function completePasswordReset(token, newPassword) {
  const hashedToken = crypto.createHash('sha256').update(token).digest('hex');

  const user = await userService.findByResetToken(hashedToken);
  if (!user || user.resetTokenExpiry < Date.now()) {
    throw new Error('Invalid or expired reset token');
  }

  await validatePassword(newPassword, user.email);
  const hashedPassword = await hashPassword(newPassword);

  await userService.updatePassword(user.id, hashedPassword);
  await userService.clearResetToken(user.id);

  // Invalidate all sessions
  await sessionService.revokeAllUserSessions(user.id);
}
```

---

## API Key Authentication

```javascript
class APIKeyService {
  async generateAPIKey(userId, name) {
    // Generate random key
    const rawKey = `pk_${crypto.randomBytes(32).toString('hex')}`;

    // Store only the hash
    const hashedKey = crypto.createHash('sha256').update(rawKey).digest('hex');
    const prefix = rawKey.substring(0, 8);  // For identification

    await this.db.apiKeys.create({
      userId,
      name,
      prefix,
      hashedKey,
      createdAt: new Date()
    });

    // Return raw key ONCE - cannot be retrieved later
    return rawKey;
  }

  async validateAPIKey(rawKey) {
    if (!rawKey.startsWith('pk_')) {
      return null;
    }

    const hashedKey = crypto.createHash('sha256').update(rawKey).digest('hex');

    const apiKey = await this.db.apiKeys.findFirst({
      where: { hashedKey, isActive: true }
    });

    if (apiKey) {
      // Update last used
      await this.db.apiKeys.update({
        where: { id: apiKey.id },
        data: { lastUsedAt: new Date() }
      });
    }

    return apiKey;
  }
}

// API Key middleware
const authenticateAPIKey = async (req, res, next) => {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  const keyData = await apiKeyService.validateAPIKey(apiKey);
  if (!keyData) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  req.apiKeyId = keyData.id;
  req.userId = keyData.userId;

  next();
};
```

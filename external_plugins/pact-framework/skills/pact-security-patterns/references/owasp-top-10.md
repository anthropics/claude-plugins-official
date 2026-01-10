# OWASP Top 10 Mitigations (2021)

Comprehensive guide to understanding and mitigating the OWASP Top 10 vulnerabilities
in web applications. Each section includes vulnerability description, real-world impact,
mitigation patterns, and code examples.

## A01:2021 - Broken Access Control

**Description**: Users can act outside their intended permissions. This includes
accessing other users' data, modifying access rights, or performing privileged actions.

**Impact**: Data theft, unauthorized modifications, complete system compromise.

### Mitigation Patterns

**1. Deny by Default**
```javascript
// Middleware that denies access unless explicitly granted
const accessControl = (requiredPermission) => {
  return (req, res, next) => {
    const userPermissions = req.user?.permissions || [];

    if (!userPermissions.includes(requiredPermission)) {
      return res.status(403).json({
        error: 'Access denied',
        required: requiredPermission
      });
    }
    next();
  };
};

// Usage
app.delete('/api/users/:id',
  authenticate,
  accessControl('users:delete'),
  deleteUserHandler
);
```

**2. Resource Ownership Verification**
```javascript
// Always verify the user owns the resource
app.get('/api/documents/:id', authenticate, async (req, res) => {
  const document = await Document.findById(req.params.id);

  if (!document) {
    return res.status(404).json({ error: 'Not found' });
  }

  // CRITICAL: Verify ownership
  if (document.ownerId !== req.user.id) {
    // Log potential attack
    logger.warn('Access denied', {
      userId: req.user.id,
      documentId: req.params.id,
      documentOwner: document.ownerId
    });
    return res.status(403).json({ error: 'Access denied' });
  }

  res.json(document);
});
```

**3. IDOR Prevention**
```javascript
// Use UUIDs instead of sequential IDs
const { v4: uuidv4 } = require('uuid');

const document = new Document({
  id: uuidv4(),  // Random, unpredictable ID
  ownerId: req.user.id,
  content: req.body.content
});
```

---

## A02:2021 - Cryptographic Failures

**Description**: Failures related to cryptography that expose sensitive data, including
weak algorithms, improper key management, and missing encryption.

**Impact**: Data breaches, identity theft, regulatory violations.

### Mitigation Patterns

**1. Encryption at Rest**
```javascript
const crypto = require('crypto');

class FieldEncryption {
  constructor(key) {
    // Key should be 256 bits (32 bytes) for AES-256
    this.key = Buffer.from(key, 'hex');
    this.algorithm = 'aes-256-gcm';
  }

  encrypt(plaintext) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    // Return IV + AuthTag + Ciphertext
    return iv.toString('hex') + ':' +
           authTag.toString('hex') + ':' +
           encrypted;
  }

  decrypt(encryptedData) {
    const parts = encryptedData.split(':');
    const iv = Buffer.from(parts[0], 'hex');
    const authTag = Buffer.from(parts[1], 'hex');
    const encrypted = parts[2];

    const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// Usage for PII
const encryption = new FieldEncryption(process.env.ENCRYPTION_KEY);
const encryptedSSN = encryption.encrypt('123-45-6789');
```

**2. Secure Key Management**
```javascript
// Load encryption keys from secure source
const loadEncryptionKey = async () => {
  if (process.env.NODE_ENV === 'production') {
    // Use AWS Secrets Manager, HashiCorp Vault, etc.
    const secret = await secretsManager.getSecret('encryption-key');
    return secret.value;
  }
  // Development only - never use in production
  return process.env.ENCRYPTION_KEY;
};
```

**3. TLS Configuration**
```javascript
const https = require('https');
const fs = require('fs');

const server = https.createServer({
  key: fs.readFileSync('private-key.pem'),
  cert: fs.readFileSync('certificate.pem'),

  // TLS 1.2+ only
  minVersion: 'TLSv1.2',

  // Strong cipher suites
  ciphers: [
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384'
  ].join(':')
}, app);
```

---

## A03:2021 - Injection

**Description**: Untrusted data is sent to an interpreter as part of a command or query,
allowing attackers to execute unintended commands or access unauthorized data.

**Impact**: Data theft, data corruption, system compromise, denial of service.

### Mitigation Patterns

**1. SQL Injection Prevention**
```javascript
// VULNERABLE
const getUser = async (userId) => {
  const query = `SELECT * FROM users WHERE id = '${userId}'`;
  return db.query(query);  // NEVER DO THIS
};

// SECURE - Parameterized query
const getUser = async (userId) => {
  const query = 'SELECT * FROM users WHERE id = $1';
  return db.query(query, [userId]);
};

// SECURE - ORM with Prisma
const getUser = async (userId) => {
  return prisma.user.findUnique({
    where: { id: userId }
  });
};
```

**2. NoSQL Injection Prevention**
```javascript
// VULNERABLE - MongoDB
const findUser = async (username, password) => {
  return db.users.findOne({
    username: username,
    password: password  // If password is { $gt: '' }, bypasses auth
  });
};

// SECURE - Validate types
const findUser = async (username, password) => {
  if (typeof username !== 'string' || typeof password !== 'string') {
    throw new Error('Invalid input type');
  }

  const hashedPassword = await bcrypt.hash(password, 12);
  return db.users.findOne({
    username: { $eq: username },  // Explicit equality
    password: hashedPassword
  });
};
```

**3. Command Injection Prevention**
```javascript
const { execFile } = require('child_process');

// VULNERABLE
const runCommand = (userInput) => {
  exec(`convert ${userInput} output.png`);  // NEVER DO THIS
};

// SECURE - Use execFile with explicit arguments
const runCommand = (filename) => {
  // Validate filename
  if (!/^[a-zA-Z0-9_-]+\.(jpg|png)$/.test(filename)) {
    throw new Error('Invalid filename');
  }

  execFile('convert', [filename, 'output.png'], (error, stdout, stderr) => {
    if (error) {
      logger.error('Command failed', { error });
    }
  });
};
```

**4. LDAP Injection Prevention**
```javascript
// Escape LDAP special characters
const escapeLdap = (str) => {
  return str.replace(/[\\*()]/g, (char) => '\\' + char.charCodeAt(0).toString(16));
};

const searchUser = async (username) => {
  const escaped = escapeLdap(username);
  const filter = `(uid=${escaped})`;
  return ldapClient.search('ou=users,dc=example,dc=com', { filter });
};
```

---

## A04:2021 - Insecure Design

**Description**: Missing or ineffective security controls at the design level.
This is a broad category focusing on design and architectural flaws.

**Impact**: Systemic vulnerabilities that cannot be fixed with code changes alone.

### Mitigation Patterns

**1. Threat Modeling**
```markdown
## Threat Model Template

### Asset Identification
- User credentials
- Payment information
- Personal data

### Threat Actors
- External attackers
- Malicious insiders
- Automated bots

### Attack Vectors
| Asset | Threat | Mitigation |
|-------|--------|------------|
| Credentials | Brute force | Rate limiting, MFA |
| Payment data | Data theft | Encryption, PCI compliance |
| Personal data | Unauthorized access | RBAC, audit logging |
```

**2. Secure Business Logic**
```javascript
// Business logic abuse prevention
class OrderService {
  async createOrder(userId, items, couponCode) {
    // Validate coupon usage
    if (couponCode) {
      const usage = await this.getCouponUsage(userId, couponCode);
      if (usage >= 1) {
        throw new Error('Coupon already used');
      }
    }

    // Validate inventory before order
    for (const item of items) {
      const stock = await this.getStock(item.productId);
      if (stock < item.quantity) {
        throw new Error(`Insufficient stock for ${item.productId}`);
      }
    }

    // Use transaction for consistency
    return this.db.transaction(async (tx) => {
      const order = await tx.orders.create({ userId, items });
      await tx.inventory.decrementMany(items);
      if (couponCode) {
        await tx.couponUsage.create({ userId, couponCode });
      }
      return order;
    });
  }
}
```

---

## A05:2021 - Security Misconfiguration

**Description**: Missing or improper security hardening across the application stack,
including default configurations, open cloud storage, verbose error messages.

**Impact**: Unauthorized access, information disclosure, system compromise.

### Mitigation Patterns

**1. Environment Configuration**
```javascript
// config/security.js
const securityConfig = {
  development: {
    verboseErrors: true,
    csrfEnabled: false,
    rateLimit: { max: 1000 }
  },
  production: {
    verboseErrors: false,
    csrfEnabled: true,
    rateLimit: { max: 100 }
  }
};

// Use environment-specific config
const config = securityConfig[process.env.NODE_ENV] || securityConfig.production;
```

**2. Error Handling**
```javascript
// Global error handler - hide internal errors in production
app.use((err, req, res, next) => {
  const errorId = uuidv4();

  // Always log full error
  logger.error('Request error', {
    errorId,
    error: err.message,
    stack: err.stack,
    path: req.path,
    userId: req.user?.id
  });

  // Return sanitized response
  if (process.env.NODE_ENV === 'production') {
    res.status(500).json({
      error: 'An error occurred',
      errorId  // For support reference
    });
  } else {
    res.status(500).json({
      error: err.message,
      stack: err.stack,
      errorId
    });
  }
});
```

**3. Security Headers Checklist**
```javascript
// Verify all security headers are set
const requiredHeaders = [
  'X-Content-Type-Options',
  'X-Frame-Options',
  'X-XSS-Protection',
  'Strict-Transport-Security',
  'Content-Security-Policy'
];

// Test in integration tests
describe('Security Headers', () => {
  it('should include all required security headers', async () => {
    const response = await request(app).get('/');

    requiredHeaders.forEach(header => {
      expect(response.headers[header.toLowerCase()]).toBeDefined();
    });
  });
});
```

---

## A06:2021 - Vulnerable and Outdated Components

**Description**: Using components with known vulnerabilities or failing to update
components in a timely manner.

**Impact**: Application compromise through exploiting known CVEs.

### Mitigation Patterns

**1. Dependency Auditing**
```bash
# Regular security audits
npm audit
npm audit fix

# Use Snyk for deeper analysis
npx snyk test

# GitHub Dependabot (in .github/dependabot.yml)
```

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

**2. Version Pinning with Audit**
```json
{
  "scripts": {
    "preinstall": "npm audit --audit-level=high",
    "postinstall": "npm audit"
  }
}
```

---

## A07:2021 - Identification and Authentication Failures

**Description**: Weaknesses in authentication mechanisms, including weak passwords,
session management issues, and credential stuffing vulnerabilities.

**Impact**: Account takeover, identity theft, unauthorized access.

### Mitigation Patterns

See [authentication-patterns.md](authentication-patterns.md) for comprehensive coverage.

**Quick Reference:**
```javascript
// Password requirements
const passwordSchema = Joi.string()
  .min(12)
  .pattern(/[A-Z]/)  // Uppercase
  .pattern(/[a-z]/)  // Lowercase
  .pattern(/[0-9]/)  // Number
  .pattern(/[^A-Za-z0-9]/)  // Special char
  .required();

// Check against breached passwords
const hibp = require('hibp');
const isBreached = await hibp.pwnedPassword(password) > 0;
```

---

## A08:2021 - Software and Data Integrity Failures

**Description**: Code and infrastructure that does not protect against integrity
violations, including insecure CI/CD pipelines and auto-updates without verification.

**Impact**: Malicious code execution, supply chain attacks.

### Mitigation Patterns

**1. Subresource Integrity**
```html
<!-- Verify external scripts haven't been tampered with -->
<script
  src="https://cdn.example.com/library.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
  crossorigin="anonymous">
</script>
```

**2. Package Lock Files**
```bash
# Always commit lock files
git add package-lock.json

# Use npm ci in CI/CD (uses lock file exactly)
npm ci
```

---

## A09:2021 - Security Logging and Monitoring Failures

**Description**: Insufficient logging, detection, monitoring, and active response
that allows attacks to go unnoticed.

**Impact**: Delayed breach detection, inability to investigate incidents.

### Mitigation Patterns

**1. Security Event Logging**
```javascript
const securityLogger = {
  authSuccess: (userId, ip) => {
    logger.info('AUTH_SUCCESS', { userId, ip, timestamp: new Date() });
  },

  authFailure: (username, ip, reason) => {
    logger.warn('AUTH_FAILURE', { username, ip, reason, timestamp: new Date() });
  },

  accessDenied: (userId, resource, ip) => {
    logger.warn('ACCESS_DENIED', { userId, resource, ip, timestamp: new Date() });
  },

  suspiciousActivity: (details) => {
    logger.error('SUSPICIOUS_ACTIVITY', { ...details, timestamp: new Date() });
  }
};
```

**2. Audit Trail**
```javascript
// Middleware to log all API access
const auditMiddleware = (req, res, next) => {
  const startTime = Date.now();

  res.on('finish', () => {
    logger.info('API_ACCESS', {
      method: req.method,
      path: req.path,
      userId: req.user?.id,
      ip: req.ip,
      statusCode: res.statusCode,
      duration: Date.now() - startTime,
      userAgent: req.get('user-agent')
    });
  });

  next();
};
```

---

## A10:2021 - Server-Side Request Forgery (SSRF)

**Description**: Application fetches remote resources without validating the
user-supplied URL, allowing attackers to access internal services.

**Impact**: Internal network scanning, data exfiltration, remote code execution.

### Mitigation Patterns

**1. URL Validation**
```javascript
const { URL } = require('url');

const validateUrl = (urlString) => {
  try {
    const url = new URL(urlString);

    // Only allow HTTPS
    if (url.protocol !== 'https:') {
      throw new Error('Only HTTPS URLs allowed');
    }

    // Block internal IPs
    const blockedPatterns = [
      /^localhost$/i,
      /^127\./,
      /^10\./,
      /^172\.(1[6-9]|2[0-9]|3[01])\./,
      /^192\.168\./,
      /^169\.254\./,
      /^0\./,
      /::1/,
      /^fc00:/i,
      /^fe80:/i
    ];

    if (blockedPatterns.some(pattern => pattern.test(url.hostname))) {
      throw new Error('Internal URLs not allowed');
    }

    // Allowlist specific domains if possible
    const allowedDomains = ['api.trusted.com', 'cdn.example.com'];
    if (!allowedDomains.includes(url.hostname)) {
      throw new Error('Domain not in allowlist');
    }

    return url.toString();
  } catch (error) {
    throw new Error(`Invalid URL: ${error.message}`);
  }
};
```

**2. Fetch with Restrictions**
```javascript
const fetchWithRestrictions = async (urlString) => {
  const validatedUrl = validateUrl(urlString);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(validatedUrl, {
      signal: controller.signal,
      redirect: 'error',  // Don't follow redirects
      headers: {
        'User-Agent': 'MyApp/1.0'
      }
    });

    return response;
  } finally {
    clearTimeout(timeout);
  }
};
```

---

## Testing for OWASP Vulnerabilities

### Automated Testing Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| OWASP ZAP | Web app scanner | `zap-cli quick-scan http://localhost:3000` |
| Burp Suite | Manual + automated testing | Interactive proxy |
| npm audit | Dependency vulnerabilities | `npm audit --production` |
| Snyk | Deep dependency analysis | `snyk test` |
| SQLMap | SQL injection testing | `sqlmap -u "http://target/id=1"` |

### Manual Testing Checklist

- [ ] Test all input fields for injection (SQL, XSS, command)
- [ ] Attempt to access other users' resources
- [ ] Test authentication bypass techniques
- [ ] Check for sensitive data in responses
- [ ] Verify security headers in responses
- [ ] Test rate limiting on sensitive endpoints
- [ ] Check for verbose error messages
- [ ] Test CORS configuration

# Data Protection Patterns

Comprehensive guide to protecting data at rest and in transit, handling PII,
and implementing compliance patterns for GDPR, HIPAA, and other regulations.

## Data Classification

Before implementing protections, classify your data:

| Classification | Examples | Protection Level |
|----------------|----------|------------------|
| Public | Marketing content, public APIs | Integrity only |
| Internal | Business documents, logs | Access control |
| Confidential | Customer data, financials | Encryption + access control |
| Restricted | PII, PHI, payment data | Full protection suite |

---

## Encryption at Rest

### Field-Level Encryption

Encrypt sensitive fields individually while keeping other data queryable.

```javascript
const crypto = require('crypto');

class FieldEncryption {
  constructor(masterKey) {
    // Derive key using HKDF for key separation
    this.algorithm = 'aes-256-gcm';
    this.masterKey = Buffer.from(masterKey, 'hex');
  }

  // Derive a unique key for each field type
  deriveKey(context) {
    return crypto.hkdfSync(
      'sha256',
      this.masterKey,
      Buffer.from('salt'),  // Use proper salt in production
      Buffer.from(context),
      32  // 256 bits for AES-256
    );
  }

  encrypt(plaintext, context) {
    const key = this.deriveKey(context);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, key, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    // Format: version:iv:authTag:ciphertext
    return `v1:${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  decrypt(encryptedData, context) {
    const parts = encryptedData.split(':');
    const version = parts[0];

    if (version !== 'v1') {
      throw new Error(`Unsupported encryption version: ${version}`);
    }

    const iv = Buffer.from(parts[1], 'hex');
    const authTag = Buffer.from(parts[2], 'hex');
    const encrypted = parts[3];

    const key = this.deriveKey(context);
    const decipher = crypto.createDecipheriv(this.algorithm, key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// Usage
const encryption = new FieldEncryption(process.env.ENCRYPTION_KEY);

// Encrypt SSN
const encryptedSSN = encryption.encrypt('123-45-6789', 'ssn');

// Encrypt credit card
const encryptedCard = encryption.encrypt('4111111111111111', 'payment_card');
```

### Database Column Encryption

```javascript
// Prisma middleware for automatic field encryption
const sensitiveFields = {
  User: ['ssn', 'dateOfBirth'],
  Payment: ['cardNumber', 'cvv']
};

prisma.$use(async (params, next) => {
  const fields = sensitiveFields[params.model];

  if (fields && params.action === 'create') {
    for (const field of fields) {
      if (params.args.data[field]) {
        params.args.data[field] = encryption.encrypt(
          params.args.data[field],
          `${params.model}.${field}`
        );
      }
    }
  }

  const result = await next(params);

  // Decrypt on read
  if (fields && result && (params.action === 'findUnique' || params.action === 'findFirst')) {
    for (const field of fields) {
      if (result[field]) {
        result[field] = encryption.decrypt(
          result[field],
          `${params.model}.${field}`
        );
      }
    }
  }

  return result;
});
```

### Full Disk Encryption

For cloud deployments, ensure storage is encrypted:

```yaml
# AWS RDS - encryption at rest
Resources:
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      StorageEncrypted: true
      KmsKeyId: !Ref DatabaseEncryptionKey

# MongoDB Atlas - enable encryption
# Navigate to Cluster > Advanced Settings > Encryption at Rest
```

---

## Encryption in Transit

### TLS Configuration

```javascript
const https = require('https');
const fs = require('fs');

const server = https.createServer({
  key: fs.readFileSync('/path/to/private.key'),
  cert: fs.readFileSync('/path/to/certificate.crt'),
  ca: fs.readFileSync('/path/to/ca-bundle.crt'),

  // TLS settings
  minVersion: 'TLSv1.2',
  maxVersion: 'TLSv1.3',

  // Strong ciphers only
  ciphers: [
    'TLS_AES_256_GCM_SHA384',
    'TLS_CHACHA20_POLY1305_SHA256',
    'TLS_AES_128_GCM_SHA256',
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES128-GCM-SHA256'
  ].join(':'),

  // Prefer server cipher order
  honorCipherOrder: true
}, app);
```

### Certificate Pinning (Mobile/Client Apps)

```javascript
// Node.js example - verify specific certificate
const https = require('https');
const crypto = require('crypto');

const expectedFingerprint = 'AB:CD:EF:...';  // Your cert fingerprint

const options = {
  hostname: 'api.example.com',
  port: 443,
  path: '/data',
  method: 'GET',
  checkServerIdentity: (host, cert) => {
    const fingerprint = crypto
      .createHash('sha256')
      .update(cert.raw)
      .digest('hex')
      .toUpperCase()
      .match(/.{2}/g)
      .join(':');

    if (fingerprint !== expectedFingerprint) {
      throw new Error('Certificate fingerprint mismatch');
    }
  }
};
```

---

## PII Handling

### Identifying PII

| Category | Examples | Sensitivity |
|----------|----------|-------------|
| Direct identifiers | SSN, passport, driver license | Very High |
| Contact info | Email, phone, address | High |
| Financial | Credit card, bank account | Very High |
| Health | Medical records, conditions | Very High (PHI) |
| Biometric | Fingerprints, facial data | Very High |
| Demographic | Age, gender, ethnicity | Medium |
| Online identifiers | IP address, cookies | Medium |

### PII Data Model

```javascript
// User model with proper PII handling
const userSchema = {
  // Non-PII
  id: { type: 'uuid' },
  createdAt: { type: 'datetime' },

  // PII - encrypted at rest
  email: {
    type: 'string',
    encrypt: true,
    index: 'hash'  // Hashed index for lookup
  },

  // PII - encrypted, never logged
  ssn: {
    type: 'string',
    encrypt: true,
    mask: true,  // Show only last 4
    noLog: true
  },

  // PII - with retention policy
  phone: {
    type: 'string',
    encrypt: true,
    retention: '2 years'
  }
};

// Masking utility
function maskPII(type, value) {
  if (!value) return null;

  switch (type) {
    case 'ssn':
      return `***-**-${value.slice(-4)}`;
    case 'phone':
      return `***-***-${value.slice(-4)}`;
    case 'email':
      const [local, domain] = value.split('@');
      return `${local[0]}***@${domain}`;
    case 'credit_card':
      return `****-****-****-${value.slice(-4)}`;
    default:
      return '***';
  }
}
```

### Audit Logging for PII Access

```javascript
class PIIAuditLogger {
  async logAccess(options) {
    const { userId, accessedUserId, fields, reason, ip } = options;

    await this.db.piiAccessLog.create({
      data: {
        accessorId: userId,
        accessedId: accessedUserId,
        fieldsAccessed: fields,
        reason,
        ipAddress: ip,
        timestamp: new Date(),
        sessionId: this.getSessionId()
      }
    });
  }

  async logExport(options) {
    const { userId, recordCount, format, reason } = options;

    await this.db.piiExportLog.create({
      data: {
        userId,
        recordCount,
        format,
        reason,
        timestamp: new Date(),
        approvedBy: options.approvedBy
      }
    });
  }
}

// Middleware for automatic PII access logging
const logPIIAccess = (sensitiveFields) => {
  return async (req, res, next) => {
    const originalJson = res.json.bind(res);

    res.json = (data) => {
      const accessedFields = sensitiveFields.filter(f =>
        hasField(data, f)
      );

      if (accessedFields.length > 0) {
        piiLogger.logAccess({
          userId: req.user?.id,
          accessedUserId: data.id,
          fields: accessedFields,
          reason: req.headers['x-access-reason'] || 'API request',
          ip: req.ip
        });
      }

      return originalJson(data);
    };

    next();
  };
};
```

---

## GDPR Compliance

### Consent Management

```javascript
class ConsentManager {
  async recordConsent(userId, consents) {
    // Consents: { marketing: true, analytics: false, ... }

    const consentRecord = await this.db.consent.create({
      data: {
        userId,
        consents: JSON.stringify(consents),
        version: this.getCurrentPolicyVersion(),
        ipAddress: this.getHashedIP(),
        timestamp: new Date(),
        source: 'signup_form'
      }
    });

    // Update user preferences
    await this.db.user.update({
      where: { id: userId },
      data: {
        consentRecordId: consentRecord.id,
        marketingConsent: consents.marketing,
        analyticsConsent: consents.analytics
      }
    });

    return consentRecord;
  }

  async withdrawConsent(userId, consentType) {
    await this.db.consentWithdrawal.create({
      data: {
        userId,
        consentType,
        timestamp: new Date()
      }
    });

    // Update preferences
    await this.db.user.update({
      where: { id: userId },
      data: { [`${consentType}Consent`]: false }
    });

    // Trigger any necessary cleanup
    await this.handleConsentWithdrawal(userId, consentType);
  }
}
```

### Data Subject Rights

```javascript
class DataSubjectRightsHandler {
  // Right to Access (DSAR)
  async handleAccessRequest(userId) {
    const user = await this.db.user.findUnique({
      where: { id: userId },
      include: {
        orders: true,
        preferences: true,
        consents: true,
        activityLogs: { take: 1000 }
      }
    });

    // Generate exportable format
    const exportData = {
      personalData: {
        email: user.email,
        name: user.name,
        phone: user.phone,
        address: user.address
      },
      transactionHistory: user.orders.map(o => ({
        date: o.createdAt,
        amount: o.total,
        items: o.items
      })),
      consentHistory: user.consents,
      accountActivity: user.activityLogs
    };

    // Log the access request
    await this.logDSAR(userId, 'access');

    return exportData;
  }

  // Right to Erasure (Right to be Forgotten)
  async handleErasureRequest(userId) {
    // Verify we can delete (check legal holds, etc.)
    const canDelete = await this.verifyErasureEligibility(userId);
    if (!canDelete.eligible) {
      throw new Error(`Cannot delete: ${canDelete.reason}`);
    }

    // Anonymize rather than delete for audit trail
    await this.db.user.update({
      where: { id: userId },
      data: {
        email: `deleted_${userId}@anonymized.local`,
        name: 'Deleted User',
        phone: null,
        address: null,
        deletedAt: new Date(),
        deletionReason: 'GDPR erasure request'
      }
    });

    // Delete from other systems
    await this.propagateDeletion(userId);

    // Log the erasure
    await this.logDSAR(userId, 'erasure');

    return { success: true, completedAt: new Date() };
  }

  // Right to Rectification
  async handleRectificationRequest(userId, corrections) {
    const before = await this.db.user.findUnique({ where: { id: userId }});

    await this.db.user.update({
      where: { id: userId },
      data: corrections
    });

    // Log the change
    await this.logDSAR(userId, 'rectification', {
      before: this.sanitizeForLog(before),
      after: this.sanitizeForLog(corrections)
    });
  }

  // Right to Data Portability
  async handlePortabilityRequest(userId, format = 'json') {
    const data = await this.handleAccessRequest(userId);

    switch (format) {
      case 'json':
        return JSON.stringify(data, null, 2);
      case 'csv':
        return this.convertToCSV(data);
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }
}
```

### Data Retention

```javascript
class DataRetentionManager {
  // Define retention policies
  policies = {
    user_data: { duration: '7 years', basis: 'legal_requirement' },
    transaction_logs: { duration: '7 years', basis: 'legal_requirement' },
    session_logs: { duration: '90 days', basis: 'legitimate_interest' },
    marketing_data: { duration: '2 years', basis: 'consent' },
    support_tickets: { duration: '3 years', basis: 'contract' }
  };

  async runRetentionCleanup() {
    const now = new Date();

    for (const [dataType, policy] of Object.entries(this.policies)) {
      const cutoffDate = this.calculateCutoff(now, policy.duration);

      const deleted = await this.deleteExpiredData(dataType, cutoffDate);

      await this.logRetentionRun({
        dataType,
        cutoffDate,
        recordsDeleted: deleted,
        timestamp: now
      });
    }
  }

  calculateCutoff(now, duration) {
    const match = duration.match(/(\d+)\s*(days?|years?)/);
    const value = parseInt(match[1]);
    const unit = match[2];

    const date = new Date(now);
    if (unit.startsWith('day')) {
      date.setDate(date.getDate() - value);
    } else if (unit.startsWith('year')) {
      date.setFullYear(date.getFullYear() - value);
    }

    return date;
  }
}
```

---

## Key Management

### Key Hierarchy

```
Master Key (HSM/KMS)
    |
    +-- Data Encryption Key (DEK) for users
    |
    +-- Data Encryption Key (DEK) for payments
    |
    +-- Data Encryption Key (DEK) for documents
```

### AWS KMS Integration

```javascript
const { KMSClient, GenerateDataKeyCommand, DecryptCommand } = require('@aws-sdk/client-kms');

class KeyManager {
  constructor() {
    this.kms = new KMSClient({ region: process.env.AWS_REGION });
    this.masterKeyId = process.env.KMS_MASTER_KEY_ID;
  }

  // Generate a new data encryption key
  async generateDataKey() {
    const command = new GenerateDataKeyCommand({
      KeyId: this.masterKeyId,
      KeySpec: 'AES_256'
    });

    const response = await this.kms.send(command);

    return {
      plaintext: response.Plaintext,  // Use immediately, don't store
      encrypted: response.CiphertextBlob  // Store this
    };
  }

  // Decrypt a data key
  async decryptDataKey(encryptedKey) {
    const command = new DecryptCommand({
      CiphertextBlob: encryptedKey,
      KeyId: this.masterKeyId
    });

    const response = await this.kms.send(command);
    return response.Plaintext;
  }

  // Envelope encryption pattern
  async encryptData(data) {
    const { plaintext: dek, encrypted: encryptedDek } = await this.generateDataKey();

    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', dek, iv);

    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag();

    // Clear DEK from memory
    dek.fill(0);

    return {
      encryptedDek: encryptedDek.toString('base64'),
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64'),
      ciphertext: encrypted
    };
  }

  async decryptData(envelope) {
    const dek = await this.decryptDataKey(
      Buffer.from(envelope.encryptedDek, 'base64')
    );

    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      dek,
      Buffer.from(envelope.iv, 'base64')
    );
    decipher.setAuthTag(Buffer.from(envelope.authTag, 'base64'));

    let decrypted = decipher.update(envelope.ciphertext, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    // Clear DEK from memory
    dek.fill(0);

    return decrypted;
  }
}
```

### Key Rotation

```javascript
class KeyRotationManager {
  async rotateDataKeys() {
    // Get all records with old key version
    const records = await this.db.encryptedData.findMany({
      where: { keyVersion: { lt: this.currentKeyVersion }}
    });

    for (const record of records) {
      // Decrypt with old key
      const plaintext = await this.decryptWithVersion(
        record.ciphertext,
        record.keyVersion
      );

      // Re-encrypt with new key
      const newCiphertext = await this.encryptWithCurrentKey(plaintext);

      // Update record
      await this.db.encryptedData.update({
        where: { id: record.id },
        data: {
          ciphertext: newCiphertext,
          keyVersion: this.currentKeyVersion,
          rotatedAt: new Date()
        }
      });
    }

    // Mark old key for deletion after grace period
    await this.scheduleKeyDeletion(this.currentKeyVersion - 1, '30 days');
  }
}
```

---

## Compliance Checklist

### GDPR

- [ ] Privacy policy updated and accessible
- [ ] Consent mechanism implemented (granular, freely given)
- [ ] Data subject rights handlers implemented
- [ ] Data Processing Agreements with vendors
- [ ] Data Protection Impact Assessment completed
- [ ] DPO appointed (if required)
- [ ] Breach notification process defined
- [ ] Data retention policies implemented
- [ ] Cross-border transfer mechanisms in place

### CCPA/CPRA

- [ ] "Do Not Sell My Personal Information" link
- [ ] Opt-out mechanism for data selling
- [ ] Verifiable consumer request process
- [ ] Privacy policy with CCPA disclosures
- [ ] Employee training on CCPA requirements

### HIPAA (if handling PHI)

- [ ] Business Associate Agreements signed
- [ ] PHI encrypted at rest and in transit
- [ ] Access controls and audit logging
- [ ] Risk assessment completed
- [ ] Breach notification procedures
- [ ] Employee HIPAA training

### PCI DSS (if handling payment cards)

- [ ] Cardholder data encrypted
- [ ] Network segmentation implemented
- [ ] Access to cardholder data restricted
- [ ] Regular vulnerability scans
- [ ] Penetration testing completed
- [ ] Security policies documented

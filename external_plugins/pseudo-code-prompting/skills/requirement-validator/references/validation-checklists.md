# Validation Checklists

Comprehensive checklists for validating different types of requirements.

## General Validation Checklist

### Core Requirements
- [ ] Function name is clear and descriptive
- [ ] All required parameters are present
- [ ] Parameter types are appropriate
- [ ] Default values are sensible
- [ ] Function purpose is unambiguous

### Security Requirements
- [ ] Authentication specified (if needed)
- [ ] Authorization/permissions defined
- [ ] Input validation requirements present
- [ ] Sensitive data handling specified
- [ ] Security constraints documented

### Data Requirements
- [ ] Data sources identified
- [ ] Data formats specified
- [ ] Validation rules defined
- [ ] Storage strategy clear
- [ ] Data relationships documented

### Error Handling
- [ ] Error scenarios identified
- [ ] Error responses defined
- [ ] Fallback behaviors specified
- [ ] Logging requirements present
- [ ] User feedback mechanism clear

### Performance Requirements
- [ ] Scalability needs specified
- [ ] Timeout values defined
- [ ] Resource limits present
- [ ] Caching strategy considered
- [ ] Performance metrics identified

---

## Feature-Specific Checklists

### Authentication Feature Checklist
- [ ] Authentication method specified (oauth, jwt, session, api_key)
- [ ] Providers listed (if oauth/social login)
- [ ] Token lifetime defined
- [ ] Refresh token strategy specified
- [ ] Storage mechanism for credentials
- [ ] Redirect URIs defined
- [ ] Logout mechanism present
- [ ] Session management strategy
- [ ] Multi-factor authentication considered
- [ ] Password requirements (if applicable)
- [ ] Account recovery process
- [ ] Failed login handling
- [ ] Concurrent session policy

### API Endpoint Checklist
- [ ] HTTP method specified (GET, POST, PUT, DELETE, PATCH)
- [ ] Path/route defined
- [ ] Authentication requirement specified
- [ ] Authorization rules defined
- [ ] Request schema/body format
- [ ] Response format defined
- [ ] Error responses for all codes (400, 401, 403, 404, 500)
- [ ] Rate limiting strategy
- [ ] CORS configuration
- [ ] Request validation rules
- [ ] Pagination (for list endpoints)
- [ ] Filtering/sorting (for list endpoints)
- [ ] API versioning strategy
- [ ] Documentation/OpenAPI spec

### Database Operation Checklist
- [ ] Operation type (read, write, update, delete)
- [ ] Table/collection names
- [ ] Schema definition
- [ ] Indexes specified
- [ ] Query optimization strategy
- [ ] Transaction requirements
- [ ] Isolation level (if applicable)
- [ ] Cascade delete rules
- [ ] Foreign key constraints
- [ ] Data validation rules
- [ ] Migration strategy (if schema change)
- [ ] Backup/restore considerations
- [ ] Concurrent access handling
- [ ] Connection pooling strategy

### Caching Implementation Checklist
- [ ] Cache storage type (redis, memcached, in-memory)
- [ ] Cache key strategy
- [ ] TTL (time to live) specified
- [ ] Cache invalidation strategy
- [ ] Cache warming strategy
- [ ] Cache miss handling
- [ ] Cache size limits
- [ ] Eviction policy
- [ ] Cache coherency strategy
- [ ] Monitoring/metrics

### File Upload Checklist
- [ ] Maximum file size specified
- [ ] Allowed file types/extensions
- [ ] Storage location (s3, filesystem, database)
- [ ] File validation rules
- [ ] Virus scanning requirements
- [ ] Upload progress tracking
- [ ] Chunked upload support (for large files)
- [ ] File naming strategy
- [ ] Duplicate file handling
- [ ] Access control for uploaded files
- [ ] Cleanup/retention policy
- [ ] Error handling for failed uploads

### Search Feature Checklist
- [ ] Search fields specified
- [ ] Search algorithm (full-text, fuzzy, exact)
- [ ] Indexing strategy
- [ ] Search query syntax
- [ ] Result ranking/sorting
- [ ] Pagination of results
- [ ] Filtering options
- [ ] Performance for large datasets
- [ ] Search analytics/tracking
- [ ] Autocomplete/suggestions
- [ ] Multi-language support (if applicable)

### Email/Notification Checklist
- [ ] Notification types specified
- [ ] Delivery method (email, SMS, push, in-app)
- [ ] Template system
- [ ] Personalization parameters
- [ ] Sender address/credentials
- [ ] Delivery service (SendGrid, SES, etc.)
- [ ] Rate limiting
- [ ] Retry strategy for failures
- [ ] Unsubscribe mechanism
- [ ] Tracking (opens, clicks)
- [ ] Scheduling/delayed sending
- [ ] Batch sending strategy

### Payment Integration Checklist
- [ ] Payment provider specified (Stripe, PayPal, etc.)
- [ ] Supported payment methods
- [ ] Currency support
- [ ] Transaction amount validation
- [ ] Payment flow (one-time, recurring)
- [ ] Webhook handling
- [ ] Refund process
- [ ] Failed payment handling
- [ ] PCI compliance requirements
- [ ] Invoice generation
- [ ] Payment history storage
- [ ] Security/encryption requirements
- [ ] Testing/sandbox mode

### Report Generation Checklist
- [ ] Report format (PDF, CSV, Excel, HTML)
- [ ] Data sources specified
- [ ] Query/aggregation logic
- [ ] Report parameters/filters
- [ ] Scheduling options
- [ ] Generation performance (async for large reports)
- [ ] Storage of generated reports
- [ ] Access control
- [ ] Retention policy
- [ ] Email delivery options
- [ ] Template customization

---

## Edge Case Validation Checklist

### Common Edge Cases
- [ ] Empty/null input handling
- [ ] Invalid input handling
- [ ] Boundary values (min/max)
- [ ] Concurrent requests
- [ ] Network failures
- [ ] Timeout scenarios
- [ ] Database connection failures
- [ ] Third-party service failures
- [ ] Rate limit exceeded
- [ ] Storage/memory full
- [ ] Invalid state transitions
- [ ] Race conditions
- [ ] Duplicate submissions
- [ ] Partial failures

### Security Edge Cases
- [ ] Injection attacks (SQL, XSS, CSRF)
- [ ] Brute force attempts
- [ ] Session hijacking
- [ ] Token theft/replay
- [ ] Unauthorized access attempts
- [ ] Data exfiltration attempts
- [ ] Denial of service scenarios
- [ ] Man-in-the-middle attacks

---

## Validation Severity Levels

### Critical (Must Fix Before Implementation)
- Missing authentication on sensitive endpoints
- No input validation on user data
- Undefined error handling
- Missing required parameters
- Security vulnerabilities
- Data loss risks

### High (Should Fix Before Implementation)
- Missing important parameters
- Ambiguous requirements
- Performance constraints not specified
- Incomplete error handling
- Missing edge case handling

### Medium (Address During Implementation)
- Missing optional parameters
- Documentation gaps
- Additional validation rules
- Optimization opportunities
- Enhanced error messages

### Low (Nice to Have)
- Extra convenience features
- Additional monitoring
- Enhanced UX details
- Future extensibility

---
description: Compress verbose requirements into concise pseudo-code format
argument-hint: [verbose-requirements]
---

# Compress Context

Transform verbose, detailed requirements into concise pseudo-code while preserving all essential information.

## Task

Compress the following verbose requirements: `$ARGUMENTS`

Apply context compression techniques:

1. **Extract Core Intent** - Identify the primary action and objective
2. **Distill Parameters** - Convert descriptions into structured parameters
3. **Preserve Constraints** - Keep all validation, security, and performance requirements
4. **Maintain Clarity** - Ensure compressed form is unambiguous
5. **Reduce Redundancy** - Remove repetitive or implied information

## Compression Strategy

### From Prose to Parameters
Convert descriptive text into structured function parameters:
- Sentences → Key-value pairs
- Lists → Arrays or enums
- Conditions → Constraint expressions
- Requirements → Parameter specifications

### Information Preservation
Keep essential details:
- Security requirements (auth, permissions)
- Validation rules (types, constraints)
- Error handling (strategies, fallbacks)
- Performance specs (timeouts, limits)
- Integration points (APIs, services)

### Redundancy Elimination
Remove unnecessary information:
- Obvious defaults
- Implied behaviors
- Repetitive descriptions
- Background context (unless critical)

## Output Format

Return compressed pseudo-code with compression summary:

```
Original Length: [X words/lines]
Compressed Length: [Y words]
Compression Ratio: [X/Y]

Compressed Pseudo-Code:
[concise function call with parameters]

Information Preserved:
✓ [Category 1]: [What was kept]
✓ [Category 2]: [What was kept]

Information Removed:
✗ [What was eliminated and why]
```

## Compression Examples

### Example 1: Verbose API Description

**Original (150 words)**:
```
We need to create a new REST API endpoint that handles user registration.
The endpoint should accept POST requests at the /api/register path.
Users need to provide their email address, which must be validated to ensure
it's a proper email format and not already in use. They also need to provide
a password that meets our security requirements: at least 12 characters,
including uppercase, lowercase, numbers, and special characters. The system
should hash the password using bcrypt before storing it. If registration is
successful, return a 201 status with the new user ID. If the email is already
taken, return a 409 error. If validation fails, return a 400 error with details
about what went wrong. We should also rate limit this endpoint to prevent abuse,
allowing maximum 10 registration attempts per hour from the same IP address.
```

**Compressed (1 line)**:
```
create_endpoint(
  path="/api/register",
  method="POST",
  request_schema={
    "email": "email:required:unique",
    "password": "string:required:min(12):requires(upper,lower,number,special)"
  },
  password_hash="bcrypt",
  response_codes={
    "201": {"user_id": "string"},
    "400": "validation_error",
    "409": "duplicate_email"
  },
  rate_limit={"max": 10, "window": "1h", "key": "ip"}
)
```

**Compression Ratio**: 150 words → 1 structured call (95% reduction)

### Example 2: Verbose Database Query

**Original (80 words)**:
```
I need a function that queries the users table in our PostgreSQL database.
It should be able to filter users by their status (active, inactive, or suspended)
and their role (admin, user, or guest). The results should be paginated with 20
users per page by default, but allow up to 100 per page. Include pagination
metadata in the response. Sort by creation date in descending order. For
performance, only return essential fields: id, username, email, status, and role.
Cache the results for 5 minutes using Redis.
```

**Compressed (1 line)**:
```
query_users(
  table="users",
  db="postgresql",
  filter={"status": "enum[active,inactive,suspended]", "role": "enum[admin,user,guest]"},
  fields=["id", "username", "email", "status", "role"],
  pagination={"default": 20, "max": 100, "include_metadata": true},
  sort={"field": "created_at", "order": "desc"},
  cache={"type": "redis", "ttl": "5m"}
)
```

**Compression Ratio**: 80 words → 1 structured call (90% reduction)

### Example 3: Verbose Feature Request

**Original (100 words)**:
```
We want to add a notification system that can send messages to users through
multiple channels. Users should be able to receive notifications via email,
SMS, and push notifications on their mobile devices. When sending an email,
use SendGrid as our email service provider. For SMS, use Twilio. Push
notifications should go through Firebase Cloud Messaging. Users should be
able to configure their preferences for which types of notifications they
want to receive on which channels. The system should retry failed deliveries
up to 3 times with exponential backoff. Track delivery status and log all
notification attempts for auditing purposes.
```

**Compressed (1 line)**:
```
implement_notifications(
  channels={
    "email": {"provider": "SendGrid"},
    "sms": {"provider": "Twilio"},
    "push": {"provider": "FCM"}
  },
  user_preferences=true,
  retry_strategy={"attempts": 3, "backoff": "exponential"},
  tracking=true,
  audit_logging=true
)
```

**Compression Ratio**: 100 words → 1 structured call (92% reduction)

## Compression Rules

### What to Keep
- **Core functionality** - The main action and objective
- **Required parameters** - Essential inputs and configuration
- **Constraints** - Validation rules, limits, security requirements
- **Error handling** - How failures should be managed
- **Integration details** - External services, APIs, dependencies
- **Performance specs** - Timeouts, caching, rate limits

### What to Remove
- **Explanatory text** - "We need to", "The system should"
- **Obvious defaults** - Standard behaviors that are implied
- **Background context** - Why the feature is needed (unless it affects implementation)
- **Repetition** - Saying the same thing multiple ways
- **Unnecessary adjectives** - "Important", "critical", "essential" (make everything a parameter instead)

### What to Simplify
- **Long descriptions** → enum values or constraint expressions
- **Multiple sentences** → single parameter
- **Conditional logic** → constraint parameters
- **Workflow steps** → ordered parameters or pipeline

## Compression Techniques

### Technique 1: Parameter Grouping
```
Before: email is required, email must be unique, email must be valid format
After: email="email:required:unique"
```

### Technique 2: Enum Conversion
```
Before: status can be pending, completed, or cancelled
After: status="enum[pending,completed,cancelled]"
```

### Technique 3: Nested Objects
```
Before: retry 3 times, use exponential backoff, max delay 60 seconds
After: retry={"attempts": 3, "backoff": "exponential", "max_delay": "60s"}
```

### Technique 4: Array Reduction
```
Before: return user id, user name, user email, and creation timestamp
After: fields=["id", "name", "email", "created_at"]
```

### Technique 5: Implicit Defaults
```
Before: use standard pagination (20 per page, max 100)
After: pagination=true (defaults are implied)
OR: pagination={"default": 20, "max": 100} (if non-standard)
```

## Quality Checks

Compressed pseudo-code should:
- [ ] Contain all security requirements
- [ ] Include all validation rules
- [ ] Specify error handling
- [ ] Define performance constraints
- [ ] List integration dependencies
- [ ] Be implementable without additional context
- [ ] Be shorter than original by 80%+
- [ ] Maintain clarity and specificity

## Best Practices

1. **Preserve Intent** - Don't lose the "what" or "why" if it's implementation-critical
2. **Use Standard Patterns** - Follow common parameter naming conventions
3. **Be Consistent** - Use the same compression style throughout
4. **Validate Completeness** - Ensure nothing critical was lost
5. **Optimize Readability** - Compressed doesn't mean cryptic

## Integration with Other Commands

- Use `/validate-requirements` after compression to ensure nothing was lost
- Use `/optimize-prompt` if compressed version needs enhancement
- Use `/transform-query` for initial conversion before compression

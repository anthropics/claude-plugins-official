---
description: Optimize pseudo-code for clarity, completeness, and implementation readiness
argument-hint: [pseudo-code]
---

# Optimize Prompt

Enhance pseudo-code by adding missing parameters, clarifying ambiguities, and ensuring implementation readiness.

## Task

Optimize the following pseudo-code: `$ARGUMENTS`

Apply systematic optimization techniques:

1. **Add Missing Parameters** - Include commonly needed but omitted parameters
2. **Clarify Ambiguities** - Replace vague terms with specific values
3. **Enhance Constraints** - Add validation rules, limits, and guards
4. **Improve Error Handling** - Specify error scenarios and fallbacks
5. **Add Context** - Include performance, security, and integration details

## Optimization Strategy

### Parameter Enhancement
- Add authentication/authorization where needed
- Include validation rules and constraints
- Specify data formats and types
- Define error handling strategies
- Add performance constraints

### Context Addition
- Security requirements (auth, validation)
- Performance expectations (timeouts, scale)
- Error handling (retries, fallbacks)
- Data persistence (storage, caching)
- Integration points (APIs, services)

### Constraint Specification
- Input validation rules
- Output format definitions
- Resource limits (size, time, memory)
- Business logic constraints
- Compatibility requirements

## Output Format

Return optimized pseudo-code with explanations:

```
Original:
[original pseudo-code]

Optimized:
[enhanced pseudo-code with all improvements]

Improvements Made:
✓ [Improvement category 1]
  - [Specific change 1]
  - [Specific change 2]
✓ [Improvement category 2]
  - [Specific change 3]

Rationale:
- [Why this improvement matters]
- [What problems it prevents]
```

## Common Optimizations

### Add Authentication
```
Before: create_endpoint(path="/api/data")
After: create_endpoint(path="/api/data", auth=true, roles=["user"])
```

### Add Validation
```
Before: create_user(email)
After: create_user(email="email:required:unique", validation=true)
```

### Add Error Handling
```
Before: fetch_data(url)
After: fetch_data(url, timeout="5s", error_handling="retry", retries=3)
```

### Add Performance Constraints
```
Before: search_products(query)
After: search_products(query, pagination=true, cache="5m", max_results=100)
```

### Add Integration Details
```
Before: send_notification(message)
After: send_notification(
  message,
  channel=["email", "sms"],
  provider="SendGrid",
  template="notifications/alert",
  retry_on_failure=true
)
```

## Optimization Priorities

1. **Security First** - Auth, validation, sanitization
2. **Error Handling** - Graceful failures, retries, logging
3. **Performance** - Timeouts, caching, limits
4. **Data Integrity** - Validation, constraints, transactions
5. **Integration** - Dependencies, APIs, versioning

## Quality Checks

Ensure optimized pseudo-code has:
- [ ] Clear authentication requirements
- [ ] Explicit validation rules
- [ ] Defined error handling
- [ ] Performance constraints
- [ ] Data format specifications
- [ ] Integration dependencies
- [ ] Resource limits
- [ ] Logging/monitoring hints

## Examples

### Example 1: API Endpoint
```
Original: create_endpoint(path="/api/users", method="POST")

Optimized: create_endpoint(
  path="/api/users",
  method="POST",
  auth=true,
  roles=["admin"],
  request_schema={
    "name": "string:required:max(100)",
    "email": "email:required:unique"
  },
  response_format={"user_id": "string", "created_at": "timestamp"},
  error_responses={
    "400": "invalid_input",
    "409": "duplicate_email"
  },
  rate_limit="100/hour"
)

Improvements Made:
✓ Security
  - Added authentication requirement
  - Specified admin role authorization
✓ Data Validation
  - Defined request schema with constraints
  - Specified response format
✓ Error Handling
  - Added specific error responses
✓ Performance
  - Added rate limiting
```

### Example 2: Database Operation
```
Original: query_users(filter)

Optimized: query_users(
  filter="object:required",
  pagination={"page": 1, "per_page": 20, "max": 100},
  fields=["id", "name", "email"],
  sort={"field": "created_at", "order": "desc"},
  cache={"enabled": true, "ttl": "5m"},
  timeout="10s",
  error_handling="return_empty_array"
)

Improvements Made:
✓ Pagination
  - Added pagination with sensible defaults
✓ Performance
  - Limited fields returned
  - Added caching strategy
  - Specified timeout
✓ Usability
  - Added sorting capability
✓ Error Handling
  - Defined failure behavior
```

## Best Practices

1. **Don't Over-Engineer** - Add parameters that matter for the use case
2. **Be Specific** - Replace "handle errors" with "retry_3_times_then_log"
3. **Follow Patterns** - Use common parameter names (auth, timeout, validation)
4. **Consider Context** - Simple scripts need less than production APIs
5. **Maintain Readability** - Group related parameters logically

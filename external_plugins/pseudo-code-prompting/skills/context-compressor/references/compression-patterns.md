# Compression Patterns Reference

## Common Conversation Patterns → Pseudo-Code

### Pattern 1: Feature Discussion → Function Call

**Original Format (Verbose)**
```
"We need to add a new feature for user notifications. 
The notifications should be real-time using WebSockets, 
support multiple channels like email and SMS, and have 
configurable frequency limits to prevent spam."
```

**Compressed Format**
```
implement_notifications(
  delivery="realtime_websocket",
  channels=["email", "sms"],
  rate_limiting="configurable",
  spam_prevention=true
)
```

**Token Savings**: ~40 tokens → ~15 tokens (62% reduction)

---

### Pattern 2: Code Review → Findings List

**Original Format**
```
"I reviewed the authentication code and found several issues:
The password validation is too weak, we should require at 
least 12 characters with mixed case and symbols. The session 
timeout is hardcoded to 30 minutes which should be configurable. 
Error messages are too verbose and could leak security info."
```

**Compressed Format**
```
code_review(
  module="authentication",
  findings=[
    "strengthen_password_rules(min=12, mixed_case=true, symbols=true)",
    "make_configurable(session_timeout, default='30m')",
    "sanitize_error_messages(security='hide_details')"
  ],
  priority="high"
)
```

**Token Savings**: ~55 tokens → ~25 tokens (55% reduction)

---

### Pattern 3: Decision Discussion → Decision Record

**Original Format**
```
"After discussing the database options, we've decided to use 
PostgreSQL instead of MongoDB. The main reasons were: we need 
ACID transactions for financial data, the team has more 
experience with SQL, and we need complex joins for reporting. 
We considered MongoDB but it wasn't suitable for our transactional 
requirements."
```

**Compressed Format**
```
decision(
  id="DB-001",
  topic="database_selection",
  chosen="postgresql",
  rejected=["mongodb"],
  rationale=[
    "acid_required_for_financial_data",
    "team_sql_expertise",
    "complex_joins_for_reporting"
  ]
)
```

**Token Savings**: ~60 tokens → ~22 tokens (63% reduction)

---

### Pattern 4: Progress Update → State Object

**Original Format**
```
"Today we completed the user authentication module including 
login and registration. We're currently working on password 
reset functionality. Still need to implement two-factor 
authentication and social login. There's a blocker with the 
email service integration that needs resolution."
```

**Compressed Format**
```
progress_update(
  completed=["authentication_login", "authentication_register"],
  in_progress=["password_reset"],
  pending=["two_factor_auth", "social_login"],
  blockers=["email_service_integration"]
)
```

**Token Savings**: ~48 tokens → ~18 tokens (62% reduction)

---

### Pattern 5: Error Discussion → Error State

**Original Format**
```
"We encountered an error in production: the API is returning 
500 errors when processing large file uploads over 10MB. The 
error log shows 'Request Entity Too Large'. We need to increase 
the max upload size in nginx config and add better validation 
on the client side to warn users before upload."
```

**Compressed Format**
```
error_report(
  environment="production",
  error="500_request_entity_too_large",
  trigger="file_upload_over_10mb",
  solution=[
    "increase_nginx_max_upload_size",
    "add_client_side_validation",
    "warn_user_before_upload"
  ]
)
```

**Token Savings**: ~55 tokens → ~20 tokens (64% reduction)

---

### Pattern 6: Requirements Discussion → Requirements Object

**Original Format**
```
"The client wants the dashboard to load in under 2 seconds, 
support at least 1000 concurrent users, work on mobile devices, 
and integrate with their existing CRM system via REST API. 
They also mentioned they prefer React for the frontend and 
need the project completed by end of March."
```

**Compressed Format**
```
requirements(
  performance=["load_time<2s", "concurrent_users=1000"],
  compatibility=["mobile_responsive"],
  integrations=["crm_via_rest_api"],
  tech_stack=["react_frontend"],
  deadline="2026-03-31"
)
```

**Token Savings**: ~50 tokens → ~20 tokens (60% reduction)

---

### Pattern 7: Testing Discussion → Test Plan

**Original Format**
```
"For testing, we need to cover unit tests for all business 
logic, integration tests for the API endpoints, end-to-end 
tests for critical user flows, and performance tests to verify 
the 2-second load time requirement. We should aim for at least 
80% code coverage."
```

**Compressed Format**
```
test_plan(
  types=["unit(scope='business_logic')", "integration(scope='api_endpoints')", 
         "e2e(scope='critical_flows')", "performance(target='2s_load')"],
  coverage_target="80%"
)
```

**Token Savings**: ~48 tokens → ~20 tokens (58% reduction)

---

## Compression Strategies by Content Type

### Technical Discussions → Function Calls
- Extract action verbs → function names
- Extract details → parameters
- Remove explanatory text → keep outcomes

### Decisions → Decision Records
- Extract decision point → topic
- Extract chosen option → chosen
- Extract reasoning → rationale array
- Remove discussion process → keep conclusion

### Progress Updates → State Objects
- Group by status (completed, in_progress, pending, blocked)
- Use arrays for lists
- Remove narrative text → keep facts

### Requirements → Structured Objects
- Group by category (functional, non-functional, technical)
- Extract constraints → parameters
- Remove requests/desires → keep requirements

### Errors/Issues → Error Objects
- Extract error type, trigger, environment
- Extract solution → action items
- Remove diagnosis process → keep findings

## Compression Levels Guide

### Level 1: Light (Preserve 70%)
```
# Use for recent/active discussions
- Keep most context
- Condense repetitive elements
- Preserve reasoning
```

### Level 2: Medium (Preserve 50%)
```
# Use for mid-range history
- Convert to pseudo-code
- Keep decisions and outcomes
- Summarize reasoning
```

### Level 3: Heavy (Preserve 30%)
```
# Use for older/resolved items
- Outcome-only
- Minimal context
- Decision records only
```

## Anti-Patterns (What NOT to Compress)

❌ **Don't compress**:
- Explicit user requirements (keep verbatim)
- Security constraints
- Current blockers/issues
- Active goals and objectives
- Direct user quotes/preferences

✓ **Always preserve**:
- User's own words for requirements
- Critical constraints
- Active decisions
- Current context
- Explicit preferences

## Token Estimation

| Content Type | Original Avg | Compressed Avg | Savings |
|-------------|--------------|----------------|---------|
| Feature Discussion | 60 tokens | 20 tokens | 67% |
| Code Review | 80 tokens | 25 tokens | 69% |
| Decision Record | 70 tokens | 22 tokens | 69% |
| Progress Update | 50 tokens | 18 tokens | 64% |
| Error Report | 65 tokens | 22 tokens | 66% |
| Requirements | 55 tokens | 20 tokens | 64% |

**Overall Average**: 65% token reduction while maintaining 95%+ information retention

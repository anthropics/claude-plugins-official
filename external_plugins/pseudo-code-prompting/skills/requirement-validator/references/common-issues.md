# Common Issues and Solutions

A reference guide for identifying and fixing common issues in pseudo-code requirements.

## Missing Authentication/Authorization

### Issue Pattern
```
create_endpoint(path="/api/admin/users", method="DELETE")
```

### Problems
- No authentication specified
- No authorization check
- Sensitive operation unprotected

### Solution
```
create_endpoint(
  path="/api/admin/users",
  method="DELETE",
  auth=true,
  roles=["admin"],
  permissions=["users:delete"],
  audit_log=true
)
```

---

## Incomplete Data Validation

### Issue Pattern
```
create_user(name, email)
```

### Problems
- No validation rules
- No constraints on input
- No format specification

### Solution
```
create_user(
  name="string:required:max(100):min(2)",
  email="email:required:unique",
  validation_rules={
    "name": "^[a-zA-Z ]+$",
    "email": "RFC5322"
  },
  sanitization=true
)
```

---

## Missing Error Handling

### Issue Pattern
```
fetch_user_data(user_id)
```

### Problems
- No error handling strategy
- No fallback behavior
- No timeout specified

### Solution
```
fetch_user_data(
  user_id="string:required",
  timeout="5s",
  error_handling="return_null",
  fallback_data={"name": "Unknown", "status": "unavailable"},
  retry_strategy={"attempts": 3, "backoff": "exponential"},
  logging=true
)
```

---

## Vague Performance Requirements

### Issue Pattern
```
optimize_query(target="user_search")
```

### Problems
- No specific optimization goal
- No performance metrics
- No constraints specified

### Solution
```
optimize_query(
  target="user_search",
  optimization_goal="latency",
  target_latency="<100ms",
  scale="10000_concurrent_users",
  caching={"type": "redis", "ttl": "5m"},
  indexing=["email", "username"],
  monitoring=true
)
```

---

## Ambiguous Scope

### Issue Pattern
```
add_notifications()
```

### Problems
- Too vague
- No specific types
- No delivery method

### Solution
```
implement_notifications(
  types=["email", "in_app", "push"],
  triggers=["new_message", "mention", "system_alert"],
  delivery_service="SendGrid",
  templates={
    "email": "templates/email/",
    "push": "templates/push/"
  },
  user_preferences=true,
  rate_limiting={"max_per_hour": 10},
  batching={"enabled": true, "interval": "15m"}
)
```

---

## Missing Edge Case Handling

### Issue Pattern
```
upload_file(file)
```

### Problems
- No file size limit
- No type validation
- No error scenarios

### Solution
```
upload_file(
  file="binary:required",
  max_size="10MB",
  allowed_types=["image/jpeg", "image/png", "application/pdf"],
  virus_scan=true,
  storage="s3://uploads/",
  error_handling={
    "file_too_large": "return_error_413",
    "invalid_type": "return_error_415",
    "virus_detected": "quarantine_and_alert",
    "upload_failed": "retry_3_times"
  },
  cleanup_on_error=true
)
```

---

## Incomplete API Specifications

### Issue Pattern
```
create_endpoint(path="/api/products", method="GET")
```

### Problems
- No response format
- No pagination
- No filtering

### Solution
```
create_endpoint(
  path="/api/products",
  method="GET",
  auth=false,
  response_schema={
    "products": "array",
    "pagination": {"page": "int", "total": "int", "per_page": "int"}
  },
  pagination={"default_per_page": 20, "max_per_page": 100},
  filtering={
    "category": "string:optional",
    "price_min": "float:optional",
    "price_max": "float:optional",
    "in_stock": "boolean:optional"
  },
  sorting={"fields": ["price", "name", "created_at"], "default": "name:asc"},
  rate_limit="1000/hour",
  caching={"ttl": "5m", "vary_by": ["category", "filters"]}
)
```

---

## Missing Database Constraints

### Issue Pattern
```
create_table(name="orders")
```

### Problems
- No schema definition
- No indexes
- No relationships

### Solution
```
create_table(
  name="orders",
  schema={
    "id": "uuid:primary_key",
    "user_id": "uuid:foreign_key(users.id):not_null:indexed",
    "status": "enum[pending,completed,cancelled]:not_null:default(pending)",
    "total": "decimal(10,2):not_null",
    "created_at": "timestamp:not_null:default(now)",
    "updated_at": "timestamp:not_null:on_update(now)"
  },
  indexes=[
    {"fields": ["user_id", "status"], "type": "btree"},
    {"fields": ["created_at"], "type": "btree"}
  ],
  constraints={
    "total": "total >= 0",
    "status_transitions": "pending->completed|cancelled"
  },
  on_delete_user="cascade"
)
```

---

## Insufficient Security Measures

### Issue Pattern
```
implement_authentication(type="password")
```

### Problems
- No password requirements
- No rate limiting
- No security best practices

### Solution
```
implement_authentication(
  type="password",
  password_requirements={
    "min_length": 12,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_numbers": true,
    "require_special": true,
    "no_common_passwords": true
  },
  hashing="argon2id",
  rate_limiting={
    "max_attempts": 5,
    "lockout_duration": "15m",
    "progressive_delay": true
  },
  mfa_support=true,
  session_management={
    "token_type": "jwt",
    "token_ttl": "1h",
    "refresh_token_ttl": "30d",
    "secure_cookies": true,
    "httponly": true,
    "same_site": "strict"
  },
  audit_logging=true
)
```

---

## Missing Rollback/Recovery Strategy

### Issue Pattern
```
deploy_feature(name="new_checkout")
```

### Problems
- No rollback plan
- No feature flag
- No monitoring

### Solution
```
deploy_feature(
  name="new_checkout",
  rollout_strategy="gradual",
  percentage_rollout={"initial": 5, "increment": 10, "interval": "1h"},
  feature_flag=true,
  monitoring={
    "error_rate_threshold": 5,
    "latency_threshold": "500ms",
    "auto_rollback": true
  },
  rollback_plan={
    "trigger": "error_rate>5% OR latency>500ms",
    "action": "disable_feature_flag",
    "notification": ["team@example.com", "slack:#incidents"]
  },
  compatibility="backward_compatible",
  database_migrations={
    "forward": "migrations/001_add_checkout_fields.sql",
    "backward": "migrations/001_rollback_checkout.sql"
  }
)
```

---

## Unclear Data Flow

### Issue Pattern
```
sync_data(source="api", destination="database")
```

### Problems
- No transformation logic
- No conflict resolution
- No failure handling

### Solution
```
sync_data(
  source={"type": "api", "endpoint": "https://api.example.com/data", "auth": "bearer"},
  destination={"type": "database", "table": "synced_data"},
  transformation={
    "map_fields": {"external_id": "id", "ext_name": "name"},
    "convert_types": {"date_str": "timestamp"},
    "filter": "status == 'active'"
  },
  conflict_resolution="source_wins",
  sync_frequency="hourly",
  error_handling={
    "api_down": "skip_and_alert",
    "invalid_data": "log_and_continue",
    "database_error": "retry_3_times_then_alert"
  },
  monitoring={
    "track_metrics": ["records_synced", "errors", "duration"],
    "alert_on_failure": true
  },
  idempotency=true
)
```

---

## Pattern Recognition Tips

### Red Flags to Watch For
1. **No auth specified** on sensitive operations
2. **No validation** on user inputs
3. **No error handling** mentioned
4. **Vague terms** like "optimize", "improve", "handle"
5. **No constraints** on resources (time, memory, size)
6. **Missing data types** or formats
7. **No edge cases** considered
8. **Undefined behavior** for failures
9. **No monitoring/logging** specified
10. **Missing rollback** or recovery strategies

### Quick Validation Questions
- Can this fail? How is failure handled?
- Is this protected? Who can access it?
- Is input validated? What happens with bad data?
- What are the performance expectations?
- How do we know it's working? (monitoring)
- Can we roll back if needed?
- What happens under load?
- Are there any security implications?

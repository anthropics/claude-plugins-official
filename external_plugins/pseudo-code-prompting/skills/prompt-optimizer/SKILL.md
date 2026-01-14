# Prompt Optimizer Skill

## Overview
Optimize transformed pseudo-code for token efficiency, clarity, and maintainability. This skill reduces verbosity while preserving semantic meaning and improving readability.

## Core Capabilities

### 1. Token Reduction
Minimize token count without losing information:
- Shorten verbose parameter names
- Use abbreviations for common terms
- Consolidate repetitive structures
- Remove unnecessary qualifiers

### 2. Parameter Consolidation
Combine related parameters into efficient structures:
- Group related boolean flags
- Use objects for related parameters
- Apply sensible defaults
- Eliminate redundant information

### 3. Naming Optimization
Improve function and parameter names for clarity:
- Use consistent naming conventions
- Prefer concise but clear names
- Remove redundant prefixes/suffixes
- Apply domain-standard terminology

### 4. Redundancy Removal
Eliminate duplicate or implied information:
- Remove parameters inferable from context
- Consolidate duplicate constraints
- Eliminate obvious defaults
- Simplify nested structures

## Optimization Techniques

### Technique 1: Parameter Grouping
**Before**:
```
implement_feature(
  enable_caching=true,
  cache_type="redis",
  cache_ttl="3600",
  enable_logging=true,
  log_level="info",
  log_destination="file"
)
```

**After**:
```
implement_feature(
  cache={type:"redis", ttl:3600},
  logging={level:"info", dest:"file"}
)
```

### Technique 2: Smart Defaults
**Before**:
```
create_api_endpoint(
  path="/users",
  method="GET",
  authentication=true,
  authorization=true,
  rate_limiting=true,
  cors_enabled=true
)
```

**After**:
```
create_api_endpoint(
  path="/users",
  secured=true  // implies auth, authz, rate-limit, cors
)
```

### Technique 3: Abbreviation Standards
**Before**:
```
optimize_database_performance(
  target_table="users",
  optimization_type="indexing",
  performance_metric="query_latency",
  measurement_unit="milliseconds"
)
```

**After**:
```
optimize_db(
  table="users",
  type="index",
  metric="latency_ms"
)
```

### Technique 4: Context Inference
**Before**:
```
implement_authentication(
  authentication_type="oauth",
  oauth_provider="google",
  oauth_version="2.0",
  session_type="jwt",
  jwt_algorithm="HS256"
)
```

**After**:
```
implement_auth(
  oauth="google",  // v2.0 implied
  session="jwt"    // HS256 is default
)
```

## Optimization Process

### Step 1: Analyze Current Structure
```
analyze_pseudo_code(
  token_count="[CURRENT]",
  parameter_count="[COUNT]",
  redundancies=[...],
  optimization_potential="[PERCENTAGE]"
)
```

### Step 2: Identify Optimization Opportunities
- Verbose naming
- Redundant parameters
- Unnecessary nesting
- Inferable values
- Consolidation possibilities

### Step 3: Apply Optimizations
```
apply_optimizations(
  techniques=[
    "parameter_grouping",
    "smart_defaults",
    "abbreviation",
    "context_inference"
  ],
  preserve_semantics=true
)
```

### Step 4: Validate Result
```
validate_optimization(
  semantic_equivalence=true,
  clarity_maintained=true,
  token_reduction="[PERCENTAGE]"
)
```

## Optimization Guidelines

### Always Preserve:
- Core semantic meaning
- Critical constraints
- Unique requirements
- Domain-specific details

### Consider Removing:
- Obvious defaults (e.g., `enabled=true` when context implies it)
- Redundant qualifiers (e.g., `user_authentication` → `auth`)
- Verbose parameter names (e.g., `maximum_retry_attempts` → `max_retries`)
- Implied relationships (e.g., `oauth_provider="google"` implies OAuth 2.0)

### Balance Trade-offs:
- **Brevity vs. Clarity**: Don't sacrifice understanding for tokens
- **Consistency vs. Optimization**: Maintain patterns across similar functions
- **Abbreviation vs. Readability**: Use standard abbreviations only
- **Defaults vs. Explicitness**: Make critical values explicit

## Examples

### Example 1: API Endpoint Optimization

**Original (142 tokens)**:
```
create_api_endpoint(
  endpoint_path="/api/v1/users",
  http_method="POST",
  request_body_validation=true,
  validation_schema="strict",
  authentication_required=true,
  authentication_type="jwt",
  authorization_required=true,
  authorization_roles=["admin", "user"],
  rate_limiting_enabled=true,
  rate_limit_requests=100,
  rate_limit_window="60s",
  cors_enabled=true,
  cors_origins=["https://app.example.com"],
  response_format="json",
  error_handling="structured"
)
```

**Optimized (68 tokens, 52% reduction)**:
```
create_endpoint(
  path="/api/v1/users",
  method="POST",
  auth={type:"jwt", roles:["admin","user"]},
  validate="strict",
  rate_limit={req:100, window:"60s"},
  cors=["https://app.example.com"]
)
```

### Example 2: Database Operation Optimization

**Original (89 tokens)**:
```
optimize_database_query(
  target_database="postgres",
  target_table="orders",
  optimization_strategy="indexing",
  index_columns=["customer_id", "order_date"],
  index_type="btree",
  analyze_statistics=true,
  vacuum_after_index=true
)
```

**Optimized (42 tokens, 53% reduction)**:
```
optimize_db(
  table="orders",
  index=["customer_id","order_date"],
  analyze=true
)
```
*Defaults: postgres (from context), btree (standard), vacuum (auto)*

### Example 3: Feature Implementation Optimization

**Original (156 tokens)**:
```
implement_user_authentication_feature(
  authentication_providers=["google", "github", "microsoft"],
  authentication_protocol="oauth2",
  session_management_type="jwt",
  token_expiration_time="24h",
  refresh_token_enabled=true,
  refresh_token_expiration="7d",
  multi_factor_authentication=false,
  password_hashing_algorithm="bcrypt",
  password_salt_rounds=10
)
```

**Optimized (72 tokens, 54% reduction)**:
```
implement_auth(
  providers=["google","github","microsoft"],
  session={type:"jwt", ttl:"24h", refresh:"7d"},
  password={hash:"bcrypt", rounds:10}
)
```

## Optimization Metrics

### Token Efficiency Score
- **Excellent**: >50% reduction with full semantic preservation
- **Good**: 30-50% reduction
- **Acceptable**: 15-30% reduction
- **Minimal**: <15% reduction

### Clarity Impact Assessment
- **Improved**: More readable and concise
- **Maintained**: Same clarity level
- **Slight reduction**: Minor clarity loss, acceptable
- **Degraded**: Clarity significantly impacted (avoid)

## When to Use

### Use this skill when:
- Pseudo-code is verbose or repetitive
- Token budget is constrained
- Clarity can be improved
- Consolidation opportunities exist

### Don't optimize when:
- Explicitness is critical for safety
- Domain requires verbose naming
- Clarity would be significantly compromised
- Original is already optimal

## Integration with Other Skills

- **After prompt-structurer**: Optimize newly created pseudo-code
- **After prompt-analyzer**: Address verbosity issues identified
- **Before requirement-validator**: Ensure optimized code still valid
- **With context-compressor**: Part of overall efficiency strategy

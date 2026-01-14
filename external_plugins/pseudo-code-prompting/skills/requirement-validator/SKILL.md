# Requirement Validator

Validate transformed pseudo-code to ensure completeness, correctness, and clarity of requirements.

## Purpose

The Requirement Validator skill analyzes transformed pseudo-code to identify:
- Missing or incomplete parameters
- Ambiguous requirements
- Edge cases not covered
- Potential implementation risks
- Constraint violations

## When to Use

Use this skill when:
- You've transformed natural language to pseudo-code
- You need to verify requirement completeness
- You're about to implement a feature
- You want to catch gaps before development
- You're reviewing transformation quality

## Validation Process

### 1. Parameter Completeness Check
Verify all required parameters are present:
- Required vs. optional parameters identified
- Parameter types specified where needed
- Default values provided appropriately
- Parameter constraints defined

### 2. Constraint Validation
Check for necessary constraints:
- Security requirements (auth, permissions)
- Performance constraints (timeouts, limits)
- Data validation rules
- Compatibility requirements
- Business logic constraints

### 3. Edge Case Identification
Identify scenarios not explicitly covered:
- Error handling requirements
- Boundary conditions
- Null/empty value handling
- Concurrent access scenarios
- Failure mode behaviors

### 4. Requirement Clarity
Assess clarity and specificity:
- Vague terms flagged for clarification
- Measurable criteria defined
- Success conditions explicit
- Acceptance criteria clear

## Validation Criteria

### High Priority Issues (Must Fix)
- Missing critical parameters (auth, data sources)
- Security vulnerabilities (no auth specified)
- Data loss risks (no validation)
- Undefined error handling

### Medium Priority Issues (Should Fix)
- Missing optional parameters that affect UX
- Incomplete constraint specifications
- Ambiguous naming or descriptions
- Missing edge case handling

### Low Priority Issues (Nice to Have)
- Additional optimization opportunities
- Enhanced error messages
- Extra validation rules
- Documentation improvements

## Output Format

```
Requirement Validation Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Function: function_name(params...)

✓ PASSED CHECKS
- [Check description]
- [Check description]

⚠ WARNINGS (Medium Priority)
- [Warning description + suggestion]
- [Warning description + suggestion]

✗ CRITICAL ISSUES (Must Fix)
- [Issue description + required action]
- [Issue description + required action]

📋 EDGE CASES TO CONSIDER
- [Edge case description]
- [Edge case description]

💡 RECOMMENDATIONS
- [Recommendation]
- [Recommendation]

Overall Status: [READY/NEEDS REVIEW/BLOCKED]
```

## Validation Checklist

### Security Validation
- [ ] Authentication requirements specified
- [ ] Authorization/permissions defined
- [ ] Input validation requirements present
- [ ] Sensitive data handling specified
- [ ] Rate limiting considered (for APIs)

### Data Validation
- [ ] Required fields identified
- [ ] Data types specified
- [ ] Value constraints defined (min/max, regex)
- [ ] Relationship constraints specified
- [ ] Data persistence strategy clear

### Error Handling
- [ ] Error scenarios identified
- [ ] Error messages defined
- [ ] Fallback behaviors specified
- [ ] Logging requirements present
- [ ] User feedback mechanism defined

### Performance Validation
- [ ] Scalability requirements present
- [ ] Timeout values specified
- [ ] Resource limits defined
- [ ] Caching strategy considered
- [ ] Optimization criteria clear

### Integration Validation
- [ ] Dependencies identified
- [ ] API contracts specified
- [ ] Data format requirements clear
- [ ] Compatibility constraints defined
- [ ] Migration strategy present (if needed)

## Examples

### Example 1: Authentication Feature

**Input:**
```
implement_authentication(type="oauth", providers=["google"])
```

**Validation Report:**
```
⚠ WARNINGS
- Missing token_ttl parameter (default lifespan?)
- No refresh token strategy specified
- Missing user data storage specification

✗ CRITICAL ISSUES
- No error handling for failed authentication
- Missing redirect_uri specification
- No logout mechanism defined

📋 EDGE CASES
- What happens if user denies consent?
- Handle expired tokens during active session
- Multiple concurrent login attempts
```

**Improved Version:**
```
implement_authentication(
  type="oauth",
  providers=["google"],
  token_ttl="1h",
  refresh_token=true,
  redirect_uri="/auth/callback",
  error_handling="redirect_to_login",
  user_data_storage="database",
  logout_endpoint="/auth/logout",
  session_management="jwt"
)
```

### Example 2: API Endpoint

**Input:**
```
create_endpoint(path="/api/users", method="POST")
```

**Validation Report:**
```
✗ CRITICAL ISSUES
- No authentication requirement specified
- Missing request body schema
- No response format defined
- No error responses specified

⚠ WARNINGS
- Rate limiting not mentioned
- No validation rules for input
- Missing CORS configuration

📋 EDGE CASES
- Duplicate user creation attempts
- Invalid data format handling
- Database connection failures
```

**Improved Version:**
```
create_endpoint(
  path="/api/users",
  method="POST",
  auth=true,
  request_schema={
    "name": "string:required:max(100)",
    "email": "email:required:unique",
    "role": "enum[user,admin]:optional:default(user)"
  },
  response_format={"user_id": "string", "created_at": "timestamp"},
  error_responses={
    "400": "invalid_input",
    "409": "duplicate_email",
    "500": "server_error"
  },
  rate_limit="100/hour",
  cors=["https://app.example.com"]
)
```

## Integration with Other Skills

- **Works After**: prompt-structurer, prompt-optimizer
- **Triggers**: prompt-analyzer (for ambiguity scoring)
- **Provides To**: Implementation phase, code generation

## Best Practices

1. **Always validate before implementation** - Catch issues early
2. **Use domain knowledge** - Apply security, performance patterns
3. **Think about edge cases** - Consider failure modes
4. **Be specific in recommendations** - Provide actionable fixes
5. **Prioritize issues** - Focus on critical gaps first
6. **Consider context** - Simple scripts need less validation than production APIs

## Common Validation Patterns

### Authentication/Authorization
```
Missing: auth requirement
Add: auth=true, roles=["admin"], permissions=["users:write"]
```

### Data Validation
```
Missing: input validation
Add: validation_rules={"field": "type:required:constraints"}
```

### Error Handling
```
Missing: error handling
Add: error_handling="strategy", fallback="behavior"
```

### Performance
```
Missing: scalability constraints
Add: scale="size", cache=true, timeout="duration"
```

### Integration
```
Missing: dependency specification
Add: depends_on=["service"], api_version="v1"
```

## Tips for Effective Validation

1. **Check against domain patterns** - Use reference libraries for common scenarios
2. **Look for implicit assumptions** - Make them explicit
3. **Validate completeness** - Can this be implemented without questions?
4. **Consider maintenance** - Is this clear for future developers?
5. **Think production-ready** - Security, performance, monitoring

## Success Criteria

A well-validated requirement should:
- Have all critical parameters specified
- Include necessary constraints and validation
- Address common edge cases
- Be implementable without ambiguity
- Consider security and performance
- Define clear success/failure conditions

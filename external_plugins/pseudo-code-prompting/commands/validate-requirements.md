---
description: Validate pseudo-code requirements for completeness and correctness
argument-hint: [pseudo-code]
---

# Validate Requirements

Analyze transformed pseudo-code to identify missing parameters, ambiguous requirements, and potential implementation risks.

## Task

Validate the following pseudo-code: `$ARGUMENTS`

Apply comprehensive requirement validation:

1. **Parameter Completeness** - Verify all required parameters are present
2. **Constraint Validation** - Check for necessary security, performance, and data constraints
3. **Edge Case Identification** - Identify unhandled scenarios and boundary conditions
4. **Clarity Assessment** - Flag vague terms and ensure specificity

## Validation Checklist

Use the requirement-validator skill capabilities:

### Security Requirements
- [ ] Authentication specified (if needed)
- [ ] Authorization/permissions defined
- [ ] Input validation requirements present
- [ ] Sensitive data handling specified

### Data Requirements
- [ ] Data sources identified
- [ ] Data formats specified
- [ ] Validation rules defined
- [ ] Storage strategy clear

### Error Handling
- [ ] Error scenarios identified
- [ ] Error responses defined
- [ ] Fallback behaviors specified
- [ ] Logging requirements present

### Performance Requirements
- [ ] Scalability needs specified
- [ ] Timeout values defined
- [ ] Resource limits present
- [ ] Caching strategy considered

## Output Format

Return validation results in this format:

```
Requirement Validation Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Function: [function_name]

✓ PASSED CHECKS
- [Check description]

⚠ WARNINGS (Medium Priority)
- [Warning description + suggestion]

✗ CRITICAL ISSUES (Must Fix)
- [Issue description + required action]

📋 EDGE CASES TO CONSIDER
- [Edge case description]

💡 RECOMMENDATIONS
- [Recommendation]

Overall Status: [READY/NEEDS REVIEW/BLOCKED]
```

## Issue Severity Levels

- **Critical**: Missing auth, no validation, security vulnerabilities, data loss risks
- **High**: Missing important parameters, ambiguous requirements, incomplete error handling
- **Medium**: Missing optional parameters, documentation gaps, optimization opportunities
- **Low**: Nice-to-have features, enhanced UX details

## Key Validation Patterns

- Authentication: Check for auth=true, roles, permissions
- Data Validation: Look for validation rules, constraints, formats
- Error Handling: Verify error_handling strategy exists
- Performance: Check for timeouts, caching, scale considerations
- Integration: Verify dependencies, API versions specified

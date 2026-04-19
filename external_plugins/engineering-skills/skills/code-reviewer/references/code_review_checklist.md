# Code Review Checklist

Structured checklists for systematic code review across different aspects.

---

## Table of Contents

- [Pre-Review Checks](#pre-review-checks)
- [Correctness](#correctness)
- [Security](#security)
- [Performance](#performance)
- [Maintainability](#maintainability)
- [Testing](#testing)
- [Documentation](#documentation)
- [Language-Specific Checks](#language-specific-checks)

---

## Pre-Review Checks

Before diving into code, verify these basics:

### Build and Tests
- [ ] Code compiles without errors
- [ ] All existing tests pass
- [ ] New tests are included for new functionality
- [ ] No unintended files included (build artifacts, IDE configs)

### PR Hygiene
- [ ] PR has clear title and description
- [ ] Changes are scoped appropriately (not too large)
- [ ] Commits follow conventional commit format
- [ ] Branch is up to date with base branch

### Scope Verification
- [ ] Changes match the stated purpose
- [ ] No unrelated changes bundled in
- [ ] Breaking changes are documented
- [ ] Migration path provided if needed

---

## Correctness

### Logic
- [ ] Algorithm implements requirements correctly
- [ ] Edge cases handled (null, empty, boundary values)
- [ ] Off-by-one errors checked
- [ ] Correct operators used (== vs ===, & vs &&)
- [ ] Loop termination conditions correct
- [ ] Recursion has proper base cases

### Data Handling
- [ ] Data types appropriate for the use case
- [ ] Numeric overflow/underflow considered
- [ ] Date/time handling accounts for timezones
- [ ] Unicode and internationalization handled
- [ ] Data validation at entry points

### State Management
- [ ] State transitions are valid
- [ ] Race conditions addressed
- [ ] Concurrent access handled correctly
- [ ] State cleanup on errors/exit

### Error Handling
- [ ] Errors caught at appropriate levels
- [ ] Error messages are actionable
- [ ] Errors don't expose sensitive information
- [ ] Recovery or graceful degradation implemented
- [ ] Resources cleaned up in error paths

---

## Security

### Input Validation
- [ ] All user input validated and sanitized
- [ ] Input length limits enforced
- [ ] File uploads validated (type, size, content)
- [ ] URL parameters validated

### Injection Prevention
- [ ] SQL queries parameterized
- [ ] Command execution uses safe APIs
- [ ] HTML output escaped to prevent XSS
- [ ] LDAP queries properly escaped
- [ ] XML parsing disables external entities

### Authentication & Authorization
- [ ] Authentication required for protected resources
- [ ] Authorization checked before operations
- [ ] Session management secure
- [ ] Password handling follows best practices
- [ ] Token expiration implemented

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] PII handled according to policy
- [ ] Secrets not hardcoded
- [ ] Logs don't contain sensitive data

### API Security
- [ ] Rate limiting implemented
- [ ] CORS configured correctly
- [ ] CSRF protection in place
- [ ] API keys/tokens secured
- [ ] Endpoints use HTTPS

---

## Performance

### Efficiency
- [ ] Appropriate data structures used
- [ ] Algorithms have acceptable complexity
- [ ] Database queries are optimized
- [ ] N+1 query problems avoided
- [ ] Indexes used where beneficial

### Resource Usage
- [ ] Memory usage bounded
- [ ] No memory leaks
- [ ] File handles properly closed
- [ ] Database connections pooled
- [ ] Network calls minimized

### Caching
- [ ] Appropriate caching strategy
- [ ] Cache invalidation handled
- [ ] Cache keys are unique and predictable
- [ ] TTL values appropriate

### Scalability
- [ ] Horizontal scaling considered
- [ ] Bottlenecks identified
- [ ] Async processing for long operations
- [ ] Batch operations where appropriate

---

## Maintainability

### Code Quality
- [ ] Functions/methods have single responsibility
- [ ] Classes follow SOLID principles
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] No dead code or commented-out code
- [ ] Magic numbers replaced with constants

### Naming
- [ ] Names are descriptive and consistent
- [ ] Naming follows project conventions
- [ ] No abbreviations that obscure meaning
- [ ] Boolean variables/functions have is/has/can prefix

### Structure
- [ ] Functions are appropriately sized (<50 lines preferred)
- [ ] Nesting depth is reasonable (<4 levels)
- [ ] Related code is grouped together
- [ ] Dependencies are minimal and explicit

### Readability
- [ ] Code is self-documenting where possible
- [ ] Complex logic has explanatory comments
- [ ] Formatting is consistent
- [ ] No overly clever or obscure code

---

## Testing

### Coverage
- [ ] New code has unit tests
- [ ] Critical paths have integration tests
- [ ] Edge cases are tested
- [ ] Error conditions are tested

### Quality
- [ ] Tests are independent
- [ ] Tests have clear assertions
- [ ] Test names describe what is tested
- [ ] Tests don't depend on external state

### Mocking
- [ ] External dependencies are mocked
- [ ] Mocks are realistic
- [ ] Mock setup is not excessive

---

## Documentation

### Code Documentation
- [ ] Public APIs are documented
- [ ] Complex algorithms explained
- [ ] Non-obvious decisions documented
- [ ] TODO/FIXME comments have context

### External Documentation
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Changelog updated
- [ ] Migration guides provided

---

## Language-Specific Checks

### TypeScript/JavaScript
- [ ] Types are explicit (avoid `any`)
- [ ] Null checks present (`?.`, `??`)
- [ ] Async/await errors handled
- [ ] No floating promises
- [ ] Memory leaks from closures checked

### Python
- [ ] Type hints used for public APIs
- [ ] Context managers for resources (`with` statements)
- [ ] Exception handling is specific (not bare `except`)
- [ ] No mutable default arguments
- [ ] List comprehensions used appropriately

### Go
- [ ] Errors checked and handled
- [ ] Goroutine leaks prevented
- [ ] Context propagation correct
- [ ] Defer statements in right order
- [ ] Interfaces minimal

### Swift
- [ ] Optionals handled safely
- [ ] Memory management correct (weak/unowned)
- [ ] Error handling uses Result or throws
- [ ] Access control appropriate
- [ ] Codable implementation correct

### Kotlin
- [ ] Null safety leveraged
- [ ] Coroutine cancellation handled
- [ ] Data classes used appropriately
- [ ] Extension functions don't obscure behavior
- [ ] Sealed classes for state

---

## Review Process Tips

### Before Approving
1. Verify all critical checks passed
2. Confirm tests are adequate
3. Consider deployment impact
4. Check for any security concerns
5. Ensure documentation is updated

### Providing Feedback
- Be specific about issues
- Explain why something is problematic
- Suggest alternatives when possible
- Distinguish blockers from suggestions
- Acknowledge good patterns

### When to Block
- Security vulnerabilities present
- Critical logic errors
- No tests for risky changes
- Breaking changes without migration
- Significant performance regressions

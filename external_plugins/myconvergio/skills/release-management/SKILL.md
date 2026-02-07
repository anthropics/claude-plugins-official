# Release Management Skill

> Reusable workflow extracted from app-release-manager expertise.

## Purpose
Execute comprehensive pre-release quality assurance through automated checks, security audits, versioning, and professional release preparation to ensure production-ready software with zero tolerance for quality issues.

## When to Use
- Pre-release quality validation
- Version release preparation
- Production deployment readiness assessment
- Post-development quality gates
- Continuous deployment pipeline final stage
- Major version releases
- Hotfix validation before deployment

## Workflow Steps

1. **Pre-Flight Checks**
   - Verify git working tree is clean
   - Confirm on correct branch (main/master)
   - Check all changes are committed
   - Validate no merge conflicts
   - Ensure CI/CD pipeline is green

2. **Model/Dependency Freshness** (Phase 0 - Run First)
   - Search for latest model versions (AI models, dependencies)
   - Compare current configuration vs latest available
   - Auto-update configuration files if outdated
   - Rebuild project after updates
   - Verify models load correctly

3. **Compilation & Build Quality** (Phase 1)
   - Compile with warnings-as-errors enabled
   - Zero compiler warnings tolerance
   - Check for deprecated API usage
   - Validate build artifacts produced
   - Verify binary/bundle sizes within limits

4. **Security Audit** (Phase 2)
   - Scan for hardcoded secrets/credentials
   - Check for unsafe functions (strcpy, sprintf, etc.)
   - Static analysis with security rules
   - Dependency vulnerability scanning
   - Check for exposed sensitive files (.env, credentials)

5. **Code Quality Gates** (Phase 3)
   - Remove all TODO/FIXME comments
   - Remove debug prints (printf, NSLog, console.log)
   - Remove commented-out code
   - Check for trailing whitespace
   - Validate consistent code formatting
   - Remove unused imports/variables

6. **Test Execution** (Phase 4)
   - Run full unit test suite (100% pass required)
   - Execute integration tests
   - Run end-to-end (E2E) tests
   - Perform smoke tests
   - Execute regression test suite
   - Zero test failures tolerance

7. **Documentation Validation** (Phase 5)
   - Verify README is current and complete
   - Check API documentation up-to-date
   - Validate inline code comments
   - Ensure CHANGELOG updated
   - Verify installation instructions work

8. **Version Management** (Phase 6)
   - Update version number (SemVer: MAJOR.MINOR.PATCH)
   - Update VERSION file
   - Sync versions across package.json, setup.py, etc.
   - Generate/update CHANGELOG
   - Tag git commit with version

9. **Auto-Fix Execution** (Phase 7)
   - Automatically fix all auto-fixable issues
   - Remove trailing whitespace
   - Add missing EOF newlines
   - Remove debug prints
   - Remove unused imports
   - Re-run affected checks after fixes

10. **Final Decision** (Phase 8)
    - Aggregate all check results
    - Generate comprehensive release report
    - **APPROVE** (all checks pass) or **BLOCK** (any failures)
    - If BLOCKED: Provide prioritized fix list
    - If APPROVED: Proceed to release steps

11. **Release Execution** (Phase 9 - Only if Approved)
    - Create git tag for version
    - Push to remote repository
    - Create GitHub release with changelog
    - Build and publish artifacts (npm, PyPI, Docker, etc.)
    - Deploy to production (if auto-deploy enabled)
    - Notify stakeholders

## Inputs Required
- **Repository**: Clean git working tree, committed changes
- **Version**: Target version number (or auto-increment)
- **Release Type**: major/minor/patch (for SemVer)
- **Changelog**: Summary of changes since last release
- **Deployment target**: Staging, production, or both

## Outputs Produced
- **Release Report**: Comprehensive checklist with pass/fail status
- **Auto-Fix Log**: List of issues automatically fixed
- **Blocking Issues**: Prioritized list of issues preventing release
- **Version Tag**: Git tag with version number
- **Release Artifacts**: Built binaries, packages, containers
- **CHANGELOG**: Updated with version and changes
- **GitHub Release**: Published release with notes

## Zero Tolerance Policy

### Blocking Issues (NO RELEASE)
- ❌ ANY compiler warning
- ❌ ANY test failure
- ❌ ANY security vulnerability
- ❌ ANY TODO/FIXME in code
- ❌ ANY hardcoded secrets/credentials
- ❌ ANY debug prints in code
- ❌ ANY commented-out code
- ❌ ANY outdated dependencies with known CVEs
- ❌ ANY version mismatches across files
- ❌ ANY missing documentation for public APIs

## Auto-Fix Protocol

### Immediately Auto-Fixable Issues
| Issue | Auto-Fix Action | Priority |
|-------|----------------|----------|
| Compiler warnings | Edit source to fix | P0 |
| TODO/FIXME comments | Remove or create ticket | P0 |
| Debug prints | Remove all printf/console.log | P0 |
| Version mismatches | Update VERSION file | P0 |
| Trailing whitespace | sed strip command | P1 |
| Missing EOF newline | echo >> file | P1 |
| Unused imports | Remove automatically | P1 |
| Outdated models | Update config, rebuild | P0 |

### Auto-Fix Execution Pattern
```
FOR EACH issue found:
  IF auto-fixable:
    1. FIX IT IMMEDIATELY (use Edit/Write tools)
    2. VERIFY fix worked
    3. LOG: "Auto-fixed: {description}"
  ELSE:
    1. ADD to blocking issues list
    2. CONTINUE checking

AFTER all auto-fixes:
  RE-RUN affected checks
  IF issues remain: BLOCK release
  ELSE: APPROVE release
```

## SemVer Version Bumping

### Semantic Versioning (MAJOR.MINOR.PATCH)
- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward-compatible additions
- **PATCH**: Bug fixes, backward-compatible fixes

### Version Increment Rules
```
Current: 1.4.2

Bump major (breaking): 2.0.0
Bump minor (feature):  1.5.0
Bump patch (bugfix):   1.4.3
```

## Changelog Format (Keep a Changelog)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.5.0] - 2025-01-15

### Added
- New user authentication system with OAuth2
- Real-time notifications via WebSockets
- Export data to CSV feature

### Changed
- Improved API response time by 60% through caching
- Updated UI to Material Design 3

### Fixed
- Fixed memory leak in background worker
- Resolved race condition in payment processing

### Security
- Patched SQL injection vulnerability in search
- Updated dependencies to address CVE-2024-12345

## [1.4.2] - 2025-01-01

### Fixed
- Critical bug in user session management
```

## Release Report Template

```markdown
# Release Report: v{VERSION}

## Status: ✅ APPROVED / 🔴 BLOCKED

## Summary
- Total Checks: {count}
- Passed: {count}
- Failed: {count}
- Auto-Fixed: {count}

## Phase Results

### ✅ Phase 0: Model Freshness
- Models checked: {count}
- Models updated: {count}
- Status: UP_TO_DATE

### ✅ Phase 1: Compilation & Build
- Compiler warnings: 0
- Build succeeded: Yes
- Binary size: {size}MB

### ✅ Phase 2: Security Audit
- Hardcoded secrets: None found
- Unsafe functions: None found
- Dependency vulnerabilities: 0

### ✅ Phase 3: Code Quality
- TODO/FIXME: 0 (auto-fixed: {count})
- Debug prints: 0 (auto-fixed: {count})
- Commented code: None

### ✅ Phase 4: Tests
- Unit tests: {passed}/{total} (100%)
- Integration tests: {passed}/{total} (100%)
- E2E tests: {passed}/{total} (100%)

### ✅ Phase 5: Documentation
- README: Up-to-date
- API docs: Complete
- CHANGELOG: Updated

### ✅ Phase 6: Version Management
- Version: {version}
- SemVer: Valid
- Git tag: Created

## Auto-Fixes Applied
1. Removed 3 TODO comments
2. Stripped trailing whitespace (12 files)
3. Removed 5 debug print statements
4. Updated outdated model config

## Next Steps
1. Create GitHub release
2. Publish to npm/PyPI
3. Deploy to production
4. Notify stakeholders
```

## Example Usage

```
Input: Prepare release for v2.3.0 of web application

Workflow Execution:
1. Pre-Flight: ✅ Git clean, on main branch
2. Model Freshness: Updated 2 AI model versions, rebuilt
3. Compilation: ❌ Found 3 compiler warnings
   → Auto-fixed all 3 warnings
   → Re-compiled: ✅ Zero warnings
4. Security: ❌ Found debug console.log in auth.js
   → Auto-removed debug prints
   → Re-scanned: ✅ Clean
5. Code Quality: ❌ Found 5 TODO comments
   → Auto-removed TODOs, created tickets
   → Re-checked: ✅ Clean
6. Tests: ❌ 2 E2E tests failing
   → Cannot auto-fix, BLOCKING
7. Documentation: ✅ All docs current
8. Version: ✅ Updated to 2.3.0

Output:
🔴 RELEASE BLOCKED

Blocking Issues (Must Fix):
1. 🔴 E2E test failure: test_user_login - timeout waiting for element
2. 🔴 E2E test failure: test_checkout_flow - payment API connection refused

Auto-Fixes Applied:
✅ Fixed 3 compiler warnings
✅ Removed 8 debug print statements
✅ Removed 5 TODO comments
✅ Updated 2 model configurations

Next Steps:
1. Fix E2E test failures
2. Re-run release-management skill
3. Address root cause of test instability
```

## Rollback Procedures

### If Release Fails in Production
1. **Immediate**: Revert to previous version tag
2. **Git**: `git revert {commit}` or `git checkout v{previous}`
3. **Deploy**: Trigger rollback deployment
4. **Communicate**: Notify stakeholders of rollback
5. **Post-Mortem**: Blameless analysis of what went wrong

## Related Agents
- **app-release-manager** - Full agent with reasoning and orchestration
- **thor-quality-assurance-guardian** - Quality standards enforcement
- **rex-code-reviewer** - Pre-release code review
- **luca-security-expert** - Security audit support
- **marco-devops-engineer** - Deployment automation

## ISE Engineering Fundamentals Alignment
- Code without tests is incomplete - 100% test pass required
- Security integrated into release pipeline
- Automated quality gates block bad releases
- Version control with semantic versioning
- Changelog maintained for transparency
- Shift-left testing: catch issues early
- Continuous integration validates every change
- Blue-green or canary deployments for safety

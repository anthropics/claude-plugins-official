---
name: audit-lite
description: Generate a risk checklist (not an audit)
---

# ContractKit: Audit-Lite

Generate a risk register and checklist. **This is NOT an audit.**

## Disclaimer

```
╔════════════════════════════════════════════════════════════════╗
║                        NOT AN AUDIT                            ║
║                                                                ║
║  This is an automated risk checklist, not a security audit.   ║
║  It cannot replace professional security review.              ║
║  Do not deploy to mainnet based solely on this report.        ║
╚════════════════════════════════════════════════════════════════╝
```

## Process

### 1. Run Tests

```bash
forge test -vvv
```

Report: pass/fail count, any failures

### 2. Check Coverage (if available)

```bash
forge coverage
```

Report: line/branch coverage percentages

### 3. Run Slither (if installed)

```bash
slither . --json slither-output.json
```

If not installed, note it as skipped and suggest installation.

### 4. Static Analysis

Analyze contract source for:

- **Access Control**
  - Are admin functions protected?
  - Can roles be granted/revoked appropriately?
  - Is there a single point of failure (single admin key)?

- **External Calls**
  - Are there calls to external contracts?
  - Is reentrancy protected?
  - Are return values checked?

- **Upgradeability**
  - Is the contract upgradeable?
  - Who controls upgrades?
  - Is there a time-lock?

- **Admin Powers**
  - What can admins do?
  - Can admins rug users?
  - Are there emergency functions?

- **Events**
  - Are state changes logged?
  - Can off-chain systems monitor activity?

### 5. Generate Risk Register

## Output Format

```markdown
# Audit-Lite Report

**NOT AN AUDIT** - This is an automated checklist.

Generated: [date]
Project: [name]

## Test Results

- Tests: X passed, Y failed
- Coverage: Z% (if available)

## Risk Register

### Access Control

| Risk | Severity | Status | Notes |
|------|----------|--------|-------|
| Single admin key | Medium | Open | Consider multi-sig |
| Unrestricted minting | High | Mitigated | Role-protected |

### External Calls

| Risk | Severity | Status | Notes |
|------|----------|--------|-------|
| Reentrancy | High | N/A | No external calls |

### Upgradeability

| Risk | Severity | Status | Notes |
|------|----------|--------|-------|
| Malicious upgrade | Critical | N/A | Not upgradeable |

### Admin Powers

| Risk | Severity | Status | Notes |
|------|----------|--------|-------|
| Unlimited minting | High | Open | Minter can inflate supply |

### Events

| Check | Status |
|-------|--------|
| Transfer events | OK |
| Role change events | OK |
| Mint events | OK |

## Recommendations

1. [Specific recommendation]
2. [Specific recommendation]

## Before Mainnet

- [ ] Professional security audit
- [ ] Multi-sig for admin roles
- [ ] Monitoring and alerting
- [ ] Incident response plan
- [ ] Bug bounty program
```

## Severity Levels

| Level | Description |
|-------|-------------|
| Critical | Can lead to total loss of funds |
| High | Can lead to significant loss or DoS |
| Medium | Can cause unexpected behavior |
| Low | Best practice violation |
| Info | Informational finding |

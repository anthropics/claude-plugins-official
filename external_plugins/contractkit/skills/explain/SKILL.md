---
name: explain
description: Explain what a contract does and its risks
---

# ContractKit: Explain

Explain what a contract does, who can do what, and potential risks.

## Usage

```
/contractkit:explain [mode]
```

Modes:
- `standard` (default) - Balanced technical explanation
- `paranoid` - Focus on risks and attack vectors
- `vc` - Business-focused, what does it enable
- `lawyer` - Formal, focuses on rights and obligations

## Process

### 1. Read Contract Sources

Read all `.sol` files in `src/`:
```bash
find src -name "*.sol"
```

### 2. Read Documentation

Check for:
- `README.md`
- `SECURITY.md`
- `THREAT_MODEL.md`

### 3. Analyze and Generate Report

Generate a report covering:

#### What This Contract Does
- Core functionality in plain language
- What problem it solves
- Key features

#### Who Can Do What
| Role | Capabilities |
|------|--------------|
| Owner/Admin | ... |
| Minter | ... |
| Anyone | ... |

#### Risk Summary
- Access control risks
- Economic risks
- Technical risks

#### Things to Review Before Mainnet
- Checklist of items to verify
- Suggested auditor focus areas

## Output Format

### Standard Mode

```markdown
## What This Contract Does

[Plain language description]

## Who Can Do What

| Role | Capabilities |
|------|--------------|
| ... | ... |

## Risk Summary

- **Access Control**: [risks]
- **Economic**: [risks]
- **Technical**: [risks]

## Before Mainnet

- [ ] Item 1
- [ ] Item 2
```

### Paranoid Mode

Focus on attack vectors, worst-case scenarios, and trust assumptions.

### VC Mode

Focus on value proposition, market fit, and business model implications.

### Lawyer Mode

Formal language, focus on rights, obligations, and liability considerations.

## Example

User: `/contractkit:explain`

```markdown
## What This Contract Does

This is an ERC20 token with role-based minting. Designated minters
can create new tokens, while a separate admin role controls who
can mint.

## Who Can Do What

| Role | Capabilities |
|------|--------------|
| DEFAULT_ADMIN_ROLE | Grant/revoke roles, including minter |
| MINTER_ROLE | Mint new tokens to any address |
| Token Holder | Transfer, approve, transferFrom |
| Anyone | View balances and allowances |

## Risk Summary

- **Access Control**: Admin key compromise enables unlimited minting
- **Economic**: No supply cap; minters can inflate supply
- **Technical**: Standard OZ implementation, well-tested

## Before Mainnet

- [ ] Transfer admin to multi-sig
- [ ] Implement minting limits or caps
- [ ] Set up monitoring for large mints
- [ ] Get security audit
```

# Security Posture

ContractKit's approach to security.

## Philosophy

1. **Templates are starting points, not production code**
2. **Security is the user's responsibility**
3. **Minimal attack surface**
4. **No network calls beyond user-specified RPC**

## What ContractKit Does NOT Do

- Store or transmit private keys
- Make network calls except to user-specified RPC
- Auto-deploy to mainnet
- Provide audit guarantees
- Handle user funds

## Upgradeability Stance

ContractKit templates are **non-upgradeable by default**.

Upgradeable contracts introduce significant complexity and risk:
- Proxy admin key compromise
- Storage layout collisions
- Implementation bugs
- Governance attacks

If you need upgradeability:
1. Understand the risks thoroughly
2. Use OpenZeppelin's upgrade patterns
3. Implement time-locks
4. Use multi-sig governance
5. Get professional audit

## Admin Key Risks

All templates grant admin rights to the deployer. This is a single point of failure.

**Before mainnet:**
- Transfer admin to multi-sig
- Consider time-locks for sensitive operations
- Document admin capabilities
- Plan for key rotation

## Why "Audit-Lite" is NOT an Audit

`/contractkit:audit-lite` provides:
- Automated static analysis
- Common vulnerability checks
- Risk categorization

It does NOT provide:
- Manual code review
- Business logic analysis
- Economic attack modeling
- Formal verification
- Security guarantees

**Always get professional audit before mainnet.**

## Key Handling

ContractKit never:
- Asks for private keys
- Stores keys anywhere
- Transmits keys over network

Keys are used by:
- Forge/Cast tools locally
- User's environment variables
- Hardware wallets (via RPC)

**User responsibilities:**
- Secure `.env` files
- Use `.gitignore` properly
- Use hardware wallets for mainnet
- Never share keys

## Dependency Security

Templates use:
- OpenZeppelin Contracts (audited, pinned version)
- Foundry tools (open source, widely used)

We:
- Pin dependency versions
- Review OpenZeppelin releases before updating
- Minimize external dependencies

## Reporting Security Issues

See [SECURITY.md](../../../SECURITY.md) for responsible disclosure.

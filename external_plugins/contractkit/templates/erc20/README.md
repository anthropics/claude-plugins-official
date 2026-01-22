# {{PROJECT_NAME}}

An ERC20 token with role-based access control.

## Overview

This token uses OpenZeppelin's ERC20 and AccessControl contracts:

- **MINTER_ROLE**: Can mint new tokens
- **DEFAULT_ADMIN_ROLE**: Can grant/revoke roles

## Quick Start

```bash
# Install dependencies
forge install

# Run tests
forge test

# Deploy locally
anvil &
forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
```

## Functions

| Function | Access | Description |
|----------|--------|-------------|
| `mint(to, amount)` | MINTER_ROLE | Mint tokens to an address |
| `transfer(to, amount)` | Public | Transfer tokens |
| `approve(spender, amount)` | Public | Approve spending |
| `grantRole(role, account)` | Admin | Grant a role |
| `revokeRole(role, account)` | Admin | Revoke a role |

## Security

See [SECURITY.md](SECURITY.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

**This contract has not been audited. Do not deploy to mainnet without security review.**

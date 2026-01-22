# {{PROJECT_NAME}}

A simple ETH vault with deposit, withdraw, and pause functionality.

## Overview

This vault contract allows users to:

- **Deposit** ETH and track their balance
- **Withdraw** specific amounts or all funds
- **Pause/Unpause** (admin only) to halt operations in emergencies

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
| `deposit()` | Anyone | Deposit ETH (payable) |
| `withdraw(amount)` | Depositor | Withdraw specific amount |
| `withdrawAll()` | Depositor | Withdraw entire balance |
| `pause()` | PAUSER_ROLE | Pause all operations |
| `unpause()` | PAUSER_ROLE | Resume operations |
| `balanceOf(account)` | View | Check account balance |
| `totalDeposits()` | View | Total ETH deposited |
| `vaultBalance()` | View | Actual contract balance |

## Roles

| Role | Capabilities |
|------|--------------|
| DEFAULT_ADMIN_ROLE | Grant/revoke roles |
| PAUSER_ROLE | Pause/unpause vault |

## Security Features

- **ReentrancyGuard**: Prevents reentrancy attacks on withdrawals
- **Pausable**: Emergency stop mechanism
- **Access Control**: Role-based permissions

## Security

See [SECURITY.md](SECURITY.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

**This contract has not been audited. Do not deploy to mainnet without security review.**

# {{PROJECT_NAME}}

A three-party escrow contract with release, refund, and dispute resolution.

## Overview

This escrow contract facilitates secure payments between parties:

- **Payer**: Deposits funds, can release to payee or initiate dispute
- **Payee**: Can refund to payer or initiate dispute
- **Arbiter**: Resolves disputes by awarding funds to payer or payee

## States

| State | Description |
|-------|-------------|
| Created | Escrow created, awaiting funding |
| Funded | Funds deposited, awaiting release/refund |
| Released | Funds sent to payee |
| Refunded | Funds returned to payer |
| Disputed | Dispute initiated, awaiting arbiter resolution |

## Quick Start

```bash
# Install dependencies
forge install

# Run tests
forge test

# Set environment variables for deployment
export PAYEE_ADDRESS=0x...
export ARBITER_ADDRESS=0x...
export ESCROW_AMOUNT=1000000000000000000  # 1 ETH in wei

# Deploy locally
anvil &
forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
```

## Functions

| Function | Caller | Description |
|----------|--------|-------------|
| `fund()` | Payer | Deposit the agreed amount |
| `release()` | Payer | Release funds to payee |
| `refund()` | Payee | Return funds to payer |
| `dispute()` | Payer/Payee | Initiate a dispute |
| `resolve(winner)` | Arbiter | Award funds to winner |

## Flow

```
1. Deploy: Payer creates escrow specifying payee, arbiter, amount
2. Fund: Payer deposits exact amount
3. Complete:
   - Happy path: Payer calls release() → funds go to payee
   - Refund path: Payee calls refund() → funds go to payer
   - Dispute path: Either party calls dispute() → arbiter resolves
```

## Security

See [SECURITY.md](SECURITY.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

**This contract has not been audited. Do not deploy to mainnet without security review.**

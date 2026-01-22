# {{PROJECT_NAME}}

An ERC721 NFT collection with role-based access control.

## Overview

This NFT uses OpenZeppelin's ERC721 and AccessControl contracts:

- **MINTER_ROLE**: Can mint new NFTs
- **DEFAULT_ADMIN_ROLE**: Can grant/revoke roles and set base URI

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
| `mint(to)` | MINTER_ROLE | Mint a new NFT to an address |
| `setBaseURI(uri)` | Admin | Set metadata base URI |
| `transferFrom(from, to, tokenId)` | Owner/Approved | Transfer NFT |
| `approve(to, tokenId)` | Owner | Approve transfer |
| `grantRole(role, account)` | Admin | Grant a role |
| `revokeRole(role, account)` | Admin | Revoke a role |

## Metadata

Set `BASE_URI` environment variable before deployment:

```bash
export BASE_URI="https://your-api.com/metadata/"
```

Token URI format: `{BASE_URI}{tokenId}`

## Security

See [SECURITY.md](SECURITY.md) and [THREAT_MODEL.md](THREAT_MODEL.md).

**This contract has not been audited. Do not deploy to mainnet without security review.**

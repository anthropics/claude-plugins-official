# ContractKit

A Claude Code plugin for building, testing, and deploying Solidity smart contracts using Foundry.

## Security Model

**Keys & Data:**
- Keys read only from local env / Foundry config
- Nothing sent externally (only to user-specified RPC)
- No key storage or transmission

**Deployment:**
- Local (Anvil) and Sepolia testnet only
- No mainnet deploy by design
- Templates are starting points, not production code

**Audit-Lite Disclaimer:**
`/contractkit:audit-lite` provides automated checks only — it is **not** a security audit. Always get a professional audit before mainnet deployment.

See [docs/security-posture.md](docs/security-posture.md) for full details.

## Templates

| Template | Description |
|----------|-------------|
| `erc20` | Fungible token with role-based minting |
| `erc721` | NFT collection with metadata support |
| `escrow` | Three-party escrow with dispute resolution |
| `vault` | ETH deposit/withdraw with pause functionality |

All templates use audited [OpenZeppelin Contracts](https://github.com/OpenZeppelin/openzeppelin-contracts).

## Commands

```bash
/contractkit:new <template> <name> [symbol]  # Scaffold project
/contractkit:test                            # Run tests
/contractkit:local                           # Start Anvil node
/contractkit:deploy [network]                # Deploy contract
/contractkit:call <address> <function>       # Call contract
/contractkit:status                          # Check status
/contractkit:explain                         # Explain code
/contractkit:audit-lite                      # Security review
```

## Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation) installed
- Claude Code

## Quick Start

```bash
# Create an ERC20 token
/contractkit:new erc20 MyToken MTK

# Run tests
/contractkit:test

# Start local node and deploy
/contractkit:local
/contractkit:deploy local
```

## Documentation

- [Plugin Usage](docs/plugin-usage.md)
- [Template Guidelines](docs/template-guidelines.md)
- [Security Posture](docs/security-posture.md)
- [Architecture](docs/architecture.md)

## Links

- **Repository:** https://github.com/HCS412/contractkit
- **Wiki:** https://github.com/HCS412/contractkit/wiki
- **Issues:** https://github.com/HCS412/contractkit/issues

## License

MIT

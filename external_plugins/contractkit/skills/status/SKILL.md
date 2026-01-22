---
name: status
description: Show project status and deployment information
---

# ContractKit: Status

Display current project status, network configuration, and deployed contract addresses.

## Usage

```
/contractkit:status [--network <network>]
```

## Process

### 1. Verify Project

Check that `foundry.toml` exists. If not:
```
Error: Not in a ContractKit/Foundry project.
Run /contractkit:new to create a project first.
```

### 2. Check Local Chain

Test if Anvil is running:
```bash
curl -s http://127.0.0.1:8545 -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### 3. Load Deployments

Check for deployment files:
- `deployments/local.json`
- `deployments/sepolia.json`

### 4. Display Status

## Output Format

```
=== ContractKit Status ===

Project: MyToken
Directory: /path/to/mytoken

=== Networks ===

Local (http://127.0.0.1:8545)
  Status: Running (block #42)
  Deployments:
    Token: 0x5FbDB2315678afecb367f032d93F642f64180aa3

Sepolia
  Status: Configured (RPC in .env)
  Deployments:
    Token: 0x1234...abcd

=== Quick Commands ===

  /contractkit:call name                    # Get token name
  /contractkit:call balanceOf --args "0x..."  # Check balance
  /contractkit:deploy local                 # Deploy to local
```

## Deployment File Schema

`deployments/<network>.json`:
```json
{
  "Token": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  "deployedAt": "2024-01-15T10:30:00Z",
  "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
}
```

## Error States

### No Project
```
Error: Not in a ContractKit project.
Navigate to a project directory or run /contractkit:new
```

### No Deployments
```
=== Deployments ===
No deployments found.

Run /contractkit:deploy local to deploy.
```

### Local Chain Not Running
```
Local (http://127.0.0.1:8545)
  Status: Not running

Start with: /contractkit:local
```

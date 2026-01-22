---
name: local
description: Start a local Anvil blockchain for development
---

# ContractKit: Local Chain

Start a local Anvil blockchain for development and testing.

## Process

### 1. Check Foundry Installation

Verify `anvil` is installed:
```bash
command -v anvil
```

If not found, instruct user to install Foundry:
```
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 2. Start Anvil

Start Anvil in the background or instruct the user to open a new terminal:

```bash
anvil
```

Default configuration:
- RPC URL: `http://127.0.0.1:8545`
- Chain ID: `31337`
- Block time: Instant (mines on transaction)

### 3. Create Environment File

Create or update `.env.local` in the project:
```
LOCAL_RPC_URL=http://127.0.0.1:8545
```

### 4. Report Status

Print:
- RPC URL
- Note about test accounts being available
- Next step: `/contractkit:deploy local`

## Test Accounts

Anvil provides pre-funded test accounts. These are for **local development only**.

## Example Usage

User: `/contractkit:local`

```
Starting local Anvil chain...

RPC URL: http://127.0.0.1:8545
Chain ID: 31337

Test accounts are pre-funded and ready.

Next: /contractkit:deploy local
```

## Notes

- Anvil must keep running for local deployments to work
- State is reset when Anvil restarts
- Use `--state` flag to persist state if needed

## Stopping Anvil

Press `Ctrl+C` in the terminal running Anvil, or:
```bash
pkill anvil
```

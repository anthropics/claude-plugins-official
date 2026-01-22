---
name: call
description: Call functions on deployed contracts
---

# ContractKit: Call

Call functions on deployed contracts.

## Usage

```
/contractkit:call <function> [--args <arguments>] [--network <network>] [--contract <name>]
```

## Process

### 1. Verify Project

Check that `foundry.toml` exists. If not:
```
Error: Not in a ContractKit project.
Navigate to a project directory or run /contractkit:new
```

### 2. Determine Network

Default: `local`

RPC URLs:
- `local`: `http://127.0.0.1:8545`
- `sepolia`: From `SEPOLIA_RPC_URL` in `.env`

### 3. Load Deployment

Check for `deployments/<network>.json`. If missing:
```
Error: No deployment found for network 'local'.

To deploy:
  1. Start local chain: /contractkit:local
  2. Deploy: /contractkit:deploy local

To check status: /contractkit:status
```

### 4. Select Contract

**Contract selection rules:**
1. If `--contract <name>` specified, use that
2. If only one contract in deployment file, use it
3. If multiple contracts, default to "Token"
4. If "Token" not found and multiple exist, ask user

Example deployment file:
```json
{
  "Token": "0x5FbDB2315678afecb367f032d93F642f64180aa3"
}
```

### 5. Load ABI

Find ABI from Foundry output:
```
out/<ContractName>.sol/<ContractName>.json
```

If ABI not found:
```
Error: ABI not found. Run 'forge build' first.
```

### 6. Determine Call Type

**View/Pure functions** (read-only) → `cast call`
**State-changing functions** → `cast send`

Known view functions:
- `name`, `symbol`, `decimals`, `totalSupply`
- `balanceOf`, `allowance`, `owner`
- `hasRole`, `getRoleAdmin`
- `supportsInterface`

### 7. Execute Call

For view functions:
```bash
cast call <address> "<signature>" <args> --rpc-url <rpc>
```

For state-changing functions:
```bash
cast send <address> "<signature>" <args> --rpc-url <rpc>
```

### 8. Display Result

Decode and show human-readable output:
```
Token.name() → "MyToken"
Token.balanceOf(0xf39F...) → 1000000000000000000 (1.0 TOKEN)
```

## Function Signatures

Common ERC20/AccessControl signatures:

| Function | Signature | Type | Args |
|----------|-----------|------|------|
| `name` | `name()` | view | none |
| `symbol` | `symbol()` | view | none |
| `decimals` | `decimals()` | view | none |
| `totalSupply` | `totalSupply()` | view | none |
| `balanceOf` | `balanceOf(address)` | view | 1 address |
| `allowance` | `allowance(address,address)` | view | 2 addresses |
| `mint` | `mint(address,uint256)` | write | address, amount |
| `transfer` | `transfer(address,uint256)` | write | address, amount |
| `approve` | `approve(address,uint256)` | write | address, amount |
| `grantRole` | `grantRole(bytes32,address)` | write | role, address |
| `revokeRole` | `revokeRole(bytes32,address)` | write | role, address |
| `hasRole` | `hasRole(bytes32,address)` | view | role, address |

For unknown functions, ask user for full signature or check ABI.

## Examples

### Read Token Name
```
/contractkit:call name
```
Output: `MyToken`

### Check Balance
```
/contractkit:call balanceOf --args "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
```
Output: `1000000000000000000 (1.0 tokens)`

### Mint Tokens
```
/contractkit:call mint --args "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" "1000000000000000000"
```
Output: `Transaction sent: 0x... (success)`

### Check on Sepolia
```
/contractkit:call name --network sepolia
```

### Specify Contract
```
/contractkit:call name --contract MyToken
```

## Error Messages

### No Deployment
```
Error: No deployment found for network 'local'.

Have you deployed yet?
  /contractkit:local     # Start local chain
  /contractkit:deploy local  # Deploy contracts

Check status: /contractkit:status
```

### Chain Not Running
```
Error: Cannot connect to local chain at http://127.0.0.1:8545

Start Anvil: /contractkit:local
```

### Function Not Found
```
Error: Function 'foo' not found in Token ABI.

Available functions:
  - name()
  - symbol()
  - balanceOf(address)
  - mint(address,uint256)
  ...

Tip: Use full signature for custom functions:
  /contractkit:call "myFunction(uint256,address)" --args "123" "0x..."
```

### Wrong Arguments
```
Error: Function 'balanceOf' expects 1 argument, got 0.

Usage: /contractkit:call balanceOf --args "<address>"
```

### Execution Reverted
```
Error: Transaction reverted.

Reason: AccessControl: account 0x... is missing role 0x...

This usually means:
  - You don't have permission (check roles)
  - A require() condition failed
  - The contract is paused
```

### Missing RPC URL
```
Error: SEPOLIA_RPC_URL not set.

Add to your .env file:
  SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
```

## Tips

- Use `/contractkit:status` to see deployed contracts and addresses
- For amounts, use wei (1 ETH = 1000000000000000000 wei)
- The `--network` flag defaults to `local`
- State-changing calls require a funded account on the network

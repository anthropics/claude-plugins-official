---
name: deploy
description: Deploy contracts to local or testnet
---

# ContractKit: Deploy

Deploy contracts to a local chain or testnet.

## Usage

```
/contractkit:deploy <network>
```

Networks:
- `local` - Local Anvil chain (default)
- `sepolia` - Sepolia testnet

## Process

### Local Deployment

1. Verify Anvil is running:
   ```bash
   curl -s http://127.0.0.1:8545 -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

2. Deploy:
   ```bash
   forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
   ```

3. Parse deployment addresses and save to `deployments/local.json`

### Sepolia Deployment

1. Check required environment variables:
   - `SEPOLIA_RPC_URL` - Required
   - `ETHERSCAN_API_KEY` - Optional, for verification

2. Warn user about testnet deployment (costs test ETH)

3. Deploy:
   ```bash
   forge script script/Deploy.s.sol --rpc-url $SEPOLIA_RPC_URL --broadcast --verify
   ```

4. Parse deployment addresses and save to `deployments/sepolia.json`

## Output

After deployment, report:
- Contract address(es)
- Transaction hash
- Block explorer link (for testnet)
- Example call commands:
  ```
  /contractkit:call balanceOf --args "0x..."
  ```

## Deployment Files

Deployments are saved to `deployments/<network>.json`:
```json
{
  "Token": "0x..."
}
```

## Example Usage

User: `/contractkit:deploy local`

```
Deploying to local chain...

Transaction sent: 0x...
Token deployed at: 0x5FbDB2315678afecb367f032d93F642f64180aa3

Saved to deployments/local.json

Example calls:
  /contractkit:call name
  /contractkit:call balanceOf --args "0xf39F..."
```

## Troubleshooting

### "Anvil not running"
Start Anvil first: `/contractkit:local`

### "Insufficient funds" (Sepolia)
Get testnet ETH from a faucet:
- https://sepoliafaucet.com
- https://faucet.sepolia.dev

### "Script not found"
Ensure `script/Deploy.s.sol` exists in your project.

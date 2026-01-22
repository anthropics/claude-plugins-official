# ContractKit Plugin Usage

## Installation

```bash
claude /plugin install contractkit
```

## Commands

### `/contractkit:new`

Scaffold a new smart contract project.

```bash
claude /contractkit:new
```

Options:
- Blueprint: `erc20`, `erc721`, `escrow`, `vault`
- Project name: Your project/token name
- Symbol: Token symbol (for ERC20/721)

### `/contractkit:test`

Format code and run tests.

```bash
cd your-project
claude /contractkit:test
```

### `/contractkit:local`

Start a local Anvil chain.

```bash
claude /contractkit:local
```

### `/contractkit:deploy`

Deploy to local or testnet.

```bash
# Local deployment
claude /contractkit:deploy local

# Sepolia deployment (requires RPC URL)
claude /contractkit:deploy sepolia
```

### `/contractkit:call`

Call contract functions.

```bash
# View functions
claude /contractkit:call name
claude /contractkit:call balanceOf --args "0x..."

# State-changing functions
claude /contractkit:call mint --args "0x..." "1000000000000000000"
```

### `/contractkit:explain`

Explain what a contract does.

```bash
claude /contractkit:explain
claude /contractkit:explain --mode paranoid
```

### `/contractkit:audit-lite`

Generate a risk checklist (not an audit).

```bash
claude /contractkit:audit-lite
```

## End-to-End Walkthrough

```bash
# 1. Create a new ERC20 project
claude /contractkit:new
# Select: erc20, name: MyToken, symbol: MTK

# 2. Navigate to project
cd contractkit-projects/mytoken

# 3. Run tests
claude /contractkit:test

# 4. Start local chain
claude /contractkit:local

# 5. Deploy locally
claude /contractkit:deploy local

# 6. Interact with your token
claude /contractkit:call name
claude /contractkit:call mint --args "0xYourAddress" "1000000000000000000"
claude /contractkit:call balanceOf --args "0xYourAddress"

# 7. Review risks
claude /contractkit:audit-lite
```

## Requirements

- [Foundry](https://book.getfoundry.sh/getting-started/installation)
- [Claude Code](https://claude.ai/code)

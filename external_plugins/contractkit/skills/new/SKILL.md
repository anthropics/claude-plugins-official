---
name: new
description: Scaffold a new smart contract project from a template
---

# ContractKit: New Project

Scaffold a new smart contract project from a template.

## Process

### 1. Gather Requirements

Ask the user for the following (use defaults if not specified):

| Parameter | Default | Options |
|-----------|---------|---------|
| Blueprint | `erc20` | `erc20`, `erc721`, `escrow`, `vault` |
| Project name | Required | Any valid name |
| Token symbol | Required for erc20/erc721 | 3-5 uppercase letters |
| Output directory | `./contractkit-projects/<slug>` | Any path |

### 2. Create Project

1. Create output directory
2. Copy template from `plugins/contractkit/templates/<blueprint>/`
3. Replace placeholders in all files:
   - `{{PROJECT_NAME}}` → project name
   - `{{PROJECT_SLUG}}` → lowercase slug
   - `{{TOKEN_NAME}}` → project name (for tokens)
   - `{{TOKEN_SYMBOL}}` → token symbol

### 3. Initialize Project

```bash
cd <project_directory>
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit
```

### 4. Verify

```bash
forge fmt
forge build
forge test
```

If tests fail, diagnose and fix before completing.

### 5. Report Success

Print:
- Project location
- Next steps:
  ```
  cd <project>
  /contractkit:test     # Run tests
  /contractkit:local    # Start local chain
  /contractkit:deploy local  # Deploy locally
  ```

## Example Usage

User: `/contractkit:new`

Response: "What blueprint would you like? (erc20, erc721, escrow, vault)"

User: "erc20"

Response: "What's the project/token name?"

User: "MyToken"

Response: "What's the token symbol? (e.g., MTK)"

User: "MTK"

Then execute the process above.

## Template Locations

Templates are in the plugin directory:
- `plugins/contractkit/templates/erc20/`
- `plugins/contractkit/templates/erc721/`
- `plugins/contractkit/templates/escrow/`
- `plugins/contractkit/templates/vault/`

## Placeholder Reference

| Placeholder | Replaced With |
|-------------|---------------|
| `{{PROJECT_NAME}}` | User's project name |
| `{{PROJECT_SLUG}}` | Lowercase, hyphenated slug |
| `{{TOKEN_NAME}}` | Token name (same as project name) |
| `{{TOKEN_SYMBOL}}` | User's symbol (uppercase) |

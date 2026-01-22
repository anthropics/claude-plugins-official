# Template Guidelines

How to create and maintain ContractKit templates.

## Template Structure

Every template must have:

```
templates/<blueprint>/
  foundry.toml          # Foundry configuration
  remappings.txt        # Import remappings
  src/
    <Contract>.sol      # Main contract
  test/
    <Contract>.t.sol    # Tests
  script/
    Deploy.s.sol        # Deployment script
    Interact.s.sol      # Interaction helpers (optional)
  README.md             # Project readme
  SECURITY.md           # Security notes
  THREAT_MODEL.md       # Threat analysis
  .env.example          # Environment template
  deployments/
    .gitkeep            # Placeholder for deployment files
```

## Placeholder System

Use these placeholders in template files:

| Placeholder | Replaced With |
|-------------|---------------|
| `{{PROJECT_NAME}}` | User's project name |
| `{{PROJECT_SLUG}}` | Lowercase, hyphenated slug |
| `{{TOKEN_NAME}}` | Token name (same as project name) |
| `{{TOKEN_SYMBOL}}` | User's symbol (uppercase) |

Example:
```solidity
/// @title {{TOKEN_NAME}}
contract Token is ERC20 {
    constructor() ERC20("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}") {}
}
```

## Solidity Standards

- Pragma: `pragma solidity ^0.8.20;`
- Use OpenZeppelin contracts (pinned to stable version)
- Follow [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- Run `forge fmt` before committing

## Test Requirements

Every template must have tests covering:

1. Basic functionality
2. Access control (who can do what)
3. Edge cases and failure modes
4. Event emissions

Minimum test coverage: 80%

## Security Requirements

1. No known vulnerabilities
2. Access control on sensitive functions
3. Reentrancy guards where needed
4. Documented trust assumptions in THREAT_MODEL.md

## Adding a New Template

1. Create directory: `templates/<blueprint>/`
2. Copy structure from existing template
3. Implement contract with placeholders
4. Write comprehensive tests
5. Create deployment script
6. Document in README, SECURITY, THREAT_MODEL
7. Test with `./tools/validate_templates.sh`
8. Submit PR

## Validation

Before submitting:

```bash
# Validate all templates
./tools/validate_templates.sh

# Run smoke test
./tools/smoke_test.sh
```

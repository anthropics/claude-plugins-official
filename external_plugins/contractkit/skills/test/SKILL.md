---
name: test
description: Format and run tests for the current project
---

# ContractKit: Test

Format and run tests for the current Foundry project.

## Process

### 1. Verify Project

Check that `foundry.toml` exists in the current directory. If not, ask the user to navigate to a Foundry project.

### 2. Format Code

```bash
forge fmt
```

### 3. Run Tests

```bash
forge test -vvv
```

### 4. Report Results

**If all tests pass:**
- Report number of tests passed
- Suggest next steps: `/contractkit:deploy local`

**If tests fail:**
- Show which tests failed
- Show the failure reason
- Offer to help fix the issue

## Options

| Flag | Description |
|------|-------------|
| `--match-test <pattern>` | Run only tests matching pattern |
| `--match-contract <pattern>` | Run only contracts matching pattern |
| `-vvvv` | Maximum verbosity for debugging |

## Example Usage

User: `/contractkit:test`

```
Running forge fmt...
Running forge test -vvv...

[PASS] test_Name() (gas: 5432)
[PASS] test_Symbol() (gas: 5478)
[PASS] test_MinterCanMint() (gas: 54321)
...

All 10 tests passed.

Next: /contractkit:deploy local
```

## Troubleshooting

### Missing Dependencies

If tests fail with import errors:
```bash
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit
```

### Compilation Errors

Run `forge build` first to see detailed compilation errors.

---
name: subgraph-testing
description: This skill should be used when the user asks to test a subgraph, write unit tests, use Matchstick, mock events or contract calls, run the Subgraph Linter, assert entities, or set up CI/CD for subgraph testing on The Graph protocol.
version: 1.0.0
---

# Subgraph Testing Skill

Expert knowledge for testing subgraphs using Matchstick framework, Subgraph Linter, and integration testing patterns.

## Overview

Subgraph quality assurance involves three complementary approaches:

1. **Static Analysis (Subgraph Linter)** - Catches bugs before runtime
2. **Unit Testing (Matchstick)** - Tests mapping logic in isolation
3. **Integration Testing** - Validates end-to-end behavior

## Subgraph Linter

Subgraph Linter is a static analysis tool that detects common patterns leading to runtime crashes, corrupted entity state, or silent data errors—before deployment.

### When to Use

Run Subgraph Linter to detect issues that compile fine but crash at runtime:

- Entities saved with missing required fields
- Entity overwrite from stale instances after helpers
- Optional values force-unwrapped without null checks
- Division without zero-denominator guards
- @derivedFrom fields mutated directly
- Contract calls not declared in manifest

### Installation

```bash
# CLI
git clone https://github.com/graphprotocol/subgraph-linter.git
cd subgraph-linter && npm install && npm run build

# VS Code Extension - install from marketplace
```

### CLI Usage

```bash
# Run against manifest
npm run check -- --manifest ../your-subgraph/subgraph.yaml

# With custom tsconfig
npm run check -- --manifest ../subgraph.yaml --tsconfig ../tsconfig.json

# With config file
npm run check -- --manifest ../subgraph.yaml --config ./subgraph-linter.config.json
```

### Key Checks

| Check | Detects |
|-------|---------|
| `entity-overwrite` | Stale entity saves after helper modifications |
| `unexpected-null` | Missing required fields, @derivedFrom mutations |
| `unchecked-load` | `Entity.load()!` without null handling |
| `unchecked-nonnull` | `value!` on optional fields |
| `division-guard` | Division with potentially zero denominator |
| `derived-field-guard` | Derived fields not recomputed before save |
| `helper-return-contract` | Helpers returning uninitialized entities |
| `undeclared-eth-call` | Contract calls not in manifest `calls:` block |

### Common Patterns to Fix

```typescript
// BAD - unchecked-load
let token = Token.load(address)!

// GOOD - explicit null check
let token = Token.load(address)
if (token == null) {
  token = new Token(address)
  // initialize all required fields
}
```

```typescript
// BAD - entity-overwrite
let token = Token.load(address)!
updateTokenMetrics(address)  // Helper saves token
token.lastUpdate = timestamp
token.save()  // Overwrites helper's changes!

// GOOD - reload after helper
updateTokenMetrics(address)
let token = Token.load(address)!
token.lastUpdate = timestamp
token.save()
```

```typescript
// BAD - division-guard
let price = amountOut.div(amountIn)

// GOOD - guard zero
if (amountIn.gt(BigInt.zero())) {
  let price = amountOut.div(amountIn)
}
```

### Configuration

Create `subgraph-linter.config.json`:

```json
{
  "severityOverrides": {
    "division-guard": "error",
    "undeclared-eth-call": "warning"
  },
  "suppression": {
    "allowWarnings": true,
    "allowErrors": true
  }
}
```

### Inline Suppression

```typescript
// Suppress specific check when you know it's safe
// [allow(derived-field-guard)]
entity.save()

// Suppress all checks on line
// [allow(all)]
riskyButSafeOperation()
```

---

## Matchstick Unit Testing

Matchstick provides unit testing capabilities for AssemblyScript mappings.

## Matchstick Setup

### Installation

```bash
# Add to package.json
npm install --save-dev matchstick-as

# Or with yarn
yarn add --dev matchstick-as
```

### Project Configuration

Add test script to `package.json`:

```json
{
  "scripts": {
    "codegen": "graph codegen",
    "build": "graph build",
    "test": "graph test"
  }
}
```

### Directory Structure

```
my-subgraph/
├── src/
│   └── mapping.ts
├── tests/
│   ├── mapping.test.ts      # Test files
│   └── helpers/
│       └── utils.ts         # Test utilities
├── schema.graphql
├── subgraph.yaml
└── package.json
```

## Writing Tests

### Basic Test Structure

```typescript
import { describe, test, beforeEach, afterEach, clearStore, assert } from "matchstick-as"
import { Address, BigInt, Bytes } from "@graphprotocol/graph-ts"
import { handleTransfer } from "../src/mapping"
import { Transfer } from "../generated/ERC20/ERC20"
import { Token, TransferEvent } from "../generated/schema"

describe("Transfer Handler", () => {
  beforeEach(() => {
    // Setup runs before each test
  })

  afterEach(() => {
    // Cleanup after each test
    clearStore()
  })

  test("creates Transfer entity on Transfer event", () => {
    // Create mock event
    let event = createTransferEvent(
      Address.fromString("0x1234567890123456789012345678901234567890"),
      Address.fromString("0x0987654321098765432109876543210987654321"),
      BigInt.fromI32(1000)
    )

    // Call handler
    handleTransfer(event)

    // Assert entity was created
    assert.entityCount("TransferEvent", 1)
  })
})
```

### Creating Mock Events

```typescript
import { newMockEvent } from "matchstick-as"
import { ethereum, Address, BigInt } from "@graphprotocol/graph-ts"
import { Transfer } from "../generated/ERC20/ERC20"

export function createTransferEvent(
  from: Address,
  to: Address,
  value: BigInt
): Transfer {
  let event = changetype<Transfer>(newMockEvent())

  event.parameters = new Array()
  event.parameters.push(
    new ethereum.EventParam("from", ethereum.Value.fromAddress(from))
  )
  event.parameters.push(
    new ethereum.EventParam("to", ethereum.Value.fromAddress(to))
  )
  event.parameters.push(
    new ethereum.EventParam("value", ethereum.Value.fromUnsignedBigInt(value))
  )

  // Set event metadata
  event.address = Address.fromString("0xTokenAddress...")
  event.block.number = BigInt.fromI32(12345678)
  event.block.timestamp = BigInt.fromI32(1640000000)
  event.transaction.hash = Bytes.fromHexString("0xabc123...")

  return event
}
```

### Assertions

```typescript
import { assert } from "matchstick-as"

// Entity existence
assert.entityCount("Token", 1)
assert.notInStore("Token", "nonexistent-id")

// Field values
assert.fieldEquals("Token", tokenId, "name", "My Token")
assert.fieldEquals("Token", tokenId, "symbol", "MTK")
assert.fieldEquals("Token", tokenId, "decimals", "18")

// BigInt fields
assert.fieldEquals("Token", tokenId, "totalSupply", "1000000000000000000")

// Bytes fields (as hex string)
assert.fieldEquals("Transfer", transferId, "from", "0x1234...")

// Boolean fields
assert.fieldEquals("Pool", poolId, "active", "true")

// Null checks
assert.assertNull(entity.optionalField)
assert.assertNotNull(entity.requiredField)

// Custom assertions
assert.assertTrue(value > 0)
assert.equals(ethereum.Value.fromI32(expected), ethereum.Value.fromI32(actual))
```

### Store Operations in Tests

```typescript
import { clearStore, createMockedFunction } from "matchstick-as"
import { store } from "@graphprotocol/graph-ts"

// Clear all entities between tests
clearStore()

// Pre-populate store with test data
let token = new Token("0x...")
token.name = "Test Token"
token.symbol = "TEST"
token.decimals = 18
token.totalSupply = BigInt.fromI32(0)
token.save()

// Verify entity exists
let loaded = Token.load("0x...")
assert.assertNotNull(loaded)
```

### Mocking Contract Calls

```typescript
import { createMockedFunction } from "matchstick-as"
import { Address, BigInt, ethereum } from "@graphprotocol/graph-ts"

// Mock a contract function
createMockedFunction(
  Address.fromString("0xContractAddress..."),
  "name",
  "name():(string)"
)
  .returns([ethereum.Value.fromString("Mocked Token")])

createMockedFunction(
  Address.fromString("0xContractAddress..."),
  "decimals",
  "decimals():(uint8)"
)
  .returns([ethereum.Value.fromI32(18)])

// Mock with specific input
createMockedFunction(
  Address.fromString("0xContractAddress..."),
  "balanceOf",
  "balanceOf(address):(uint256)"
)
  .withArgs([ethereum.Value.fromAddress(userAddress)])
  .returns([ethereum.Value.fromUnsignedBigInt(BigInt.fromI32(1000))])

// Mock to revert
createMockedFunction(
  Address.fromString("0xContractAddress..."),
  "name",
  "name():(string)"
)
  .reverts()
```

### Testing Data Source Templates

```typescript
import { DataSourceContext } from "@graphprotocol/graph-ts"
import { assert, dataSourceMock } from "matchstick-as"

test("handles pool creation with context", () => {
  // Set up data source context
  let context = new DataSourceContext()
  context.setBytes("factory", factoryAddress)
  dataSourceMock.setContext(context)

  // Set data source address
  dataSourceMock.setAddress(poolAddress.toHexString())

  // Call handler that uses dataSource.context()
  handleSwap(event)

  // Assert...
})
```

## Test Patterns

### Testing Entity Creation

```typescript
test("creates new token on first transfer", () => {
  let event = createTransferEvent(from, to, value)

  // Verify token doesn't exist
  assert.notInStore("Token", event.address.toHexString())

  // Call handler
  handleTransfer(event)

  // Verify token was created with correct values
  assert.entityCount("Token", 1)
  assert.fieldEquals("Token", event.address.toHexString(), "name", "Mocked Token")
})
```

### Testing Entity Updates

```typescript
test("updates existing token on subsequent transfer", () => {
  // Create existing token
  let token = new Token(tokenAddress)
  token.name = "Test"
  token.totalSupply = BigInt.fromI32(1000)
  token.save()

  // Create transfer event
  let event = createTransferEvent(from, to, BigInt.fromI32(500))
  handleTransfer(event)

  // Verify update
  assert.fieldEquals("Token", tokenAddress, "totalSupply", "1500")
})
```

### Testing Edge Cases

```typescript
describe("Edge Cases", () => {
  test("handles zero value transfer", () => {
    let event = createTransferEvent(from, to, BigInt.zero())
    handleTransfer(event)

    // Verify behavior...
  })

  test("handles transfer to self", () => {
    let event = createTransferEvent(address, address, value)
    handleTransfer(event)

    // Verify behavior...
  })

  test("handles maximum BigInt value", () => {
    let maxValue = BigInt.fromString("115792089237316195423570985008687907853269984665640564039457584007913129639935")
    let event = createTransferEvent(from, to, maxValue)
    handleTransfer(event)

    // Verify no overflow...
  })
})
```

### Testing Relationships

```typescript
test("creates correct pool-swap relationship", () => {
  // Create pool first
  let pool = new Pool(poolAddress)
  pool.token0 = token0Address
  pool.token1 = token1Address
  pool.save()

  // Create swap event
  let event = createSwapEvent(poolAddress, amount0, amount1)
  handleSwap(event)

  // Verify relationship
  let swapId = event.transaction.hash.concatI32(event.logIndex.toI32()).toHexString()
  assert.fieldEquals("Swap", swapId, "pool", poolAddress.toHexString())
})
```

## Running Tests

```bash
# Run all tests
graph test

# Run specific test file
graph test mapping

# Run with coverage
graph test -c

# Run in Docker (for CI)
graph test -d

# Verbose output
graph test -v
```

## Integration Testing

### Local Graph Node Testing

1. **Start local graph-node**:
```bash
docker-compose up -d
```

2. **Deploy subgraph locally**:
```bash
graph create --node http://localhost:8020/ my-subgraph
graph deploy --node http://localhost:8020/ --ipfs http://localhost:5001 my-subgraph
```

3. **Send test transactions** to local blockchain

4. **Query and verify**:
```graphql
{
  tokens(first: 10) {
    id
    name
    symbol
  }
}
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test Subgraph

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Generate types
        run: npm run codegen

      - name: Run tests
        run: npm test

      - name: Build subgraph
        run: npm run build
```

## Best Practices

### Test Organization

```
tests/
├── handlers/
│   ├── transfer.test.ts
│   ├── swap.test.ts
│   └── poolCreated.test.ts
├── helpers/
│   ├── events.ts          # Event creation helpers
│   ├── mocks.ts           # Contract mocks
│   └── fixtures.ts        # Test data
└── integration/
    └── full-flow.test.ts
```

### Test Coverage Goals

- [ ] All event handlers tested
- [ ] Entity creation paths tested
- [ ] Entity update paths tested
- [ ] Edge cases (zero values, max values)
- [ ] Error handling (reverted calls)
- [ ] Relationships between entities
- [ ] Data source templates

### Common Pitfalls

1. **Forgetting clearStore()**: Always clear between tests
2. **Not mocking contract calls**: Tests hang without mocks
3. **Wrong function signatures**: Must match ABI exactly
4. **Missing event metadata**: Set block, timestamp, tx hash
5. **Not testing null cases**: Entity.load() can return null

## Complete Quality Workflow

1. **Write code** with VS Code Subgraph Linter extension for real-time feedback
2. **Generate safe helpers** with Subgraph Uncrashable (optional)
3. **Run static analysis** with Subgraph Linter CLI before commit
4. **Write unit tests** with Matchstick for handler logic
5. **Integration test** with local graph-node
6. **CI pipeline** runs linter + tests before merge

```yaml
# .github/workflows/quality.yml
name: Subgraph Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Generate types
        run: npm run codegen

      - name: Run Subgraph Linter
        run: npx subgraph-linter --manifest subgraph.yaml

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
```

## References

- [Matchstick Documentation](https://thegraph.com/docs/en/subgraphs/developing/creating/unit-testing-framework/)
- [Matchstick GitHub](https://github.com/LimeChain/matchstick)
- [Subgraph Linter](https://thegraph.com/docs/en/subgraphs/developing/subgraph-linter/)
- [Subgraph Uncrashable](https://thegraph.com/docs/en/subgraphs/developing/subgraph-uncrashable/)
- [AssemblyScript Testing Patterns](https://thegraph.com/docs/en/subgraphs/developing/creating/unit-testing-framework/#writing-tests)

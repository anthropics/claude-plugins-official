---
name: subgraph-optimization
description: This skill should be used when the user asks to optimize a subgraph, improve indexing speed, reduce query time, discusses pruning, @derivedFrom, immutable entities, avoiding eth_calls, timeseries aggregations, or grafting on The Graph protocol.
version: 1.0.0
---

# Subgraph Optimization Skill

Expert knowledge for optimizing subgraph performance, indexing speed, and query responsiveness. This skill covers The Graph's official best practices.

## Overview

Subgraph optimization focuses on six key areas:
1. Pruning with indexerHints
2. Arrays with @derivedFrom
3. Immutable Entities and Bytes as IDs
4. Avoiding eth_calls
5. Timeseries and Aggregations
6. Grafting for Hotfixes

## 1. Pruning with indexerHints

Pruning removes outdated historical entities from the database, significantly improving query performance.

### Configuration

Add `indexerHints` to your `subgraph.yaml`:

```yaml
specVersion: 1.3.0
schema:
  file: ./schema.graphql
indexerHints:
  prune: auto
dataSources:
  - kind: ethereum/contract
    name: Contract
    network: mainnet
```

### Pruning Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `prune: auto` | Retains minimum necessary history | Default for most subgraphs |
| `prune: <number>` | Keeps specific number of blocks | Custom retention needs |
| `prune: never` | Retains entire history | Time Travel Queries required |

### Important Considerations

- **Time Travel Queries**: If you need historical queries, use explicit block retention instead of `auto`
- **Grafting**: Cannot graft at a block height that has been pruned
- **graph-cli version**: Auto pruning is default for >= 0.66.0

## 2. Arrays with @derivedFrom

Large arrays significantly slow down subgraph performance. Use `@derivedFrom` to create efficient one-to-many relationships.

### Problem: Direct Arrays

```graphql
# BAD - Arrays grow unbounded and slow queries
type Pool @entity {
  id: Bytes!
  swaps: [Swap!]!  # This array will grow huge
}
```

### Solution: @derivedFrom

```graphql
# GOOD - Data stored on child entity, derived on parent
type Pool @entity {
  id: Bytes!
  swaps: [Swap!]! @derivedFrom(field: "pool")
}

type Swap @entity {
  id: Bytes!
  pool: Pool!  # Reference stored here
  amountIn: BigInt!
  amountOut: BigInt!
}
```

### Benefits

- Reduces entity size
- Improves indexing speed
- Enables efficient reverse lookups
- Supports Derived Field Loaders in mappings

### Mapping Usage

```typescript
// Access derived entities efficiently
let pool = Pool.load(poolId)
if (pool) {
  // Swaps are loaded on-demand, not stored on pool
  // Query them via GraphQL instead
}
```

## 3. Immutable Entities and Bytes as IDs

Combined, these optimizations provide ~28% query improvement and ~48% faster indexing.

### Immutable Entities

Use for entities that never change after creation (event-derived data):

```graphql
# Mark event data as immutable
type Transfer @entity(immutable: true) {
  id: Bytes!
  from: Bytes!
  to: Bytes!
  value: BigInt!
  timestamp: BigInt!
  blockNumber: BigInt!
}

type Swap @entity(immutable: true) {
  id: Bytes!
  pool: Pool!
  sender: Bytes!
  amount0In: BigInt!
  amount1Out: BigInt!
}
```

**Why it works**: graph-node skips validity tracking for immutable entities, eliminating database overhead.

**Don't use when**: Entity fields need updates (e.g., user balances, pool reserves).

### Bytes as IDs

Use `Bytes` instead of `String` for entity IDs:

```typescript
// BAD - String concatenation
let id = event.transaction.hash.toHex() + "-" + event.logIndex.toString()

// GOOD - Bytes concatenation with concatI32
let id = event.transaction.hash.concatI32(event.logIndex.toI32())
```

**Why it works**:
- Bytes use half the storage of equivalent hex strings
- Byte comparisons are faster than UTF-8 string comparisons

### ID Patterns

```typescript
// Transaction + log index (most common for events)
let id = event.transaction.hash.concatI32(event.logIndex.toI32())

// Address combination (for balances, positions)
let id = userAddress.concat(tokenAddress)

// Multiple components
let id = poolAddress.concat(userAddress).concatI32(event.logIndex.toI32())
```

### Sorting with Bytes IDs

Bytes sort by hex value, not numerically. For sequential sorting, add a BigInt field:

```graphql
type Transfer @entity(immutable: true) {
  id: Bytes!
  index: BigInt!  # For sequential sorting
  # ... other fields
}
```

## 4. Avoiding eth_calls

eth_calls are external RPC calls that significantly slow indexing. Subgraph performance depends on external node response times.

### Why eth_calls Are Slow

- Require network round-trip to Ethereum node
- Cannot be parallelized within a handler
- Node performance varies
- Rate limiting issues

### Solution 1: Emit Data in Events (Preferred)

Design smart contracts to emit all needed data:

```solidity
// BAD - Requires eth_call to get pool info
event Swap(address indexed pool, uint256 amountIn, uint256 amountOut);

// GOOD - All data in event
event Swap(
    address indexed pool,
    address indexed sender,
    address tokenIn,
    address tokenOut,
    uint256 amountIn,
    uint256 amountOut,
    uint256 reserve0,
    uint256 reserve1
);
```

### Solution 2: Declared eth_calls (If Unavoidable)

For spec version 1.2.0+, declare calls in manifest for parallel execution:

```yaml
dataSources:
  - kind: ethereum/contract
    name: Pool
    network: mainnet
    source:
      address: "0x..."
      abi: Pool
      startBlock: 12345678
    mapping:
      kind: ethereum/events
      apiVersion: 0.0.9
      language: wasm/assemblyscript
      entities:
        - Pool
      abis:
        - name: Pool
          file: ./abis/Pool.json
      eventHandlers:
        - event: Swap(indexed address,uint256,uint256)
          handler: handleSwap
          calls:
            token0: Pool[event.address].token0()
            token1: Pool[event.address].token1()
      file: ./src/mapping.ts
```

Benefits of declared calls:
- Executed in parallel before handlers run
- Results cached in memory
- Handlers read from cache instead of RPC

### Solution 3: Cache Contract Data

Store contract metadata on first interaction:

```typescript
export function handleSwap(event: Swap): void {
  let pool = Pool.load(event.address)

  if (pool == null) {
    pool = new Pool(event.address)

    // Only call contract once, on first event
    let contract = PoolContract.bind(event.address)
    pool.token0 = contract.token0()
    pool.token1 = contract.token1()
    pool.fee = contract.fee()
    pool.save()
  }

  // Use cached data for subsequent events
  let swap = new SwapEvent(event.transaction.hash.concatI32(event.logIndex.toI32()))
  swap.pool = pool.id
  swap.token0 = pool.token0
  swap.token1 = pool.token1
  swap.save()
}
```

## 5. Timeseries and Aggregations

Offload aggregation computations to the database for better performance.

### Requirements

- Spec version 1.1.0 or higher
- graph-node with aggregation support

### Timeseries Entity

```graphql
type TokenHourData @entity(timeseries: true) {
  id: Int8!                    # Auto-incremented
  timestamp: Timestamp!        # Auto-set to block timestamp
  token: Token!
  priceUSD: BigDecimal!
  volumeUSD: BigDecimal!
  txCount: Int!
}
```

### Aggregation Entity

```graphql
type TokenDayData @aggregation(
  intervals: ["hour", "day"],
  source: "TokenHourData"
) {
  id: Int8!
  timestamp: Timestamp!
  token: Token!

  # Aggregated fields
  avgPrice: BigDecimal! @aggregate(fn: "avg", arg: "priceUSD")
  totalVolume: BigDecimal! @aggregate(fn: "sum", arg: "volumeUSD")
  maxPrice: BigDecimal! @aggregate(fn: "max", arg: "priceUSD")
  minPrice: BigDecimal! @aggregate(fn: "min", arg: "priceUSD")
  txCount: Int8! @aggregate(fn: "count")
}
```

### Supported Aggregation Functions

| Function | Description |
|----------|-------------|
| `sum` | Sum of values |
| `count` | Count of records |
| `min` | Minimum value |
| `max` | Maximum value |
| `first` | First value in interval |
| `last` | Last value in interval |
| `avg` | Average value |

### Mapping for Timeseries

```typescript
export function handleSwap(event: Swap): void {
  // Create timeseries point - id and timestamp are auto-set
  let hourData = new TokenHourData(0)  // id ignored, auto-incremented
  hourData.token = event.params.token
  hourData.priceUSD = calculatePrice(event)
  hourData.volumeUSD = event.params.amountUSD
  hourData.txCount = 1
  hourData.save()

  // Aggregations are computed automatically by the database
}
```

## 6. Grafting for Hotfixes

Deploy fixes quickly without re-indexing from genesis.

### Configuration

```yaml
specVersion: 1.3.0
features:
  - grafting
graft:
  base: QmExistingSubgraphDeploymentId
  block: 18000000  # Block to graft from
schema:
  file: ./schema.graphql
# ... rest of manifest
```

### Use Cases

1. **Bug fixes**: Fix mapping logic without losing indexed data
2. **Schema additions**: Add new entities while keeping existing data
3. **Performance improvements**: Deploy optimizations quickly

### Limitations

- Cannot change existing entity schemas (only add new entities/fields)
- Cannot graft from pruned blocks
- Base subgraph must be synced past graft block

### Best Practice Workflow

1. Deploy fix to a test subgraph first
2. Verify fix works correctly
3. Graft production subgraph from test deployment
4. Monitor for issues
5. Eventually re-deploy from genesis for clean state

## Performance Checklist

Before deploying, verify:

- [ ] `indexerHints.prune: auto` enabled (unless Time Travel needed)
- [ ] No large arrays in schema (use @derivedFrom)
- [ ] Event-derived entities marked as immutable
- [ ] Using Bytes for IDs (not String)
- [ ] Minimized eth_calls (emit data in events)
- [ ] Timeseries used for time-based aggregations
- [ ] No unnecessary entity loads in handlers
- [ ] Proper null checks to avoid redundant saves

## References

- [Pruning Documentation](https://thegraph.com/docs/en/subgraphs/best-practices/pruning/)
- [@derivedFrom Guide](https://thegraph.com/docs/en/subgraphs/best-practices/derivedfrom/)
- [Immutable Entities](https://thegraph.com/docs/en/subgraphs/best-practices/immutable-entities-bytes-as-ids/)
- [Avoiding eth_calls](https://thegraph.com/docs/en/subgraphs/best-practices/avoid-eth-calls/)
- [Timeseries](https://thegraph.com/docs/en/subgraphs/best-practices/timeseries/)
- [Grafting](https://thegraph.com/docs/en/subgraphs/best-practices/grafting-hotfix/)

---
name: subgraph-dev
description: This skill should be used when the user asks to develop, build, or create a subgraph, discusses schema design, mapping handlers, subgraph.yaml manifests, AssemblyScript, event handlers, data sources, contract bindings, or deployment to The Graph protocol.
version: 1.0.0
---

# Subgraph Development Skill

Expert knowledge for developing subgraphs with The Graph protocol. This skill covers schema design, mapping handlers, data sources, and deployment workflows.

## Overview

Subgraphs are open APIs that extract data from blockchain networks, process it, and store it for efficient querying via GraphQL. They consist of three main components:

1. **Schema (schema.graphql)** - Defines the data structure
2. **Manifest (subgraph.yaml)** - Configures data sources and handlers
3. **Mappings (src/*.ts)** - AssemblyScript handlers that process events

## Project Structure

```
my-subgraph/
├── schema.graphql          # GraphQL schema
├── subgraph.yaml           # Manifest file
├── src/
│   └── mapping.ts          # Event handlers
├── abis/
│   └── Contract.json       # Contract ABIs
├── generated/              # Auto-generated types
├── build/                  # Compiled output
└── package.json
```

## CLI Commands

```bash
# Install graph-cli globally
npm install -g @graphprotocol/graph-cli

# Initialize new subgraph
graph init --product subgraph-studio

# Generate types from schema and ABIs
graph codegen

# Build the subgraph
graph build

# Authenticate with Subgraph Studio
graph auth --studio <DEPLOY_KEY>

# Deploy to Subgraph Studio
graph deploy --studio <SUBGRAPH_SLUG>

# Deploy to hosted service (deprecated)
graph deploy --product hosted-service <GITHUB_USER>/<SUBGRAPH_NAME>
```

## Schema Design

### Entity Definition

```graphql
type Token @entity {
  id: Bytes!                          # Unique identifier
  name: String!                       # Token name
  symbol: String!                     # Token symbol
  decimals: Int!                      # Decimal places
  totalSupply: BigInt!                # Total supply
  holders: [TokenBalance!]! @derivedFrom(field: "token")
}

type TokenBalance @entity {
  id: Bytes!                          # address + token address
  token: Token!                       # Reference to token
  account: Bytes!                     # Holder address
  amount: BigInt!                     # Balance amount
}
```

### Field Types

| Type | Description | Example |
|------|-------------|---------|
| `Bytes` | Byte array (addresses, hashes) | `id: Bytes!` |
| `String` | UTF-8 string | `name: String!` |
| `Int` | 32-bit integer | `decimals: Int!` |
| `Int8` | 64-bit integer | `id: Int8!` |
| `BigInt` | Arbitrary precision integer | `totalSupply: BigInt!` |
| `BigDecimal` | Arbitrary precision decimal | `price: BigDecimal!` |
| `Boolean` | True/false | `active: Boolean!` |
| `Timestamp` | Unix timestamp | `timestamp: Timestamp!` |

### Relationships

```graphql
# One-to-many with @derivedFrom (recommended)
type Pool @entity {
  id: Bytes!
  swaps: [Swap!]! @derivedFrom(field: "pool")
}

type Swap @entity {
  id: Bytes!
  pool: Pool!
}

# Many-to-many
type User @entity {
  id: Bytes!
  pools: [PoolMembership!]! @derivedFrom(field: "user")
}

type PoolMembership @entity {
  id: Bytes!
  user: User!
  pool: Pool!
}
```

## Manifest Configuration

### Basic Structure (subgraph.yaml)

```yaml
specVersion: 1.3.0
schema:
  file: ./schema.graphql
indexerHints:
  prune: auto
dataSources:
  - kind: ethereum/contract
    name: ERC20
    network: mainnet
    source:
      address: "0x..."
      abi: ERC20
      startBlock: 12345678
    mapping:
      kind: ethereum/events
      apiVersion: 0.0.9
      language: wasm/assemblyscript
      entities:
        - Token
        - Transfer
      abis:
        - name: ERC20
          file: ./abis/ERC20.json
      eventHandlers:
        - event: Transfer(indexed address,indexed address,uint256)
          handler: handleTransfer
      file: ./src/mapping.ts
```

### Handler Types

```yaml
# Event handlers (most common)
eventHandlers:
  - event: Transfer(indexed address,indexed address,uint256)
    handler: handleTransfer

# Call handlers (for function calls)
callHandlers:
  - function: transfer(address,uint256)
    handler: handleTransferCall

# Block handlers (every block or filtered)
blockHandlers:
  - handler: handleBlock
  - handler: handleBlockWithFilter
    filter:
      kind: call
```

### Data Source Templates

For dynamically created contracts (e.g., factory patterns):

```yaml
templates:
  - kind: ethereum/contract
    name: Pool
    network: mainnet
    source:
      abi: Pool
    mapping:
      kind: ethereum/events
      apiVersion: 0.0.9
      language: wasm/assemblyscript
      entities:
        - Pool
        - Swap
      abis:
        - name: Pool
          file: ./abis/Pool.json
      eventHandlers:
        - event: Swap(indexed address,uint256,uint256)
          handler: handleSwap
      file: ./src/pool.ts
```

## Mapping Handlers

### Basic Event Handler

```typescript
import { Transfer } from "../generated/ERC20/ERC20"
import { Token, TransferEvent } from "../generated/schema"

export function handleTransfer(event: Transfer): void {
  // Load or create token entity
  let token = Token.load(event.address)
  if (token == null) {
    token = new Token(event.address)
    token.name = "Unknown"
    token.symbol = "???"
    token.decimals = 18
    token.totalSupply = BigInt.zero()
  }
  token.save()

  // Create transfer event entity
  let transfer = new TransferEvent(
    event.transaction.hash.concatI32(event.logIndex.toI32())
  )
  transfer.token = token.id
  transfer.from = event.params.from
  transfer.to = event.params.to
  transfer.amount = event.params.value
  transfer.timestamp = event.block.timestamp
  transfer.blockNumber = event.block.number
  transfer.save()
}
```

### Creating Template Instances

```typescript
import { PoolCreated } from "../generated/Factory/Factory"
import { Pool as PoolTemplate } from "../generated/templates"
import { Pool } from "../generated/schema"

export function handlePoolCreated(event: PoolCreated): void {
  // Create entity
  let pool = new Pool(event.params.pool)
  pool.token0 = event.params.token0
  pool.token1 = event.params.token1
  pool.createdAt = event.block.timestamp
  pool.save()

  // Start indexing the new pool contract
  PoolTemplate.create(event.params.pool)
}
```

### Contract Calls (when necessary)

```typescript
import { ERC20 } from "../generated/ERC20/ERC20"

export function handleTransfer(event: Transfer): void {
  let contract = ERC20.bind(event.address)

  // try_ methods return null on revert
  let nameResult = contract.try_name()
  let name = nameResult.reverted ? "Unknown" : nameResult.value

  let symbolResult = contract.try_symbol()
  let symbol = symbolResult.reverted ? "???" : symbolResult.value
}
```

## Common Patterns

### BigInt/BigDecimal Math

```typescript
import { BigInt, BigDecimal } from "@graphprotocol/graph-ts"

// BigInt operations
let a = BigInt.fromI32(100)
let b = BigInt.fromString("1000000000000000000")
let sum = a.plus(b)
let diff = b.minus(a)
let product = a.times(b)
let quotient = b.div(a)

// BigDecimal for precision
let decimals = BigInt.fromI32(18)
let divisor = BigInt.fromI32(10).pow(decimals.toI32() as u8)
let price = new BigDecimal(amount).div(new BigDecimal(divisor))
```

### Bytes ID Concatenation

```typescript
// Preferred: Use concatI32 for unique IDs
let id = event.transaction.hash.concatI32(event.logIndex.toI32())

// For address combinations
let balanceId = event.params.account.concat(event.address)
```

### Loading with Null Check

```typescript
let entity = Entity.load(id)
if (entity == null) {
  entity = new Entity(id)
  // Initialize required fields
}
entity.save()
```

## Subgraph Composition

Combine multiple subgraphs into a single composed subgraph for data aggregation.

### Configuration

```yaml
# composed-subgraph/subgraph.yaml
specVersion: 1.3.0
schema:
  file: ./schema.graphql
dataSources:
  - kind: subgraph
    name: TokenSource
    network: mainnet
    source:
      address: "QmSourceSubgraphId..."  # Deployment ID
      startBlock: 18000000
    mapping:
      kind: subgraph/triggers
      apiVersion: 0.0.9
      language: wasm/assemblyscript
      entities:
        - AggregatedData
      triggers:
        - entity: Token
          handler: handleToken
      file: ./src/composition.ts
```

### Handler

```typescript
import { Token } from "../generated/TokenSource/schema"
import { AggregatedData } from "../generated/schema"

export function handleToken(entity: Token): void {
  let data = AggregatedData.load(entity.id)
  if (data == null) {
    data = new AggregatedData(entity.id)
  }
  data.tokenName = entity.name
  data.save()
}
```

### Requirements

- Source subgraphs: specVersion 1.3.0+, immutable entities only
- Composed subgraphs: max 5 sources, same chain, no nesting

See [subgraph-composition.md](references/subgraph-composition.md) for full details.

## Networks

Supported networks include:
- `mainnet` (Ethereum)
- `arbitrum-one`
- `optimism`
- `polygon`
- `base`
- `avalanche`
- `bsc` (BNB Chain)
- `gnosis`
- `fantom`
- `celo`
- And many more...

See full list: https://thegraph.com/docs/en/supported-networks/

## References

- [The Graph Documentation](https://thegraph.com/docs/)
- [AssemblyScript API](https://thegraph.com/docs/en/subgraphs/developing/creating/assemblyscript-api/)
- [Schema Reference](https://thegraph.com/docs/en/subgraphs/developing/creating/creating-a-subgraph/#the-graphql-schema)
- [Subgraph Composition](https://thegraph.com/docs/en/subgraphs/guides/subgraph-composition/)
- [Subgraph Uncrashable](https://thegraph.com/docs/en/subgraphs/developing/subgraph-uncrashable/)

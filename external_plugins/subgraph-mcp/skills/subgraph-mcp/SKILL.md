---
name: subgraph-mcp
description: This skill should be used when the user asks to search for subgraphs, query blockchain data, find DeFi/NFT/DAO data on The Graph, look up Uniswap/Aave/Compound/ENS or other protocol data, get a subgraph schema, run a GraphQL query against a subgraph, or check query volumes. Provides guidance on using The Graph's Subgraph MCP tools.
version: 1.0.0
---

# Subgraph MCP Skill

Access 15,000+ blockchain subgraphs via The Graph Network using natural language.

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `search_subgraphs` | Find subgraphs by keyword or protocol name |
| `get_schema` | Retrieve GraphQL schema for any subgraph |
| `execute_query` | Run a GraphQL query against any subgraph |
| `get_subgraph_info` | Get metadata and deployment details |
| `get_query_volume` | Check 30-day query statistics |

## How to Use

### Finding subgraphs
Always search first — do not guess deployment IDs.
1. Use `search_subgraphs` with a keyword (e.g., "uniswap", "aave", "ens")
2. Check `get_query_volume` to pick the most active deployment
3. Use `get_schema` to understand available entities before querying

### Running queries
1. Get the schema first to know entity names and fields
2. Use `execute_query` with a focused GraphQL query
3. Request only the fields needed

## Example Interactions

**Find and query a protocol:**
```
User: Show me the top Uniswap V3 pools by volume
→ search_subgraphs("uniswap v3")
→ get_query_volume(ipfsHash) — pick highest volume deployment
→ get_schema(deploymentId)
→ execute_query: { pools(orderBy: volumeUSD, orderDirection: desc, first: 10) { id token0 { symbol } token1 { symbol } volumeUSD } }
```

**Explore a new protocol:**
```
User: What data is available for Aave?
→ search_subgraphs("aave")
→ get_schema(deploymentId) — list entities and fields
→ Explain relationships and suggest useful queries
```

## Authentication

Requires a free Graph API key from [Subgraph Studio](https://thegraph.com/studio/).
Set as `GRAPH_API_KEY` environment variable (100,000 free queries/month).

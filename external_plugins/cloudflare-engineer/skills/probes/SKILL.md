---
name: probes
description: Pre-built audit probes for Cloudflare services. Reference these query patterns when validating D1 indexes, observability metrics, AI Gateway costs, and queue health via MCP tools.
triggers:
  - validating D1 queries
  - checking observability data
  - auditing AI Gateway costs
  - queue health checks
  - MCP tool orchestration
  - EXPLAIN QUERY PLAN
---

# Cloudflare Audit Probes

Pre-built diagnostic queries for live validation. Use these probes when `--validate` mode is enabled to compare static analysis findings against actual production data.

## MCP Availability Check

Before running any probes, verify MCP tool availability:

```javascript
// Lightweight probe to test MCP connectivity
mcp__cloudflare-bindings__workers_list()

// Expected: Returns array of workers
// Failure: MCP tools unavailable, fall back to static analysis
```

**Graceful Degradation**:
- If MCP call succeeds: Proceed with live validation
- If MCP call fails/times out: Note "MCP tools unavailable" and continue with static analysis
- Tag all findings appropriately: `[STATIC]`, `[LIVE-VALIDATED]`, `[LIVE-REFUTED]`, `[INCOMPLETE]`

---

## D1 Database Probes

### Schema Discovery

List all tables in the database:

```sql
SELECT name, sql
FROM sqlite_master
WHERE type='table'
ORDER BY name;
```

**MCP Call**:
```javascript
mcp__cloudflare-bindings__d1_database_query({
  database_id: "your-database-id",
  sql: "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
})
```

### Index Inventory

List all indexes with their definitions:

```sql
SELECT name, tbl_name, sql
FROM sqlite_master
WHERE type='index'
AND name NOT LIKE 'sqlite_%'
ORDER BY tbl_name, name;
```

**Interpretation**:
- Missing indexes on foreign keys = potential performance issue
- Missing indexes on frequently filtered columns = query scan risk

### Query Plan Analysis

Validate query efficiency:

```sql
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = ?;
```

**MCP Call**:
```javascript
mcp__cloudflare-bindings__d1_database_query({
  database_id: "your-database-id",
  sql: "EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = ?"
})
```

**Interpretation**:
| Output Contains | Meaning | Action |
|----------------|---------|--------|
| `SCAN TABLE` | Full table scan, no index | Add index on filtered column |
| `SEARCH USING INDEX` | Index used | Good performance |
| `COVERING INDEX` | Index contains all needed data | Optimal |
| `USING TEMP B-TREE` | Temporary sort required | Consider index on ORDER BY column |

### Table Row Counts

Get approximate table sizes:

```sql
SELECT name,
       (SELECT COUNT(*) FROM pragma_table_info(name)) as columns,
       (SELECT seq FROM sqlite_sequence WHERE name = m.name) as approx_rows
FROM sqlite_master m
WHERE type='table'
AND name NOT LIKE 'sqlite_%';
```

---

## Observability Probes

### Error Rate by Worker (7 days)

```javascript
mcp__cloudflare-observability__query_worker_observability({
  view: "calculations",
  parameters: {
    calculations: [
      { operator: "count", as: "total_requests" },
      {
        operator: "countIf",
        as: "errors",
        condition: {
          field: "$metadata.outcome",
          operator: "eq",
          value: "exception"
        }
      }
    ],
    groupBys: [
      { type: "string", value: "$metadata.service" }
    ]
  },
  timeframe: {
    reference: "now",
    offset: "-7d"
  }
})
```

**Interpretation**:
- Error rate > 1%: Investigate immediately
- Error rate > 0.1%: Monitor closely
- Compare static findings against actual error patterns

### Latency Percentiles by Endpoint

```javascript
mcp__cloudflare-observability__query_worker_observability({
  view: "calculations",
  parameters: {
    calculations: [
      { operator: "p50", field: "$metadata.duration", as: "p50_ms" },
      { operator: "p95", field: "$metadata.duration", as: "p95_ms" },
      { operator: "p99", field: "$metadata.duration", as: "p99_ms" }
    ],
    groupBys: [
      { type: "string", value: "$metadata.path" }
    ]
  },
  timeframe: {
    reference: "now",
    offset: "-24h"
  }
})
```

**Interpretation**:
- P99 > 10s: Likely timeout issues
- P95/P50 ratio > 10: High variance, investigate outliers
- Compare against D1 query patterns identified in static analysis

### Request Volume by Endpoint

```javascript
mcp__cloudflare-observability__query_worker_observability({
  view: "calculations",
  parameters: {
    calculations: [
      { operator: "count", as: "requests" }
    ],
    groupBys: [
      { type: "string", value: "$metadata.path" },
      { type: "time", interval: "1h" }
    ]
  },
  timeframe: {
    reference: "now",
    offset: "-7d"
  }
})
```

**Use Case**: Identify high-traffic endpoints for cost optimization focus.

### CPU Time Analysis

```javascript
mcp__cloudflare-observability__query_worker_observability({
  view: "calculations",
  parameters: {
    calculations: [
      { operator: "sum", field: "$metadata.cpuTime", as: "total_cpu_ms" },
      { operator: "avg", field: "$metadata.cpuTime", as: "avg_cpu_ms" }
    ],
    groupBys: [
      { type: "string", value: "$metadata.service" }
    ]
  },
  timeframe: {
    reference: "now",
    offset: "-30d"
  }
})
```

**Cost Impact**: CPU time directly impacts Workers billing on paid plans.

---

## AI Gateway Probes

### Cost by Model (30 days)

```javascript
const logs = await mcp__cloudflare-ai-gateway__list_logs({
  gateway_id: "your-gateway-id",
  per_page: 1000,
  order_by: "created_at",
  direction: "desc"
});

// Aggregate by model
const costByModel = {};
for (const log of logs.result) {
  const model = log.model;
  const tokens = log.tokens_in + log.tokens_out;
  costByModel[model] = (costByModel[model] || 0) + tokens;
}
```

**Pricing Reference** (per 1K tokens):
| Model | Input | Output |
|-------|-------|--------|
| @cf/meta/llama-3-8b-instruct | $0.00019 | $0.00019 |
| @cf/mistral/mistral-7b-instruct | $0.00011 | $0.00011 |
| @hf/thebloke/deepseek-coder-6.7b-instruct | $0.00013 | $0.00013 |

### Cache Hit Rate

```javascript
const logs = await mcp__cloudflare-ai-gateway__list_logs({
  gateway_id: "your-gateway-id",
  per_page: 1000
});

const total = logs.result.length;
const cached = logs.result.filter(l => l.cached).length;
const cacheHitRate = (cached / total * 100).toFixed(1);
```

**Interpretation**:
- Cache hit rate < 10%: Significant cost savings opportunity
- Review request patterns for cacheable queries
- Consider increasing cache TTL for stable prompts

### Token Usage Distribution

```javascript
const logs = await mcp__cloudflare-ai-gateway__list_logs({
  gateway_id: "your-gateway-id",
  per_page: 1000
});

// Analyze token distribution
const tokenBuckets = { small: 0, medium: 0, large: 0, xlarge: 0 };
for (const log of logs.result) {
  const total = log.tokens_in + log.tokens_out;
  if (total < 100) tokenBuckets.small++;
  else if (total < 500) tokenBuckets.medium++;
  else if (total < 2000) tokenBuckets.large++;
  else tokenBuckets.xlarge++;
}
```

**Use Case**: Identify if smaller models could handle high-volume, low-token requests.

---

## Queue Probes

### Queue List and Status

```javascript
mcp__cloudflare-bindings__queues_list()
```

**Check For**:
- Queues without corresponding DLQ (dead-letter queue)
- Queue naming patterns (should have `-dlq` suffix for DLQs)

### Consumer Configuration

From wrangler config, verify:

```jsonc
{
  "queues": {
    "consumers": [{
      "queue": "my-queue",
      "max_batch_size": 10,      // 1-100, default 10
      "max_batch_timeout": 5,    // 0-30 seconds
      "max_retries": 2,          // 0-100, recommend <= 2
      "dead_letter_queue": "my-queue-dlq",  // REQUIRED for resilience
      "max_concurrency": 10      // 1-20
    }]
  }
}
```

**Audit Checks**:
| Setting | Risk | Recommendation |
|---------|------|----------------|
| `max_retries > 2` | Cost multiplication | Reduce to 2, use DLQ |
| Missing `dead_letter_queue` | Message loss | Always configure DLQ |
| `max_batch_size = 1` | Inefficient processing | Increase for throughput |

### DLQ Depth (Manual Check)

Currently no direct MCP tool for queue depth. Check via:
1. Cloudflare Dashboard > Queues
2. wrangler CLI: `wrangler queues list`

**Warning Signs**:
- DLQ with messages > 0: Processing failures occurring
- DLQ message age > 24h: Failures not being addressed

---

## R2 Probes

### Bucket List

```javascript
mcp__cloudflare-bindings__r2_buckets_list()
```

### Storage Class Distribution

From R2 metrics (when available):
- Standard storage: Most expensive
- Infrequent Access: 80% cheaper storage, higher retrieval cost

**Cost Optimization**:
- Objects not accessed in 30+ days: Consider lifecycle rules
- Large objects with frequent partial reads: Enable range requests

---

## KV Probes

### Namespace List

```javascript
mcp__cloudflare-bindings__kv_namespaces_list()
```

### Key Pattern Analysis

KV doesn't support listing all keys efficiently. Instead, analyze code for:
- Key naming patterns (prefix-based for organization)
- TTL usage (expiring keys save storage)
- Value sizes (KV has 25MB limit, prefer R2 for large values)

**Cost Note**: KV writes are 10x more expensive than reads ($5/M vs $0.50/M).

---

## Vectorize Probes

### Index List

```javascript
mcp__cloudflare-bindings__vectorize_indexes_list()
```

### Index Statistics

For each index, check:
- Dimension count (affects query cost)
- Vector count (affects storage cost)
- Metadata fields (affects query flexibility)

---

## Probe Output Format

When reporting probe results, use provenance tags:

```markdown
### [LIVE-VALIDATED] COST001: D1 writes at 85% of projected
- **Probe**: D1 write volume query
- **Expected** (static): 50M writes/month
- **Actual** (live): 42.5M writes/month
- **Evidence**: Observability data, 30-day window

### [LIVE-REFUTED] PERF001: Missing indexes on users.email
- **Probe**: EXPLAIN QUERY PLAN
- **Static Finding**: No index detected in migrations
- **Live Result**: `SEARCH USING COVERING INDEX idx_users_email`
- **Conclusion**: Index exists, not in tracked migrations

### [INCOMPLETE] SEC001: Rate limiting status
- **Probe**: Could not verify (MCP tool unavailable)
- **Static Finding**: No rate limiting detected in code
- **Action**: Manual verification required
```

---

## Best Practices

1. **Always check MCP availability first** before running probes
2. **Use bounded time ranges** (7 days, 30 days) to limit data volume
3. **Compare static vs live** findings and tag appropriately
4. **Note when probes are incomplete** due to MCP unavailability
5. **Aggregate expensive queries** - don't run per-endpoint probes individually

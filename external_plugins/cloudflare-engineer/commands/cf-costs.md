---
description: "Generate Cloudflare cost report with projections and optimization recommendations [--validate for live data]"
argument-hint: "[wrangler-path] [--validate] [--detailed]"
allowed-tools: ["Read", "Glob", "Grep", "Bash", "mcp__cloudflare-observability__*", "mcp__cloudflare-ai-gateway__*", "mcp__cloudflare-bindings__*"]
---

# Cloudflare Cost Report

Generate a comprehensive cost analysis for your Cloudflare architecture with optimization recommendations.

**Arguments:** "$ARGUMENTS"

## Modes

| Mode | Description | MCP Tools |
|------|-------------|-----------|
| **Static** (default) | Analyze config and code only | None |
| **Validate** (`--validate`) | Compare static findings against live data | observability, ai-gateway, bindings |

## Workflow

### Step 0: Parse Arguments and Detect Mode

Parse `$ARGUMENTS` for:
- `--validate`: Enable live data validation
- `--detailed`: Per-binding cost breakdown
- `[path]`: Explicit wrangler config path

**Mode Selection:**
- If `--validate` present: **Live Validation Mode**
- Otherwise: **Static Analysis Mode**

### Step 1: MCP Availability Check (if --validate)

Before using MCP tools, verify availability:

```javascript
// Lightweight probe to test MCP connectivity
mcp__cloudflare-bindings__workers_list()
```

**Expected outcomes:**
- **Success**: MCP tools available, proceed with live validation
- **Failure/Timeout**: Note "MCP tools unavailable" in output
  - Continue with static analysis
  - Tag all findings as `[STATIC]`
  - Add footer: "Note: Some findings may be incomplete without live observability data"

### Step 2: Locate Wrangler Config

If path provided, use it. Otherwise search:
```bash
# Find wrangler.toml or wrangler.jsonc
find . -name "wrangler.toml" -o -name "wrangler.jsonc" | head -5
```

### Step 3: Parse Configuration

Read the wrangler config and identify all bindings:
- D1 databases
- R2 buckets
- KV namespaces
- Queues (check `max_retries`)
- Vectorize indexes
- AI bindings
- Durable Objects
- Analytics Engine datasets

### Step 4: Gather Usage Data

#### Static Mode
Analyze code patterns:
- Count D1 queries in source files
- Identify batch vs per-row inserts
- Check queue publish frequency
- Scan for AI model usage

#### Validate Mode (MCP Available)
Use MCP tools to collect real usage metrics. Reference @skills/probes/SKILL.md for query patterns.

1. **Worker Metrics** (cloudflare-observability):
   ```javascript
   mcp__cloudflare-observability__query_worker_observability({
     view: "calculations",
     parameters: {
       calculations: [
         { operator: "count", as: "total_requests" },
         { operator: "sum", field: "$metadata.cpuTime", as: "total_cpu_ms" }
       ],
       groupBys: [{ type: "string", value: "$metadata.service" }]
     },
     timeframe: { reference: "now", offset: "-30d" }
   })
   ```

2. **AI Gateway Logs** (cloudflare-ai-gateway):
   ```javascript
   mcp__cloudflare-ai-gateway__list_logs({
     gateway_id: "...",
     per_page: 1000
   })
   // Aggregate by model, calculate actual costs
   ```

3. **Resource Lists** (cloudflare-bindings):
   ```javascript
   mcp__cloudflare-bindings__d1_databases_list()
   mcp__cloudflare-bindings__r2_buckets_list()
   mcp__cloudflare-bindings__kv_namespaces_list()
   ```

### Step 5: Calculate Costs

Apply 2026 Cloudflare pricing:

| Service | Read | Write | Storage |
|---------|------|-------|---------|
| D1 | $0.25/B rows | $1.00/M rows | $0.75/GB |
| R2 | $0.36/M (Class B) | $4.50/M (Class A) | $0.015/GB |
| KV | $0.50/M | $5.00/M | $0.50/GB |
| Queues | $0.40/M messages | - | - |
| Workers | $0.30/M requests | - | - |
| Workers AI | Varies by model | - | - |

### Step 6: Identify Optimizations

Check for common cost traps:

1. **D1 Anti-patterns:**
   - Per-row inserts (should batch)
   - Missing indexes (SCAN TABLE)
   - SELECT * usage

2. **Queue Anti-patterns:**
   - `max_retries > 1` for idempotent consumers
   - Missing dead-letter queue

3. **AI Anti-patterns:**
   - No caching for repeated prompts
   - Large models for simple tasks
   - Missing rate limiting

4. **General Anti-patterns:**
   - Frequent cron jobs (batch work)
   - Missing Smart Placement
   - Subrequest exhaustion

### Step 7: Live Validation (if --validate and MCP available)

Compare static estimates against live data:

1. **D1 Write Volume**
   - Static estimate: Count INSERT/UPDATE in code × estimated frequency
   - Live data: Query observability for actual write counts
   - Compare and tag: `[LIVE-VALIDATED]` or `[LIVE-REFUTED]`

2. **AI Gateway Costs**
   - Static estimate: Model pricing × estimated requests
   - Live data: Aggregate from AI Gateway logs
   - Identify cache hit opportunities

3. **Queue Retry Rates**
   - Static estimate: Based on `max_retries` config
   - Live data: Query actual retry patterns
   - Calculate real retry cost multiplier

4. **EXPLAIN QUERY PLAN** (D1)
   ```javascript
   mcp__cloudflare-bindings__d1_database_query({
     database_id: "...",
     sql: "EXPLAIN QUERY PLAN [detected query]"
   })
   ```
   - Validate index usage claims
   - Identify SCAN TABLE issues not caught statically

### Step 8: Generate Report with Provenance Tags

Output format:

```markdown
# Cloudflare Cost Report
Generated: [date]
Project: [wrangler name]
Mode: [Static | Live Validated]

## Summary
- **Estimated Monthly Cost**: $XX.XX
- **Cost Trend**: [Stable|Rising|Declining]
- **Optimization Potential**: $XX.XX/month
- **Validation Status**: [Full | Partial | Static Only]

## Service Breakdown

| Service | Monthly Cost | % Total | Status | Source |
|---------|-------------|---------|--------|--------|
| D1 | $XX.XX | XX% | [OK|Warning|Critical] | [STATIC|LIVE] |
| Workers | $XX.XX | XX% | [OK|Warning|Critical] | [STATIC|LIVE] |
| ... | ... | ... | ... | ... |

## Cost Drivers

### [LIVE-VALIDATED] D1 Writes - XX% of total
- **Static Estimate**: $XX.XX/month
- **Live Actual**: $XX.XX/month
- **Evidence**: Observability data, 30-day window
- Root cause: [explanation]

### [STATIC] Queue Retries - XX% of total
- **Estimate**: $XX.XX/month
- Root cause: [explanation]
- Note: Live validation unavailable

### [LIVE-REFUTED] AI Gateway - XX% of total
- **Static Estimate**: $XX.XX/month (based on code patterns)
- **Live Actual**: $XX.XX/month (cache hits reducing cost)
- **Evidence**: AI Gateway logs show 40% cache hit rate

## Optimization Opportunities

| Opportunity | Savings | Effort | Priority | Source |
|-------------|---------|--------|----------|--------|
| [Description] | $XX/mo | [Low|Med|High] | [P1|P2|P3] | [STATIC|LIVE-VALIDATED] |

## Warnings

- [List any concerning patterns with provenance tags]

## Action Items

1. [ ] [LIVE-VALIDATED] [Specific action with file:line reference]
2. [ ] [STATIC] [Specific action with file:line reference]

---
**Finding Tags:**
- `[STATIC]` - Inferred from code/config analysis
- `[LIVE-VALIDATED]` - Confirmed by observability (--validate mode)
- `[LIVE-REFUTED]` - Code smell not observed in production
- `[INCOMPLETE]` - Some MCP tools unavailable
```

## Usage Examples

**Basic cost report (static):**
```
/cf-costs
```

**Cost report with live validation:**
```
/cf-costs --validate
```

**Specific wrangler file with validation:**
```
/cf-costs workers/wrangler.jsonc --validate
```

**Detailed report with per-binding breakdown:**
```
/cf-costs --detailed --validate
```

## Tips

- Run weekly to track cost trends
- Use `--validate` for accurate cost attribution
- Compare before/after deployments
- Use `--detailed` for capacity planning
- Check D1 writes first (usually the culprit)
- If MCP tools unavailable, findings marked `[STATIC]` should be verified manually

## MCP Tool Requirements

For `--validate` mode, these MCP servers should be configured:
- `cloudflare-observability` - Worker metrics, D1 usage
- `cloudflare-ai-gateway` - AI cost data
- `cloudflare-bindings` - Resource lists, D1 queries

If any MCP server is unavailable, the command will:
1. Note which tools are missing
2. Continue with available data
3. Tag affected findings as `[INCOMPLETE]`

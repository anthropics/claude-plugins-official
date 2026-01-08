---
name: optimize-costs
description: Analyze Cloudflare architecture and predict monthly costs with optimization recommendations. Use this skill when the user asks about costs, billing, pricing, or wants to understand their Cloudflare spend. Works with wrangler configs, observability data, and AI Gateway logs.
---

# Cloudflare Cost Optimization Skill

Analyze Cloudflare architectures and predict monthly costs with actionable optimization recommendations. This skill provides engineering-grade cost estimates based on 2026 Cloudflare pricing.

## Pricing Reference (2026)

### Workers
- **Requests**: $0.30/million (after 10M free)
- **CPU Time**: $0.02/million GB-seconds
- **Unbound**: $12.50/million duration-ms (15M free)
- **Subrequests**: Count against request limits

### D1 (SQLite)
- **Reads**: $0.25/billion rows
- **Writes**: $1.00/million rows (4x more expensive than reads!)
- **Storage**: $0.75/GB/month
- **Cost Trap**: `for(row){db.insert()}` = N× writes. Always batch ≤1,000.

### R2 (Object Storage)
- **Class A (writes)**: $4.50/million
- **Class B (reads)**: $0.36/million
- **Storage**: $0.015/GB/month
- **Egress**: FREE (major advantage)

### KV (Key-Value)
- **Reads**: $0.50/million
- **Writes**: $5.00/million (10x more than reads!)
- **Storage**: $0.50/GB/month
- **Rate Limit**: 1 write/sec/key

### Queues
- **Standard**: $0.40/million messages
- **Batch**: $0.40/million batches
- **Cost Trap**: `max_retries: 3` = up to 3× message cost

### Vectorize
- **Queries**: $0.01/million
- **Stored Vectors**: $0.05/100M dimensions×vectors
- **Hard Limit**: 5M vectors/index, 1,536 dimensions

### Workers AI
- **Neurons**: $0.011/1,000 (reset daily UTC)
- **Large Models** (Llama 11B+): $0.68/M output tokens - expensive!
- **Recommendation**: Use smaller models (1B-8B) or Gemini Flash for bulk

### AI Gateway
- **Caching**: Only caches IDENTICAL prompts (no semantic)
- **Logs**: 10M free, then $0.10/million
- **Cost Trap**: Forgetting cache = paying full LLM cost every time

### Analytics Engine
- **Essentially FREE** - no per-write charges
- **Note**: Use `SUM(_sample_interval)` at scale (adaptive sampling)

## Analysis Workflow

### Step 1: Gather Architecture Data

Use MCP tools to collect current usage:

```
1. Read wrangler.toml/wrangler.jsonc for bindings
2. Query cloudflare-observability for Worker metrics
3. Query cloudflare-ai-gateway for AI costs
4. Check cloudflare-bindings for resource lists
```

### Step 2: Calculate Per-Service Costs

For each service bound in wrangler config:

**Workers:**
```
monthly_cost = (requests - 10M) / 1M * $0.30
            + cpu_gb_seconds / 1M * $0.02
```

**D1:**
```
monthly_cost = reads / 1B * $0.25
            + writes / 1M * $1.00
            + storage_gb * $0.75
```

**R2:**
```
monthly_cost = class_a_ops / 1M * $4.50
            + class_b_ops / 1M * $0.36
            + storage_gb * $0.015
```

**KV:**
```
monthly_cost = reads / 1M * $0.50
            + writes / 1M * $5.00
            + storage_gb * $0.50
```

**Queues:**
```
monthly_cost = messages / 1M * $0.40 * (1 + avg_retries)
```

### Step 3: Identify Cost Drivers

Flag any service that's >20% of total cost. Common patterns:

| Cost Driver | Typical Cause | Fix |
|-------------|--------------|-----|
| D1 writes dominating | Per-row inserts | Batch to ≤1,000 |
| Queue costs high | Retries enabled | Set `max_retries: 1` if idempotent |
| AI Gateway expensive | No caching | Enable cache, deduplicate prompts |
| Workers AI | Large model | Switch to smaller model or external LLM |
| R2 Class A | Frequent writes | Buffer writes, use R2 presigned |

### Step 4: Generate Recommendations

For each optimization opportunity, provide:

1. **Current**: What it costs now
2. **Optimized**: What it could cost
3. **Savings**: Monthly/annual savings
4. **Trade-off**: What changes in behavior
5. **Implementation**: Specific code/config change

## Output Format

```markdown
# Cloudflare Cost Analysis

## Monthly Cost Estimate: $X.XX

### Breakdown by Service

| Service | Cost | % of Total | Status |
|---------|------|------------|--------|
| D1 | $X.XX | X% | ⚠️ Cost driver |
| Workers | $X.XX | X% | ✅ Normal |
| R2 | $X.XX | X% | ✅ Normal |

### Cost Drivers Identified

1. **D1 Writes** (80% of total)
   - Current: 50M writes/month = $50
   - Pattern detected: Per-row inserts in cron job
   - Fix: Batch inserts to ≤1,000 rows

### Optimization Opportunities

| Opportunity | Current | Optimized | Savings | Effort |
|-------------|---------|-----------|---------|--------|
| Batch D1 writes | $50/mo | $5/mo | $45/mo ($540/yr) | Low |
| Reduce queue retries | $10/mo | $3/mo | $7/mo ($84/yr) | Trivial |

### Warnings

- ⚠️ D1 writes >50M/day is a red flag
- ⚠️ Workers AI Llama 11B is expensive for high-volume

### Action Items

1. [ ] Change `for(row){insert()}` to `db.batch()` in `processor.ts`
2. [ ] Set `max_retries: 1` for `layer2-queue` in wrangler.jsonc
3. [ ] Consider switching AI model from llama-3-11b to llama-3-8b
```

## MCP Tools to Use

- `mcp__cloudflare-observability__query_worker_observability` - Worker request/duration metrics
- `mcp__cloudflare-ai-gateway__list_logs` - AI request costs
- `mcp__cloudflare-bindings__workers_get_worker` - Worker details
- `mcp__cloudflare-bindings__d1_databases_list` - D1 databases
- `mcp__cloudflare-bindings__r2_buckets_list` - R2 buckets
- `mcp__cloudflare-bindings__kv_namespaces_list` - KV namespaces

## Tips

- **D1 is usually the culprit**: Writes are 4× more expensive than reads
- **Queue retries multiply costs**: Each retry = another message charge
- **Analytics Engine is nearly free**: Use it heavily for metrics
- **R2 egress is free**: Use R2 over S3 when possible
- **AI caching only works for identical prompts**: Deduplicate inputs

## Example Usage

When user asks:
- "How much is this costing me?"
- "Optimize my Cloudflare costs"
- "Why is my D1 bill so high?"
- "Estimate monthly costs for this architecture"

Invoke this skill to provide detailed cost analysis with actionable recommendations.

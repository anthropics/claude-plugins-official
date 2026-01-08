---
name: guardian
description: Audit Cloudflare Worker configurations for security vulnerabilities, resilience gaps, and cost traps. Use this skill when reviewing wrangler configs, before deployments, or when investigating production issues.
---

# Cloudflare Guardian Skill

Audit wrangler configurations for security vulnerabilities, performance issues, cost traps, and resilience gaps. Acts as a senior SRE reviewing infrastructure-as-code.

## Audit Categories

### Security Audit Rules

| ID | Name | Severity | Check |
|----|------|----------|-------|
| SEC001 | Secrets in plaintext | CRITICAL | `vars.*` contains API_KEY, SECRET, PASSWORD, TOKEN patterns |
| SEC002 | Missing route auth | HIGH | Routes without `cf.access` or auth middleware |
| SEC003 | CORS wildcard | MEDIUM | `cors.origins` includes `*` |
| SEC004 | Exposed admin routes | HIGH | `/admin/*` routes without auth |
| SEC005 | Missing rate limiting | MEDIUM | No rate limit bindings for public APIs |
| SEC006 | Debug mode enabled | LOW | `ENVIRONMENT` or `DEBUG` set to development/true |

### Performance Audit Rules

| ID | Name | Severity | Check |
|----|------|----------|-------|
| PERF001 | Missing Smart Placement | LOW | `placement.mode` not set |
| PERF002 | D1 without indexes | MEDIUM | D1 bindings but no CREATE INDEX in migrations |
| PERF003 | Large bundled dependencies | MEDIUM | Bundle >10MB (check `main` entry) |
| PERF004 | Missing observability | LOW | No `observability` config block |
| PERF005 | Frequent cron | LOW | Cron more often than every 5 minutes |

### Cost Audit Rules

| ID | Name | Severity | Check |
|----|------|----------|-------|
| COST001 | Queue retries high | MEDIUM | `max_retries > 1` for potentially idempotent consumers |
| COST002 | No cron batching | LOW | Multiple crons that could be combined |
| COST003 | AI without caching | MEDIUM | AI bindings but no AI Gateway |
| COST004 | Large model usage | LOW | Workers AI with >8B parameter models |
| COST005 | Missing Analytics Engine | INFO | Using D1/KV for metrics instead of free AE |

### Resilience Audit Rules

| ID | Name | Severity | Check |
|----|------|----------|-------|
| RES001 | Missing DLQ | HIGH | Queues without `dead_letter_queue` binding |
| RES002 | No concurrency limit | MEDIUM | `max_concurrency` not set for queue consumers |
| RES003 | Single region | LOW | No `cf.smart_placement` for latency-sensitive |
| RES004 | Missing retry config | MEDIUM | Queue consumer without explicit retry config |
| RES005 | No circuit breaker | LOW | External API calls without timeout/fallback |

## Audit Workflow

### Step 1: Parse Wrangler Config

Support both TOML and JSONC formats:
```
1. Read wrangler.toml or wrangler.jsonc
2. Parse into structured format
3. Extract: name, bindings, routes, triggers, vars
```

### Step 2: Run Security Checks

```
For each security rule:
1. Check if pattern exists in config
2. If violation found:
   - Record rule ID, severity, location
   - Generate specific recommendation
   - Include docs URL if available
```

### Step 3: Run Performance Checks

```
For each performance rule:
1. Check config for anti-patterns
2. Cross-reference with migrations (for D1 index checks)
3. Record findings with optimization recommendations
```

### Step 4: Run Cost Checks

```
For each cost rule:
1. Identify cost-amplifying patterns
2. Estimate impact if possible
3. Provide specific fixes
```

### Step 5: Run Resilience Checks

```
For each resilience rule:
1. Check for missing failure handling
2. Identify single points of failure
3. Recommend redundancy patterns
```

### Step 6: Calculate Score

```
score = 100 - (critical × 25) - (high × 15) - (medium × 5) - (low × 2)
```

Grades:
- 90-100: A (Production ready)
- 80-89: B (Minor issues)
- 70-79: C (Address before deployment)
- 60-69: D (Significant issues)
- <60: F (Critical problems)

## Output Format

```markdown
# Cloudflare Configuration Audit

**Score**: XX/100 (Grade: X)
**File**: wrangler.jsonc

## Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | X | X | X | X |
| Performance | X | X | X | X |
| Cost | X | X | X | X |
| Resilience | X | X | X | X |

## Critical Issues (Must Fix)

### SEC001: Secrets in plaintext
- **Location**: `vars.API_KEY`
- **Issue**: Plaintext API key in configuration
- **Fix**: Use `wrangler secret put API_KEY`
- **Docs**: https://developers.cloudflare.com/workers/configuration/secrets/

## High Priority Issues

### RES001: Missing dead letter queue
- **Location**: `queues[0]` (harvest-queue)
- **Issue**: No DLQ for failed message inspection
- **Fix**: Add `dead_letter_queue = "harvest-dlq"`

## Medium Priority Issues

[List all medium issues]

## Low Priority Issues

[List all low issues]

## Recommendations

1. [ ] Move secrets to wrangler secret
2. [ ] Add DLQ for all production queues
3. [ ] Enable Smart Placement
4. [ ] Consider Analytics Engine for metrics
```

## Migration Checks

When D1 bindings exist, also scan migration files:

```sql
-- Good: Has index
CREATE INDEX idx_projects_source ON projects(source);

-- Bad: Missing index for common query pattern
SELECT * FROM projects WHERE source = ? ORDER BY created_at DESC;
```

Flag missing indexes for:
- Columns in WHERE clauses
- Columns in ORDER BY
- Compound queries (need compound indexes)

## Wrangler Config Patterns

### Good Patterns to Recognize

```jsonc
{
  // Smart Placement enabled
  "placement": { "mode": "smart" },

  // Observability configured
  "observability": { "logs": { "enabled": true } },

  // Queue with DLQ
  "queues": {
    "consumers": [{
      "queue": "my-queue",
      "dead_letter_queue": "my-dlq",
      "max_retries": 1,
      "max_concurrency": 10
    }]
  }
}
```

### Bad Patterns to Flag

```jsonc
{
  // Secrets in vars
  "vars": { "API_KEY": "sk-xxxxx" },

  // No DLQ
  "queues": { "consumers": [{ "queue": "my-queue" }] },

  // High retries
  "queues": { "consumers": [{ "max_retries": 10 }] }
}
```

## Live Validation with Probes

When MCP tools are available (via `--validate` mode in `/cf-audit`), enhance static findings with live data.

Reference @skills/probes/SKILL.md for detailed query patterns.

### Security Validation
- **Error rate analysis**: High errors on specific paths may indicate attacks
- **Request patterns**: Verify authentication is actually enforced
- **Resource exposure**: Check KV/R2 for public access settings

### Performance Validation
- **EXPLAIN QUERY PLAN**: Verify D1 index usage
- **Latency percentiles**: P50/P95/P99 analysis
- **CPU time analysis**: Identify hotspots

### Resilience Validation
- **Queue health**: Check DLQ depth and retry rates
- **Error patterns**: Identify cascading failures

## Provenance Tagging

Tag findings based on data source:
- `[STATIC]` - Inferred from code/config analysis only
- `[LIVE-VALIDATED]` - Confirmed by observability data
- `[LIVE-REFUTED]` - Code smell not observed in production
- `[INCOMPLETE]` - MCP tools unavailable for verification

## Pattern Recommendations

When issues are found, recommend applicable patterns from @skills/patterns/:

| Finding | Recommended Pattern |
|---------|-------------------|
| Per-row D1 inserts | `d1-batching` |
| External API issues | `circuit-breaker` |
| Monolithic Worker | `service-bindings` |

## Tips

- Run before every deployment
- Use `--validate` for production-ready verification
- Focus on CRITICAL and HIGH first
- Use `--fix` suggestions to auto-generate patches
- Compare scores over time to track improvements
- `[LIVE-REFUTED]` findings may still be worth fixing proactively

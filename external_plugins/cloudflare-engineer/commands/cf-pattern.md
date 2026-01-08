---
description: "Apply Cloudflare architecture pattern to current project"
argument-hint: "<pattern-name> [--analyze-only]"
allowed-tools: ["Read", "Glob", "Grep", "Write", "Bash", "mcp__cloudflare-bindings__*"]
---

# Cloudflare Pattern Application

Apply proven architecture patterns to your Cloudflare project.

**Arguments:** "$ARGUMENTS"

## Available Patterns

| Pattern | Description | Effort |
|---------|-------------|--------|
| `service-bindings` | Decompose monolithic Worker with RPC | Medium |
| `d1-batching` | Optimize D1 write costs with batch operations | Low |
| `circuit-breaker` | Add resilience for external API dependencies | Medium |

## Usage

```bash
/cf-pattern service-bindings           # Apply pattern with guidance
/cf-pattern d1-batching --analyze-only # Analyze without modifying
/cf-pattern circuit-breaker            # Apply circuit breaker pattern
/cf-pattern                            # Interactive pattern selection
```

## Workflow

### Step 0: Parse Arguments

Parse `$ARGUMENTS` for:
- `<pattern-name>`: Which pattern to apply (or empty for interactive)
- `--analyze-only`: Just analyze, don't modify files

### Step 1: Pattern Selection

**If pattern name provided:**
Load pattern details from @skills/patterns/SKILL.md

**If no pattern name:**
Analyze codebase and recommend applicable patterns:

1. **Check for Service Bindings triggers:**
   - Large Worker file (>500 lines)
   - Multiple `fetch()` to internal URLs
   - Subrequest-heavy code paths

2. **Check for D1 Batching triggers:**
   - Per-row INSERT in loops
   - D1 mentioned as cost driver in previous audits
   - `db.run()` in forEach/map callbacks

3. **Check for Circuit Breaker triggers:**
   - External API `fetch()` calls without timeout
   - No fallback behavior for third-party services
   - Error handling that just re-throws

### Step 2: Current State Analysis

Scan project for pattern-specific indicators:

**For service-bindings:**
```bash
# Find main Worker file size
wc -l src/index.ts

# Find internal fetch calls
grep -r "fetch.*localhost\|fetch.*127.0.0.1\|fetch.*internal" src/

# Check subrequest patterns
grep -r "fetch(" src/ | wc -l
```

**For d1-batching:**
```bash
# Find per-row inserts
grep -rn "for.*await.*db\." src/
grep -rn "forEach.*await.*INSERT" src/
grep -rn "\.map.*await.*\.run" src/
```

**For circuit-breaker:**
```bash
# Find unprotected external fetches
grep -rn "fetch\s*(" src/ | grep -v "localhost\|127.0.0.1"

# Check for timeout usage
grep -r "AbortSignal.timeout\|setTimeout" src/
```

### Step 3: Generate Analysis Report

```markdown
# Pattern Analysis: [pattern-name]

## Applicability Score: [High | Medium | Low]

## Detected Triggers

| Trigger | Found | Location |
|---------|-------|----------|
| [trigger 1] | Yes/No | file:line |
| [trigger 2] | Yes/No | file:line |

## Current State

[Summary of current implementation]

## Recommended Changes

1. [Change 1]
   - File: [path]
   - Current: [code snippet]
   - After: [code snippet]

2. [Change 2]
   ...

## Estimated Effort

- Files to modify: X
- New files: Y
- Complexity: [Low | Medium | High]

## Trade-offs

**Benefits:**
- [Benefit 1]
- [Benefit 2]

**Costs:**
- [Cost 1]
- [Cost 2]
```

### Step 4: Apply Pattern (unless --analyze-only)

**If `--analyze-only`:**
Stop after analysis report.

**Otherwise:**
Apply pattern changes:

1. **Confirm with user** before making changes
2. Generate new files (if any)
3. Modify existing files
4. Update wrangler.jsonc
5. Provide migration/testing instructions

## Pattern Details

### service-bindings

**When to Apply:**
- Worker > 500 lines
- Multiple `fetch()` to internal URLs
- Approaching subrequest limits
- Multiple teams need independent deploys

**What Gets Created:**
- Separate Worker projects per domain
- Service binding configuration in wrangler.jsonc
- Shared types package (optional)

**What Gets Modified:**
- Main Worker (becomes gateway)
- wrangler.jsonc (adds service bindings)

Reference: @skills/patterns/service-bindings.md

### d1-batching

**When to Apply:**
- Per-row INSERT in loops
- D1 writes > 50% of costs
- Cron jobs with unbatched writes

**What Gets Modified:**
- Insert/update functions to use batch
- Loop structures to accumulate then flush

**No New Files** (in-place optimization)

Reference: @skills/patterns/d1-batching.md

### circuit-breaker

**When to Apply:**
- External API calls without timeout
- No fallback behavior
- Error rate spikes from upstream

**What Gets Created:**
- `circuit-breaker.ts` utility
- KV namespace for circuit state (in wrangler.jsonc)

**What Gets Modified:**
- External API call sites wrapped with breaker
- Error handling enhanced with fallbacks

Reference: @skills/patterns/circuit-breaker.md

## Interactive Mode

When run without pattern name:

```markdown
# Pattern Recommendation

Based on analysis of your codebase:

## Recommended Patterns

1. **d1-batching** (High applicability)
   - Found 5 per-row insert loops
   - Estimated savings: $XX/month

2. **circuit-breaker** (Medium applicability)
   - Found 3 unprotected external API calls
   - Improves resilience

3. **service-bindings** (Low applicability)
   - Worker is 200 lines (threshold: 500)
   - Consider when Worker grows

## Quick Apply

Run: `/cf-pattern d1-batching` to apply top recommendation
```

## Example Output

```markdown
# Pattern Analysis: d1-batching

## Applicability Score: High

## Detected Triggers

| Trigger | Found | Location |
|---------|-------|----------|
| Per-row INSERT in loop | Yes | src/api/users.ts:45 |
| Per-row INSERT in loop | Yes | src/cron/sync.ts:23 |
| D1 cost driver | Yes | (from /cf-costs analysis) |

## Current State

Found 2 locations with per-row inserts:

**src/api/users.ts:45**
```typescript
for (const user of users) {
  await db.run('INSERT INTO users (email) VALUES (?)', [user.email]);
}
```

**src/cron/sync.ts:23**
```typescript
items.forEach(async (item) => {
  await db.run('INSERT INTO items (name) VALUES (?)', [item.name]);
});
```

## Recommended Changes

### 1. src/api/users.ts

**Before:**
```typescript
for (const user of users) {
  await db.run('INSERT INTO users (email) VALUES (?)', [user.email]);
}
```

**After:**
```typescript
const BATCH_SIZE = 100;
for (let i = 0; i < users.length; i += BATCH_SIZE) {
  const batch = users.slice(i, i + BATCH_SIZE);
  const placeholders = batch.map(() => '(?)').join(', ');
  const values = batch.map(u => u.email);
  await db.run(`INSERT INTO users (email) VALUES ${placeholders}`, values);
}
```

### 2. src/cron/sync.ts

[Similar transformation...]

## Estimated Effort

- Files to modify: 2
- New files: 0
- Complexity: Low

## Trade-offs

**Benefits:**
- 10-100x reduction in D1 write operations
- Faster execution (fewer round trips)
- Lower monthly costs

**Costs:**
- Slightly more complex code
- Need error handling per batch
- Higher memory usage for large batches

---

Proceed with changes? Use `/cf-pattern d1-batching` to apply.
```

## Tips

- Run `/cf-costs` first to identify which patterns have highest ROI
- Use `--analyze-only` to preview changes before applying
- Start with `d1-batching` (lowest risk, quick wins)
- `circuit-breaker` is recommended for any production external API usage
- `service-bindings` is a larger refactor - plan accordingly

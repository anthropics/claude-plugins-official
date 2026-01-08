# D1 Batching Pattern

Optimize D1 write costs by batching operations instead of per-row inserts.

## Problem

D1 writes are expensive ($1/M writes vs $0.25/B reads):
- Per-row INSERT in loops multiplies write costs
- Cron jobs processing records one at a time
- Webhook handlers inserting single records
- Import operations without batching

**Cost Example**:
- 10,000 users, each with 10 records = 100,000 individual inserts
- At $1/M writes = $0.10 per import
- Daily import = $3/month just for one operation
- With batching (100 records/batch) = 1,000 writes = $0.001

---

## Solution

Batch multiple operations into single database calls:
- Use `db.batch()` for multiple statements
- Use multi-row INSERT syntax
- Buffer writes and flush periodically
- Process in chunks for large datasets

---

## Before (Anti-Pattern)

```typescript
// Per-row inserts - EXPENSIVE!
export async function importUsers(users: User[], db: D1Database) {
  for (const user of users) {
    // Each iteration = 1 write operation = $$$
    await db.prepare(
      'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
    ).bind(user.id, user.email, user.name).run();
  }
}

// 10,000 users = 10,000 write operations
```

**Problems**:
- 10,000 writes for 10,000 records
- Sequential execution (slow)
- No transaction safety (partial failures)

---

## After (Batched)

### Option 1: db.batch() for Multiple Statements

```typescript
export async function importUsers(users: User[], db: D1Database) {
  // Prepare all statements
  const statements = users.map(user =>
    db.prepare(
      'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
    ).bind(user.id, user.email, user.name)
  );

  // Execute as single batch (1 write operation!)
  // Note: D1 batch has limits, chunk if needed
  const BATCH_SIZE = 100;
  for (let i = 0; i < statements.length; i += BATCH_SIZE) {
    const batch = statements.slice(i, i + BATCH_SIZE);
    await db.batch(batch);
  }
}

// 10,000 users = 100 write operations (100x cheaper!)
```

### Option 2: Multi-Row INSERT Syntax

```typescript
export async function importUsers(users: User[], db: D1Database) {
  const BATCH_SIZE = 100;

  for (let i = 0; i < users.length; i += BATCH_SIZE) {
    const batch = users.slice(i, i + BATCH_SIZE);

    // Build multi-row INSERT
    const placeholders = batch.map(() => '(?, ?, ?)').join(', ');
    const values = batch.flatMap(u => [u.id, u.email, u.name]);

    await db.prepare(
      `INSERT INTO users (id, email, name) VALUES ${placeholders}`
    ).bind(...values).run();
  }
}

// Single statement per batch, even more efficient
```

### Option 3: Write Buffer for Streaming Data

```typescript
class D1WriteBuffer {
  private buffer: User[] = [];
  private readonly FLUSH_SIZE = 100;
  private readonly FLUSH_INTERVAL_MS = 1000;
  private flushTimer: number | null = null;

  constructor(private db: D1Database) {}

  async add(user: User): Promise<void> {
    this.buffer.push(user);

    if (this.buffer.length >= this.FLUSH_SIZE) {
      await this.flush();
    } else if (!this.flushTimer) {
      // Flush after interval even if buffer not full
      this.flushTimer = setTimeout(() => this.flush(), this.FLUSH_INTERVAL_MS);
    }
  }

  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const toFlush = this.buffer.splice(0, this.buffer.length);
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    const placeholders = toFlush.map(() => '(?, ?, ?)').join(', ');
    const values = toFlush.flatMap(u => [u.id, u.email, u.name]);

    await this.db.prepare(
      `INSERT INTO users (id, email, name) VALUES ${placeholders}`
    ).bind(...values).run();
  }

  async close(): Promise<void> {
    await this.flush();
  }
}

// Usage
const buffer = new D1WriteBuffer(env.DB);
for await (const user of userStream) {
  await buffer.add(user);
}
await buffer.close();
```

### Option 4: Upsert with Conflict Handling

```typescript
export async function upsertUsers(users: User[], db: D1Database) {
  const BATCH_SIZE = 100;

  for (let i = 0; i < users.length; i += BATCH_SIZE) {
    const batch = users.slice(i, i + BATCH_SIZE);

    const placeholders = batch.map(() => '(?, ?, ?)').join(', ');
    const values = batch.flatMap(u => [u.id, u.email, u.name]);

    // INSERT OR REPLACE for upsert behavior
    await db.prepare(
      `INSERT OR REPLACE INTO users (id, email, name) VALUES ${placeholders}`
    ).bind(...values).run();
  }
}
```

---

## Batch Size Guidelines

| Scenario | Recommended Batch Size | Reason |
|----------|----------------------|--------|
| Simple inserts | 100-500 rows | Balance between efficiency and memory |
| Complex rows (many columns) | 50-100 rows | SQLite statement size limits |
| With foreign key checks | 50-100 rows | Constraint validation overhead |
| Real-time streaming | 10-50 rows | Lower latency |
| Background import | 500-1000 rows | Maximum throughput |

**Hard Limits**:
- D1 `batch()` supports up to 100 statements
- SQLite has ~1MB statement size limit
- Worker memory limits apply

---

## Error Handling

### Per-Batch Error Recovery

```typescript
export async function importUsersWithRecovery(
  users: User[],
  db: D1Database
): Promise<{ success: number; failed: User[] }> {
  const BATCH_SIZE = 100;
  let success = 0;
  const failed: User[] = [];

  for (let i = 0; i < users.length; i += BATCH_SIZE) {
    const batch = users.slice(i, i + BATCH_SIZE);

    try {
      const placeholders = batch.map(() => '(?, ?, ?)').join(', ');
      const values = batch.flatMap(u => [u.id, u.email, u.name]);

      await db.prepare(
        `INSERT INTO users (id, email, name) VALUES ${placeholders}`
      ).bind(...values).run();

      success += batch.length;
    } catch (error) {
      // Batch failed - try individual inserts to identify bad records
      for (const user of batch) {
        try {
          await db.prepare(
            'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
          ).bind(user.id, user.email, user.name).run();
          success++;
        } catch {
          failed.push(user);
        }
      }
    }
  }

  return { success, failed };
}
```

### Transaction Wrapper

```typescript
export async function importUsersTransactional(
  users: User[],
  db: D1Database
): Promise<void> {
  const BATCH_SIZE = 100;

  // D1 batch() is automatically transactional
  const allStatements: D1PreparedStatement[] = [];

  for (const user of users) {
    allStatements.push(
      db.prepare(
        'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
      ).bind(user.id, user.email, user.name)
    );
  }

  // Execute in transactional batches
  for (let i = 0; i < allStatements.length; i += BATCH_SIZE) {
    const batch = allStatements.slice(i, i + BATCH_SIZE);
    await db.batch(batch);  // All-or-nothing per batch
  }
}
```

---

## Implementation Steps

### Step 1: Identify Write Hot Spots

Search codebase for patterns:
```bash
# Find per-row inserts in loops
grep -r "for.*await.*db\." src/
grep -r "\.forEach.*await.*INSERT" src/
grep -r "map.*await.*\.run\(\)" src/
```

### Step 2: Measure Current Costs

Query observability for D1 write counts:
```javascript
// Use probes skill for this
mcp__cloudflare-observability__query_worker_observability({
  // ... D1 write metrics
})
```

### Step 3: Implement Batching

1. Choose appropriate batch size
2. Implement chunking logic
3. Add error handling
4. Test with realistic data volumes

### Step 4: Validate Savings

Compare before/after:
- Write operation count
- Request latency (batching is often faster too)
- Monthly cost projection

---

## Trade-offs

| Aspect | Pro | Con |
|--------|-----|-----|
| Cost | 10-100x cheaper | Slightly more complex code |
| Performance | Faster (fewer round trips) | Higher memory usage |
| Atomicity | Batch is transactional | Partial batch failures need handling |
| Latency | Higher for individual writes | Lower for bulk operations |

---

## Validation Checklist

- [ ] No per-row inserts in loops remain
- [ ] Batch size appropriate for data shape
- [ ] Error handling per batch implemented
- [ ] Memory usage acceptable for batch size
- [ ] Cost reduction verified in observability

---

## Common Mistakes

1. **Batch Too Large**: Hitting memory or statement limits
2. **No Error Recovery**: Single bad record fails entire import
3. **Ignoring Constraints**: Foreign key violations not handled
4. **Unbounded Buffers**: Write buffer growing without limit

---

## Related Patterns

- **Service Bindings**: Dedicated data service for write optimization
- **Event Sourcing**: Queue writes for async processing
- **Read Replicas**: Separate read/write paths for different optimization

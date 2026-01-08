---
name: scale
description: Recommend sharding, caching strategies, and read-replication patterns for Cloudflare architectures. Use this skill when preparing for growth, hitting limits, or optimizing for high traffic.
---

# Cloudflare Scaling Skill

Strategies for scaling Cloudflare architectures beyond default limits while maintaining cost efficiency.

## Scaling Decision Matrix

| Bottleneck | Symptom | Solution |
|------------|---------|----------|
| D1 read latency | >50ms queries | Add KV cache layer |
| D1 write throughput | Queue backlog | Batch writes, add queue buffer |
| D1 storage | Approaching 10GB | Archive to R2, partition tables |
| KV read latency | Cache misses | Key prefixing, predictable keys |
| KV write rate | 1 write/sec/key limit | Shard keys, batch writes |
| R2 throughput | Slow uploads | Presigned URLs, multipart |
| Worker memory | 128MB limit | Streaming, chunked processing |
| Worker CPU | 30s timeout | Queues, Workflows, DO |
| Subrequests | 1000/request limit | Service Bindings RPC |
| Queue throughput | Consumer lag | Increase concurrency, batch size |

## Caching Strategies

### Cache Hierarchy

```
Request → Edge Cache → KV Cache → D1 → Origin
           (Tiered)    (Global)   (Primary)
```

### KV Cache Patterns

#### Write-Through Cache
```typescript
async function getWithCache<T>(
  kv: KVNamespace,
  db: D1Database,
  key: string,
  query: () => Promise<T>,
  ttl: number = 3600
): Promise<T> {
  // Try cache first
  const cached = await kv.get(key, 'json');
  if (cached !== null) {
    return cached as T;
  }

  // Cache miss - fetch from D1
  const fresh = await query();

  // Write to cache (non-blocking)
  kv.put(key, JSON.stringify(fresh), { expirationTtl: ttl });

  return fresh;
}
```

#### Cache Invalidation
```typescript
// Pattern 1: TTL-based (simple, eventual consistency)
await kv.put(key, value, { expirationTtl: 300 }); // 5 min

// Pattern 2: Version-based (immediate, more complex)
const version = await kv.get('cache:version');
const key = `data:${id}:v${version}`;

// Invalidate by incrementing version
await kv.put('cache:version', String(Number(version) + 1));

// Pattern 3: Tag-based (flexible, requires cleanup)
await kv.put(`user:${userId}:profile`, data);
await kv.put(`user:${userId}:settings`, settings);

// Invalidate all user data
const keys = await kv.list({ prefix: `user:${userId}:` });
for (const key of keys.keys) {
  await kv.delete(key.name);
}
```

### Tiered Cache (Cloudflare CDN)

Enable in Worker for static-like responses:
```typescript
// Cache API for fine-grained control
const cache = caches.default;

app.get('/api/products/:id', async (c) => {
  const cacheKey = new Request(c.req.url);

  // Check cache
  const cached = await cache.match(cacheKey);
  if (cached) {
    return cached;
  }

  // Fetch fresh data
  const product = await getProduct(c.env.DB, c.req.param('id'));

  const response = c.json(product);
  response.headers.set('Cache-Control', 's-maxage=300');

  // Store in cache
  c.executionCtx.waitUntil(cache.put(cacheKey, response.clone()));

  return response;
});
```

## Sharding Strategies

### Key-Based Sharding (KV)

When hitting 1 write/sec/key limit:

```typescript
// Problem: High-frequency counter
await kv.put('page:views', views); // Limited to 1/sec

// Solution: Shard across multiple keys
const SHARD_COUNT = 10;

async function incrementCounter(kv: KVNamespace, key: string) {
  const shard = Math.floor(Math.random() * SHARD_COUNT);
  const shardKey = `${key}:shard:${shard}`;

  const current = Number(await kv.get(shardKey)) || 0;
  await kv.put(shardKey, String(current + 1));
}

async function getCounter(kv: KVNamespace, key: string): Promise<number> {
  let total = 0;
  for (let i = 0; i < SHARD_COUNT; i++) {
    const value = await kv.get(`${key}:shard:${i}`);
    total += Number(value) || 0;
  }
  return total;
}
```

### Time-Based Sharding (D1)

For high-volume time-series data:

```sql
-- Partition by month
CREATE TABLE events_2025_01 (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    data TEXT
);

CREATE TABLE events_2025_02 (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    data TEXT
);

-- Query router in code
function getEventsTable(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  return `events_${year}_${month}`;
}
```

### Entity-Based Sharding (D1)

For multi-tenant applications:

```typescript
// Tenant-specific D1 databases
interface Bindings {
  DB_TENANT_A: D1Database;
  DB_TENANT_B: D1Database;
  // Or use Hyperdrive for external Postgres
}

function getDbForTenant(env: Bindings, tenantId: string): D1Database {
  const dbMapping: Record<string, D1Database> = {
    'tenant-a': env.DB_TENANT_A,
    'tenant-b': env.DB_TENANT_B,
  };
  return dbMapping[tenantId] ?? env.DB_DEFAULT;
}
```

## Read Replication Patterns

### D1 Read Replicas

D1 automatically creates read replicas. Optimize access:

```typescript
// Enable Smart Placement in wrangler.jsonc
{
  "placement": { "mode": "smart" }
}

// Worker runs near data, reducing latency
```

### Multi-Region with Durable Objects

For global coordination with regional caching:

```typescript
// Durable Object for region-local state
export class RegionalCache {
  private state: DurableObjectState;
  private cache: Map<string, { value: unknown; expires: number }>;

  constructor(state: DurableObjectState) {
    this.state = state;
    this.cache = new Map();
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const key = url.searchParams.get('key');

    if (request.method === 'GET' && key) {
      const cached = this.cache.get(key);
      if (cached && cached.expires > Date.now()) {
        return Response.json({ value: cached.value, source: 'cache' });
      }
      return Response.json({ value: null, source: 'miss' });
    }

    if (request.method === 'PUT' && key) {
      const { value, ttl } = await request.json();
      this.cache.set(key, {
        value,
        expires: Date.now() + (ttl * 1000),
      });
      return Response.json({ success: true });
    }

    return Response.json({ error: 'Invalid request' }, { status: 400 });
  }
}
```

### Eventual Consistency Pattern

For data that can tolerate staleness:

```typescript
interface CacheEntry<T> {
  data: T;
  cachedAt: number;
  staleAfter: number;
  expireAfter: number;
}

async function getWithStaleWhileRevalidate<T>(
  kv: KVNamespace,
  key: string,
  fetcher: () => Promise<T>,
  options: {
    staleAfter: number;  // Serve stale, revalidate in background
    expireAfter: number; // Force fresh fetch
  }
): Promise<T> {
  const cached = await kv.get<CacheEntry<T>>(key, 'json');
  const now = Date.now();

  if (cached) {
    // Fresh - return immediately
    if (now < cached.staleAfter) {
      return cached.data;
    }

    // Stale but not expired - return stale, revalidate async
    if (now < cached.expireAfter) {
      // Background revalidation
      kv.put(key, JSON.stringify(await buildCacheEntry(fetcher, options)));
      return cached.data;
    }
  }

  // Expired or missing - must fetch fresh
  const entry = await buildCacheEntry(fetcher, options);
  await kv.put(key, JSON.stringify(entry));
  return entry.data;
}

async function buildCacheEntry<T>(
  fetcher: () => Promise<T>,
  options: { staleAfter: number; expireAfter: number }
): Promise<CacheEntry<T>> {
  const now = Date.now();
  return {
    data: await fetcher(),
    cachedAt: now,
    staleAfter: now + options.staleAfter,
    expireAfter: now + options.expireAfter,
  };
}
```

## Queue Scaling

### Horizontal Scaling (Concurrency)

```jsonc
{
  "queues": {
    "consumers": [
      {
        "queue": "events",
        "max_batch_size": 100,     // Max messages per invocation
        "max_concurrency": 20,     // Parallel consumer instances
        "max_retries": 1,
        "dead_letter_queue": "events-dlq"
      }
    ]
  }
}
```

### Batch Processing Optimization

```typescript
export default {
  async queue(batch: MessageBatch, env: Bindings) {
    // Group messages for efficient D1 batching
    const byType = new Map<string, unknown[]>();

    for (const msg of batch.messages) {
      const type = msg.body.type;
      if (!byType.has(type)) byType.set(type, []);
      byType.get(type)!.push(msg.body.payload);
    }

    // Process each type as a batch
    for (const [type, payloads] of byType) {
      await processBatch(type, payloads, env);
    }

    // Ack all at once
    batch.ackAll();
  },
};

async function processBatch(
  type: string,
  payloads: unknown[],
  env: Bindings
) {
  // Batch insert to D1 (≤1000 at a time)
  const BATCH_SIZE = 1000;
  for (let i = 0; i < payloads.length; i += BATCH_SIZE) {
    const chunk = payloads.slice(i, i + BATCH_SIZE);
    await insertBatch(env.DB, type, chunk);
  }
}
```

## Memory Management

### Streaming for Large Payloads

```typescript
// Problem: Loading entire file into memory
const data = await r2.get(key);
const json = await data.json(); // May exceed 128MB

// Solution: Stream processing
app.get('/export/:key', async (c) => {
  const object = await c.env.R2.get(c.req.param('key'));
  if (!object) return c.json({ error: 'Not found' }, 404);

  return new Response(object.body, {
    headers: {
      'Content-Type': object.httpMetadata?.contentType ?? 'application/octet-stream',
      'Content-Length': String(object.size),
    },
  });
});
```

### Chunked Processing with Durable Objects

```typescript
// For files >50MB, process in chunks with checkpointing
export class ChunkedProcessor {
  private state: DurableObjectState;

  async processFile(r2Key: string, chunkSize: number = 1024 * 1024) {
    // Get checkpoint
    let offset = (await this.state.storage.get<number>('offset')) ?? 0;

    const object = await this.env.R2.get(r2Key, {
      range: { offset, length: chunkSize },
    });

    if (!object) {
      // Processing complete
      await this.state.storage.delete('offset');
      return { complete: true };
    }

    // Process chunk
    await this.processChunk(await object.arrayBuffer());

    // Save checkpoint
    await this.state.storage.put('offset', offset + chunkSize);

    // Schedule next chunk via alarm
    await this.state.storage.setAlarm(Date.now() + 100);

    return { complete: false, offset: offset + chunkSize };
  }
}
```

## Scaling Checklist

### Before Launch
- [ ] KV cache layer for hot data
- [ ] D1 indexes on all query columns
- [ ] Queue DLQs configured
- [ ] Smart Placement enabled
- [ ] Batch size ≤1000 for D1 writes

### At 10K req/day
- [ ] Monitor D1 query performance
- [ ] Review cache hit rates
- [ ] Check queue consumer lag

### At 100K req/day
- [ ] Add Analytics Engine for metrics (free)
- [ ] Consider key sharding for hot KV keys
- [ ] Review batch processing efficiency

### At 1M req/day
- [ ] Implement Tiered Cache
- [ ] Add read-through caching
- [ ] Consider time-based D1 partitioning
- [ ] Review and optimize indexes

### At 10M req/day
- [ ] Multi-region strategy
- [ ] Entity-based sharding
- [ ] Durable Objects for coordination
- [ ] Custom rate limiting

## Cost Implications

| Scaling Strategy | Additional Cost | When to Use |
|------------------|-----------------|-------------|
| KV caching | $0.50/M reads | D1 read heavy |
| Key sharding | More KV reads | >1 write/sec/key |
| Time partitioning | None (same D1) | >10GB data |
| Tiered Cache | None (CDN) | Cacheable responses |
| DO coordination | CPU time | Global state |
| Queue scaling | Per message | High throughput |

## Anti-Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| Cache everything | KV costs add up | Cache hot data only |
| Shard too early | Complexity without benefit | Monitor first |
| Ignore TTLs | Stale data | Set appropriate TTLs |
| Skip DLQ | Lost messages | Always add DLQ |
| Over-replicate | Cost multiplication | Right-size replication |

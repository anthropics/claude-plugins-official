---
name: implement
description: Scaffold Cloudflare Workers with Hono, Drizzle ORM, and TypeScript best practices. Use this skill when implementing new Workers, adding endpoints, or setting up database schemas.
---

# Cloudflare Implementation Skill

Scaffold production-ready Cloudflare Workers following modern patterns with Hono, Drizzle ORM, and TypeScript.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Router | Hono v4+ | Lightweight, fast, TypeScript-first |
| ORM | Drizzle | Type-safe D1 queries, migrations |
| Validation | Zod | Request/response validation |
| Runtime | Workers | Edge compute |

## Project Structure

```
worker/
├── src/
│   ├── index.ts          # Hono app entry
│   ├── routes/           # Route handlers
│   │   ├── api.ts
│   │   └── health.ts
│   ├── middleware/       # Hono middleware
│   │   ├── auth.ts
│   │   └── errors.ts
│   ├── services/         # Business logic
│   │   └── users.ts
│   ├── db/               # Drizzle schema + queries
│   │   ├── schema.ts
│   │   └── queries.ts
│   └── types.ts          # Shared types
├── migrations/           # D1 migrations
│   └── 0001_initial.sql
├── wrangler.jsonc
├── drizzle.config.ts
├── package.json
└── tsconfig.json
```

## Code Templates

### Entry Point (src/index.ts)

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { timing } from 'hono/timing';
import { errorHandler } from './middleware/errors';
import { apiRoutes } from './routes/api';
import { healthRoutes } from './routes/health';
import type { Bindings } from './types';

const app = new Hono<{ Bindings: Bindings }>();

// Middleware
app.use('*', timing());
app.use('*', logger());
app.use('*', cors());
app.onError(errorHandler);

// Routes
app.route('/health', healthRoutes);
app.route('/api', apiRoutes);

// 404 handler
app.notFound((c) => c.json({ error: 'Not found' }, 404));

export default app;
```

### Type Definitions (src/types.ts)

```typescript
export interface Bindings {
  // D1 Database
  DB: D1Database;

  // KV Namespace
  CACHE: KVNamespace;

  // R2 Bucket
  STORAGE: R2Bucket;

  // Queue Producer
  QUEUE: Queue<QueueMessage>;

  // AI
  AI: Ai;

  // Environment variables
  ENVIRONMENT: 'development' | 'staging' | 'production';
}

export interface QueueMessage {
  type: string;
  payload: unknown;
  timestamp: number;
}

// Hono context helper
export type AppContext = Context<{ Bindings: Bindings }>;
```

### Drizzle Schema (src/db/schema.ts)

```typescript
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: text('created_at')
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text('updated_at')
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
});

export const projects = sqliteTable('projects', {
  id: text('id').primaryKey(),
  userId: text('user_id')
    .notNull()
    .references(() => users.id),
  title: text('title').notNull(),
  status: text('status', { enum: ['draft', 'active', 'archived'] })
    .notNull()
    .default('draft'),
  metadata: text('metadata', { mode: 'json' }).$type<Record<string, unknown>>(),
  createdAt: text('created_at')
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
});

// Type exports for queries
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Project = typeof projects.$inferSelect;
export type NewProject = typeof projects.$inferInsert;
```

### Drizzle Config (drizzle.config.ts)

```typescript
import type { Config } from 'drizzle-kit';

export default {
  schema: './src/db/schema.ts',
  out: './migrations',
  dialect: 'sqlite',
} satisfies Config;
```

### Database Queries (src/db/queries.ts)

```typescript
import { drizzle } from 'drizzle-orm/d1';
import { eq, desc, and, sql } from 'drizzle-orm';
import * as schema from './schema';

export function getDb(d1: D1Database) {
  return drizzle(d1, { schema });
}

export async function getUserById(db: D1Database, id: string) {
  const d = getDb(db);
  return d.query.users.findFirst({
    where: eq(schema.users.id, id),
  });
}

export async function createUser(db: D1Database, user: schema.NewUser) {
  const d = getDb(db);
  return d.insert(schema.users).values(user).returning().get();
}

export async function getProjectsByUser(
  db: D1Database,
  userId: string,
  options: { limit?: number; offset?: number } = {}
) {
  const d = getDb(db);
  const { limit = 20, offset = 0 } = options;

  return d.query.projects.findMany({
    where: eq(schema.projects.userId, userId),
    orderBy: desc(schema.projects.createdAt),
    limit,
    offset,
  });
}

// Batch insert pattern (≤1000 rows)
export async function batchInsertProjects(
  db: D1Database,
  projects: schema.NewProject[]
) {
  const d = getDb(db);
  const BATCH_SIZE = 1000;

  for (let i = 0; i < projects.length; i += BATCH_SIZE) {
    const batch = projects.slice(i, i + BATCH_SIZE);
    await d.insert(schema.projects).values(batch);
  }
}
```

### Route Handler (src/routes/api.ts)

```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import type { Bindings } from '../types';
import * as queries from '../db/queries';

const api = new Hono<{ Bindings: Bindings }>();

// Validation schemas
const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().optional(),
});

const paginationSchema = z.object({
  limit: z.coerce.number().min(1).max(100).default(20),
  offset: z.coerce.number().min(0).default(0),
});

// GET /api/users/:id
api.get('/users/:id', async (c) => {
  const id = c.req.param('id');
  const user = await queries.getUserById(c.env.DB, id);

  if (!user) {
    return c.json({ error: 'User not found' }, 404);
  }

  return c.json(user);
});

// POST /api/users
api.post('/users', zValidator('json', createUserSchema), async (c) => {
  const data = c.req.valid('json');
  const id = crypto.randomUUID();

  const user = await queries.createUser(c.env.DB, {
    id,
    ...data,
  });

  return c.json(user, 201);
});

// GET /api/users/:id/projects
api.get(
  '/users/:id/projects',
  zValidator('query', paginationSchema),
  async (c) => {
    const userId = c.req.param('id');
    const { limit, offset } = c.req.valid('query');

    const projects = await queries.getProjectsByUser(c.env.DB, userId, {
      limit,
      offset,
    });

    return c.json({ projects, limit, offset });
  }
);

export { api as apiRoutes };
```

### Error Middleware (src/middleware/errors.ts)

```typescript
import type { ErrorHandler } from 'hono';
import type { Bindings } from '../types';

export const errorHandler: ErrorHandler<{ Bindings: Bindings }> = (
  err,
  c
) => {
  console.error('Unhandled error:', err);

  // Don't leak internal errors in production
  if (c.env.ENVIRONMENT === 'production') {
    return c.json({ error: 'Internal server error' }, 500);
  }

  return c.json(
    {
      error: err.message,
      stack: err.stack,
    },
    500
  );
};
```

### Auth Middleware (src/middleware/auth.ts)

```typescript
import { createMiddleware } from 'hono/factory';
import type { Bindings } from '../types';

interface AuthVariables {
  userId: string;
}

export const requireAuth = createMiddleware<{
  Bindings: Bindings;
  Variables: AuthVariables;
}>(async (c, next) => {
  const authHeader = c.req.header('Authorization');

  if (!authHeader?.startsWith('Bearer ')) {
    return c.json({ error: 'Missing authorization' }, 401);
  }

  const token = authHeader.slice(7);

  // Validate token (replace with your auth logic)
  try {
    const userId = await validateToken(token, c.env);
    c.set('userId', userId);
    await next();
  } catch {
    return c.json({ error: 'Invalid token' }, 401);
  }
});

async function validateToken(token: string, env: Bindings): Promise<string> {
  // Implement your token validation
  // e.g., JWT verification, database lookup, etc.
  throw new Error('Not implemented');
}
```

### Queue Consumer (src/queue.ts)

```typescript
import type { Bindings, QueueMessage } from './types';

export default {
  async queue(
    batch: MessageBatch<QueueMessage>,
    env: Bindings
  ): Promise<void> {
    // Process in batches for efficiency
    const messages = batch.messages;

    for (const msg of messages) {
      try {
        await processMessage(msg.body, env);
        msg.ack();
      } catch (error) {
        console.error('Failed to process message:', error);
        // Will retry or go to DLQ based on wrangler config
        msg.retry();
      }
    }
  },
};

async function processMessage(
  message: QueueMessage,
  env: Bindings
): Promise<void> {
  switch (message.type) {
    case 'user.created':
      await handleUserCreated(message.payload, env);
      break;
    case 'project.updated':
      await handleProjectUpdated(message.payload, env);
      break;
    default:
      console.warn('Unknown message type:', message.type);
  }
}

async function handleUserCreated(payload: unknown, env: Bindings) {
  // Process user creation event
}

async function handleProjectUpdated(payload: unknown, env: Bindings) {
  // Process project update event
}
```

### Health Check (src/routes/health.ts)

```typescript
import { Hono } from 'hono';
import type { Bindings } from '../types';

const health = new Hono<{ Bindings: Bindings }>();

health.get('/', async (c) => {
  const checks: Record<string, 'ok' | 'error'> = {};

  // Check D1
  try {
    await c.env.DB.prepare('SELECT 1').first();
    checks.d1 = 'ok';
  } catch {
    checks.d1 = 'error';
  }

  // Check KV
  try {
    await c.env.CACHE.get('health-check');
    checks.kv = 'ok';
  } catch {
    checks.kv = 'error';
  }

  const healthy = Object.values(checks).every((v) => v === 'ok');

  return c.json(
    {
      status: healthy ? 'healthy' : 'degraded',
      checks,
      timestamp: new Date().toISOString(),
    },
    healthy ? 200 : 503
  );
});

export { health as healthRoutes };
```

### Migration Template (migrations/0001_initial.sql)

```sql
-- Migration: Initial schema
-- Created: YYYY-MM-DD

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'archived')),
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Always create indexes for WHERE and ORDER BY columns
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_user_status ON projects(user_id, status);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
```

### Package.json Template

```json
{
  "name": "worker-name",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "wrangler d1 migrations apply DB",
    "db:migrate:local": "wrangler d1 migrations apply DB --local",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "hono": "^4.0.0",
    "@hono/zod-validator": "^0.2.0",
    "drizzle-orm": "^0.29.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20240000.0",
    "drizzle-kit": "^0.20.0",
    "typescript": "^5.3.0",
    "wrangler": "^3.0.0"
  }
}
```

### TSConfig Template

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["@cloudflare/workers-types"],
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "jsxImportSource": "hono/jsx"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

## Best Practices

### D1 Query Patterns

```typescript
// GOOD: Batch inserts
const BATCH_SIZE = 1000;
for (let i = 0; i < items.length; i += BATCH_SIZE) {
  await db.insert(table).values(items.slice(i, i + BATCH_SIZE));
}

// BAD: Per-row inserts
for (const item of items) {
  await db.insert(table).values(item); // N statements = N × cost
}
```

### KV Caching Pattern

```typescript
async function getCached<T>(
  kv: KVNamespace,
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 3600
): Promise<T> {
  const cached = await kv.get(key, 'json');
  if (cached) return cached as T;

  const fresh = await fetcher();
  await kv.put(key, JSON.stringify(fresh), { expirationTtl: ttl });
  return fresh;
}
```

### Queue Publishing Pattern

```typescript
// Publish to queue with type safety
async function enqueue<T extends QueueMessage['type']>(
  queue: Queue<QueueMessage>,
  type: T,
  payload: Extract<QueueMessage, { type: T }>['payload']
) {
  await queue.send({
    type,
    payload,
    timestamp: Date.now(),
  });
}
```

### Error Handling Pattern

```typescript
// Custom error classes
class NotFoundError extends Error {
  status = 404;
}

class ValidationError extends Error {
  status = 400;
}

// Error handler catches and formats
const errorHandler: ErrorHandler = (err, c) => {
  const status = 'status' in err ? (err.status as number) : 500;
  return c.json({ error: err.message }, status);
};
```

## Service Bindings RPC

For Worker-to-Worker calls, use Service Bindings instead of HTTP:

```typescript
// In wrangler.jsonc
{
  "services": [
    { "binding": "AUTH_SERVICE", "service": "auth-worker" }
  ]
}

// In code
interface AuthService {
  validateToken(token: string): Promise<{ userId: string }>;
}

// Call via RPC (no HTTP overhead)
const result = await c.env.AUTH_SERVICE.validateToken(token);
```

## Commands

```bash
# Generate migration from schema changes
npm run db:generate

# Apply migrations locally
npm run db:migrate:local

# Apply migrations to remote D1
npm run db:migrate

# Development
npm run dev

# Deploy
npm run deploy
```

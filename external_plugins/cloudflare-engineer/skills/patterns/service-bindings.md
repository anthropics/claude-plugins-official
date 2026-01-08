# Service Bindings Pattern

Decompose monolithic Workers into service-bound microservices using RPC instead of HTTP fetch.

## Problem

Monolithic Worker is hitting limits or becoming unmaintainable:
- Approaching 1,000 subrequest/request limit
- Single Worker handling unrelated domains (auth, data, notifications)
- HTTP `fetch()` between internal Workers adds latency and counts against limits
- Large bundle size (>1MB)
- Multiple teams blocked on single deployment pipeline

## Solution

Split into separate Workers connected via Service Bindings RPC:
- Zero network overhead (direct memory access)
- No subrequest counting
- Type-safe interfaces
- Independent deployments

---

## Before (Anti-Pattern)

```typescript
// monolith/src/index.ts - Everything in one Worker
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);

    // Auth check via HTTP fetch (counts as subrequest)
    const authResponse = await fetch(`${env.AUTH_URL}/validate`, {
      headers: { Authorization: request.headers.get('Authorization') || '' }
    });
    if (!authResponse.ok) return new Response('Unauthorized', { status: 401 });

    // Data fetch via HTTP (another subrequest)
    if (url.pathname.startsWith('/api/users')) {
      const dataResponse = await fetch(`${env.DATA_URL}/users${url.search}`);
      return dataResponse;
    }

    // Notification via HTTP (another subrequest)
    if (request.method === 'POST' && url.pathname === '/api/notify') {
      await fetch(`${env.NOTIFY_URL}/send`, {
        method: 'POST',
        body: request.body
      });
      return new Response('OK');
    }

    return new Response('Not Found', { status: 404 });
  }
};
```

**Problems**:
- Each internal fetch counts against 1,000 subrequest limit
- Network latency between Workers (even in same region)
- No type safety across service boundaries
- Single point of failure for all functionality

---

## After (Service Bindings)

### 1. Auth Service Worker

```typescript
// auth-service/src/index.ts
export interface AuthService {
  validateToken(token: string): Promise<{ valid: boolean; userId?: string }>;
  generateToken(userId: string): Promise<string>;
}

export default {
  async fetch(request: Request, env: Env) {
    // HTTP endpoint for external access if needed
    return new Response('Auth Service');
  },

  // RPC methods exposed via Service Binding
  async validateToken(token: string): Promise<{ valid: boolean; userId?: string }> {
    // Validate JWT or session token
    try {
      const payload = await verifyJWT(token, env.JWT_SECRET);
      return { valid: true, userId: payload.sub };
    } catch {
      return { valid: false };
    }
  },

  async generateToken(userId: string): Promise<string> {
    return await signJWT({ sub: userId }, env.JWT_SECRET);
  }
} satisfies ExportedHandler<Env> & AuthService;
```

### 2. Data Service Worker

```typescript
// data-service/src/index.ts
export interface DataService {
  getUsers(params: { limit?: number; offset?: number }): Promise<User[]>;
  getUser(id: string): Promise<User | null>;
  createUser(data: CreateUserInput): Promise<User>;
}

export default {
  async fetch(request: Request, env: Env) {
    return new Response('Data Service');
  },

  async getUsers(params: { limit?: number; offset?: number }): Promise<User[]> {
    const { limit = 20, offset = 0 } = params;
    const result = await env.DB.prepare(
      'SELECT * FROM users LIMIT ? OFFSET ?'
    ).bind(limit, offset).all();
    return result.results as User[];
  },

  async getUser(id: string): Promise<User | null> {
    const result = await env.DB.prepare(
      'SELECT * FROM users WHERE id = ?'
    ).bind(id).first();
    return result as User | null;
  },

  async createUser(data: CreateUserInput): Promise<User> {
    const id = crypto.randomUUID();
    await env.DB.prepare(
      'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
    ).bind(id, data.email, data.name).run();
    return { id, ...data };
  }
} satisfies ExportedHandler<Env> & DataService;
```

### 3. Gateway Worker (Orchestrator)

```typescript
// gateway/src/index.ts
import type { AuthService } from '../auth-service/src';
import type { DataService } from '../data-service/src';

interface Env {
  AUTH_SERVICE: Service<AuthService>;
  DATA_SERVICE: Service<DataService>;
}

export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);

    // Auth check via RPC (zero subrequest cost!)
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (token) {
      const auth = await env.AUTH_SERVICE.validateToken(token);
      if (!auth.valid) {
        return new Response('Unauthorized', { status: 401 });
      }
    }

    // Data access via RPC (zero subrequest cost!)
    if (url.pathname === '/api/users') {
      const users = await env.DATA_SERVICE.getUsers({
        limit: Number(url.searchParams.get('limit')) || 20,
        offset: Number(url.searchParams.get('offset')) || 0
      });
      return Response.json(users);
    }

    if (url.pathname.startsWith('/api/users/')) {
      const id = url.pathname.split('/').pop()!;
      const user = await env.DATA_SERVICE.getUser(id);
      if (!user) return new Response('Not Found', { status: 404 });
      return Response.json(user);
    }

    return new Response('Not Found', { status: 404 });
  }
};
```

### 4. Wrangler Configurations

**gateway/wrangler.jsonc**:
```jsonc
{
  "name": "gateway",
  "main": "src/index.ts",
  "compatibility_date": "2024-01-01",
  "services": [
    {
      "binding": "AUTH_SERVICE",
      "service": "auth-service"
    },
    {
      "binding": "DATA_SERVICE",
      "service": "data-service"
    }
  ]
}
```

**auth-service/wrangler.jsonc**:
```jsonc
{
  "name": "auth-service",
  "main": "src/index.ts",
  "compatibility_date": "2024-01-01",
  "vars": {
    "JWT_SECRET": "your-secret-here"  // Use secrets in production!
  }
}
```

**data-service/wrangler.jsonc**:
```jsonc
{
  "name": "data-service",
  "main": "src/index.ts",
  "compatibility_date": "2024-01-01",
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "my-database",
      "database_id": "your-database-id"
    }
  ]
}
```

---

## Implementation Steps

### Step 1: Identify Domain Boundaries

Map your monolith's functionality into domains:

| Domain | Responsibility | Dependencies |
|--------|---------------|--------------|
| Auth | Token validation, user sessions | None |
| Data | CRUD operations, D1 access | None |
| Notification | Email, push notifications | Auth (for user lookup) |
| Gateway | Routing, orchestration | Auth, Data, Notification |

### Step 2: Extract First Service

Start with the service that has:
- Fewest dependencies
- Clearest interface
- Highest reuse potential

Usually: **Auth service** (stateless, well-defined interface)

### Step 3: Define RPC Interface

```typescript
// types/auth.ts (shared)
export interface AuthService {
  validateToken(token: string): Promise<AuthResult>;
  generateToken(userId: string): Promise<string>;
  revokeToken(token: string): Promise<void>;
}

export interface AuthResult {
  valid: boolean;
  userId?: string;
  permissions?: string[];
}
```

### Step 4: Implement Service

Create new Worker project:
```bash
mkdir auth-service
cd auth-service
npm init -y
npm install wrangler typescript
```

### Step 5: Update Gateway

1. Add service binding to wrangler.jsonc
2. Replace `fetch()` calls with RPC calls
3. Update types to use service interfaces

### Step 6: Deploy and Test

```bash
# Deploy service first
cd auth-service && wrangler deploy

# Then update gateway
cd gateway && wrangler deploy
```

### Step 7: Repeat for Remaining Services

Extract one service at a time, maintaining backward compatibility.

---

## Trade-offs

| Aspect | Pro | Con |
|--------|-----|-----|
| Performance | Zero network overhead | Shared Worker memory limits |
| Complexity | Clear separation of concerns | More projects to manage |
| Deployment | Independent releases | Coordination for breaking changes |
| Type Safety | Full TypeScript support | Interface versioning needed |
| Debugging | Isolated failures | Distributed tracing more complex |

---

## Validation Checklist

Before considering this pattern complete:

- [ ] Each service has single responsibility
- [ ] No circular dependencies between services
- [ ] Shared types in common package
- [ ] Each service deployable independently
- [ ] Gateway handles service failures gracefully
- [ ] Monitoring/observability per service
- [ ] Documentation for RPC interfaces

---

## Common Mistakes

1. **Too Fine-Grained**: Don't create a service for every function. Group by domain.
2. **Shared State**: Services should not share D1/KV bindings directly. Use RPC.
3. **Synchronous Chains**: Avoid A → B → C → D chains. Consider async patterns.
4. **Missing Error Handling**: RPC calls can fail. Handle timeouts and errors.

---

## Related Patterns

- **Circuit Breaker**: Add resilience to service calls
- **Event Sourcing**: Use Queues for async communication between services
- **CQRS**: Separate read/write services for different scaling needs

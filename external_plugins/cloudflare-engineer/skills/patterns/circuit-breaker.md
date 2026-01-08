# Circuit Breaker Pattern

Add resilience for external API dependencies with fail-fast behavior and graceful degradation.

## Problem

External API failures cascade to your Worker:
- Third-party APIs go down, your service fails
- Slow responses cause timeouts and poor UX
- No fallback when dependencies are unavailable
- Error rate spikes correlate with upstream issues
- Resources wasted retrying doomed requests

**Impact Example**:
- External API has 5-minute outage
- Your Worker keeps retrying every request
- All requests timeout (30s each)
- User experience: 30s wait then error
- Cost: Wasted CPU time, subrequests

---

## Solution

Implement circuit breaker pattern:
- **Closed**: Normal operation, requests pass through
- **Open**: Failing, fast-fail without calling external API
- **Half-Open**: Testing if external API recovered

With fallback behavior for degraded operation.

---

## Before (Anti-Pattern)

```typescript
export async function getExternalData(userId: string): Promise<UserData> {
  // No timeout - can hang forever
  const response = await fetch(`https://external-api.com/users/${userId}`);

  // No error handling for non-200
  const data = await response.json();

  // No fallback if API is down
  return data;
}

// Called in handler with no protection
export default {
  async fetch(request: Request, env: Env) {
    const userId = new URL(request.url).searchParams.get('userId');

    // Every request hits external API, even if it's known to be down
    const userData = await getExternalData(userId);

    return Response.json(userData);
  }
};
```

**Problems**:
- No timeout protection
- No fallback behavior
- No circuit breaking
- Keeps hitting failing API

---

## After (Circuit Breaker)

### Core Circuit Breaker Implementation

```typescript
// circuit-breaker.ts

interface CircuitBreakerState {
  status: 'closed' | 'open' | 'half-open';
  failures: number;
  lastFailure: number;
  successesSinceHalfOpen: number;
}

interface CircuitBreakerConfig {
  failureThreshold: number;      // Failures before opening
  resetTimeoutMs: number;        // Time before trying again
  halfOpenSuccesses: number;     // Successes needed to close
  timeoutMs: number;             // Request timeout
}

const DEFAULT_CONFIG: CircuitBreakerConfig = {
  failureThreshold: 5,
  resetTimeoutMs: 30000,         // 30 seconds
  halfOpenSuccesses: 3,
  timeoutMs: 5000                // 5 seconds
};

export class CircuitBreaker {
  private state: CircuitBreakerState = {
    status: 'closed',
    failures: 0,
    lastFailure: 0,
    successesSinceHalfOpen: 0
  };

  constructor(
    private name: string,
    private kv: KVNamespace,
    private config: CircuitBreakerConfig = DEFAULT_CONFIG
  ) {}

  // Load state from KV (shared across Worker instances)
  private async loadState(): Promise<void> {
    const stored = await this.kv.get(`circuit:${this.name}`, 'json');
    if (stored) {
      this.state = stored as CircuitBreakerState;
    }
  }

  // Save state to KV
  private async saveState(): Promise<void> {
    await this.kv.put(
      `circuit:${this.name}`,
      JSON.stringify(this.state),
      { expirationTtl: 3600 }  // 1 hour TTL
    );
  }

  async execute<T>(
    operation: () => Promise<T>,
    fallback?: () => Promise<T>
  ): Promise<T> {
    await this.loadState();

    // Check if circuit should transition from open to half-open
    if (this.state.status === 'open') {
      const timeSinceFailure = Date.now() - this.state.lastFailure;
      if (timeSinceFailure >= this.config.resetTimeoutMs) {
        this.state.status = 'half-open';
        this.state.successesSinceHalfOpen = 0;
        await this.saveState();
      }
    }

    // Fast-fail if circuit is open
    if (this.state.status === 'open') {
      if (fallback) {
        return fallback();
      }
      throw new CircuitOpenError(`Circuit ${this.name} is open`);
    }

    // Execute operation with timeout
    try {
      const result = await this.withTimeout(operation);
      await this.onSuccess();
      return result;
    } catch (error) {
      await this.onFailure();

      if (fallback) {
        return fallback();
      }
      throw error;
    }
  }

  private async withTimeout<T>(operation: () => Promise<T>): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      this.config.timeoutMs
    );

    try {
      return await operation();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private async onSuccess(): Promise<void> {
    if (this.state.status === 'half-open') {
      this.state.successesSinceHalfOpen++;
      if (this.state.successesSinceHalfOpen >= this.config.halfOpenSuccesses) {
        // Enough successes - close the circuit
        this.state.status = 'closed';
        this.state.failures = 0;
      }
    } else if (this.state.status === 'closed') {
      // Reset failure count on success
      this.state.failures = 0;
    }
    await this.saveState();
  }

  private async onFailure(): Promise<void> {
    this.state.failures++;
    this.state.lastFailure = Date.now();

    if (this.state.status === 'half-open') {
      // Any failure in half-open reopens the circuit
      this.state.status = 'open';
    } else if (this.state.failures >= this.config.failureThreshold) {
      // Threshold reached - open the circuit
      this.state.status = 'open';
    }
    await this.saveState();
  }

  async getStatus(): Promise<CircuitBreakerState> {
    await this.loadState();
    return { ...this.state };
  }
}

export class CircuitOpenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CircuitOpenError';
  }
}
```

### Using the Circuit Breaker

```typescript
// external-api.ts
import { CircuitBreaker } from './circuit-breaker';

interface Env {
  CIRCUIT_STATE: KVNamespace;
}

export async function getExternalData(
  userId: string,
  env: Env
): Promise<UserData> {
  const breaker = new CircuitBreaker('external-api', env.CIRCUIT_STATE, {
    failureThreshold: 5,
    resetTimeoutMs: 30000,
    halfOpenSuccesses: 3,
    timeoutMs: 5000
  });

  return breaker.execute(
    // Primary operation
    async () => {
      const response = await fetch(
        `https://external-api.com/users/${userId}`,
        { signal: AbortSignal.timeout(5000) }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return response.json() as Promise<UserData>;
    },

    // Fallback when circuit is open or operation fails
    async () => {
      // Return cached data, default data, or partial response
      const cached = await env.CIRCUIT_STATE.get(
        `cache:user:${userId}`,
        'json'
      );

      if (cached) {
        return { ...cached, _stale: true } as UserData;
      }

      // No cache - return minimal default
      return {
        id: userId,
        name: 'Unknown',
        _unavailable: true
      } as UserData;
    }
  );
}
```

### Worker Handler

```typescript
export default {
  async fetch(request: Request, env: Env) {
    const userId = new URL(request.url).searchParams.get('userId');

    if (!userId) {
      return new Response('Missing userId', { status: 400 });
    }

    try {
      const userData = await getExternalData(userId, env);

      // Indicate if data is stale/fallback
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (userData._stale) {
        headers['X-Data-Status'] = 'stale';
      }
      if (userData._unavailable) {
        headers['X-Data-Status'] = 'fallback';
      }

      return new Response(JSON.stringify(userData), { headers });
    } catch (error) {
      if (error instanceof CircuitOpenError) {
        return new Response(
          JSON.stringify({ error: 'Service temporarily unavailable' }),
          { status: 503, headers: { 'Retry-After': '30' } }
        );
      }
      throw error;
    }
  }
};
```

### Wrangler Configuration

```jsonc
{
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2024-01-01",
  "kv_namespaces": [
    {
      "binding": "CIRCUIT_STATE",
      "id": "your-kv-namespace-id"
    }
  ]
}
```

---

## Circuit States Explained

```
     ┌─────────────────────────────────────────────┐
     │                                             │
     ▼                                             │
┌─────────┐  failure >= threshold   ┌──────┐      │
│ CLOSED  │────────────────────────►│ OPEN │      │
└─────────┘                         └──────┘      │
     ▲                                  │         │
     │                                  │ timeout │
     │                                  ▼         │
     │ success >= threshold      ┌───────────┐   │
     └───────────────────────────│ HALF-OPEN │   │
                                 └───────────┘   │
                                      │          │
                                      │ failure  │
                                      └──────────┘
```

| State | Behavior | Transition |
|-------|----------|------------|
| **Closed** | Normal operation | Opens after N failures |
| **Open** | Fast-fail, use fallback | Half-opens after timeout |
| **Half-Open** | Test with limited requests | Closes on success, reopens on failure |

---

## Configuration Guidelines

| Setting | Low Traffic | High Traffic | Critical Path |
|---------|-------------|--------------|---------------|
| `failureThreshold` | 3-5 | 10-20 | 3 |
| `resetTimeoutMs` | 60000 | 30000 | 15000 |
| `halfOpenSuccesses` | 2 | 5 | 2 |
| `timeoutMs` | 10000 | 5000 | 3000 |

---

## Fallback Strategies

### 1. Cached Data

```typescript
async () => {
  const cached = await kv.get(`cache:${key}`, 'json');
  return cached || defaultValue;
}
```

### 2. Degraded Response

```typescript
async () => {
  return {
    data: partialData,
    features: ['basic'],  // Limited feature set
    _degraded: true
  };
}
```

### 3. Alternative Service

```typescript
async () => {
  // Try backup API
  const response = await fetch('https://backup-api.com/...');
  return response.json();
}
```

### 4. Queue for Later

```typescript
async () => {
  // Queue request for retry when service recovers
  await env.RETRY_QUEUE.send({ userId, timestamp: Date.now() });
  return { status: 'queued', retryAfter: 60 };
}
```

---

## Implementation Steps

### Step 1: Identify External Dependencies

List all external API calls:
```bash
grep -r "fetch\s*(" src/ | grep -v "localhost\|127.0.0.1"
```

### Step 2: Add KV Namespace

```bash
wrangler kv:namespace create CIRCUIT_STATE
```

Update wrangler.jsonc with the namespace ID.

### Step 3: Implement Circuit Breaker

Copy the core implementation or use a library.

### Step 4: Wrap External Calls

Replace direct `fetch()` with circuit breaker wrapper.

### Step 5: Define Fallbacks

For each external call, define:
- What to return when unavailable
- How to indicate degraded status
- Cache strategy for known-good data

### Step 6: Monitor Circuit State

Add observability for circuit state changes:
```typescript
console.log(JSON.stringify({
  event: 'circuit_state_change',
  circuit: this.name,
  from: previousStatus,
  to: this.state.status,
  failures: this.state.failures
}));
```

---

## Trade-offs

| Aspect | Pro | Con |
|--------|-----|-----|
| Resilience | Prevents cascade failures | Complexity added |
| UX | Fast fallback vs slow timeout | Users may see stale data |
| Resources | Stops wasting requests | KV storage for state |
| Recovery | Auto-heals when service returns | May be slow to detect recovery |

---

## Validation Checklist

- [ ] All external APIs wrapped with circuit breaker
- [ ] Fallback defined for each dependency
- [ ] Timeout configured appropriately
- [ ] Circuit state persisted in KV
- [ ] Observability for state transitions
- [ ] Degraded response indicates status to clients

---

## Common Mistakes

1. **No Fallback**: Circuit opens but no alternative behavior
2. **Shared State Issues**: Circuit state not persisted across instances
3. **Too Sensitive**: Opens on transient errors (tune threshold)
4. **Too Slow to Recover**: Reset timeout too long
5. **Ignoring Half-Open**: Not testing enough to close circuit

---

## Related Patterns

- **Service Bindings**: Internal services should also have resilience
- **Retry with Backoff**: Before circuit opens, retry with exponential backoff
- **Bulkhead**: Isolate resources per dependency to prevent starvation

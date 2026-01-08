---
name: architect
description: Design industry-grade Cloudflare architectures with wrangler.toml generation and Mermaid diagrams. Use this skill when designing new systems, planning migrations, or evaluating architecture options.
---

# Cloudflare Architect Skill

Design production-ready Cloudflare architectures with proper service selection, wrangler configuration generation, and visual diagrams.

## Core Capabilities

### 1. Architecture Design
- Service selection based on use case requirements
- Data flow design between components
- Scalability and cost trade-off analysis
- Security boundary definition

### 2. Configuration Generation
- Complete wrangler.toml/wrangler.jsonc files
- Environment-specific configurations (dev/staging/prod)
- Binding declarations with proper naming
- Trigger configuration (routes, crons, queues)

### 3. Visual Documentation
- Mermaid architecture diagrams
- Data flow sequence diagrams
- Component relationship graphs

## Service Selection Matrix

### Storage Selection

| Need | Service | Limits | Cost |
|------|---------|--------|------|
| Relational queries | D1 | 10GB, 128MB memory | $0.25/B reads, $1/M writes |
| Key-value lookups | KV | 25MB/value, 1 write/sec/key | $0.50/M reads, $5/M writes |
| Large files/blobs | R2 | 5TB/object | $0.36/M reads, $4.50/M writes |
| Coordination/locks | Durable Objects | Per-object isolation | CPU time based |
| Time-series metrics | Analytics Engine | Adaptive sampling | FREE |
| Vector similarity | Vectorize | 1536 dims, 5M vectors | $0.01/M queries |

### Compute Selection

| Need | Service | Limits | Best For |
|------|---------|--------|----------|
| HTTP handlers | Workers | 128MB, 30s/req | API endpoints |
| Background jobs | Queues | 128KB/msg, batches ≤100 | Async processing |
| Long-running tasks | Workflows | 1024 steps, 1GB state | Multi-step pipelines |
| Stateful coordination | Durable Objects | Per-object | Sessions, locks |
| Scheduled jobs | Cron Triggers | 1-minute minimum | Periodic tasks |

### AI/ML Selection

| Need | Service | Cost | Best For |
|------|---------|------|----------|
| LLM inference | Workers AI | $0.011/1K neurons | Serverless AI |
| LLM caching/logging | AI Gateway | Free tier + $0.10/M | Production AI |
| Embeddings + search | Vectorize | Per-dimension | RAG, semantic search |

## Architecture Templates

### Template 1: API Gateway

**Use Case**: REST/GraphQL API with database backend

```mermaid
graph LR
    subgraph "Edge"
        W[Worker<br/>Hono Router]
    end
    subgraph "Storage"
        D1[(D1<br/>Primary DB)]
        KV[(KV<br/>Cache)]
    end
    subgraph "Auth"
        Access[CF Access]
    end

    Client --> Access --> W
    W --> KV
    KV -.->|miss| D1
    W --> D1
```

**Wrangler Config**:
```jsonc
{
  "name": "api-gateway",
  "main": "src/index.ts",
  "compatibility_date": "2025-01-01",
  "placement": { "mode": "smart" },
  "observability": { "logs": { "enabled": true } },
  "d1_databases": [
    { "binding": "DB", "database_name": "api-db", "database_id": "..." }
  ],
  "kv_namespaces": [
    { "binding": "CACHE", "id": "..." }
  ],
  "routes": [
    { "pattern": "api.example.com/*", "zone_name": "example.com" }
  ]
}
```

### Template 2: Event Pipeline

**Use Case**: Ingest events, process async, store results

```mermaid
graph LR
    subgraph "Ingest"
        I[Ingest Worker]
    end
    subgraph "Processing"
        Q1[Queue]
        P[Processor]
        DLQ[Dead Letter]
    end
    subgraph "Storage"
        D1[(D1)]
        R2[(R2<br/>Raw Data)]
        AE[Analytics Engine]
    end

    Client --> I
    I --> Q1 --> P
    P --> D1
    P --> R2
    P --> AE
    P -.->|failed| DLQ
```

**Wrangler Config**:
```jsonc
{
  "name": "event-pipeline",
  "main": "src/index.ts",
  "compatibility_date": "2025-01-01",
  "observability": { "logs": { "enabled": true } },
  "d1_databases": [
    { "binding": "DB", "database_name": "events-db", "database_id": "..." }
  ],
  "r2_buckets": [
    { "binding": "RAW_DATA", "bucket_name": "events-raw" }
  ],
  "analytics_engine_datasets": [
    { "binding": "METRICS", "dataset": "event_metrics" }
  ],
  "queues": {
    "producers": [
      { "binding": "EVENTS_QUEUE", "queue": "events" }
    ],
    "consumers": [
      {
        "queue": "events",
        "max_batch_size": 100,
        "max_retries": 1,
        "dead_letter_queue": "events-dlq",
        "max_concurrency": 10
      }
    ]
  }
}
```

### Template 3: AI Application

**Use Case**: LLM-powered application with RAG

```mermaid
graph LR
    subgraph "Edge"
        W[Worker]
    end
    subgraph "AI"
        GW[AI Gateway]
        WAI[Workers AI]
    end
    subgraph "Storage"
        V[(Vectorize)]
        KV[(KV<br/>Prompt Cache)]
        D1[(D1<br/>Conversations)]
    end

    Client --> W
    W --> KV
    W --> V
    W --> GW --> WAI
    W --> D1
```

**Wrangler Config**:
```jsonc
{
  "name": "ai-app",
  "main": "src/index.ts",
  "compatibility_date": "2025-01-01",
  "placement": { "mode": "smart" },
  "observability": { "logs": { "enabled": true } },
  "ai": { "binding": "AI" },
  "vectorize": [
    { "binding": "VECTORS", "index_name": "knowledge-base" }
  ],
  "kv_namespaces": [
    { "binding": "PROMPT_CACHE", "id": "..." }
  ],
  "d1_databases": [
    { "binding": "DB", "database_name": "conversations", "database_id": "..." }
  ],
  "vars": {
    "AI_GATEWAY_SLUG": "ai-app-gateway"
  }
}
```

### Template 4: Static Site with Functions

**Use Case**: Marketing site with API endpoints

```mermaid
graph LR
    subgraph "Static"
        Assets[R2<br/>Static Assets]
    end
    subgraph "Dynamic"
        W[Worker<br/>API Routes]
        D1[(D1)]
    end

    Client --> Assets
    Client --> W --> D1
```

**Wrangler Config**:
```jsonc
{
  "name": "marketing-site",
  "main": "src/worker.ts",
  "compatibility_date": "2025-01-01",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS"
  },
  "d1_databases": [
    { "binding": "DB", "database_name": "site-db", "database_id": "..." }
  ],
  "routes": [
    { "pattern": "example.com/*", "zone_name": "example.com" }
  ]
}
```

## Design Workflow

### Step 1: Requirements Gathering

Ask about:
1. **Traffic patterns**: Requests/second, geographic distribution
2. **Data characteristics**: Size, structure, access patterns
3. **Processing needs**: Sync vs async, latency requirements
4. **Budget constraints**: Target monthly cost
5. **Compliance**: Data residency, encryption requirements

### Step 2: Service Selection

For each requirement, select appropriate service:
- High read:write ratio → KV for reads, D1 for writes
- Large files → R2 with presigned URLs
- Time-series data → Analytics Engine (free)
- Search/similarity → Vectorize
- Long processes → Workflows or Queues
- Real-time coordination → Durable Objects

### Step 3: Architecture Draft

Create initial Mermaid diagram showing:
- All Workers and their responsibilities
- Storage bindings and data flow
- Queue topology (if async processing)
- External service integrations

### Step 4: Configuration Generation

Generate wrangler.jsonc with:
- All bindings properly named
- Environment-specific overrides
- Proper placement mode
- Observability enabled
- Queue DLQs configured

### Step 5: Cost Estimation

Calculate monthly costs using:
- Request volume × $0.30/M (Workers)
- Storage GB × service rates
- Operation counts × service rates
- AI usage × neuron/token rates

### Step 6: Review Checklist

Before finalizing, verify:
- [ ] All queues have DLQs
- [ ] D1 has appropriate indexes planned
- [ ] Smart placement enabled for latency-sensitive
- [ ] Observability configured
- [ ] Secrets use wrangler secret (not vars)
- [ ] Rate limiting for public APIs

## Mermaid Diagram Patterns

### Basic Worker Flow
```mermaid
graph LR
    A[Client] --> B[Worker]
    B --> C[(D1)]
    B --> D[(KV)]
```

### Queue Processing
```mermaid
graph LR
    A[Producer] --> B[Queue]
    B --> C[Consumer]
    C --> D[(Storage)]
    C -.->|failed| E[DLQ]
```

### Service Bindings
```mermaid
graph LR
    A[Gateway Worker] -->|RPC| B[Auth Worker]
    A -->|RPC| C[Data Worker]
    B --> D[(KV)]
    C --> E[(D1)]
```

### Multi-Region
```mermaid
graph TB
    subgraph "Region A"
        WA[Worker A]
        DA[(D1 Primary)]
    end
    subgraph "Region B"
        WB[Worker B]
        DB[(D1 Replica)]
    end
    WA --> DA
    WB --> DB
    DA -.->|sync| DB
```

## Output Format

When designing an architecture, provide:

1. **Requirements Summary** - Confirmed requirements
2. **Architecture Diagram** - Mermaid visualization
3. **Service Justification** - Why each service was chosen
4. **Wrangler Configuration** - Complete, deployable config
5. **Cost Estimate** - Monthly projection with breakdown
6. **Migration Path** - If replacing existing system
7. **Next Steps** - Implementation order

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| HTTP between Workers | 1000 subrequest limit | Service Bindings RPC |
| D1 as queue | Expensive, no guarantees | Use Queues |
| KV for large files | 25MB limit, expensive | Use R2 |
| Polling for events | Wasteful, slow | Queues or WebSocket |
| Per-request AI calls | Expensive, slow | Cache with KV |
| No DLQ | Lost messages | Always add DLQ |

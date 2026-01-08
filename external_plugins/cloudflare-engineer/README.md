# Cloudflare Engineer Plugin

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/littlebearapps/cloudflare-engineer/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.0.12+-purple.svg)](https://claude.com/claude-code)

A Claude Code plugin that provides **Senior Cloudflare Systems Engineer** capabilities for designing, implementing, optimizing, and securing Cloudflare Workers applications.

## Quick Install

```bash
# From GitHub (recommended)
/plugin marketplace add littlebearapps/cloudflare-engineer
/plugin install cloudflare-engineer@littlebearapps

# Or install directly
/plugin install github:littlebearapps/cloudflare-engineer
```

> [!TIP]
> This plugin works fully without any additional setup. For enhanced capabilities like live validation and real-time cost analysis, configure the optional [Cloudflare MCP servers](#mcp-tool-integration).

## Features at a Glance

| Category | What You Get |
|----------|--------------|
| **7 Skills** | Cost optimization, security auditing, architecture design, implementation patterns |
| **4 Commands** | `/cf-costs`, `/cf-audit`, `/cf-design`, `/cf-pattern` |
| **3 Agents** | Deep analysis with MCP tool integration |
| **1 Hook** | Pre-deploy validation catches issues before they hit production |

## Supported Cloudflare Services

- Workers (standard & Durable Objects)
- D1 (SQLite database)
- R2 (object storage)
- KV (key-value store)
- Queues (with DLQ support)
- Vectorize (vector database)
- AI Gateway (LLM routing)
- Workflows (durable execution)
- Hyperdrive (connection pooling)
- Analytics Engine

## What's New in v1.1.0

### Live Validation Mode (`--validate`)

Commands now support **live validation** against Cloudflare MCP tools:

```bash
/cf-costs --validate    # Compare estimates with live observability data
/cf-audit --validate    # Verify findings against production metrics
```

### Provenance Tagging

All findings are tagged with their data source:

| Tag | Meaning |
|-----|---------|
| `[STATIC]` | Inferred from code/config analysis |
| `[LIVE-VALIDATED]` | Confirmed by observability data |
| `[LIVE-REFUTED]` | Code smell not observed in production |
| `[INCOMPLETE]` | MCP tools unavailable for verification |

### Architecture Pattern Catalog

Apply battle-tested patterns with code examples:

| Pattern | Problem | Solution |
|---------|---------|----------|
| `service-bindings` | Monolithic Worker hitting subrequest limits | Decompose with RPC |
| `d1-batching` | High D1 write costs | Batch INSERT operations |
| `circuit-breaker` | External API cascading failures | Fail-fast with fallback |

```bash
/cf-pattern service-bindings
/cf-pattern d1-batching --analyze-only
```

## Commands

| Command | Purpose |
|---------|---------|
| `/cf-costs [--validate]` | Cost report with monthly projections |
| `/cf-audit [--validate] [--category=<cat>]` | Security/performance/cost audit |
| `/cf-design` | Interactive architecture design wizard |
| `/cf-pattern <name> [--analyze-only]` | Apply architecture pattern |

## Skills (Auto-Invoked)

Skills activate automatically based on your questions:

```
"How much will this worker cost?"     -> optimize-costs
"Is my worker secure?"                -> guardian
"Design a queue-based pipeline"       -> architect
"Scaffold a Hono API with D1"         -> implement
"How do I scale to 1M requests/day?"  -> scale
```

## Pre-Deploy Validation Hook

Automatically validates `wrangler.toml` before deployment:

| Check | Severity | Description |
|-------|----------|-------------|
| SEC001 | CRITICAL | Plaintext secrets in config |
| SEC002 | HIGH | Missing vars encryption |
| RES001 | HIGH | Queues without dead letter queues |
| COST001 | MEDIUM | High retry counts |
| PERF001 | MEDIUM | Smart placement disabled |
| PERF004 | LOW | Observability not configured |

**CRITICAL issues block deployment.** Other severities are warnings.

## MCP Tool Integration

For `--validate` mode, configure these Cloudflare MCP servers:

| MCP Server | Used For |
|------------|----------|
| `cloudflare-observability` | Worker metrics, error rates, latency |
| `cloudflare-ai-gateway` | AI costs, cache hit rates |
| `cloudflare-bindings` | D1 queries, resource inventory |

### What Works Without MCP

| Feature | Without MCP | With MCP |
|---------|-------------|----------|
| `/cf-costs` | Static estimates from config | + Live usage validation |
| `/cf-audit` | Config & code analysis | + Production metrics |
| `/cf-design` | Full functionality | Same |
| `/cf-pattern` | Full functionality | Same |
| Pre-deploy hook | Full functionality | Same |
| All 7 skills | Full functionality | Same |
| All 3 agents | Static analysis | + Real-time data |

**Graceful Degradation**: Commands continue with static analysis if MCP tools are unavailable, tagging affected findings as `[INCOMPLETE]`.

## Usage Examples

```bash
# Cost analysis
/cf-costs                              # Static cost estimate
/cf-costs --validate                   # With live data validation

# Security audit
/cf-audit                              # Full audit
/cf-audit --validate --category=security

# Architecture design
/cf-design                             # Interactive wizard

# Apply patterns
/cf-pattern circuit-breaker            # Apply pattern
/cf-pattern service-bindings --analyze-only  # Analysis only
```

## Requirements

- Claude Code v2.0.12+
- Python 3.8+ (for pre-deploy hook)
- Cloudflare account with Workers enabled
- (Optional) Cloudflare MCP servers for `--validate` mode

## Directory Structure

```
cloudflare-engineer/
├── .claude-plugin/plugin.json    # Plugin manifest
├── skills/                       # 7 auto-invoked skills
├── agents/                       # 3 deep-analysis agents
├── commands/                     # 4 slash commands
├── hooks/                        # Pre-deploy validation
├── LICENSE                       # MIT
├── CONTRIBUTING.md               # Contribution guide
├── SECURITY.md                   # Security policy
└── CHANGELOG.md                  # Version history
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

---

Made with care by [Little Bear Apps](https://littlebearapps.com)

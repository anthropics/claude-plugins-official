---
name: docker-development
description: >
  This skill should be used when the user asks to "analyze a Dockerfile",
  "optimize Docker layers", "validate docker-compose", "check container
  best practices", or "audit Docker configurations".
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: containers
  updated: 2026-04-02
  tags: [docker, containers, devops, compose, dockerfile]
---
# Docker Development

> **Category:** Engineering
> **Domain:** Container Development & Optimization

## Overview

The **Docker Development** skill provides automated analysis of Dockerfiles and docker-compose configurations. It identifies layer optimization opportunities, security issues, best practice violations, and compose service misconfigurations. Use this skill to enforce container standards across your team and catch issues before they reach production.

## Quick Start

```bash
# Analyze a Dockerfile for best practices
python scripts/dockerfile_analyzer.py --file Dockerfile

# Analyze with JSON output
python scripts/dockerfile_analyzer.py --file Dockerfile --format json

# Validate a docker-compose file
python scripts/compose_validator.py --file docker-compose.yml

# Check for port conflicts across compose files
python scripts/compose_validator.py --file docker-compose.yml --check-ports
```

## Tools Overview

### dockerfile_analyzer.py

Analyzes Dockerfiles for best practices, security issues, and optimization opportunities.

| Feature | Description |
|---------|-------------|
| Layer optimization | Detects unnecessary layers, recommends combining RUN statements |
| Multi-stage analysis | Validates multi-stage build patterns and final image size |
| Security scanning | Flags running as root, use of latest tags, exposed secrets |
| Base image checks | Recommends smaller base images (alpine, distroless, slim) |
| Cache optimization | Identifies poor layer ordering that breaks Docker cache |

```bash
# Full analysis
python scripts/dockerfile_analyzer.py --file Dockerfile

# Security-focused scan
python scripts/dockerfile_analyzer.py --file Dockerfile --security-only

# JSON output for CI integration
python scripts/dockerfile_analyzer.py --file Dockerfile --format json
```

### compose_validator.py

Validates docker-compose files for correctness, dependency issues, and port conflicts.

| Feature | Description |
|---------|-------------|
| Schema validation | Checks compose file structure and syntax |
| Dependency graph | Validates depends_on chains for circular dependencies |
| Port conflict detection | Identifies duplicate host port bindings |
| Volume mount checks | Validates volume paths and mount configurations |
| Network analysis | Checks network definitions and service connectivity |

```bash
# Full validation
python scripts/compose_validator.py --file docker-compose.yml

# Check port conflicts only
python scripts/compose_validator.py --file docker-compose.yml --check-ports

# JSON output
python scripts/compose_validator.py --file docker-compose.yml --format json
```

## Workflows

### Dockerfile Review Workflow

1. **Analyze** - Run dockerfile_analyzer.py against the target Dockerfile
2. **Review findings** - Address critical security issues first (root user, secrets)
3. **Optimize layers** - Combine RUN statements, reorder for cache efficiency
4. **Validate base images** - Switch to minimal base images where possible
5. **Re-analyze** - Confirm improvements and verify no regressions

### Compose Validation Workflow

1. **Validate structure** - Run compose_validator.py for syntax and schema checks
2. **Check dependencies** - Review service dependency graph for circular refs
3. **Audit ports** - Ensure no host port conflicts across services
4. **Review volumes** - Confirm volume mounts are correct and necessary
5. **Network review** - Verify service isolation and connectivity

### CI Integration Workflow

```yaml
# Example GitHub Actions step
- name: Docker Lint
  run: |
    python scripts/dockerfile_analyzer.py --file Dockerfile --format json > results.json
    python scripts/compose_validator.py --file docker-compose.yml --format json >> results.json
```

## Reference Documentation

- [Docker Best Practices](references/docker-best-practices.md) - Comprehensive guide to Dockerfile and Compose patterns

## Common Patterns Quick Reference

| Pattern | Good | Bad |
|---------|------|-----|
| Base image | `FROM python:3.12-slim` | `FROM python:latest` |
| User | `USER appuser` | Running as root |
| Layer combining | `RUN apt-get update && apt-get install -y pkg` | Separate RUN for update and install |
| COPY ordering | Copy requirements first, then code | Copy everything at once |
| Multi-stage | Use builder stage + minimal runtime | Single stage with build tools |
| Secrets | Use build secrets or env at runtime | `COPY .env .` or `ENV SECRET=value` |
| Health checks | `HEALTHCHECK CMD curl -f http://localhost/` | No health check defined |
| .dockerignore | Include node_modules, .git, etc. | No .dockerignore file |

### Compose Patterns

| Pattern | Good | Bad |
|---------|------|-----|
| Restart policy | `restart: unless-stopped` | No restart policy |
| Resource limits | `deploy.resources.limits` set | Unlimited resources |
| Named volumes | `volumes: [db-data:/var/lib/postgresql]` | Anonymous volumes |
| Networks | Explicit network definitions | Default bridge only |
| Environment | `env_file: .env` | Inline secrets in compose |

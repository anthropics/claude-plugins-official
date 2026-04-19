# Docker Best Practices Reference

## Base Image Selection

### Image Size Hierarchy (smallest to largest)
1. **scratch** - Empty image, for statically compiled binaries
2. **distroless** - Google's minimal images, no shell
3. **alpine** - ~5MB, musl libc, good for most use cases
4. **slim** - Debian-based, ~80MB, glibc compatible
5. **full** - Complete OS, 200MB+, use only when necessary

### Version Pinning
- Always pin major.minor: `python:3.12-slim`
- For reproducibility, pin digest: `python:3.12-slim@sha256:abc...`
- Never use `latest` in production Dockerfiles

## Multi-Stage Build Patterns

### Builder Pattern
```dockerfile
FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server

FROM gcr.io/distroless/static
COPY --from=builder /app/server /server
CMD ["/server"]
```

### Testing Pattern
```dockerfile
FROM node:20-slim AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS test
COPY . .
RUN npm test

FROM base AS production
COPY . .
RUN npm prune --production
USER node
CMD ["node", "server.js"]
```

## Layer Optimization

### Combine RUN Instructions
```dockerfile
# Good: single layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Bad: multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y ca-certificates
```

### Order for Cache Efficiency
1. System dependencies (rarely change)
2. Language runtime setup
3. Dependency files (package.json, requirements.txt)
4. Dependency install
5. Application code (changes most often)
6. Build step

## Security Hardening

### Non-Root User
```dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

### Read-Only Filesystem
```yaml
# docker-compose.yml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

### Secrets Management
- Use Docker BuildKit secrets: `RUN --mount=type=secret,id=key`
- Use runtime environment variables for application secrets
- Never COPY .env files or embed secrets in images

## Compose Best Practices

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Networking
- Use custom networks for service isolation
- Avoid `network_mode: host` in production
- Use internal networks for backend services

## .dockerignore Essentials

```
.git
.gitignore
node_modules
__pycache__
*.pyc
.env*
.vscode
.idea
*.md
Dockerfile*
docker-compose*
.dockerignore
```

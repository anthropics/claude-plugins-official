---
name: mandu-deploy
description: "프로덕션 배포 파이프라인. Docker/CI-CD/nginx"
disable-model-invocation: true
---

# Mandu Deploy

프로덕션 배포 파이프라인 가이드.
Build -> Test -> Deploy 체크리스트와 Docker/CI-CD/nginx 설정을 다룹니다.

## Build -> Test -> Deploy Checklist

### 1. Pre-Deploy Checks

```bash
# Architecture validation
bunx mandu guard arch --ci

# TypeScript check
bunx tsc --noEmit

# Run tests
bun test

# Production build
bun run build
```

### 2. Dockerfile

```dockerfile
FROM oven/bun:1.2-alpine AS base
WORKDIR /app

# Install dependencies
FROM base AS deps
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile --production

# Build
FROM base AS build
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

# Production
FROM base AS production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/.mandu ./.mandu
COPY --from=build /app/app ./app
COPY --from=build /app/src ./src
COPY --from=build /app/spec ./spec
COPY --from=build /app/package.json ./

ENV NODE_ENV=production
ENV PORT=3333
EXPOSE 3333

CMD ["bun", "run", "start"]
```

### 3. docker-compose.yml

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "3333:3333"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3333/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      - run: bun install --frozen-lockfile
      - run: bunx mandu guard arch --ci
      - run: bun test
      - run: bun run build

      - name: Deploy
        run: |
          # docker build & push, or platform-specific deploy
          docker build -t myapp:${{ github.sha }} .
          docker push myapp:${{ github.sha }}
```

### 5. nginx Reverse Proxy

```nginx
upstream mandu_app {
    server 127.0.0.1:3333;
    keepalive 32;
}

server {
    listen 80;
    server_name example.com;

    # Static assets (long cache)
    location /.mandu/client/ {
        proxy_pass http://mandu_app;
        proxy_cache_valid 200 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    # API routes
    location /api/ {
        proxy_pass http://mandu_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # All other routes (SSR)
    location / {
        proxy_pass http://mandu_app;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Environment Variables

```bash
# .env.production
NODE_ENV=production
PORT=3333
DATABASE_URL=postgresql://user:pass@host:5432/db
```

IMPORTANT: `.env` 파일은 절대 git에 커밋하지 않기. `.gitignore`에 추가 확인.

## Production Optimizations

| Area | Action |
|------|--------|
| Build | `bun run build` (minification, tree-shaking) |
| CSS | Tailwind purge (자동) |
| Islands | `"visible"` or `"idle"` priority (not `"immediate"`) |
| Static | nginx에서 `.mandu/client/` 장기 캐시 |
| Health | `/api/health` endpoint 필수 |

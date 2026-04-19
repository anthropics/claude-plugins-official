---
name: senior-devops
description: >
  Use when building CI/CD pipelines, containerizing applications, managing
  Kubernetes clusters, provisioning cloud infrastructure with Terraform,
  implementing deployment strategies (blue-green, canary, rolling), setting up
  monitoring/observability, optimizing cloud costs, or handling infrastructure
  incident response.
license: MIT + Commons Clause
metadata:
  version: 2.1.0
  author: borghei
  category: engineering
  domain: infrastructure
  updated: 2026-04-02
  tags: [docker, kubernetes, terraform, ci-cd, monitoring]
  python-tools: pipeline_generator.py, terraform_scaffolder.py, deployment_manager.py
  tech-stack: python, docker, kubernetes, terraform, prometheus
---
# Senior DevOps Engineer

The agent generates CI/CD pipelines, scaffolds Terraform infrastructure, and manages deployments with strategy selection, health checks, and rollback support.

---

## Quick Start

```bash
# Generate CI/CD pipeline from project analysis
python scripts/pipeline_generator.py <project-path> --platform github-actions --verbose

# Scaffold Terraform infrastructure
python scripts/terraform_scaffolder.py <target-path> --provider aws --env production --verbose

# Manage deployment with canary strategy
python scripts/deployment_manager.py <target-path> --strategy canary --verbose
```

## Tools Overview

| Tool | Input | Output |
|------|-------|--------|
| `pipeline_generator.py` | Project path | CI/CD pipeline config (GitHub Actions, GitLab CI, Jenkins, CircleCI) |
| `terraform_scaffolder.py` | Target path + provider | Terraform module structure with state config |
| `deployment_manager.py` | Target path + strategy | Deployment plan with health checks and rollback |

All tools support `--json` for machine-readable output and `--output` / `-o` for file writing.

---

## Workflow 1: Containerize and Deploy

**Step 1 -- Build a production Dockerfile.**

The agent generates multi-stage Dockerfiles following this pattern:

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/healthz || exit 1
CMD ["node", "dist/server.js"]
```

**Validation checkpoint:** Image builds with `docker build -t app:test .` and `docker run --rm app:test` returns healthy.

**Step 2 -- Deploy to Kubernetes.**

The agent creates a Deployment with probes, resource limits, and security context:

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.2.3
      resources:
        requests: { cpu: 250m, memory: 256Mi }
        limits: { cpu: "1", memory: 512Mi }
      livenessProbe:
        httpGet: { path: /healthz, port: 3000 }
        initialDelaySeconds: 15
        periodSeconds: 20
      readinessProbe:
        httpGet: { path: /ready, port: 3000 }
        initialDelaySeconds: 5
        periodSeconds: 10
      startupProbe:
        httpGet: { path: /healthz, port: 3000 }
        failureThreshold: 30
        periodSeconds: 10
```

**Probe decision:**
- **startupProbe**: Slow-starting apps (JVM, model loading). Prevents liveness from killing during startup.
- **livenessProbe**: Detects deadlocks. Keep simple -- do not check downstream dependencies.
- **readinessProbe**: Controls traffic routing. Include dependency checks here.

**Validation checkpoint:** `kubectl get pods -l app=myapp` shows all pods Running and Ready.

---

## Workflow 2: Infrastructure as Code with Terraform

**Step 1 -- Scaffold the module structure.**

```bash
python scripts/terraform_scaffolder.py ./infrastructure --provider aws --env production --verbose
```

The agent produces:
```
infrastructure/
  modules/
    vpc/         # main.tf, variables.tf, outputs.tf
    eks/
    rds/
  environments/
    staging/     # main.tf, terraform.tfvars, backend.tf
    production/
```

**Step 2 -- Configure remote state.**

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "production/infrastructure.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

**Step 3 -- Run drift detection in CI.**

```bash
terraform plan -detailed-exitcode -out=plan.tfplan
# Exit 0 = clean, Exit 1 = error, Exit 2 = drift detected
```

**Validation checkpoint:** `terraform plan` shows no unexpected changes. Drift alerts fire within 24 hours.

**Key rules:**
- One state file per environment per component (blast radius control)
- Never store state locally or in git
- Run `terraform plan` in CI, `terraform apply` only after approval
- Use directories for environment separation, modules for shared logic

---

## Workflow 3: CI/CD Pipeline Design

```bash
python scripts/pipeline_generator.py /path/to/project --platform github-actions --json
```

The agent generates pipelines following these principles:

1. **Fail fast** -- lint and unit tests before expensive integration tests
2. **Cache aggressively** -- node_modules, Docker layers, pip packages
3. **Immutable artifacts** -- build once, deploy the same artifact everywhere
4. **Gate promotions** -- manual approval or smoke tests before production
5. **Parallel execution** -- independent test suites and security scans run concurrently

**Example: GitHub Actions with matrix testing and deployment gates**

```yaml
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "${{ matrix.node-version }}", cache: npm }
      - run: npm ci && npm run lint && npm test -- --coverage

  build:
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    environment: staging
    steps:
      - run: helm upgrade --install app charts/myapp --set image.tag=${{ github.sha }} --wait

  deploy-production:
    needs: deploy-staging
    environment: production  # requires manual approval
```

**Validation checkpoint:** Pipeline runs in under 15 minutes. All stages produce exit code 0.

---

## Deployment Strategy Selection

| Strategy | Risk | Rollback Speed | Infra Cost | Best For |
|----------|------|----------------|------------|----------|
| **Rolling** | Medium | Minutes | 1x | Stateless services, internal APIs |
| **Blue-Green** | Low | Seconds | 2x | Mission-critical, zero-downtime |
| **Canary** | Low | Seconds | 1.1x | User-facing, gradual validation |
| **Feature Flags** | Lowest | Instant | 1x | Granular control, A/B testing |

**Canary promotion ladder:**
1. Deploy at 5% traffic. Monitor error rate and latency for 10 min.
2. Promote to 25%. Monitor 10 min.
3. Promote to 50%. Monitor 15 min.
4. Promote to 100%.
5. Automated rollback if error rate exceeds baseline by 2x at any step.

---

## Monitoring Essentials

Every service dashboard includes the **Four Golden Signals**:

1. **Latency** -- P50, P90, P99 response times
2. **Traffic** -- Requests per second by endpoint and status code
3. **Errors** -- 5xx rate, 4xx rate, application error codes
4. **Saturation** -- CPU, memory, connection pool, queue depth

**SLO targets (example):**

| Service | SLI | SLO | Error Budget |
|---------|-----|-----|--------------|
| API Gateway | Successful requests / Total | 99.9% (43.8 min/month downtime) | 0.1% |
| API Latency | Requests < 500ms / Total | P99 < 500ms | 1% |

When the error budget is exhausted, the agent recommends freezing feature deployments until the budget recovers.

---

## Anti-Patterns

1. **Monolithic state** -- one Terraform state for everything. Split by component and environment.
2. **`latest` tag in production** -- always use specific image tags.
3. **Secrets in image layers** -- inject at runtime via environment or mounted secrets. Verify with `docker history --no-trunc`.
4. **No resource limits** -- every container needs CPU/memory limits to prevent noisy-neighbor attacks.
5. **Manual deployments** -- automate with approval gates instead.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Terraform state lock stuck | Interrupted `terraform apply` left DynamoDB lock | `terraform force-unlock <LOCK_ID>` after confirming no apply running |
| Pods in `CrashLoopBackOff` | Failing health checks or missing config/secrets | `kubectl logs <pod>`, verify ConfigMaps/Secrets, increase `startupProbe.failureThreshold` |
| Docker builds slow (10+ min) | Layer cache invalidated by early COPY of changing files | Copy dependency manifests before source; use BuildKit cache mounts |
| Helm upgrade fails "another operation in progress" | Previous release in pending/failed state | `helm history <release>`, then `helm rollback <release> <last-good>` |
| Canary shows healthy but users report errors | Metrics aggregated across all pods mask canary errors | Use per-revision metric labels; configure Istio/Nginx to tag canary traffic |

---

## References

| Guide | Path | Content |
|-------|------|---------|
| CI/CD Pipeline Guide | `references/cicd_pipeline_guide.md` | Pipeline patterns, platform comparisons, optimization |
| Infrastructure as Code | `references/infrastructure_as_code.md` | Terraform patterns, module design, state management |
| Deployment Strategies | `references/deployment_strategies.md` | Strategy details, rollback procedures, traffic management |

See also: `references/kubernetes_patterns.md` for Helm charts, HPA/VPA/KEDA decisions, network policies, and RBAC patterns. `references/cloud_platform_guide.md` for AWS/GCP/Azure service comparison, multi-cloud strategy, and cost optimization.

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `senior-secops` | Security scanning in CI/CD, container image scanning, compliance checks |
| `senior-architect` | Infrastructure design decisions, service topology |
| `senior-backend` | Application containerization, health endpoints, config management |
| `code-reviewer` | Terraform plan review, pipeline config review |
| `incident-commander` | Incident escalation, postmortem, rollback procedures |

---

**Last Updated:** April 2026
**Version:** 2.1.0

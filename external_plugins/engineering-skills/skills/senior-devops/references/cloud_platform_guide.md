# Cloud Platform Guide

## Service Comparison Matrix

| Capability | AWS | GCP | Azure |
|------------|-----|-----|-------|
| **Managed K8s** | EKS | GKE | AKS |
| **Serverless** | Lambda | Cloud Functions / Cloud Run | Azure Functions |
| **Containers** | ECS/Fargate | Cloud Run | Container Apps |
| **Object Storage** | S3 | Cloud Storage | Blob Storage |
| **Managed DB** | RDS / Aurora | Cloud SQL / AlloyDB | Azure SQL / Cosmos DB |
| **Message Queue** | SQS / SNS | Pub/Sub | Service Bus |
| **CDN** | CloudFront | Cloud CDN | Azure CDN / Front Door |
| **DNS** | Route 53 | Cloud DNS | Azure DNS |
| **Secrets** | Secrets Manager | Secret Manager | Key Vault |
| **IAM** | IAM + STS | IAM + Workload Identity | Entra ID + RBAC |

## Multi-Cloud Decision Framework

**When multi-cloud makes sense:**
- Regulatory requirements mandate vendor diversity
- Acquisition brings workloads on a different cloud
- Best-of-breed services (GCP for ML, AWS for breadth)

**When it does not:**
- Avoiding lock-in as the sole motivation (operational tax exceeds savings)
- Small teams that cannot afford complexity overhead

**If you go multi-cloud:**
- Use Terraform for the abstraction layer
- Standardize on Kubernetes as compute plane
- Centralize observability (Datadog, Grafana Cloud)
- Invest in a platform engineering team

## Cost Optimization

### Right-Sizing Methodology

1. Collect 2-4 weeks of CPU/memory utilization
2. Identify instances below 40% average CPU
3. Recommend one size down
4. Validate in staging under load test
5. Apply in production during maintenance window
6. Monitor for 1 week post-change

### Spot/Preemptible Strategy

| Workload | Spot? | Pattern |
|----------|-------|---------|
| Stateless web (behind LB) | Yes | 70% spot + 30% on-demand |
| CI/CD runners | Yes | 100% spot with retry |
| Batch / ETL | Yes | Spot fleet with checkpointing |
| Databases / stateful | No | Reserved instances |
| Dev/test environments | Yes | 100% spot |

### FinOps Practices

- **Tagging**: Enforce `team`, `environment`, `service`, `cost-center` on all resources
- **Budget alerts**: 50%, 80%, 100% of monthly budget
- **Reserved capacity**: 1-year for baseline workloads (30-40% savings)
- **Scheduled scaling**: Scale down non-prod outside business hours
- **Storage lifecycle**: S3 lifecycle policies for Glacier/Archive tiers
- **Unused resources**: Weekly scan for unattached EBS, idle LBs, stale snapshots

## Prometheus Alerting Rules

```yaml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Error rate exceeds 5% for 5 minutes"

      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2.0
        for: 10m
        labels: { severity: warning }

      - alert: PodCrashLooping
        expr: increase(kube_pod_container_status_restarts_total[1h]) > 5
        for: 5m
        labels: { severity: critical }

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
        for: 10m
        labels: { severity: warning }
```

## Incident Response Quick Reference

### Severity Classification

| Severity | Definition | Response Time |
|----------|-----------|---------------|
| SEV-1 | Complete outage, data loss risk | 15 min |
| SEV-2 | Significant degradation | 30 min |
| SEV-3 | Minor degradation, workaround available | 4 hours |
| SEV-4 | Cosmetic / informational | Next business day |

### Runbook Template

```markdown
## Symptoms
- What alerts fire, what users report

## Diagnosis
1. kubectl get pods -n production -l app=myapp
2. helm history myapp -n production
3. kubectl logs -l app=myapp --tail=100

## Quick Fix (< 5 min)
- kubectl rollout restart deployment/myapp
- kubectl scale deployment/myapp --replicas=10

## Rollback (< 10 min)
- helm rollback myapp [previous-revision]
```

### Postmortem (required for SEV-1/SEV-2)
1. Timeline reconstruction
2. Root cause (5 Whys)
3. Impact assessment
4. What went well / poorly
5. Action items with owners and due dates

# Kubernetes Patterns Reference

## Pod Design Patterns

### Sidecar Pattern

Add capabilities without modifying the main container:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      serviceAccountName: app-sa
      securityContext:
        runAsNonRoot: true
        fsGroup: 1001
      containers:
        - name: app
          image: myapp:1.2.3
          ports:
            - containerPort: 3000
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits: { cpu: "1", memory: 512Mi }
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: db-password
        - name: log-shipper
          image: fluent/fluent-bit:2.2
          volumeMounts:
            - name: app-logs
              mountPath: /var/log/app
      volumes:
        - name: app-logs
          emptyDir: {}
```

## Helm Chart Structure

```
charts/myapp/
  Chart.yaml
  values.yaml
  values-staging.yaml
  values-production.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    hpa.yaml
    networkpolicy.yaml
    serviceaccount.yaml
    _helpers.tpl
```

Key `values.yaml` patterns:

```yaml
replicaCount: 3
image:
  repository: myapp
  tag: "1.2.3"
  pullPolicy: IfNotPresent

resources:
  requests: { cpu: 250m, memory: 256Mi }
  limits: { cpu: "1", memory: 512Mi }

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: app-tls
      hosts:
        - app.example.com
```

## HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 25
          periodSeconds: 120
```

## HPA vs VPA vs KEDA

| Scaler | Use When | Avoid When |
|--------|----------|------------|
| **HPA** | Stateless services, predictable CPU/memory | Stateful workloads, bursty event-driven |
| **VPA** | Right-sizing requests/limits, batch jobs | Alone for latency-sensitive services |
| **KEDA** | Event-driven (queue depth, HTTP rate, cron) | Simple CPU-based scaling (HPA is simpler) |

## Network Policies

Default-deny with explicit allow:

```yaml
# Default deny all
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

---
# Allow app traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 3000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

## RBAC Best Practices

- Least privilege: grant minimum permissions needed
- Use ClusterRoles for cluster-wide, Roles for namespace-scoped
- Bind service accounts to roles, not users
- Audit: `kubectl auth can-i --list --as=system:serviceaccount:production:app-sa`
- Never grant `cluster-admin` to application service accounts

## Container Security Checklist

- [ ] Base images from trusted registries (Docker Official, Chainguard, Distroless)
- [ ] Scanned with Trivy/Grype: `trivy image --severity HIGH,CRITICAL myapp:latest`
- [ ] No root processes -- `USER` directive required
- [ ] Read-only root filesystem: `--read-only --tmpfs /tmp`
- [ ] Resource limits enforced (CPU, memory)
- [ ] No secrets in image layers -- verify with `docker history --no-trunc`
- [ ] Minimal base images (Alpine, Distroless)

## Secret Management Decision Matrix

| Tool | Best For | Avoid When |
|------|----------|------------|
| **HashiCorp Vault** | Dynamic secrets, PKI, multi-cloud | Small teams, simple apps |
| **AWS Secrets Manager** | AWS-native, automatic rotation | Multi-cloud |
| **K8s Secrets** | Pod-level injection (with encryption at rest) | Long-term storage, cross-cluster |
| **SOPS / age** | Encrypted secrets in git (gitops) | Teams unfamiliar with key management |

## Supply Chain Security

```bash
# Sign container images
cosign sign --key cosign.key ghcr.io/myorg/myapp:1.2.3
cosign verify --key cosign.pub ghcr.io/myorg/myapp:1.2.3

# Generate and scan SBOM
syft ghcr.io/myorg/myapp:1.2.3 -o spdx-json > sbom.json
grype sbom:sbom.json --fail-on high
```

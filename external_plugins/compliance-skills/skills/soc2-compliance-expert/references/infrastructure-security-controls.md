# Infrastructure Security Controls Reference

Comprehensive reference for infrastructure security configurations required for SOC 2 compliance, covering cloud providers, DNS, TLS, endpoints, network, containers, CI/CD, hardware security keys, and secrets management.

---

## Cloud Security Configurations

### AWS Security Controls

#### IAM and Access Management

| Service | Configuration | SOC 2 Mapping | Priority |
|---------|---------------|---------------|----------|
| **AWS IAM** | Enable IAM Access Analyzer for unused permissions | CC6.1 | High |
| **AWS IAM** | Enforce MFA for all IAM users (hardware MFA for root) | CC6.1 | Critical |
| **AWS IAM** | Enable credential report and audit unused credentials | CC6.3 | High |
| **AWS Organizations** | Use SCPs to enforce guardrails across accounts | CC5.2 | High |
| **AWS IAM Identity Center** | Configure SSO with corporate IdP (SAML 2.0) | CC6.1 | High |
| **AWS IAM** | Enforce password policy: 14 chars, complexity, 90-day rotation | CC6.1 | High |

**Key AWS IAM Policies:**
```json
{
  "MinimumPasswordLength": 14,
  "RequireSymbols": true,
  "RequireNumbers": true,
  "RequireUppercaseCharacters": true,
  "RequireLowercaseCharacters": true,
  "MaxPasswordAge": 90,
  "PasswordReusePrevention": 12,
  "AllowUsersToChangePassword": true
}
```

#### Encryption

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **AWS KMS** | Create CMKs for each workload, enable automatic key rotation | CC6.1, C1.1 |
| **S3** | Enable default encryption (SSE-KMS), block public access | CC6.1, C1.1 |
| **RDS** | Enable encryption at rest, enforce SSL connections | CC6.1, C1.1, CC6.7 |
| **EBS** | Enable default EBS encryption in all regions | CC6.1, C1.1 |
| **DynamoDB** | Enable encryption at rest with CMK | CC6.1, C1.1 |
| **ElastiCache** | Enable encryption at rest and in transit | CC6.1, C1.1, CC6.7 |

#### Logging and Monitoring

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **CloudTrail** | Enable in all regions, log to centralized S3 bucket | CC7.2, CC4.1 |
| **CloudTrail** | Enable log file integrity validation | CC7.2 |
| **CloudWatch** | Configure alarms for security-relevant metrics | CC7.2 |
| **VPC Flow Logs** | Enable for all VPCs, log to CloudWatch or S3 | CC7.2, CC6.6 |
| **AWS Config** | Enable in all regions, deploy conformance packs | CC4.1, CC5.2 |
| **GuardDuty** | Enable in all regions for threat detection | CC7.2 |
| **Security Hub** | Enable with CIS and AWS Foundational benchmarks | CC4.1 |
| **Access Analyzer** | Enable for all accounts to detect external access | CC6.1, CC4.1 |

#### Network Security

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Security Groups** | Deny-by-default, restrict SSH/RDP to bastion/VPN only | CC6.6 |
| **NACLs** | Restrict egress to known destinations | CC6.6 |
| **AWS WAF** | Deploy on ALB/CloudFront, enable managed rule groups | CC6.6 |
| **AWS Shield** | Enable Shield Advanced for DDoS protection | A1.1 |
| **VPC** | Separate VPCs for production, staging, development | CC6.6 |
| **PrivateLink** | Use for inter-service communication within AWS | CC6.6, CC6.7 |

### Azure Security Controls

#### Identity and Access

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Azure AD** | Enable Conditional Access policies | CC6.1 |
| **Azure AD** | Enforce MFA for all users via security defaults or CA | CC6.1 |
| **PIM** | Enable Privileged Identity Management for JIT access | CC6.1, CC6.2 |
| **Managed Identities** | Use for all Azure service authentication | CC6.1 |
| **RBAC** | Use custom roles with least privilege | CC6.2 |

#### Encryption and Key Management

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Azure Key Vault** | Centralize key management, enable soft delete and purge protection | CC6.1, C1.1 |
| **Storage Encryption** | Enable with customer-managed keys (CMK) | C1.1 |
| **Transparent Data Encryption** | Enable for all SQL databases | C1.1 |
| **Disk Encryption** | Enable Azure Disk Encryption for all VMs | C1.1 |

#### Monitoring

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Azure Monitor** | Configure diagnostic settings for all resources | CC7.2, CC4.1 |
| **Log Analytics** | Centralize logs with 90-day minimum retention | CC7.2 |
| **Microsoft Sentinel** | Deploy SIEM with built-in detection rules | CC7.2 |
| **Defender for Cloud** | Enable for all subscriptions, enforce secure score | CC4.1, CC7.1 |
| **NSG Flow Logs** | Enable for all NSGs | CC7.2, CC6.6 |

### GCP Security Controls

#### Identity and Access

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Cloud IAM** | Enforce least privilege, use custom roles | CC6.1, CC6.2 |
| **Identity Platform** | Configure SSO with corporate IdP | CC6.1 |
| **BeyondCorp Enterprise** | Deploy Zero Trust access (context-aware) | CC6.6 |
| **Workload Identity** | Use for GKE pod authentication (no service account keys) | CC6.1 |
| **Organization Policies** | Enforce constraints across organization | CC5.2 |

#### Encryption

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Cloud KMS** | Create key rings per environment, enable automatic rotation | CC6.1, C1.1 |
| **Cloud HSM** | Use for highest-sensitivity keys (FIPS 140-2 Level 3) | CC6.1, C1.1 |
| **CMEK** | Enable customer-managed encryption keys for all services | C1.1 |
| **Cloud SQL** | Enable SSL enforcement, encryption at rest with CMEK | CC6.7, C1.1 |

#### Monitoring

| Service | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| **Cloud Audit Logs** | Enable Admin Activity and Data Access logs | CC7.2, CC4.1 |
| **Cloud Logging** | Configure sinks to centralized storage | CC7.2 |
| **Security Command Center** | Enable Premium tier for vulnerability/threat detection | CC4.1, CC7.1, CC7.2 |
| **VPC Flow Logs** | Enable on all subnets with 1.0 sampling rate | CC7.2, CC6.6 |
| **Policy Intelligence** | Use recommender for IAM policy optimization | CC6.1 |

---

## DNS Security

### SPF (Sender Policy Framework)

**Purpose:** Specifies which mail servers are authorized to send email for your domain.

**Required Configuration:**
```
v=spf1 include:_spf.google.com include:amazonses.com -all
```

**Best Practices:**
- Use `-all` (hard fail) instead of `~all` (soft fail) in production
- Keep DNS lookups under 10 (SPF lookup limit)
- Include all legitimate sending services
- Monitor SPF validation failures via DMARC aggregate reports
- Review quarterly for accuracy

**SOC 2 Mapping:** CC6.6, CC2.2

### DKIM (DomainKeys Identified Mail)

**Purpose:** Adds a digital signature to outgoing emails for authenticity verification.

**Required Configuration:**
```
selector._domainkey.example.com IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkq..."
```

**Best Practices:**
- Minimum 2048-bit RSA key (1024-bit is considered weak)
- Rotate DKIM keys annually
- Configure DKIM for all email sending services
- Test with `dig selector._domainkey.example.com TXT`
- Consider Ed25519 keys for modern implementations

**SOC 2 Mapping:** CC6.6, CC2.2

### DMARC (Domain-based Message Authentication, Reporting, and Conformance)

**Purpose:** Instructs receiving servers how to handle emails that fail SPF/DKIM checks.

**Required Configuration (production):**
```
_dmarc.example.com IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc-agg@example.com; ruf=mailto:dmarc-forensic@example.com; pct=100; adkim=s; aspf=s"
```

**Deployment Path:**
1. `p=none` - Monitor only (collect data for 30-60 days)
2. `p=quarantine; pct=10` - Gradually increase percentage
3. `p=reject` - Full enforcement (target state for SOC 2)

**Best Practices:**
- Start with `p=none` to identify legitimate email sources
- Analyze aggregate reports before increasing enforcement
- Use strict alignment (`adkim=s; aspf=s`) for maximum protection
- Monitor forensic reports for attack attempts

**SOC 2 Mapping:** CC6.6, CC2.2

### DNSSEC

**Purpose:** Cryptographically signs DNS records to prevent DNS spoofing.

**Required Configuration:**
- Enable DNSSEC signing at DNS provider
- Publish DS records at domain registrar
- Verify with: `dig +dnssec example.com`

**Best Practices:**
- Enable for all production domains
- Verify DS record propagation after enabling
- Test DNSSEC validation with online tools
- Monitor for DNSSEC validation failures

**SOC 2 Mapping:** CC6.6

### CAA (Certificate Authority Authorization)

**Purpose:** Restricts which Certificate Authorities can issue certificates for your domain.

**Required Configuration:**
```
example.com. IN CAA 0 issue "letsencrypt.org"
example.com. IN CAA 0 issue "amazon.com"
example.com. IN CAA 0 issuewild "letsencrypt.org"
example.com. IN CAA 0 iodef "mailto:security@example.com"
```

**Best Practices:**
- List only CAs you actually use
- Use `issuewild` to control wildcard certificate issuance
- Configure `iodef` for violation notifications
- Review after any CA changes

**SOC 2 Mapping:** CC6.6

### MTA-STS (Mail Transfer Agent Strict Transport Security)

**Purpose:** Enforces TLS encryption for inbound SMTP connections.

**Required Configuration:**
```
_mta-sts.example.com IN TXT "v=STSv1; id=20260101"
```

Policy file at `https://mta-sts.example.com/.well-known/mta-sts.txt`:
```
version: STSv1
mode: enforce
mx: mx1.example.com
mx: mx2.example.com
max_age: 604800
```

---

## TLS/SSL Best Practices

### Minimum Protocol Version

| Version | Status | Recommendation |
|---------|--------|---------------|
| SSL 2.0 | Broken | Disable immediately |
| SSL 3.0 | Broken (POODLE) | Disable immediately |
| TLS 1.0 | Deprecated (2020) | Disable |
| TLS 1.1 | Deprecated (2020) | Disable |
| **TLS 1.2** | **Active** | **Minimum acceptable** |
| **TLS 1.3** | **Active** | **Preferred** |

### Recommended Cipher Suites

**TLS 1.3 (all are AEAD, all are acceptable):**
- TLS_AES_256_GCM_SHA384
- TLS_AES_128_GCM_SHA256
- TLS_CHACHA20_POLY1305_SHA256

**TLS 1.2 (recommended AEAD only):**
- ECDHE-ECDSA-AES256-GCM-SHA384
- ECDHE-RSA-AES256-GCM-SHA384
- ECDHE-ECDSA-AES128-GCM-SHA256
- ECDHE-RSA-AES128-GCM-SHA256
- ECDHE-ECDSA-CHACHA20-POLY1305
- ECDHE-RSA-CHACHA20-POLY1305

**Cipher suites to disable:**
- All RC4 ciphers (broken)
- All DES/3DES ciphers (weak)
- All CBC mode ciphers (vulnerable to padding oracle)
- All export-grade ciphers
- All NULL ciphers
- All anonymous (ADH/AECDH) ciphers

### HSTS Configuration

**Recommended Header:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

| Directive | Value | Purpose |
|-----------|-------|---------|
| `max-age` | 31536000 (1 year) | Duration browsers enforce HTTPS |
| `includeSubDomains` | Present | Apply to all subdomains |
| `preload` | Present | Submit to browser preload list |

**Deployment Path:**
1. Set `max-age=300` (5 min) to test
2. Increase to `max-age=86400` (1 day)
3. Increase to `max-age=31536000` (1 year)
4. Add `includeSubDomains`
5. Add `preload` and submit to hstspreload.org

### Certificate Management

| Aspect | Requirement | Best Practice |
|--------|-------------|---------------|
| **Signature** | SHA-256 minimum | SHA-384 for high-security |
| **Key size** | 2048-bit RSA or P-256 ECDSA | P-384 ECDSA preferred |
| **Validity** | 1 year maximum | 90 days (Let's Encrypt) |
| **Renewal** | Automated | ACME protocol (certbot, Caddy) |
| **Monitoring** | Certificate transparency logs | Deploy CT monitoring |
| **Revocation** | OCSP stapling enabled | CRL distribution points |
| **Inventory** | Complete certificate inventory | Automated discovery |

### Additional TLS Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Content-Security-Policy: default-src 'self'; script-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## Endpoint Security

### MDM Platforms

| Platform | OS Support | Key Features |
|----------|-----------|-------------|
| **Jamf Pro** | macOS, iOS | FileVault management, software deployment, conditional access |
| **Microsoft Intune** | Windows, macOS, iOS, Android | Conditional access, BitLocker, compliance policies |
| **Kandji** | macOS, iOS | Blueprint-based management, auto-remediation |
| **Mosyle** | macOS, iOS | Zero-touch deployment, security compliance |
| **VMware Workspace ONE** | All platforms | Unified endpoint management |

### Disk Encryption Requirements

| OS | Technology | Configuration |
|----|-----------|---------------|
| **macOS** | FileVault 2 | Enable via MDM, escrow recovery key to MDM |
| **Windows** | BitLocker | Enable via Intune/GPO, escrow key to Azure AD |
| **Linux** | LUKS/dm-crypt | Configure at OS install, manage keys centrally |
| **iOS/Android** | Native encryption | Enforce via MDM policy (enabled by default on modern devices) |

**SOC 2 Requirement:** 100% of company-managed devices must have disk encryption enabled. Verify via MDM compliance reports.

### EDR Solutions

| Solution | Capabilities | Deployment |
|----------|-------------|-----------|
| **CrowdStrike Falcon** | EDR, XDR, threat intelligence, vulnerability management | Agent-based |
| **SentinelOne Singularity** | EDR, XDR, automated response | Agent-based |
| **Microsoft Defender for Endpoint** | EDR, threat analytics, auto-investigation | Agent + cloud |
| **Carbon Black (VMware)** | EDR, NGAV, audit/remediation | Agent-based |

**Minimum Requirements:**
- Real-time malware detection and prevention
- Behavioral analysis for zero-day threats
- Automated response capabilities (isolate, kill process)
- Central management console with alerting
- 100% endpoint coverage

### Patch Management SLAs

| Severity | SLA | Verification |
|----------|-----|-------------|
| **Critical (CVSS 9.0+)** | 14 days | MDM compliance report |
| **High (CVSS 7.0-8.9)** | 30 days | MDM compliance report |
| **Medium (CVSS 4.0-6.9)** | 60 days | MDM compliance report |
| **Low (CVSS 0.1-3.9)** | 90 days | MDM compliance report |

**Patch Management Process:**
1. Vulnerability advisory intake (vendor notifications, NVD)
2. Severity assessment and SLA assignment
3. Testing in pilot group (24-48 hours)
4. Phased rollout (pilot > general > production)
5. Compliance verification and exception management

---

## Network Security

### Network Segmentation

**Required Separation:**

| Zone | Purpose | Access |
|------|---------|--------|
| **Production** | Customer-facing services and data | Restricted to operations team |
| **Staging** | Pre-production testing | Development and QA team |
| **Development** | Engineering environments | Development team |
| **Management** | Admin tools, CI/CD, monitoring | Platform/SRE team |
| **DMZ** | Public-facing load balancers, WAF | Internet-accessible (restricted) |

**Implementation:**
- Separate VPCs/VNets per environment (preferred) or separate subnets with strict NSG/SG rules
- No direct connectivity between production and development
- All inter-zone traffic through firewall with logging
- Production data never copied to non-production (use synthetic data)

### WAF Configuration

| Rule Category | Examples | Action |
|--------------|---------|--------|
| **OWASP Top 10** | SQL injection, XSS, SSRF | Block |
| **Rate limiting** | >100 requests/second per IP | Block |
| **Bot protection** | Known bad bots, credential stuffing | Block |
| **Geo-blocking** | High-risk countries (if applicable) | Block/Challenge |
| **IP reputation** | Known malicious IPs | Block |
| **Custom rules** | Application-specific protections | Block/Log |

### DDoS Protection

| Layer | Protection | Service |
|-------|-----------|---------|
| **L3/L4** | Volumetric attacks | AWS Shield, Azure DDoS, Cloud Armor |
| **L7** | Application-layer attacks | WAF rate limiting, Cloudflare |
| **DNS** | DNS amplification | Route 53 Shield, Cloudflare DNS |

### VPN and Zero Trust

| Approach | Use Case | Implementation |
|----------|---------|---------------|
| **Site-to-site VPN** | Office to cloud connectivity | AWS VPN, Azure VPN, Cloud VPN |
| **Client VPN** | Remote employee access | WireGuard, Tailscale, Cloudflare WARP |
| **ZTNA** | Application-level access | Cloudflare Access, Zscaler, BeyondCorp |

**Zero Trust Principles:**
- Never trust, always verify
- Least privilege access
- Microsegmentation
- Continuous authentication
- Device posture assessment
- Encrypted connections everywhere

---

## Container Security

### Image Scanning Tools

| Tool | Type | Integration |
|------|------|------------|
| **Trivy** | Open source | CI/CD, registry, runtime |
| **Grype** | Open source | CI/CD integration |
| **Snyk Container** | Commercial | CI/CD, IDE, registry |
| **Docker Scout** | Commercial | Docker Desktop, CI/CD |
| **Amazon ECR scanning** | Cloud-native | AWS ECR |
| **Azure Defender for Containers** | Cloud-native | Azure ACR |
| **GCP Artifact Analysis** | Cloud-native | GCP Artifact Registry |

### Container Best Practices

**Image Security:**
- Use minimal base images (distroless, Alpine, scratch)
- Pin image versions (never use `latest` tag)
- Scan images on every build in CI/CD
- Sign images with cosign/Notary
- Private registry with access controls
- Rebuild images regularly (weekly minimum) for base image updates

**Runtime Security:**
```yaml
# Kubernetes Pod Security Standards (Restricted)
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

**Kubernetes Security:**

| Control | Configuration | SOC 2 Mapping |
|---------|---------------|---------------|
| RBAC | Namespace-scoped roles, no cluster-admin for developers | CC6.1 |
| Network Policies | Deny-by-default, explicit allow rules | CC6.6 |
| Pod Security Standards | Enforce Restricted profile | CC6.1, CC6.8 |
| Secrets | External Secrets Operator, never in pod spec | CC6.1 |
| Admission Control | OPA/Gatekeeper or Kyverno for policy enforcement | CC5.2 |
| Service Mesh | Istio/Linkerd for mTLS between services | CC6.7 |
| Audit Logging | Enable Kubernetes audit logging | CC7.2 |
| Etcd Encryption | Enable encryption at rest for etcd | C1.1 |

### Container Registry Security

- Private registry (not public Docker Hub)
- Access control with RBAC
- Vulnerability scanning on push
- Image signing and verification
- Retention policies for old images
- Geo-replication for availability

---

## CI/CD Security

### Branch Protection Rules

**GitHub Configuration:**
```
Required status checks: [ci/build, ci/test, security/sast, security/dependency-check]
Required reviewers: 1 (2 for critical repos)
Dismiss stale reviews: true
Require review from code owners: true
Restrict who can push: [release-managers]
Force push: disabled
Deletion: disabled
Require signed commits: true (recommended)
Require linear history: true (recommended)
```

**GitLab Configuration:**
- Protected branches with merge request approvals
- Code owners approval required
- No force push allowed
- Pipeline must succeed before merge

### SAST Tools

| Tool | Languages | Integration |
|------|----------|------------|
| **Semgrep** | 30+ languages | CI/CD, IDE, pre-commit |
| **SonarQube** | 30+ languages | CI/CD, IDE |
| **CodeQL** | 10+ languages | GitHub native |
| **Checkmarx** | 25+ languages | CI/CD, IDE |
| **Snyk Code** | 10+ languages | CI/CD, IDE |

### DAST Tools

| Tool | Type | Use Case |
|------|------|----------|
| **OWASP ZAP** | Open source | CI/CD, manual testing |
| **Burp Suite** | Commercial | Manual penetration testing |
| **Nuclei** | Open source | Automated vulnerability scanning |
| **StackHawk** | Commercial | CI/CD integration |

### Dependency Scanning (SCA)

| Tool | Features | Integration |
|------|---------|------------|
| **Dependabot** | Auto-PRs for updates | GitHub native |
| **Snyk** | Vulnerability database, fix PRs | CI/CD, IDE |
| **Renovate** | Auto-updates, merge confidence | CI/CD |
| **OWASP Dependency-Check** | Open source | CI/CD |
| **Socket** | Supply chain attack detection | GitHub, npm |

### Secret Scanning

**Pre-commit:**
- **gitleaks** - Comprehensive secret detection
- **truffleHog** - Entropy-based and regex detection
- **detect-secrets** - Yelp's pre-commit hook

**CI-level:**
- GitHub Secret Scanning (native)
- GitLab Secret Detection
- Snyk Code (includes secret detection)

**Configuration (gitleaks):**
```toml
[allowlist]
description = "Allowlisted files"
paths = ["test/fixtures/"]

[[rules]]
description = "AWS Access Key"
regex = '''AKIA[0-9A-Z]{16}'''
```

### SBOM Generation

**Tools:**
- **Syft** (Anchore) - Generates SPDX and CycloneDX SBOMs
- **Trivy** - SBOM generation + vulnerability scanning
- **CycloneDX CLI** - Standard SBOM format
- **Microsoft SBOM Tool** - Cross-platform SBOM generation

**Best Practice:** Generate SBOM on every release, store with release artifacts, scan for new vulnerabilities periodically.

---

## Hardware Security Keys

### YubiKey 5 Series

| Model | Interfaces | Protocols | Use Case |
|-------|-----------|----------|----------|
| **YubiKey 5 NFC** | USB-A + NFC | FIDO2, U2F, OTP, PIV, OpenPGP | Standard users |
| **YubiKey 5C NFC** | USB-C + NFC | FIDO2, U2F, OTP, PIV, OpenPGP | USB-C laptops |
| **YubiKey 5 Nano** | USB-A (nano) | FIDO2, U2F, OTP, PIV, OpenPGP | Always-in key |
| **YubiKey 5C Nano** | USB-C (nano) | FIDO2, U2F, OTP, PIV, OpenPGP | USB-C always-in |
| **YubiKey 5Ci** | USB-C + Lightning | FIDO2, U2F, OTP, PIV, OpenPGP | iOS + laptop |
| **YubiKey Bio** | USB-A/C + fingerprint | FIDO2 with biometric | Biometric MFA |

### FIDO2/WebAuthn Configuration

**Identity Provider Setup (Okta example):**
1. Enable FIDO2 (WebAuthn) as MFA factor
2. Set attestation preference to "direct" (verify key authenticity)
3. Configure user verification to "required" (PIN or biometric)
4. Restrict allowed authenticators to FIDO2 certified devices
5. Configure resident key preference based on passwordless strategy

**Browser Support:**
- Chrome 67+ (full support)
- Firefox 60+ (full support)
- Safari 13+ (full support)
- Edge 18+ (full support)

**SOC 2 Recommendation:**
- Require hardware security keys for: root accounts, admin accounts, production access, break-glass accounts
- Issue two keys per user (primary + backup)
- Store backup keys in secure location
- Register both keys with all services
- Document lost key procedures

### Phishing Resistance

| MFA Method | Phishing Resistant | SOC 2 Acceptable |
|-----------|-------------------|-------------------|
| SMS OTP | No (SIM swap) | No |
| Email OTP | No (email compromise) | No |
| TOTP (Authenticator) | No (real-time phishing) | Yes (minimum) |
| Push notification | Partial (MFA fatigue) | Yes |
| FIDO2/WebAuthn | Yes (origin-bound) | Yes (preferred) |
| Hardware key (YubiKey) | Yes (physical presence) | Yes (required for admins) |

---

## Secrets Management

### HashiCorp Vault

**Architecture:**
- Deploy in HA mode (3+ nodes) for production
- Enable audit logging to external SIEM
- Use auto-unseal with cloud KMS
- Enable Sentinel policies for governance

**Key Features for SOC 2:**

| Feature | SOC 2 Benefit | Configuration |
|---------|--------------|---------------|
| **Dynamic secrets** | Eliminates long-lived credentials | Database, AWS, Azure, GCP secret engines |
| **Secret rotation** | Automated credential rotation | Rotation period per mount |
| **Audit logging** | Complete access audit trail | File, syslog, or socket audit devices |
| **Access policies** | Least privilege enforcement | Path-based ACL policies |
| **Namespaces** | Multi-tenant isolation | Namespace per team/environment |
| **Sentinel** | Policy-as-code governance | Restrict operations, require MFA |

### AWS Secrets Manager

| Feature | Configuration |
|---------|---------------|
| **Automatic rotation** | Lambda function, 30/60/90-day rotation |
| **Cross-region replication** | Replicate secrets for DR |
| **IAM policies** | Restrict access by role/service |
| **CloudTrail logging** | All API calls logged |
| **Encryption** | KMS CMK encryption at rest |

### Azure Key Vault

| Feature | Configuration |
|---------|---------------|
| **Access policies** | RBAC or vault access policies |
| **Soft delete** | 7-90 day retention, purge protection |
| **Key rotation** | Notification-based rotation |
| **Managed HSM** | FIPS 140-2 Level 3 validation |
| **Diagnostic logs** | Azure Monitor integration |

### GCP Secret Manager

| Feature | Configuration |
|---------|---------------|
| **IAM** | Fine-grained access with conditions |
| **Versioning** | Automatic version management |
| **Rotation** | Pub/Sub notification for rotation |
| **CMEK** | Customer-managed encryption keys |
| **Audit logging** | Cloud Audit Logs integration |

### Secret Rotation Policies

| Secret Type | Maximum Lifetime | Rotation Method | Automation |
|-------------|-----------------|-----------------|-----------|
| Database passwords | 90 days | Dynamic secrets (Vault) | Fully automated |
| API keys | 90 days | Vault rotation or manual + alert | Semi-automated |
| OAuth client secrets | 1 year | Provider rotation | Manual with tracking |
| SSH keys | 1 year | Certificate-based preferred | Automated |
| TLS certificates | 90 days (recommended) | ACME protocol | Fully automated |
| Encryption keys | 1 year | Cloud KMS auto-rotation | Fully automated |
| Service account keys | 90 days | Workload identity preferred | Eliminated |
| Personal access tokens | 90 days | Developer self-service | Semi-automated |

### Git Secret Prevention

**Pre-commit hook (gitleaks):**
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

**CI Pipeline (GitHub Actions):**
```yaml
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Response to Detected Secrets:**
1. Immediately rotate the compromised credential
2. Audit access logs for unauthorized usage
3. Remove from git history (git-filter-repo)
4. Notify security team
5. Update pre-commit hooks to prevent recurrence
6. Document incident

---

## Compliance Mapping Summary

| Infrastructure Area | SOC 2 Controls | Evidence Type |
|--------------------|---------------|---------------|
| Cloud IAM | CC6.1, CC6.2, CC6.3 | Configuration screenshots, access reviews |
| Cloud Encryption | CC6.1, C1.1 | KMS configuration, encryption status |
| Cloud Logging | CC7.2, CC4.1 | Log configuration, sample alerts |
| Cloud Network | CC6.6 | Security group rules, network diagrams |
| DNS Security | CC6.6, CC2.2 | DNS record verification |
| TLS/SSL | CC6.7 | SSL Labs report, HSTS configuration |
| Endpoint Security | CC6.8, CC6.1, C1.1 | MDM reports, EDR coverage, encryption status |
| Network Security | CC6.6, A1.1 | Firewall rules, WAF logs, DDoS config |
| Container Security | CC6.1, CC7.1, CC6.6 | Image scan results, K8s policies |
| CI/CD Security | CC8.1, CC7.1 | Branch protection, scan results, pipeline config |
| Hardware Keys | CC6.1 | MFA enrollment report, key inventory |
| Secrets Management | CC6.1 | Vault configuration, rotation evidence |

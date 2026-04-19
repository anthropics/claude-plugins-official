---
name: senior-security
description: >
  Performs STRIDE threat modeling, DREAD risk scoring, secret detection, and
  secure architecture design. Use when conducting threat models, reviewing code
  for security vulnerabilities, designing defense-in-depth architectures, or
  scanning for hardcoded secrets and credentials.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: application-security
  updated: 2026-03-31
  tags: [owasp, threat-modeling, penetration-testing, application-security]
---
# Senior Security Engineer

The agent performs STRIDE threat analysis with DREAD risk scoring, designs defense-in-depth security architectures with Zero Trust principles, conducts secure code reviews against OWASP Top 10, and scans codebases for hardcoded secrets across 20+ credential patterns.

---

## Table of Contents

- [Threat Modeling Workflow](#threat-modeling-workflow)
- [Security Architecture Workflow](#security-architecture-workflow)
- [Vulnerability Assessment Workflow](#vulnerability-assessment-workflow)
- [Secure Code Review Workflow](#secure-code-review-workflow)
- [Incident Response Workflow](#incident-response-workflow)
- [Security Tools Reference](#security-tools-reference)
- [Tools and References](#tools-and-references)

---

## Threat Modeling Workflow

Identify and analyze security threats using STRIDE methodology.

### Workflow: Conduct Threat Model

1. Define system scope and boundaries:
   - Identify assets to protect
   - Map trust boundaries
   - Document data flows
2. Create data flow diagram:
   - External entities (users, services)
   - Processes (application components)
   - Data stores (databases, caches)
   - Data flows (APIs, network connections)
3. Apply STRIDE to each DFD element:
   - Spoofing: Can identity be faked?
   - Tampering: Can data be modified?
   - Repudiation: Can actions be denied?
   - Information Disclosure: Can data leak?
   - Denial of Service: Can availability be affected?
   - Elevation of Privilege: Can access be escalated?
4. Score risks using DREAD:
   - Damage potential (1-10)
   - Reproducibility (1-10)
   - Exploitability (1-10)
   - Affected users (1-10)
   - Discoverability (1-10)
5. Prioritize threats by risk score
6. Define mitigations for each threat
7. Document in threat model report
8. **Validation:** All DFD elements analyzed; STRIDE applied; threats scored; mitigations mapped

### STRIDE Threat Categories

| Category | Description | Security Property | Mitigation Focus |
|----------|-------------|-------------------|------------------|
| Spoofing | Impersonating users or systems | Authentication | MFA, certificates, strong auth |
| Tampering | Modifying data or code | Integrity | Signing, checksums, validation |
| Repudiation | Denying actions | Non-repudiation | Audit logs, digital signatures |
| Information Disclosure | Exposing data | Confidentiality | Encryption, access controls |
| Denial of Service | Disrupting availability | Availability | Rate limiting, redundancy |
| Elevation of Privilege | Gaining unauthorized access | Authorization | RBAC, least privilege |

### STRIDE per Element Matrix

| DFD Element | S | T | R | I | D | E |
|-------------|---|---|---|---|---|---|
| External Entity | X | | X | | | |
| Process | X | X | X | X | X | X |
| Data Store | | X | X | X | X | |
| Data Flow | | X | | X | X | |

See: [references/threat-modeling-guide.md](references/threat-modeling-guide.md)

---

## Security Architecture Workflow

Design secure systems using defense-in-depth principles.

### Workflow: Design Secure Architecture

1. Define security requirements:
   - Compliance requirements (GDPR, HIPAA, PCI-DSS)
   - Data classification (public, internal, confidential, restricted)
   - Threat model inputs
2. Apply defense-in-depth layers:
   - Perimeter: WAF, DDoS protection, rate limiting
   - Network: Segmentation, IDS/IPS, mTLS
   - Host: Patching, EDR, hardening
   - Application: Input validation, authentication, secure coding
   - Data: Encryption at rest and in transit
3. Implement Zero Trust principles:
   - Verify explicitly (every request)
   - Least privilege access (JIT/JEA)
   - Assume breach (segment, monitor)
4. Configure authentication and authorization:
   - Identity provider selection
   - MFA requirements
   - RBAC/ABAC model
5. Design encryption strategy:
   - Key management approach
   - Algorithm selection
   - Certificate lifecycle
6. Plan security monitoring:
   - Log aggregation
   - SIEM integration
   - Alerting rules
7. Document architecture decisions
8. **Validation:** Defense-in-depth layers defined; Zero Trust applied; encryption strategy documented; monitoring planned

### Defense-in-Depth Layers

```
Layer 1: PERIMETER
  WAF, DDoS mitigation, DNS filtering, rate limiting

Layer 2: NETWORK
  Segmentation, IDS/IPS, network monitoring, VPN, mTLS

Layer 3: HOST
  Endpoint protection, OS hardening, patching, logging

Layer 4: APPLICATION
  Input validation, authentication, secure coding, SAST

Layer 5: DATA
  Encryption at rest/transit, access controls, DLP, backup
```

### Authentication Pattern Selection

| Use Case | Recommended Pattern |
|----------|---------------------|
| Web application | OAuth 2.0 + PKCE with OIDC |
| API authentication | JWT with short expiration + refresh tokens |
| Service-to-service | mTLS with certificate rotation |
| CLI/Automation | API keys with IP allowlisting |
| High security | FIDO2/WebAuthn hardware keys |

See: [references/security-architecture-patterns.md](references/security-architecture-patterns.md)

---

## Vulnerability Assessment Workflow

Identify and remediate security vulnerabilities in applications.

### Workflow: Conduct Vulnerability Assessment

1. Define assessment scope:
   - In-scope systems and applications
   - Testing methodology (black box, gray box, white box)
   - Rules of engagement
2. Gather information:
   - Technology stack inventory
   - Architecture documentation
   - Previous vulnerability reports
3. Perform automated scanning:
   - SAST (static analysis)
   - DAST (dynamic analysis)
   - Dependency scanning
   - Secret detection
4. Conduct manual testing:
   - Business logic flaws
   - Authentication bypass
   - Authorization issues
   - Injection vulnerabilities
5. Classify findings by severity:
   - Critical: Immediate exploitation risk
   - High: Significant impact, easier to exploit
   - Medium: Moderate impact or difficulty
   - Low: Minor impact
6. Develop remediation plan:
   - Prioritize by risk
   - Assign owners
   - Set deadlines
7. Verify fixes and document
8. **Validation:** Scope defined; automated and manual testing complete; findings classified; remediation tracked

### OWASP Top 10 Mapping

| Rank | Vulnerability | Testing Approach |
|------|---------------|------------------|
| A01 | Broken Access Control | Manual IDOR testing, authorization checks |
| A02 | Cryptographic Failures | Algorithm review, key management audit |
| A03 | Injection | SAST + manual payload testing |
| A04 | Insecure Design | Threat modeling, architecture review |
| A05 | Security Misconfiguration | Configuration audit, CIS benchmarks |
| A06 | Vulnerable Components | Dependency scanning, CVE monitoring |
| A07 | Authentication Failures | Password policy, session management review |
| A08 | Software/Data Integrity | CI/CD security, code signing verification |
| A09 | Logging Failures | Log review, SIEM configuration check |
| A10 | SSRF | Manual URL manipulation testing |

### Vulnerability Severity Matrix

| Impact / Exploitability | Easy | Moderate | Difficult |
|-------------------------|------|----------|-----------|
| Critical | Critical | Critical | High |
| High | Critical | High | Medium |
| Medium | High | Medium | Low |
| Low | Medium | Low | Low |

---

## Secure Code Review Workflow

Review code for security vulnerabilities before deployment.

### Workflow: Conduct Security Code Review

1. Establish review scope:
   - Changed files and functions
   - Security-sensitive areas (auth, crypto, input handling)
   - Third-party integrations
2. Run automated analysis:
   - SAST tools (Semgrep, CodeQL, Bandit)
   - Secret scanning
   - Dependency vulnerability check
3. Review authentication code:
   - Password handling (hashing, storage)
   - Session management
   - Token validation
4. Review authorization code:
   - Access control checks
   - RBAC implementation
   - Privilege boundaries
5. Review data handling:
   - Input validation
   - Output encoding
   - SQL query construction
   - File path handling
6. Review cryptographic code:
   - Algorithm selection
   - Key management
   - Random number generation
7. Document findings with severity
8. **Validation:** Automated scans passed; auth/authz reviewed; data handling checked; crypto verified; findings documented

### Security Code Review Checklist

| Category | Check | Risk |
|----------|-------|------|
| Input Validation | All user input validated and sanitized | Injection |
| Output Encoding | Context-appropriate encoding applied | XSS |
| Authentication | Passwords hashed with Argon2/bcrypt | Credential theft |
| Session | Secure cookie flags set (HttpOnly, Secure, SameSite) | Session hijacking |
| Authorization | Server-side permission checks on all endpoints | Privilege escalation |
| SQL | Parameterized queries used exclusively | SQL injection |
| File Access | Path traversal sequences rejected | Path traversal |
| Secrets | No hardcoded credentials or keys | Information disclosure |
| Dependencies | Known vulnerable packages updated | Supply chain |
| Logging | Sensitive data not logged | Information disclosure |

### Secure vs Insecure Patterns

| Pattern | Issue | Secure Alternative |
|---------|-------|-------------------|
| SQL string formatting | SQL injection | Use parameterized queries with placeholders |
| Shell command building | Command injection | Use subprocess with argument lists, no shell |
| Path concatenation | Path traversal | Validate and canonicalize paths |
| MD5/SHA1 for passwords | Weak hashing | Use Argon2id or bcrypt |
| Math.random for tokens | Predictable values | Use crypto.getRandomValues |

---

## Incident Response Workflow

Respond to and contain security incidents.

### Workflow: Handle Security Incident

1. Identify and triage:
   - Validate incident is genuine
   - Assess initial scope and severity
   - Activate incident response team
2. Contain the threat:
   - Isolate affected systems
   - Block malicious IPs/accounts
   - Disable compromised credentials
3. Eradicate root cause:
   - Remove malware/backdoors
   - Patch vulnerabilities
   - Update configurations
4. Recover operations:
   - Restore from clean backups
   - Verify system integrity
   - Monitor for recurrence
5. Conduct post-mortem:
   - Timeline reconstruction
   - Root cause analysis
   - Lessons learned
6. Implement improvements:
   - Update detection rules
   - Enhance controls
   - Update runbooks
7. Document and report
8. **Validation:** Threat contained; root cause eliminated; systems recovered; post-mortem complete; improvements implemented

### Incident Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| P1 - Critical | Active breach, data exfiltration | Immediate | CISO, Legal, Executive |
| P2 - High | Confirmed compromise, contained | 1 hour | Security Lead, IT Director |
| P3 - Medium | Potential compromise, under investigation | 4 hours | Security Team |
| P4 - Low | Suspicious activity, low impact | 24 hours | On-call engineer |

### Incident Response Checklist

| Phase | Actions |
|-------|---------|
| Identification | Validate alert, assess scope, determine severity |
| Containment | Isolate systems, preserve evidence, block access |
| Eradication | Remove threat, patch vulnerabilities, reset credentials |
| Recovery | Restore services, verify integrity, increase monitoring |
| Lessons Learned | Document timeline, identify gaps, update procedures |

---

## Security Tools Reference

### Recommended Security Tools

| Category | Tools |
|----------|-------|
| SAST | Semgrep, CodeQL, Bandit (Python), ESLint security plugins |
| DAST | OWASP ZAP, Burp Suite, Nikto |
| Dependency Scanning | Snyk, Dependabot, npm audit, pip-audit |
| Secret Detection | GitLeaks, TruffleHog, detect-secrets |
| Container Security | Trivy, Clair, Anchore |
| Infrastructure | Checkov, tfsec, ScoutSuite |
| Network | Wireshark, Nmap, Masscan |
| Penetration | Metasploit, sqlmap, Burp Suite Pro |

### Cryptographic Algorithm Selection

| Use Case | Algorithm | Key Size |
|----------|-----------|----------|
| Symmetric encryption | AES-256-GCM | 256 bits |
| Password hashing | Argon2id | N/A (use defaults) |
| Message authentication | HMAC-SHA256 | 256 bits |
| Digital signatures | Ed25519 | 256 bits |
| Key exchange | X25519 | 256 bits |
| TLS | TLS 1.3 | N/A |

See: [references/cryptography-implementation.md](references/cryptography-implementation.md)

---

## Tools and References

### Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [threat_modeler.py](scripts/threat_modeler.py) | STRIDE threat analysis with risk scoring | `python threat_modeler.py --component "Authentication"` |
| [secret_scanner.py](scripts/secret_scanner.py) | Detect hardcoded secrets and credentials | `python secret_scanner.py /path/to/project` |

**Threat Modeler Features:**
- STRIDE analysis for any system component
- DREAD risk scoring
- Mitigation recommendations
- JSON and text output formats
- Interactive mode for guided analysis

**Secret Scanner Features:**
- Detects AWS, GCP, Azure credentials
- Finds API keys and tokens (GitHub, Slack, Stripe)
- Identifies private keys and passwords
- Supports 20+ secret patterns
- CI/CD integration ready

### References

| Document | Content |
|----------|---------|
| [security-architecture-patterns.md](references/security-architecture-patterns.md) | Zero Trust, defense-in-depth, authentication patterns, API security |
| [threat-modeling-guide.md](references/threat-modeling-guide.md) | STRIDE methodology, attack trees, DREAD scoring, DFD creation |
| [cryptography-implementation.md](references/cryptography-implementation.md) | AES-GCM, RSA, Ed25519, password hashing, key management |

---

## Security Standards Reference

### Compliance Frameworks

| Framework | Focus | Applicable To |
|-----------|-------|---------------|
| OWASP ASVS | Application security | Web applications |
| CIS Benchmarks | System hardening | Servers, containers, cloud |
| NIST CSF | Risk management | Enterprise security programs |
| PCI-DSS | Payment card data | Payment processing |
| HIPAA | Healthcare data | Healthcare applications |
| SOC 2 | Service organization controls | SaaS providers |

### Security Headers Checklist

| Header | Recommended Value |
|--------|-------------------|
| Content-Security-Policy | default-src self; script-src self |
| X-Frame-Options | DENY |
| X-Content-Type-Options | nosniff |
| Strict-Transport-Security | max-age=31536000; includeSubDomains |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation=(), microphone=(), camera=() |

---

## Related Skills

| Skill | Integration Point |
|-------|-------------------|
| [senior-devops](../senior-devops/) | CI/CD security, infrastructure hardening |
| [senior-secops](../senior-secops/) | Security monitoring, incident response |
| [senior-backend](../senior-backend/) | Secure API development |
| [senior-architect](../senior-architect/) | Security architecture decisions |

---

## Anti-Patterns

- **Security by obscurity** -- hiding endpoints or using non-standard ports is not a control; implement authentication, authorization, and encryption
- **MD5/SHA1 for password hashing** -- both are broken for this purpose; use Argon2id or bcrypt with cost factor >= 12
- **Math.random for tokens** -- predictable values allow session hijacking; use `crypto.getRandomValues()` or `secrets.token_hex()`
- **Shell=True in subprocess** -- enables command injection; use argument lists with `subprocess.run(["cmd", "arg"])`
- **Threat model without data flow diagram** -- STRIDE analysis requires DFD elements to be systematic; skip the DFD and you miss entire attack surfaces
- **Accepted risks without review cadence** -- DREAD scores drift as systems evolve; re-validate accepted risks every 90 days

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Secret scanner reports false positives on test fixtures | Test files contain example tokens that match secret patterns | Add test directories to the exclude list or filter by `--severity critical` to focus on confirmed secrets |
| Threat model returns all threats instead of component-specific ones | Component name does not match any entry in the component mapping | Use a recognized component keyword (e.g., "authentication", "api", "database", "network", "storage") or a composite like "web application" |
| DREAD scores seem inflated for low-likelihood threats | DREAD factors are derived from likelihood and severity with fixed multipliers | Interpret DREAD as a relative ranking within the report, not an absolute metric; adjust risk acceptance thresholds accordingly |
| Secret scanner misses secrets in non-standard file extensions | Only files whose extensions appear in the pattern's `file_extensions` list are scanned | Rename config files to use a recognized extension (e.g., `.conf`, `.env`, `.yml`) or extend the pattern database |
| Threat model does not cover custom component types | The `COMPONENT_MAPPING` dictionary has a fixed set of keywords | Add new entries to `COMPONENT_MAPPING` in `threat_modeler.py` for project-specific components |
| Secret scanner exits with code 1 even after fixing secrets | Previous scan results are cached or the fix introduced a new match | Re-run the scanner after every fix; exit code 1 triggers whenever any critical or high finding remains |
| Security headers audit produces incomplete results | Application is behind a reverse proxy that strips or overrides headers | Test headers at the edge (CDN/load balancer) rather than at the application origin |

---

## Success Criteria

- Zero critical- or high-severity secrets detected by `secret_scanner.py` across the entire codebase before every release.
- Threat model coverage above 90%: every component in the data flow diagram has a completed STRIDE analysis with documented mitigations.
- All OWASP Top 10 vulnerability categories addressed in the security architecture with at least one compensating control per category.
- Mean time to remediate critical vulnerabilities under 48 hours from discovery to verified fix.
- 100% of authentication and authorization code paths reviewed with the Secure Code Review Checklist before merge.
- Incident response exercises (tabletop or simulated) conducted at least quarterly with post-mortem documentation.
- DREAD risk scores for all remaining accepted risks reviewed and re-validated every 90 days.

---

## Scope & Limitations

**This skill covers:**
- Application-level security: threat modeling, secure code review, secret detection, and vulnerability assessment for web applications and APIs.
- Security architecture design: defense-in-depth layering, Zero Trust patterns, authentication/authorization model selection, and encryption strategy.
- Incident response planning: severity classification, containment procedures, post-mortem frameworks, and runbook creation.
- Compliance mapping: OWASP ASVS, CIS Benchmarks, NIST CSF, PCI-DSS, HIPAA, and SOC 2 alignment at the application layer.

**This skill does NOT cover:**
- Infrastructure and cloud security hardening (see [senior-devops](../senior-devops/) and [aws-solution-architect](../aws-solution-architect/)).
- Runtime security monitoring, SIEM rule authoring, and SOC operations (see [senior-secops](../senior-secops/)).
- Full regulatory compliance programs, audit evidence collection, and certification processes (see [ra-qm-team](../../ra-qm-team/)).
- Network penetration testing tooling, red team operations, and physical security assessments.

---

## Integration Points

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| [senior-devops](../senior-devops/) | CI/CD pipeline security gates | Threat model mitigations feed into pipeline hardening requirements; secret scanner runs as a pre-commit or CI step |
| [senior-secops](../senior-secops/) | Security monitoring and incident response | Threat model outputs define detection rules; incident severity levels align with SecOps alerting tiers |
| [senior-backend](../senior-backend/) | Secure API development | Secure code review checklist applied to backend PRs; authentication pattern selection guides API auth implementation |
| [senior-architect](../senior-architect/) | Security architecture decisions | Defense-in-depth layers and Zero Trust principles inform architecture design reviews; STRIDE results feed architecture risk register |
| [senior-qa](../senior-qa/) | Security testing integration | Vulnerability assessment findings become QA regression test cases; OWASP Top 10 mapping drives security test coverage |
| [ra-qm-team](../../ra-qm-team/) | Compliance framework alignment | Security controls mapped to SOC 2, PCI-DSS, and HIPAA requirements; threat model documentation satisfies audit evidence needs |

---

## Tool Reference

### threat_modeler.py

**Purpose:** Performs STRIDE threat analysis on system components with DREAD risk scoring, mitigation recommendations, and structured reporting.

**Usage:**

```bash
python threat_modeler.py --component "User Authentication"
python threat_modeler.py --component "API Gateway" --assets "user_data,tokens" --json
python threat_modeler.py --component "Database" --output report.txt
python threat_modeler.py --interactive
python threat_modeler.py --list-threats
```

**Flags:**

| Flag | Short | Type | Required | Description |
|------|-------|------|----------|-------------|
| `--component` | `-c` | string | Yes (unless `--interactive` or `--list-threats`) | Component to analyze (e.g., "User Authentication", "API Gateway", "Database") |
| `--assets` | `-a` | string | No | Comma-separated list of assets to protect |
| `--json` | | flag | No | Output report as JSON instead of text |
| `--interactive` | `-i` | flag | No | Run guided interactive threat modeling session |
| `--list-threats` | `-l` | flag | No | List all threats in the built-in database |
| `--output` | `-o` | string | No | Write report to file path instead of stdout |

**Example:**

```bash
$ python threat_modeler.py --component "API Gateway" --json --output api-threats.json
Report written to api-threats.json
```

**Output Formats:**
- **Text (default):** Structured report grouped by STRIDE category with risk scores, DREAD ratings, attack vectors, and mitigations.
- **JSON (`--json`):** Machine-readable object containing `component`, `analysis_date`, `summary` (counts by risk level), and `threats` array with full DREAD breakdown per threat.

---

### secret_scanner.py

**Purpose:** Detects hardcoded secrets, API keys, credentials, and private keys in source code. Supports 20+ secret patterns across cloud providers (AWS, GCP, Azure), authentication tokens (GitHub, GitLab, Slack, Stripe, Twilio, SendGrid), cryptographic keys, and generic credential patterns. Exits with code 1 when critical or high findings are present, making it CI/CD-ready.

**Usage:**

```bash
python secret_scanner.py /path/to/project
python secret_scanner.py /path/to/file.py
python secret_scanner.py /path/to/project --format json --output report.json
python secret_scanner.py /path/to/project --severity critical
python secret_scanner.py --list-patterns
```

**Flags:**

| Flag | Short | Type | Required | Description |
|------|-------|------|----------|-------------|
| `path` | | positional | Yes (unless `--list-patterns`) | File or directory path to scan |
| `--format` | `-f` | choice: `text`, `json` | No | Output format (default: `text`) |
| `--output` | `-o` | string | No | Write report to file path instead of stdout |
| `--list-patterns` | `-l` | flag | No | List all detection patterns with IDs and severity |
| `--severity` | `-s` | choice: `critical`, `high`, `medium`, `low` | No | Minimum severity threshold to report (includes all levels from critical down to the specified level) |

**Example:**

```bash
$ python secret_scanner.py ./src --severity high --format json
{
  "target": "./src",
  "scan_date": "2026-03-21T10:30:00",
  "summary": { "total": 2, "by_severity": { "critical": 1, "high": 1, "medium": 0, "low": 0 } },
  "findings": [ ... ]
}
```

**Output Formats:**
- **Text (default):** Severity-grouped report showing pattern ID, file path with line number, masked match text, and remediation recommendation.
- **JSON (`--format json`):** Machine-readable object with `target`, `scan_date`, `summary` (counts by severity), and `findings` array. Each finding includes `pattern_id`, `name`, `severity`, `file_path`, `line_number`, `matched_text` (masked), and `recommendation`.

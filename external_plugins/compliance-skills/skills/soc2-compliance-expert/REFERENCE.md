# SOC 2 Compliance Reference Material

Detailed Trust Services Criteria controls, infrastructure security checks, access control specifications, and operational requirements. Referenced by the main [SKILL.md](SKILL.md).

---

## Trust Services Criteria -- Control Details

### CC1: Control Environment

**COSO Principles:** Commitment to integrity/ethics (1), Board oversight (2), Organizational structure (3), Commitment to competence (4), Accountability enforcement (5).

| Control | Description | Evidence |
|---------|-------------|----------|
| CC1.1 | Code of conduct/ethics policy | Signed acknowledgments, policy document |
| CC1.2 | Board/management oversight structure | Org chart, board meeting minutes, committee charters |
| CC1.3 | Defined roles and responsibilities | Job descriptions, RACI matrices |
| CC1.4 | Hiring and competency standards | Background check policy, training records |
| CC1.5 | Performance evaluation and accountability | Review templates, disciplinary procedures |

**Board Oversight Requirements:**
- Documented board or committee charter for risk oversight
- Quarterly security briefings to the board or audit committee
- Board review and approval of information security policy annually
- Independent directors with cybersecurity expertise (recommended)

### CC2: Communication and Information

| Control | Description | Evidence |
|---------|-------------|----------|
| CC2.1 | Internal communication of objectives and responsibilities | Security awareness materials, policy portal |
| CC2.2 | External communication with customers and regulators | Privacy policy, security page, breach notification procedures |
| CC2.3 | System description accuracy and completeness | Documented system boundaries, data flow diagrams |

**System Description (Section III of SOC 2 Report):**
- Principal service commitments and system requirements
- Components of the system (infrastructure, software, people, procedures, data)
- System boundaries and interconnections
- Complementary user entity controls (CUECs)
- Complementary subservice organization controls (CSOCs)

### CC3: Risk Assessment

| Control | Description | Evidence |
|---------|-------------|----------|
| CC3.1 | Risk identification for business objectives | Risk register, annual risk assessment |
| CC3.2 | Fraud risk assessment | Fraud risk matrix, anti-fraud controls |
| CC3.3 | Change management risk identification | Change impact assessments, regulatory monitoring |
| CC3.4 | Risk assessment of significant changes | M&A risk reviews, new product security assessments |

**Risk Identification Process:**
1. Asset inventory and classification (data, systems, people)
2. Threat identification (internal, external, environmental)
3. Vulnerability assessment (technical, procedural, human)
4. Likelihood and impact scoring (qualitative or quantitative)
5. Risk treatment decisions (accept, mitigate, transfer, avoid)
6. Residual risk documentation and acceptance

**Fraud Risk Considerations:** Segregation of duties analysis, management override controls, financial reporting fraud risks, data manipulation risks, social engineering vulnerability assessment, insider threat program.

### CC4: Monitoring Activities

| Control | Description | Evidence |
|---------|-------------|----------|
| CC4.1 | Ongoing monitoring and separate evaluations | Continuous monitoring dashboards, periodic control testing |
| CC4.2 | Deficiency communication and remediation | Finding reports, remediation tracking, management reporting |

**Ongoing Monitoring:** SIEM, IDS/IPS, real-time alerting, KPI/KRI dashboards, cloud posture management, continuous vulnerability scanning.

**Separate Evaluations:** Internal audit (annual minimum), penetration testing (annual minimum, quarterly recommended), third-party assessments, control self-assessments, tabletop exercises.

### CC5: Control Activities

| Control | Description | Evidence |
|---------|-------------|----------|
| CC5.1 | Selection and development of control activities | Control design documentation, risk-control mapping |
| CC5.2 | Technology general controls | IT general controls documentation |
| CC5.3 | Policy and procedure deployment | Policy management system, version control, acknowledgments |

**Control Activity Categories:**
- **Preventive:** Access controls, input validation, encryption
- **Detective:** Logging, monitoring, anomaly detection, auditing
- **Corrective:** Incident response, backup restoration, patch management
- **Compensating:** Additional controls when primary controls have gaps

### CC6: Logical and Physical Access Controls

| Control | Description | Evidence |
|---------|-------------|----------|
| CC6.1 | Logical access security (authentication, authorization) | IAM configurations, SSO setup, MFA enforcement |
| CC6.2 | Access provisioning based on role | Role definitions, access request workflows |
| CC6.3 | Access modification and removal | Joiner/mover/leaver procedures, access reviews |
| CC6.4 | Physical access restrictions | Badge system logs, visitor logs, data center controls |
| CC6.5 | Logical access to assets removed upon termination | Offboarding checklists, access removal evidence |
| CC6.6 | External access points protection | Firewall rules, VPN configurations, WAF rules |
| CC6.7 | Data transmission encryption | TLS configurations, encryption standards |
| CC6.8 | Unauthorized or malicious software prevention | Endpoint protection, application whitelisting |

**Authentication Requirements:**
- MFA enforced for all users
- Password policy: minimum 12 characters, complexity requirements
- Account lockout after 5 failed attempts
- Session timeout: 15 minutes (sensitive), 30 minutes (general)
- SSO via SAML 2.0 or OIDC for all SaaS applications

**MFA Standards:**
- TOTP: Minimum acceptable
- FIDO2/WebAuthn: Preferred (phishing-resistant)
- Hardware security keys: Required for privileged access
- SMS-based MFA: Not acceptable (SIM swap vulnerability)

**Access Review Cadence:** Privileged (quarterly), Standard (semi-annual), Service accounts (quarterly), Third-party (quarterly), Dormant accounts (monthly automated detection).

**Physical Security:** Biometric + badge + escort for data center visitors, badge system with audit trail for offices, visitor sign-in/sign-out, environmental controls (fire, HVAC, water detection), CCTV 90-day retention at entry/exit.

### CC7: System Operations

| Control | Description | Evidence |
|---------|-------------|----------|
| CC7.1 | Vulnerability management and detection | Vulnerability scan reports, patch management records |
| CC7.2 | Security event monitoring and anomaly detection | SIEM configurations, alert rules, monitoring dashboards |
| CC7.3 | Security incident evaluation and response | Incident response plan, incident tickets, post-mortems |
| CC7.4 | Business continuity planning | BCP document, DR runbooks, test results |
| CC7.5 | Recovery from incidents and disasters | Recovery procedures, RTO/RPO documentation, test results |

**Vulnerability Management SLAs:** Critical (24h), High (7d), Medium (30d), Low (90d).

**Change Management:** CAB process for significant changes, emergency change procedures with post-hoc review, rollback plans required, testing in non-production environments, change calendar and blackout windows.

### CC8: Change Management

| Control | Description | Evidence |
|---------|-------------|----------|
| CC8.1 | Change authorization, design, development, and testing | Change tickets, approval workflows, test results |

**Change Authorization Process:**
1. Change request with business justification
2. Impact assessment (security, performance, compliance)
3. Peer code review (min 1 reviewer, 2 for critical)
4. Approval from change authority
5. Testing in staging/pre-production
6. Deployment with rollback plan
7. Post-deployment validation
8. Change record closure

**Deployment Controls:** Automated CI/CD pipelines, separation of dev/staging/production, restricted production access, deployment audit trail, automated rollback capability.

### CC9: Risk Mitigation

| Control | Description | Evidence |
|---------|-------------|----------|
| CC9.1 | Vendor risk identification and assessment | Vendor risk assessments, due diligence records |
| CC9.2 | Business disruption risk management | BIA results, insurance certificates, risk transfer documentation |

### A1: Availability

| Control | Description | Evidence |
|---------|-------------|----------|
| A1.1 | Capacity planning and performance monitoring | Capacity plans, monitoring dashboards, auto-scaling configs |
| A1.2 | Disaster recovery and business continuity | DR plan, failover testing, backup verification |
| A1.3 | Recovery testing and validation | DR test results, RTO/RPO achievement records |

**Backup Requirements:** Daily minimum for production, point-in-time recovery for databases, encrypted at rest/transit, monthly restoration testing, 30-day retention minimum (90 recommended), air-gapped/immutable for ransomware protection.

**SLA Management:** 99.9% uptime minimum, scheduled maintenance windows, real-time status page, SLA credit structure, monthly reporting.

### PI1: Processing Integrity

| Control | Description | Evidence |
|---------|-------------|----------|
| PI1.1 | Completeness, accuracy, timeliness, authorization | Data validation rules, reconciliation, processing logs |
| PI1.2 | Error detection and correction | Error handling procedures, exception reports |
| PI1.3 | Input and output verification | Input validation rules, output reconciliation |
| PI1.4 | Processing authorization and scheduling | Job scheduling, approval workflows |
| PI1.5 | Data quality and integrity monitoring | Data quality dashboards, integrity checks |

### C1: Confidentiality

| Control | Description | Evidence |
|---------|-------------|----------|
| C1.1 | Confidential information identification and classification | Data classification policy, labels |
| C1.2 | Confidential information disposal | Retention schedule, disposal procedures, destruction certificates |

**Data Classification:** Public, Internal, Confidential, Highly Confidential/Restricted.

**Encryption Requirements:** AES-256 at rest, TLS 1.2+ in transit (1.3 preferred), TDE or field-level for databases, HSM for production keys, annual key rotation (90 days for high-sensitivity).

### P1: Privacy

| Control | Description | Evidence |
|---------|-------------|----------|
| P1.1 | Privacy notice and consent | Privacy policy, cookie consent, ToS |
| P1.2 | Choice and consent management | Consent records, opt-out mechanisms |
| P1.3 | Personal information collection limitation | Data minimization, collection justification |
| P1.4 | Use, retention, and disposal | Retention schedules, purpose limitation |
| P1.5 | Access rights for data subjects | DSR procedures, response tracking |
| P1.6 | Disclosure to third parties | Subprocessor agreements, DPAs |
| P1.7 | Data quality assurance | Accuracy procedures, correction workflows |
| P1.8 | Monitoring and enforcement | PIAs, compliance monitoring |

**Data Subject Rights:** Access (30 days), correction/rectification, deletion/erasure, portability (machine-readable), restrict processing, object to processing, automated decision-making transparency.

---

## Infrastructure Security Checks

### Cloud Provider Security

#### AWS Security Controls
| Control | AWS Service | SOC 2 Mapping |
|---------|-------------|---------------|
| Encryption at rest | KMS, S3 default encryption | CC6.1, C1.1 |
| Encryption in transit | ACM, ALB/NLB TLS termination | CC6.7, C1.1 |
| Access management | IAM, SSO, Organizations | CC6.1-CC6.3 |
| Logging | CloudTrail, CloudWatch, VPC Flow Logs | CC7.2, CC4.1 |
| Network security | Security Groups, NACLs, WAF | CC6.6 |
| Configuration compliance | AWS Config, Security Hub | CC4.1, CC5.2 |
| Backup | AWS Backup, S3 versioning | A1.2 |
| Secrets | Secrets Manager, Parameter Store | CC6.1 |

#### Azure Security Controls
| Control | Azure Service | SOC 2 Mapping |
|---------|---------------|---------------|
| Encryption at rest | Azure Key Vault, Storage encryption | CC6.1, C1.1 |
| Encryption in transit | Application Gateway, Front Door | CC6.7, C1.1 |
| Access management | Azure AD, PIM, Conditional Access | CC6.1-CC6.3 |
| Logging | Azure Monitor, Log Analytics, NSG Flow Logs | CC7.2, CC4.1 |
| Network security | NSGs, Azure Firewall, WAF | CC6.6 |
| Configuration compliance | Azure Policy, Defender for Cloud | CC4.1, CC5.2 |
| Backup | Azure Backup, geo-redundant storage | A1.2 |
| Secrets | Key Vault | CC6.1 |

#### GCP Security Controls
| Control | GCP Service | SOC 2 Mapping |
|---------|-------------|---------------|
| Encryption at rest | Cloud KMS, default encryption | CC6.1, C1.1 |
| Encryption in transit | Cloud Load Balancing, Certificate Manager | CC6.7, C1.1 |
| Access management | Cloud IAM, Identity Platform, BeyondCorp | CC6.1-CC6.3 |
| Logging | Cloud Audit Logs, Cloud Logging | CC7.2, CC4.1 |
| Network security | VPC Firewall, Cloud Armor | CC6.6 |
| Configuration compliance | Security Command Center, Policy Intelligence | CC4.1, CC5.2 |
| Backup | Cloud Storage, persistent disk snapshots | A1.2 |
| Secrets | Secret Manager | CC6.1 |

### DNS Security

| Check | Requirement | SOC 2 Mapping |
|-------|-------------|---------------|
| SPF | `v=spf1` record, `-all` qualifier | CC6.6, CC2.2 |
| DKIM | 2048-bit RSA minimum, annual key rotation | CC6.6, CC2.2 |
| DMARC | Policy `p=reject` or `p=quarantine` | CC6.6, CC2.2 |
| DNSSEC | Domain signed, DS records at registrar | CC6.6 |
| CAA | CAA records restricting certificate issuance | CC6.6 |

### TLS/SSL Configuration

| Check | Requirement | SOC 2 Mapping |
|-------|-------------|---------------|
| Minimum TLS | TLS 1.2 (TLS 1.3 preferred) | CC6.7 |
| Cipher suites | AEAD only (AES-GCM, ChaCha20-Poly1305) | CC6.7 |
| Certificate | SHA-256+, 2048-bit RSA or P-256 ECDSA | CC6.7 |
| HSTS | `max-age=31536000; includeSubDomains; preload` | CC6.7 |
| Certificate management | Automated renewal (Let's Encrypt, ACM) | CC6.7 |
| OCSP stapling | Enabled | CC6.7 |

### Endpoint Security

| Check | Requirement | SOC 2 Mapping |
|-------|-------------|---------------|
| MDM enrollment | All company devices enrolled | CC6.8 |
| Disk encryption | FileVault (macOS), BitLocker (Windows) | CC6.1, C1.1 |
| EDR/Antivirus | CrowdStrike, SentinelOne, or equivalent | CC6.8 |
| OS patching | Critical patches within 14 days | CC7.1 |
| Screen lock | Auto-lock after 5 minutes | CC6.1 |
| Firewall | Host firewall enabled | CC6.6 |
| USB restrictions | Removable media blocked or monitored | C1.1 |

### Network, Container, and CI/CD Security

**Network:** Production/staging/development segmented, WAF on public endpoints, DDoS protection, VPN/ZTNA for remote access, egress filtering.

**Container:** Image scanning on every build, minimal hardened base images, no privileged containers, private registry with access controls, K8s RBAC and network policies, external secrets operator.

**CI/CD:** GPG-signed commits, branch protection with PR approvals, SAST on every PR, DAST in staging, dependency scanning on every build, secret scanning (pre-commit + CI), SBOM generation, immutable deployment logs.

---

## Access Control Deep-Dive

### Identity Provider Configuration

**SSO:** SAML 2.0 or OIDC for all SaaS, centralized IdP (Okta, Azure AD, Google Workspace, OneLogin), JIT provisioning, group-based access, 8-12h max session duration.

**SCIM Provisioning:** Automated provisioning/deprovisioning, group sync, real-time deprovisioning on termination, attribute mapping standardization.

### MFA Enforcement

| Method | Security Level | Use Case |
|--------|----------------|----------|
| SMS/Voice | Not Acceptable | Deprecated - SIM swap risk |
| Email OTP | Not Acceptable | Phishing risk |
| TOTP | Acceptable | Standard user access |
| Push notification | Good | Standard user with IdP app |
| FIDO2/WebAuthn | Excellent | All users (phishing-resistant) |
| Hardware key (YubiKey) | Excellent | Privileged access, admin accounts |

### Privileged Access Management

**Just-in-Time (JIT) Access:** No standing privileged access, time-bound grants (max 8h), approval workflow, automated revocation, full session recording.

**Break-Glass Procedures:** Accounts in secure vault (sealed), dual-custody (two approvers), usage triggers immediate review, credentials rotated after use, annual testing.

**Service Account Governance:** Inventory with owners, no interactive login, 90-day API key rotation, quarterly reviews, no shared credentials, secrets in vault.

### Secret Rotation Schedule

| Secret Type | Maximum Lifetime | Rotation Method |
|-------------|-----------------|-----------------|
| API keys | 90 days | Automated via vault |
| Database credentials | 90 days | Dynamic secrets (Vault) |
| SSH keys | 1 year | Certificate-based preferred |
| TLS certificates | 1 year (90 days recommended) | Automated via ACME/ACM |
| Encryption keys | 1 year | Key management service |
| OAuth tokens | Per session | Refresh token rotation |
| Personal access tokens | 90 days | Developer self-service |

---

## Vendor and Third-Party Risk Management

### Vendor Risk Tiers

| Tier | SOC 2 Report | Security Questionnaire | Pen Test | Contract Review | Reassessment |
|------|-------------|----------------------|----------|----------------|--------------|
| Critical | Required | Full SIG | Review results | Full legal | Annual |
| High | Required | SIG Lite | Request summary | Security addendum | Annual |
| Medium | Preferred | Custom short-form | Not required | Standard terms | Biennial |
| Low | Not required | Not required | Not required | Standard terms | As needed |

### Contractual Requirements
- Data Processing Agreement (DPA)
- Security requirements addendum
- Right to audit clause
- Breach notification (24-72h)
- Data return/destruction on termination
- Subprocessor notification and approval
- Insurance requirements

---

## Employee Security Awareness Training

| Training Type | Audience | Frequency | Duration |
|---------------|----------|-----------|----------|
| Security awareness | All employees | Annual + onboarding | 30-60 min |
| Phishing simulation | All employees | Monthly | Ongoing |
| Secure development | Engineering | Annual | 2-4 hours |
| Incident response | IR team | Quarterly tabletop | 1-2 hours |
| Privacy awareness | Data handlers | Annual | 30-60 min |
| Privileged access | Admins/SREs | Annual | 1-2 hours |

**Tracking:** 100% completion required (30-day grace for new hires), LMS tracking, non-completion escalated to manager then HR, phishing failure triggers additional training.

---

## Incident Response Plan

### Severity Levels

| Severity | Definition | Response Time | Update Frequency |
|----------|-----------|---------------|-------------------|
| SEV1 | Critical business impact, data breach | 15 minutes | Every 30 minutes |
| SEV2 | Major impact, service degradation | 30 minutes | Every 1 hour |
| SEV3 | Moderate impact, partial degradation | 4 hours | Every 4 hours |
| SEV4 | Low impact, no customer effect | Next business day | Daily |

### Breach Notification Requirements
- Internal: Immediately upon confirmation
- Customer: Within 72 hours (per contract/regulation)
- Regulatory: Per applicable law (GDPR 72h, CCPA expedient)
- Law enforcement: As required by legal counsel
- Insurance carrier: Per policy terms (typically 24-48h)

---

## Business Continuity and Disaster Recovery

### DR Strategy by Tier

| Tier | RTO | RPO | Strategy | Example |
|------|-----|-----|----------|---------|
| Tier 1 | < 1h | < 15 min | Active-active multi-region | Core API, database |
| Tier 2 | < 4h | < 1h | Warm standby | Internal tools, admin |
| Tier 3 | < 24h | < 24h | Backup/restore | Reporting, analytics |
| Tier 4 | < 72h | < 72h | Rebuild from IaC | Dev/staging environments |

### DR Testing Requirements
- Full DR failover: Annual minimum
- Tabletop exercise: Semi-annual
- Backup restoration: Monthly
- Communication tree: Semi-annual
- Results documented with lessons learned
- RTO/RPO achievement tracking

---

## Common Audit Findings

| # | Finding | Severity | Remediation |
|---|---------|----------|-------------|
| 1 | Incomplete or untimely access reviews | High | Automate via IGA platform |
| 2 | Missing MFA for some systems | High | Enforce via IdP conditional access |
| 3 | Incomplete security awareness training | Medium | Automate enrollment and escalation |
| 4 | Change management bypasses | High | Enforce branch protection |
| 5 | Vendor SOC 2 reports not collected | Medium | Maintain vendor review calendar |
| 6 | Incomplete system description | Medium | Engage auditor early |
| 7 | Missing or outdated policies | Medium | Policy management tool + annual cycle |
| 8 | Insufficient logging coverage | High | Centralize in SIEM, alert on gaps |
| 9 | No DR testing evidence | High | Schedule semi-annual tests |
| 10 | Terminated user access not removed promptly | Critical | Automate via SCIM |

---

## SOC 2 Report Structure

### Report Components
1. **Section I:** Independent Service Auditor's Report (opinion letter)
2. **Section II:** Management's Assertion
3. **Section III:** Description of the System
4. **Section IV:** Trust Services Criteria, Controls, Tests, and Results (Type II)
5. **Section V:** Other Information (optional)

### Report Distribution
| Report | Content | Distribution |
|--------|---------|-------------|
| SOC 2 Type I | Control design at a point in time | Restricted use (NDA required) |
| SOC 2 Type II | Control design + operating effectiveness | Restricted use (NDA required) |
| SOC 3 | General use summary (no control details) | Public distribution |

**Best Practices:** Require mutual NDA, use secure portal (not email), track recipients, watermark with recipient name, share only current-period reports.

---
name: information-security-manager-iso27001
description: >
  ISO 27001 ISMS implementation and cybersecurity governance for HealthTech and
  MedTech companies. Use for ISMS design, security risk assessment, control
  implementation, ISO 27001 certification, security audits, incident response,
  and compliance verification. Covers ISO 27001, ISO 27002, healthcare security,
  and medical device cybersecurity.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: information-security
  updated: 2026-03-31
  tags: [iso-27001, isms, annex-a, information-security, cloud-security]
---
# Information Security Manager - ISO 27001

Implement and manage Information Security Management Systems (ISMS) aligned with ISO 27001:2022 and healthcare regulatory requirements.

---

## Table of Contents

- [Trigger Phrases](#trigger-phrases)
- [Quick Start](#quick-start)
- [Tools](#tools)
- [Workflows](#workflows)
- [Reference Guides](#reference-guides)
- [Validation Checkpoints](#validation-checkpoints)

---

## Trigger Phrases

Use this skill when you hear:
- "implement ISO 27001"
- "ISMS implementation"
- "security risk assessment"
- "information security policy"
- "ISO 27001 certification"
- "security controls implementation"
- "incident response plan"
- "healthcare data security"
- "medical device cybersecurity"
- "security compliance audit"

---

## Quick Start

### Run Security Risk Assessment

```bash
python scripts/risk_assessment.py --scope "patient-data-system" --output risk_register.json
```

### Check Compliance Status

```bash
python scripts/compliance_checker.py --standard iso27001 --controls-file controls.csv
```

### Generate Gap Analysis Report

```bash
python scripts/compliance_checker.py --standard iso27001 --gap-analysis --output gaps.md
```

---

## Tools

### risk_assessment.py

Automated security risk assessment following ISO 27001 Clause 6.1.2 methodology.

**Usage:**

```bash
# Full risk assessment
python scripts/risk_assessment.py --scope "cloud-infrastructure" --output risks.json

# Healthcare-specific assessment
python scripts/risk_assessment.py --scope "ehr-system" --template healthcare --output risks.json

# Quick asset-based assessment
python scripts/risk_assessment.py --assets assets.csv --output risks.json
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--scope` | Yes | System or area to assess |
| `--template` | No | Assessment template: `general`, `healthcare`, `cloud` |
| `--assets` | No | CSV file with asset inventory |
| `--output` | No | Output file (default: stdout) |
| `--format` | No | Output format: `json`, `csv`, `markdown` |

**Output:**
- Asset inventory with classification
- Threat and vulnerability mapping
- Risk scores (likelihood × impact)
- Treatment recommendations
- Residual risk calculations

### compliance_checker.py

Verify ISO 27001/27002 control implementation status.

**Usage:**

```bash
# Check all ISO 27001 controls
python scripts/compliance_checker.py --standard iso27001

# Gap analysis with recommendations
python scripts/compliance_checker.py --standard iso27001 --gap-analysis

# Check specific control domains
python scripts/compliance_checker.py --standard iso27001 --domains "access-control,cryptography"

# Export compliance report
python scripts/compliance_checker.py --standard iso27001 --output compliance_report.md
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--standard` | Yes | Standard to check: `iso27001`, `iso27002`, `hipaa` |
| `--controls-file` | No | CSV with current control status |
| `--gap-analysis` | No | Include remediation recommendations |
| `--domains` | No | Specific control domains to check |
| `--output` | No | Output file path |

**Output:**
- Control implementation status
- Compliance percentage by domain
- Gap analysis with priorities
- Remediation recommendations

---

## Workflows

### Workflow 1: ISMS Implementation

**Step 1: Define Scope and Context**

Document organizational context and ISMS boundaries:
- Identify interested parties and requirements
- Define ISMS scope and boundaries
- Document internal/external issues

**Validation:** Scope statement reviewed and approved by management.

**Step 2: Conduct Risk Assessment**

```bash
python scripts/risk_assessment.py --scope "full-organization" --template general --output initial_risks.json
```

- Identify information assets
- Assess threats and vulnerabilities
- Calculate risk levels
- Determine risk treatment options

**Validation:** Risk register contains all critical assets with assigned owners.

**Step 3: Select and Implement Controls**

Map risks to ISO 27002 controls:

```bash
python scripts/compliance_checker.py --standard iso27002 --gap-analysis --output control_gaps.md
```

Control categories:
- Organizational (policies, roles, responsibilities)
- People (screening, awareness, training)
- Physical (perimeters, equipment, media)
- Technological (access, crypto, network, application)

**Validation:** Statement of Applicability (SoA) documents all controls with justification.

**Step 4: Establish Monitoring**

Define security metrics:
- Incident count and severity trends
- Control effectiveness scores
- Training completion rates
- Audit findings closure rate

**Validation:** Dashboard shows real-time compliance status.

### Workflow 2: Security Risk Assessment

**Step 1: Asset Identification**

Create asset inventory:

| Asset Type | Examples | Classification |
|------------|----------|----------------|
| Information | Patient records, source code | Confidential |
| Software | EHR system, APIs | Critical |
| Hardware | Servers, medical devices | High |
| Services | Cloud hosting, backup | High |
| People | Admin accounts, developers | Varies |

**Validation:** All assets have assigned owners and classifications.

**Step 2: Threat Analysis**

Identify threats per asset category:

| Asset | Threats | Likelihood |
|-------|---------|------------|
| Patient data | Unauthorized access, breach | High |
| Medical devices | Malware, tampering | Medium |
| Cloud services | Misconfiguration, outage | Medium |
| Credentials | Phishing, brute force | High |

**Validation:** Threat model covers top-10 industry threats.

**Step 3: Vulnerability Assessment**

```bash
python scripts/risk_assessment.py --scope "network-infrastructure" --output vuln_risks.json
```

Document vulnerabilities:
- Technical (unpatched systems, weak configs)
- Process (missing procedures, gaps)
- People (lack of training, insider risk)

**Validation:** Vulnerability scan results mapped to risk register.

**Step 4: Risk Evaluation and Treatment**

Calculate risk: `Risk = Likelihood × Impact`

| Risk Level | Score | Treatment |
|------------|-------|-----------|
| Critical | 20-25 | Immediate action required |
| High | 15-19 | Treatment plan within 30 days |
| Medium | 10-14 | Treatment plan within 90 days |
| Low | 5-9 | Accept or monitor |
| Minimal | 1-4 | Accept |

**Validation:** All high/critical risks have approved treatment plans.

### Workflow 3: Incident Response

**Step 1: Detection and Reporting**

Incident categories:
- Security breach (unauthorized access)
- Malware infection
- Data leakage
- System compromise
- Policy violation

**Validation:** Incident logged within 15 minutes of detection.

**Step 2: Triage and Classification**

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| Critical | Data breach, system down | Immediate |
| High | Active threat, significant risk | 1 hour |
| Medium | Contained threat, limited impact | 4 hours |
| Low | Minor violation, no impact | 24 hours |

**Validation:** Severity assigned and escalation triggered if needed.

**Step 3: Containment and Eradication**

Immediate actions:
1. Isolate affected systems
2. Preserve evidence
3. Block threat vectors
4. Remove malicious artifacts

**Validation:** Containment confirmed, no ongoing compromise.

**Step 4: Recovery and Lessons Learned**

Post-incident activities:
1. Restore systems from clean backups
2. Verify integrity before reconnection
3. Document timeline and actions
4. Conduct post-incident review
5. Update controls and procedures

**Validation:** Post-incident report completed within 5 business days.

---

## Reference Guides

### When to Use Each Reference

**references/iso27001-controls.md**
- Control selection for SoA
- Implementation guidance
- Evidence requirements
- Audit preparation

**references/risk-assessment-guide.md**
- Risk methodology selection
- Asset classification criteria
- Threat modeling approaches
- Risk calculation methods

**references/incident-response.md**
- Response procedures
- Escalation matrices
- Communication templates
- Recovery checklists

---

## Validation Checkpoints

### ISMS Implementation Validation

| Phase | Checkpoint | Evidence Required |
|-------|------------|-------------------|
| Scope | Scope approved | Signed scope document |
| Risk | Register complete | Risk register with owners |
| Controls | SoA approved | Statement of Applicability |
| Operation | Metrics active | Dashboard screenshots |
| Audit | Internal audit done | Audit report |

### Certification Readiness

Before Stage 1 audit:
- [ ] ISMS scope documented and approved
- [ ] Information security policy published
- [ ] Risk assessment completed
- [ ] Statement of Applicability finalized
- [ ] Internal audit conducted
- [ ] Management review completed
- [ ] Nonconformities addressed

Before Stage 2 audit:
- [ ] Controls implemented and operational
- [ ] Evidence of effectiveness available
- [ ] Staff trained and aware
- [ ] Incidents logged and managed
- [ ] Metrics collected for 3+ months

### Compliance Verification

Run periodic checks:

```bash
# Monthly compliance check
python scripts/compliance_checker.py --standard iso27001 --output monthly_$(date +%Y%m).md

# Quarterly gap analysis
python scripts/compliance_checker.py --standard iso27001 --gap-analysis --output quarterly_gaps.md
```

---

## Worked Example: Healthcare Risk Assessment

**Scenario:** Assess security risks for a patient data management system.

### Step 1: Define Assets

```bash
python scripts/risk_assessment.py --scope "patient-data-system" --template healthcare
```

**Asset inventory output:**

| Asset ID | Asset | Type | Owner | Classification |
|----------|-------|------|-------|----------------|
| A001 | Patient database | Information | DBA Team | Confidential |
| A002 | EHR application | Software | App Team | Critical |
| A003 | Database server | Hardware | Infra Team | High |
| A004 | Admin credentials | Access | Security | Critical |

### Step 2: Identify Risks

**Risk register output:**

| Risk ID | Asset | Threat | Vulnerability | L | I | Score |
|---------|-------|--------|---------------|---|---|-------|
| R001 | A001 | Data breach | Weak encryption | 3 | 5 | 15 |
| R002 | A002 | SQL injection | Input validation | 4 | 4 | 16 |
| R003 | A004 | Credential theft | No MFA | 4 | 5 | 20 |

### Step 3: Determine Treatment

| Risk | Treatment | Control | Timeline |
|------|-----------|---------|----------|
| R001 | Mitigate | Implement AES-256 encryption | 30 days |
| R002 | Mitigate | Add input validation, WAF | 14 days |
| R003 | Mitigate | Enforce MFA for all admins | 7 days |

### Step 4: Verify Implementation

```bash
python scripts/compliance_checker.py --controls-file implemented_controls.csv
```

**Verification output:**

```
Control Implementation Status
=============================
Cryptography (A.8.24): IMPLEMENTED
  - AES-256 at rest: YES
  - TLS 1.3 in transit: YES

Access Control (A.8.5): IMPLEMENTED
  - MFA enabled: YES
  - Admin accounts: 100% coverage

Application Security (A.8.26): PARTIAL
  - Input validation: YES
  - WAF deployed: PENDING

Overall Compliance: 87%
```

---

## ISO 27001:2022 Annex A Controls — Complete Reference

The 2022 revision restructured controls from 14 domains (114 controls) to 4 themes (93 controls). All organizations must update their Statement of Applicability (SoA) accordingly.

### Theme 1: Organizational Controls (37 controls)

| Control | Title | Priority |
|---------|-------|----------|
| A.5.1 | Policies for information security | High |
| A.5.2 | Information security roles and responsibilities | High |
| A.5.3 | Segregation of duties | High |
| A.5.4 | Management responsibilities | Medium |
| A.5.5 | Contact with authorities | Medium |
| A.5.6 | Contact with special interest groups | Low |
| A.5.7 | Threat intelligence | High |
| A.5.8 | Information security in project management | Medium |
| A.5.9 | Inventory of information and other associated assets | High |
| A.5.10 | Acceptable use of information and other associated assets | Medium |
| A.5.11 | Return of assets | Low |
| A.5.12 | Classification of information | High |
| A.5.13 | Labelling of information | Medium |
| A.5.14 | Information transfer | High |
| A.5.15 | Access control | High |
| A.5.16 | Identity management | High |
| A.5.17 | Authentication information | High |
| A.5.18 | Access rights | High |
| A.5.19 | Information security in supplier relationships | High |
| A.5.20 | Addressing information security within supplier agreements | High |
| A.5.21 | Managing information security in the ICT supply chain | High |
| A.5.22 | Monitoring, review and change management of supplier services | Medium |
| A.5.23 | Information security for use of cloud services | High |
| A.5.24 | Information security incident management planning and preparation | High |
| A.5.25 | Assessment and decision on information security events | Medium |
| A.5.26 | Response to information security incidents | High |
| A.5.27 | Learning from information security incidents | Medium |
| A.5.28 | Collection of evidence | Medium |
| A.5.29 | Information security during disruption | High |
| A.5.30 | ICT readiness for business continuity | High |
| A.5.31 | Legal, statutory, regulatory and contractual requirements | High |
| A.5.32 | Intellectual property rights | Medium |
| A.5.33 | Protection of records | Medium |
| A.5.34 | Privacy and protection of PII | High |
| A.5.35 | Independent review of information security | Medium |
| A.5.36 | Compliance with policies, rules and standards for information security | Medium |
| A.5.37 | Documented operating procedures | Medium |

### Theme 2: People Controls (8 controls)

| Control | Title | Priority |
|---------|-------|----------|
| A.6.1 | Screening | High |
| A.6.2 | Terms and conditions of employment | High |
| A.6.3 | Information security awareness, education and training | High |
| A.6.4 | Disciplinary process | Medium |
| A.6.5 | Responsibilities after termination or change of employment | Medium |
| A.6.6 | Confidentiality or non-disclosure agreements | High |
| A.6.7 | Remote working | High |
| A.6.8 | Information security event reporting | High |

### Theme 3: Physical Controls (14 controls)

| Control | Title | Priority |
|---------|-------|----------|
| A.7.1 | Physical security perimeters | High |
| A.7.2 | Physical entry | High |
| A.7.3 | Securing offices, rooms and facilities | Medium |
| A.7.4 | Physical security monitoring | Medium |
| A.7.5 | Protecting against physical and environmental threats | Medium |
| A.7.6 | Working in secure areas | Medium |
| A.7.7 | Clear desk and clear screen | Medium |
| A.7.8 | Equipment siting and protection | Medium |
| A.7.9 | Security of assets off-premises | Medium |
| A.7.10 | Storage media | High |
| A.7.11 | Supporting utilities | Medium |
| A.7.12 | Cabling security | Low |
| A.7.13 | Equipment maintenance | Medium |
| A.7.14 | Secure disposal or re-use of equipment | High |

### Theme 4: Technological Controls (34 controls)

| Control | Title | Priority |
|---------|-------|----------|
| A.8.1 | User endpoint devices | High |
| A.8.2 | Privileged access rights | High |
| A.8.3 | Information access restriction | High |
| A.8.4 | Access to source code | Medium |
| A.8.5 | Secure authentication | High |
| A.8.6 | Capacity management | Medium |
| A.8.7 | Protection against malware | High |
| A.8.8 | Management of technical vulnerabilities | High |
| A.8.9 | Configuration management | High |
| A.8.10 | Information deletion | Medium |
| A.8.11 | Data masking | Medium |
| A.8.12 | Data leakage prevention | High |
| A.8.13 | Information backup | High |
| A.8.14 | Redundancy of information processing facilities | Medium |
| A.8.15 | Logging | High |
| A.8.16 | Monitoring activities | High |
| A.8.17 | Clock synchronization | Low |
| A.8.18 | Use of privileged utility programs | Medium |
| A.8.19 | Installation of software on operational systems | Medium |
| A.8.20 | Networks security | High |
| A.8.21 | Security of network services | High |
| A.8.22 | Segregation of networks | High |
| A.8.23 | Web filtering | Medium |
| A.8.24 | Use of cryptography | High |
| A.8.25 | Secure development life cycle | High |
| A.8.26 | Application security requirements | High |
| A.8.27 | Secure system architecture and engineering principles | High |
| A.8.28 | Secure coding | High |
| A.8.29 | Security testing in development and acceptance | High |
| A.8.30 | Outsourced development | Medium |
| A.8.31 | Separation of development, test and production environments | High |
| A.8.32 | Change management | High |
| A.8.33 | Test information | Medium |
| A.8.34 | Protection of information systems during audit testing | Low |

### New Controls in ISO 27001:2022

11 controls are entirely new in the 2022 revision:

| Control | Title | Why It Was Added |
|---------|-------|------------------|
| A.5.7 | Threat intelligence | Proactive threat awareness |
| A.5.23 | Information security for use of cloud services | Cloud adoption governance |
| A.5.30 | ICT readiness for business continuity | IT-specific continuity planning |
| A.7.4 | Physical security monitoring | Enhanced surveillance requirements |
| A.8.9 | Configuration management | Baseline security configurations |
| A.8.10 | Information deletion | Data lifecycle and privacy |
| A.8.11 | Data masking | Privacy-preserving techniques |
| A.8.12 | Data leakage prevention | DLP as explicit requirement |
| A.8.16 | Monitoring activities | Active security monitoring |
| A.8.23 | Web filtering | Web-based threat mitigation |
| A.8.28 | Secure coding | Development security practices |

---

## Cross-Reference: SOC 2 Control Mapping

Map ISO 27001:2022 controls to SOC 2 Trust Services Criteria for organizations requiring both certifications:

| SOC 2 Trust Criteria | ISO 27001:2022 Controls | Notes |
|----------------------|------------------------|-------|
| CC1 — Control Environment | A.5.1, A.5.2, A.5.4, A.6.2 | Governance and organizational structure |
| CC2 — Communication and Information | A.5.14, A.6.3, A.6.8, A.5.37 | Internal/external communication |
| CC3 — Risk Assessment | A.5.7, Clause 6.1.2 (risk assessment) | Threat identification and analysis |
| CC4 — Monitoring Activities | A.8.15, A.8.16, A.5.35, A.5.36 | Logging, monitoring, compliance |
| CC5 — Control Activities | A.5.15-A.5.18, A.8.1-A.8.5 | Access control and authentication |
| CC6 — Logical and Physical Access | A.5.15, A.7.1, A.7.2, A.8.2, A.8.3 | Access management |
| CC7 — System Operations | A.8.7, A.8.8, A.8.9, A.8.32 | Change management, malware, vulnerability management |
| CC8 — Change Management | A.8.25, A.8.32, A.8.31 | SDLC, change control, environment separation |
| CC9 — Risk Mitigation | A.5.19-A.5.22, A.8.30 | Vendor/supplier risk management |
| Availability | A.5.29, A.5.30, A.8.6, A.8.14 | Business continuity, capacity, redundancy |
| Confidentiality | A.5.12, A.5.13, A.8.11, A.8.12, A.8.24 | Classification, DLP, encryption |
| Processing Integrity | A.8.25-A.8.29, A.8.33 | Secure development, testing |
| Privacy | A.5.34, A.8.10, A.8.11 | PII protection, deletion, masking |

> **See also:** `../soc2-compliance-specialist/SKILL.md` for full SOC 2 compliance workflows.

---

## Cross-Reference: NIS2 Directive Alignment

The NIS2 Directive (EU 2022/2555) mandates cybersecurity measures for essential and important entities, including healthcare organizations. ISO 27001 provides a strong foundation for NIS2 compliance:

| NIS2 Requirement (Art. 21) | ISO 27001:2022 Controls | Gap Analysis |
|---------------------------|------------------------|--------------|
| (a) Risk analysis and IS policies | Clause 6.1.2, A.5.1 | Fully covered |
| (b) Incident handling | A.5.24-A.5.28 | Add NIS2 reporting timelines (24h/72h) |
| (c) Business continuity and crisis management | A.5.29, A.5.30 | Add crisis management procedures |
| (d) Supply chain security | A.5.19-A.5.22 | Strengthen ICT supply chain assessment |
| (e) Security in network and IS acquisition | A.8.25-A.8.29 | Add vulnerability handling and disclosure |
| (f) Policies for assessing cybersecurity effectiveness | A.5.35, A.5.36 | Add metrics-based effectiveness measurement |
| (g) Basic cyber hygiene and training | A.6.3, A.6.8 | Covered |
| (h) Policies on use of cryptography and encryption | A.8.24 | Covered |
| (i) Human resources security and access control | A.5.15-A.5.18, A.6.1-A.6.8 | Covered |
| (j) Multi-factor authentication and secure communications | A.8.5, A.8.20-A.8.22 | Ensure MFA enforced for all critical systems |

**NIS2-specific additions beyond ISO 27001:**
- **Incident reporting:** 24-hour early warning to CSIRT, 72-hour incident notification, 1-month final report
- **Management accountability:** Senior management must approve cybersecurity measures and undergo training
- **Penalties:** Up to EUR 10M or 2% of global turnover for essential entities
- **Supply chain:** Must assess each direct supplier's cybersecurity practices

> **See also:** `../nis2-compliance-specialist/SKILL.md` for complete NIS2 implementation workflows.

---

## Cloud Security Controls

### AWS-Specific Controls

| ISO 27001 Control | AWS Implementation | Service |
|-------------------|-------------------|---------|
| A.5.23 Cloud services | AWS Organizations, SCPs | AWS Organizations |
| A.8.2 Privileged access | IAM roles, permission boundaries | AWS IAM |
| A.8.3 Access restriction | Resource policies, VPC endpoints | IAM, VPC |
| A.8.5 Secure authentication | IAM Identity Center, MFA | IAM |
| A.8.9 Configuration management | AWS Config rules, conformance packs | AWS Config |
| A.8.12 Data leakage prevention | Macie, S3 Block Public Access | Macie |
| A.8.13 Information backup | AWS Backup, cross-region replication | AWS Backup |
| A.8.15 Logging | CloudTrail, CloudWatch Logs | CloudTrail |
| A.8.16 Monitoring | GuardDuty, Security Hub | GuardDuty |
| A.8.20 Network security | Security Groups, NACLs, WAF | VPC, WAF |
| A.8.22 Network segregation | VPC subnets, Transit Gateway | VPC |
| A.8.24 Cryptography | KMS, CloudHSM, ACM | KMS |

### Azure-Specific Controls

| ISO 27001 Control | Azure Implementation | Service |
|-------------------|---------------------|---------|
| A.5.23 Cloud services | Management Groups, Azure Policy | Azure Policy |
| A.8.2 Privileged access | PIM, RBAC, Conditional Access | Entra ID |
| A.8.5 Secure authentication | Entra ID MFA, passwordless | Entra ID |
| A.8.9 Configuration management | Azure Policy, Blueprints | Azure Policy |
| A.8.12 Data leakage prevention | Microsoft Purview DLP | Purview |
| A.8.15 Logging | Azure Monitor, Log Analytics | Monitor |
| A.8.16 Monitoring | Microsoft Defender for Cloud | Defender |
| A.8.20 Network security | NSGs, Azure Firewall, Front Door WAF | Network |
| A.8.24 Cryptography | Azure Key Vault, Managed HSM | Key Vault |

### GCP-Specific Controls

| ISO 27001 Control | GCP Implementation | Service |
|-------------------|-------------------|---------|
| A.5.23 Cloud services | Organization policies, Resource Manager | Resource Manager |
| A.8.2 Privileged access | IAM, Workload Identity | Cloud IAM |
| A.8.5 Secure authentication | Identity Platform, 2-Step Verification | Identity |
| A.8.9 Configuration management | Security Health Analytics, Assured Workloads | SCC |
| A.8.12 Data leakage prevention | Cloud DLP (Sensitive Data Protection) | DLP |
| A.8.15 Logging | Cloud Audit Logs, Cloud Logging | Logging |
| A.8.16 Monitoring | Security Command Center, Chronicle SIEM | SCC |
| A.8.20 Network security | VPC firewall rules, Cloud Armor | VPC, Cloud Armor |
| A.8.24 Cryptography | Cloud KMS, Cloud HSM, CMEK | Cloud KMS |

---

## Zero Trust Architecture Integration

Align ISO 27001 controls with Zero Trust principles (NIST SP 800-207):

### Zero Trust Pillars Mapped to ISO 27001

| Zero Trust Pillar | Principle | ISO 27001 Controls | Implementation |
|-------------------|-----------|-------------------|----------------|
| Identity | Verify explicitly | A.5.16, A.5.17, A.8.5 | MFA everywhere, continuous authentication, identity governance |
| Devices | Validate device health | A.8.1, A.8.7, A.8.9 | Endpoint detection and response (EDR), device compliance checks |
| Networks | Segment and encrypt | A.8.20-A.8.22, A.8.24 | Microsegmentation, mTLS, encrypted tunnels |
| Applications | Secure by design | A.8.25-A.8.29 | SAST/DAST, runtime protection, API security |
| Data | Classify and protect | A.5.12, A.5.13, A.8.11, A.8.12 | Data classification, DLP, rights management |
| Visibility | Monitor and analyze | A.8.15, A.8.16, A.5.7 | SIEM/SOAR, threat intelligence, behavioral analytics |

### Zero Trust Implementation Roadmap

```
Phase 1: Foundation (0-6 months)
├── Implement identity provider with MFA for all users
├── Deploy EDR on all endpoints
├── Enable centralized logging and SIEM
└── Classify critical data assets

Phase 2: Enhancement (6-12 months)
├── Implement network microsegmentation
├── Deploy conditional access policies
├── Enable continuous device compliance monitoring
└── Implement DLP for classified data

Phase 3: Maturation (12-18 months)
├── Deploy zero-trust network access (ZTNA) replacing VPN
├── Implement just-in-time (JIT) privileged access
├── Enable automated threat response (SOAR)
└── Continuous verification with behavioral analytics
```

---

## Hardware Security Key Requirements

### FIDO2/WebAuthn Implementation

For high-assurance authentication per A.5.17 and A.8.5:

| Requirement | Specification | Priority |
|-------------|---------------|----------|
| Admin accounts | Hardware security key (YubiKey 5, Titan) mandatory | Critical |
| Developer accounts | Hardware key or platform authenticator | High |
| All employees | Hardware key recommended; MFA minimum | Medium |
| Service accounts | Certificate-based or workload identity | High |

**Supported standards:**
- FIDO2 / WebAuthn (passwordless primary authentication)
- FIDO U2F (second-factor authentication)
- PIV/Smart Card (legacy enterprise systems)
- TOTP (fallback only — hardware keys preferred)

**Deployment checklist:**
- [ ] Procure minimum 2 hardware keys per critical user (primary + backup)
- [ ] Register keys with identity provider (Entra ID, Okta, Google Workspace)
- [ ] Enforce phishing-resistant MFA policy for privileged access
- [ ] Disable SMS/voice MFA for admin accounts
- [ ] Document key recovery procedures
- [ ] Test break-glass procedures with backup keys

---

## Supply Chain Security Controls

### ICT Supply Chain Risk Management (A.5.19-A.5.22)

| Control Area | Requirements | Evidence |
|-------------|-------------|----------|
| Supplier assessment | Security questionnaire + evidence review | Completed assessment scorecard |
| Contractual requirements | Security clauses in all vendor agreements | Signed agreements with security schedule |
| Software supply chain | SBOM requirements, dependency scanning | SBOM in CycloneDX/SPDX format |
| Continuous monitoring | Monitor supplier security posture changes | Quarterly supplier security reviews |
| Incident notification | Require supplier breach notification within 24 hours | Contractual clause + test exercises |

### Software Bill of Materials (SBOM) Requirements

| Element | Description | Standard |
|---------|-------------|----------|
| Component inventory | All direct and transitive dependencies | CycloneDX or SPDX |
| Vulnerability tracking | Map components to known CVEs | OSV, NVD integration |
| License compliance | Track all open-source licenses | SPDX license identifiers |
| Update cadence | Regenerate SBOM on every release | CI/CD integration |
| Sharing | Provide SBOM to customers on request | Machine-readable format |

### Third-Party Risk Tiers

| Tier | Access Level | Assessment Frequency | Assessment Depth |
|------|-------------|---------------------|-----------------|
| Critical | Processes/stores sensitive data, system access | Annual on-site + continuous monitoring | Full security audit, penetration test review |
| High | Access to internal systems or non-sensitive data | Annual questionnaire + evidence | Security questionnaire + SOC 2 report review |
| Medium | Limited access, SaaS tools | Biennial questionnaire | Security questionnaire |
| Low | No data access, no system access | On onboarding | Basic due diligence |

---

## Cross-Framework Mapping Table

| Requirement Area | ISO 27001:2022 | SOC 2 TSC | NIST CSF 2.0 | NIS2 (Art. 21) |
|-----------------|----------------|-----------|--------------|----------------|
| Governance | A.5.1-A.5.4 | CC1.1-CC1.5 | GV.OC, GV.RM | Art. 20 |
| Risk management | Clause 6.1.2, A.5.7 | CC3.1-CC3.4 | ID.RA | Art. 21(2)(a) |
| Access control | A.5.15-A.5.18, A.8.2-A.8.5 | CC6.1-CC6.8 | PR.AA | Art. 21(2)(i) |
| Incident management | A.5.24-A.5.28 | CC7.3-CC7.5 | RS.MA, RS.AN | Art. 21(2)(b), Art. 23 |
| Business continuity | A.5.29-A.5.30 | A1.1-A1.3 | RC.RP | Art. 21(2)(c) |
| Supply chain | A.5.19-A.5.22 | CC9.1-CC9.2 | GV.SC | Art. 21(2)(d) |
| Cryptography | A.8.24 | CC6.1, CC6.7 | PR.DS | Art. 21(2)(h) |
| Network security | A.8.20-A.8.22 | CC6.6 | PR.IR | Art. 21(2)(e) |
| Vulnerability management | A.8.8 | CC7.1 | ID.RA-01 | Art. 21(2)(e) |
| Awareness and training | A.6.3 | CC1.4 | PR.AT | Art. 21(2)(g) |
| Logging and monitoring | A.8.15-A.8.16 | CC7.2 | DE.CM, DE.AE | Art. 21(2)(f) |
| Data protection | A.5.34, A.8.10-A.8.12 | P1-P8 | PR.DS | Art. 21(2)(e) |
| Secure development | A.8.25-A.8.29 | CC8.1 | PR.DS | Art. 21(2)(e) |
| Asset management | A.5.9-A.5.11 | CC6.1 | ID.AM | Art. 21(2)(a) |

> **Cross-references:** See `../gdpr-dsgvo-expert/SKILL.md` for GDPR privacy controls mapping, and `../risk-management-specialist/SKILL.md` for ISO 14971 risk management integration with ISO 27001.

---

## ISO 27001:2022 Enhanced Controls & Cross-Framework Integration

### Annex A Control Themes (93 Controls)

| Theme | Controls | Key Areas |
|-------|----------|-----------|
| **Organizational (37)** | A.5.1-A.5.37 | Policies, roles, threat intelligence, asset management, access, supplier security |
| **People (8)** | A.6.1-A.6.8 | Screening, T&C, awareness, disciplinary, termination, remote work, reporting |
| **Physical (14)** | A.7.1-A.7.14 | Perimeters, entry, offices, monitoring, utilities, cabling, equipment, storage media |
| **Technological (34)** | A.8.1-A.8.34 | Endpoints, access, authentication, code, config, data, backup, logging, networks, web |

### Hardware Security Key Requirements

- **YubiKey 5 Series:** Required for admin accounts, cloud console access, VPN, code signing
- **FIDO2/WebAuthn:** Phishing-resistant MFA for all users within 90 days of ISMS deployment
- **Policy:** SMS/voice MFA PROHIBITED (SIM swapping risk). TOTP acceptable as interim for non-admin
- **Backup Keys:** Minimum 2 hardware keys per user (primary + backup stored securely)
- **Recovery:** Manager approval + identity verification required for key replacement

### Zero Trust Architecture Integration

- **Never Trust, Always Verify:** All access decisions based on identity, device, and context
- **Microsegmentation:** Network segmentation at workload level, not just network perimeter
- **Least Privilege:** Just-in-time access, time-bounded permissions, automated deprovisioning
- **Continuous Verification:** Session-level authentication, device health checks, behavioral analytics

### Cross-Framework Mapping (ISO 27001 ↔ SOC 2 ↔ NIST CSF ↔ NIS2)

| ISO 27001 | SOC 2 TSC | NIST CSF 2.0 | NIS2 Art.21 |
|-----------|-----------|-------------|-------------|
| A.5.1 Policies | CC1.1 | GV.PO | Art.21.2.a |
| A.5.23 Cloud security | CC6.7 | PR.DS | Art.21.2.e |
| A.5.24 Incident mgmt | CC7.4 | RS.MA | Art.21.2.b |
| A.6.3 Awareness | CC1.4 | PR.AT | Art.21.2.g |
| A.8.5 Authentication | CC6.1 | PR.AA | Art.21.2.j |
| A.8.9 Config mgmt | CC8.1 | PR.PS | Art.21.2.e |
| A.8.15 Logging | CC7.2 | DE.CM | Art.21.2.b |
| A.8.24 Cryptography | CC6.7 | PR.DS | Art.21.2.h |

### Supply Chain Security Controls

- **Supplier Risk Assessment:** Due diligence before onboarding, annual reassessment
- **Contractual Security Clauses:** Data protection, incident reporting, audit rights, exit terms
- **Continuous Monitoring:** Vendor security ratings, certificate expiry alerts, breach notifications
- **SBOM Requirements:** Software Bill of Materials for all third-party software components

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| Compliance checker shows low score despite documented policies | Controls documented but not implemented or operating effectively; evidence of operation missing | Focus on evidence of control operation (logs, reports, screenshots) rather than just policy documents; run `compliance_checker.py --gap-analysis` to identify implementation gaps |
| Risk assessment generates excessive number of high/critical risks | Asset classification overly conservative or threat likelihood ratings not calibrated to organization context | Calibrate likelihood and impact scales to actual organizational experience; review threat catalog against industry benchmarks; use `--template healthcare` or `--template cloud` for context-appropriate threat catalogs |
| Stage 1 audit identifies significant documentation gaps | ISMS documentation not aligned with ISO 27001:2022 clause structure or missing mandatory documented information | Review the 2022 mandatory documentation list (information security policy, SoA, risk assessment methodology, risk treatment plan); ensure clause 4-10 documentation uses the 2022 structure |
| Transitioning from ISO 27001:2013 -- controls do not map | 2022 revision restructured 114 controls into 93 across 4 themes; some controls merged or renamed | Use the 11 new controls list as starting point; map merged controls; update Statement of Applicability to reflect 4-theme structure (Organizational, People, Physical, Technological) |
| Cloud security controls insufficient for multi-cloud environment | Generic controls applied without cloud-provider-specific implementation | Map ISO 27001 controls to provider-specific services (AWS: GuardDuty, Config; Azure: Defender, Policy; GCP: SCC, DLP); use the cloud-specific control tables in this skill |
| Zero Trust implementation conflicts with existing network architecture | Legacy perimeter-based security model incompatible with microsegmentation | Follow the phased Zero Trust roadmap (Foundation 0-6mo, Enhancement 6-12mo, Maturation 12-18mo); start with identity and MFA before network changes |
| Supply chain security assessment overwhelmed by vendor count | No vendor risk tiering applied; all vendors assessed at same depth | Apply the Third-Party Risk Tiers (Critical, High, Medium, Low); focus full security audits on Critical tier; use questionnaires for Medium/Low |

---

## Success Criteria

- **Overall compliance score above 85%** -- as measured by `compliance_checker.py`, with all high-priority controls implemented and operating effectively
- **Risk register complete with assigned owners for all high/critical risks** -- every risk assessed using Likelihood x Impact methodology with documented treatment plans and target remediation dates
- **Statement of Applicability current and approved** -- covering all 93 Annex A controls with justification for inclusion/exclusion, aligned with the 2022 four-theme structure
- **Internal audit conducted annually** -- covering all ISMS clauses (4-10) and all Annex A controls within the 3-year certification cycle, with findings documented and corrective actions tracked
- **Management review completed with documented outputs** -- including ISMS performance metrics, audit findings, risk treatment status, and improvement decisions
- **Security awareness training completion rate above 95%** -- all personnel trained annually with records maintained; specialized training for security and IT staff
- **Incident response tested and validated** -- at least one tabletop exercise or simulation annually; post-incident reviews conducted for all actual incidents; lessons learned documented and implemented

---

## Scope & Limitations

**In Scope:**
- ISO 27001:2022 ISMS implementation guidance including all 93 Annex A controls across 4 themes
- Security risk assessment following ISO 27001 Clause 6.1.2 methodology with configurable threat catalogs (general, healthcare, cloud)
- Compliance checking and gap analysis against ISO 27001 and ISO 27002 controls
- Cross-framework mapping to SOC 2 TSC, NIST CSF 2.0, and NIS2 Directive
- Cloud-specific security controls for AWS, Azure, and GCP
- Zero Trust architecture integration with phased implementation roadmap
- Hardware security key (FIDO2/WebAuthn) requirements and deployment guidance
- Supply chain security controls including SBOM requirements and vendor risk tiering

**Out of Scope:**
- ISO 27001 certification audit execution -- this skill provides preparation guidance, not audit services
- Implementation of specific security tools (SIEM, EDR, DLP, WAF) -- this skill maps requirements to tool categories
- Penetration testing or vulnerability scanning execution -- use `infrastructure-compliance-auditor` for technical checks
- ISO 27701 (privacy information management), ISO 27017 (cloud security), or ISO 27018 (cloud privacy) implementation beyond cross-reference
- Physical security system design or installation beyond control requirements

**Important Notes:**
- The ISO 27001:2013 to 2022 transition deadline was October 2025; all certifications must now conform to the 2022 edition
- The 2022 revision introduced 11 entirely new controls, notably A.5.7 (Threat intelligence), A.5.23 (Cloud services), A.8.9 (Configuration management), A.8.16 (Monitoring activities), and A.8.28 (Secure coding)
- Integration with other standards (ISO 27701, ISO 42001, ISO 9001) via the harmonized Annex SL structure is becoming standard practice

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `isms-audit-expert` | Internal and external ISMS audit management; control testing and finding management | When planning or executing ISO 27001 audits and tracking corrective actions |
| `infrastructure-compliance-auditor` | Technical infrastructure checks validate ISO 27001 Annex A technological controls | When assessing actual infrastructure security posture against ISO 27001 requirements |
| `soc2-compliance-expert` | SOC 2 Trust Services Criteria mapped to ISO 27001 controls for dual compliance | When organization requires both ISO 27001 certification and SOC 2 Type II report |
| `gdpr-dsgvo-expert` | GDPR Art. 32 security of processing aligned with ISO 27001 controls; A.5.34 PII protection | When ISMS must support GDPR compliance requirements |
| `nist-csf-specialist` | NIST CSF 2.0 functions mapped to ISO 27001 for organizations with US operations | When building unified security framework across ISO 27001 and NIST CSF |
| `dora-compliance-expert` | ISO 27001 controls support DORA Pillar 1 (ICT Risk Management) requirements for financial entities | When financial entity uses ISO 27001 as foundation for DORA compliance |

---

## Tool Reference

### risk_assessment.py

Automated security risk assessment following ISO 27001 Clause 6.1.2 methodology.

| Flag | Required | Description |
|------|----------|-------------|
| `--scope <name>` | Yes (unless `--assets`) | System or area to assess (e.g., `cloud-infrastructure`, `ehr-system`, `patient-data-system`) |
| `--template <type>` | No | Assessment template: `general` (default), `healthcare`, `cloud` -- each provides context-appropriate threat catalogs |
| `--assets <file>` | No | CSV file with asset inventory (columns: asset_id, name, type, owner, classification) |
| `--output <file>` | No | Output file path (default: stdout) |
| `--format <fmt>` | No | Output format: `json` (default), `csv`, `markdown` |

**Output:** Asset inventory with classification, threat and vulnerability mapping, risk scores (Likelihood x Impact on 1-5 scale), treatment recommendations per risk level, and residual risk calculations.

### compliance_checker.py

Verifies ISO 27001/27002 control implementation status with gap analysis and remediation recommendations.

| Flag | Required | Description |
|------|----------|-------------|
| `--standard <std>` | Yes | Standard to check: `iso27001`, `iso27002`, `hipaa` |
| `--controls-file <file>` | No | CSV file with current control implementation status |
| `--gap-analysis` | No | Include detailed remediation recommendations in output |
| `--domains <domains>` | No | Comma-separated specific control domains to check (e.g., `access-control,cryptography`) |
| `--output <file>` | No | Output file path for compliance report |

**Output:** Control implementation status per domain, compliance percentage by theme/domain, gap analysis with priorities (when `--gap-analysis` flag used), and remediation recommendations mapped to ISO 27002 control guidance.

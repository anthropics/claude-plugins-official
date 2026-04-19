---
name: nis2-directive-specialist
description: >
  NIS2 Directive (EU 2022/2555) compliance automation. Analyzes organizational
  scope, assesses compliance against all 10 minimum security measures, validates
  incident reporting readiness, and generates gap analysis reports. Use for NIS2
  compliance assessments, critical infrastructure cybersecurity planning, supply
  chain security evaluation, and incident reporting preparation.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: cybersecurity-directive
  updated: 2026-03-31
  tags: [nis2, cybersecurity-directive, incident-reporting, supply-chain]
---
# NIS2 Directive Specialist

Tools and guidance for EU Directive 2022/2555 on measures for a high common level of cybersecurity across the Union (NIS2 Directive).

---

## Table of Contents

- [NIS2 Overview](#nis2-overview)
- [Scope and Applicability](#scope-and-applicability)
- [10 Minimum Security Measures](#10-minimum-security-measures-article-21)
- [Incident Reporting Requirements](#incident-reporting-requirements)
- [Management Accountability](#management-accountability-article-20)
- [Supply Chain Security](#supply-chain-security-deep-dive)
- [Penalties](#penalties)
- [NIS2 vs NIS1 Comparison](#nis2-vs-nis1-comparison)
- [Infrastructure Security Checks](#infrastructure-security-checks)
- [Tools](#tools)
- [Reference Guides](#reference-guides)
- [Compliance Assessment Workflow](#compliance-assessment-workflow)
- [NIS2 Implementation Roadmap](#nis2-implementation-roadmap)

---

## NIS2 Overview

The **NIS2 Directive (EU 2022/2555)** is the EU's updated framework for cybersecurity, replacing the original NIS Directive (EU 2016/1148). It entered into force on January 16, 2023, with Member States required to transpose it into national law by **October 17, 2024**.

**Key objectives:**

- Establish a high common level of cybersecurity across the EU
- Harmonize cybersecurity requirements and enforcement
- Expand scope to cover more sectors and entities
- Strengthen incident reporting obligations
- Introduce management accountability for cybersecurity
- Enhance supply chain security requirements

**Legal basis:** Article 114 TFEU (internal market harmonization)

**Relationship to other frameworks:**

| Framework | Relationship |
|-----------|-------------|
| ISO 27001 | NIS2 measures map closely to ISO 27001 controls |
| GDPR | NIS2 complements GDPR for security of processing |
| CER Directive | Critical Entities Resilience — physical security complement |
| DORA | Lex specialis for financial sector entities |
| Cyber Resilience Act | Product security requirements for hardware/software |

---

## Scope and Applicability

### Essential Entities (Annex I — High Criticality Sectors)

| Sector | Sub-sectors |
|--------|------------|
| **Energy** | Electricity (DSOs, TSOs, producers, storage), oil (pipelines, production, refineries, storage), gas (DSOs, TSOs, LNG, storage), hydrogen, district heating/cooling |
| **Transport** | Air (carriers, airports, traffic management), rail (infrastructure managers, operators), water (inland, maritime, port operators), road (traffic management, ITS operators) |
| **Banking** | Credit institutions as defined in Regulation (EU) No 575/2013 |
| **Financial market infrastructure** | Trading venues, central counterparties |
| **Health** | Healthcare providers, EU reference laboratories, entities manufacturing pharmaceutical products, entities manufacturing medical devices considered critical during public health emergencies |
| **Drinking water** | Suppliers and distributors of water intended for human consumption |
| **Waste water** | Entities collecting, disposing, or treating urban waste water, domestic waste water, or industrial waste water |
| **Digital infrastructure** | IXPs, DNS providers, TLD registries, cloud computing providers, data center operators, CDN providers, trust service providers, public electronic communications networks, publicly available electronic communications services |
| **ICT service management (B2B)** | Managed service providers, managed security service providers |
| **Public administration** | Central government entities, regional government entities at NUTS level 1 and 2 |
| **Space** | Operators of ground-based infrastructure supporting space-based services |

### Important Entities (Annex II — Other Critical Sectors)

| Sector | Sub-sectors |
|--------|------------|
| **Postal and courier services** | Providers of postal services including courier services |
| **Waste management** | Entities carrying out waste management (excluding those for whom waste management is not their principal economic activity) |
| **Chemicals** | Entities manufacturing, producing, or distributing chemical substances and mixtures |
| **Food** | Food businesses engaged in wholesale distribution, industrial production, and processing |
| **Manufacturing** | Medical devices and in vitro diagnostics, computer/electronic/optical products, electrical equipment, machinery and equipment, motor vehicles/trailers, other transport equipment |
| **Digital providers** | Online marketplaces, online search engines, social networking services platforms |
| **Research** | Research organizations |

### Size Thresholds

| Category | Employees | Annual Turnover | Annual Balance Sheet |
|----------|-----------|----------------|---------------------|
| **Medium enterprise** | 50–249 | €10M–€50M | €10M–€43M |
| **Large enterprise** | 250+ | €50M+ | €43M+ |

**Automatic inclusion regardless of size:**

- Trust service providers
- TLD name registries
- DNS service providers
- Public electronic communications networks/services
- Public administration entities
- Sole provider of a service in a Member State
- Entity whose disruption could have significant impact on public safety, security, or health
- Entity whose disruption could induce systemic risk (especially cross-border)

**Exclusions:**

- Micro and small enterprises (generally excluded unless specifically designated)
- National security, public security, defense, law enforcement
- Judiciary, parliaments, central banks

---

## 10 Minimum Security Measures (Article 21)

All essential and important entities must implement appropriate and proportionate technical, operational, and organizational measures to manage cybersecurity risks. These measures must be based on an **all-hazards approach** and cover at minimum:

### 1. Risk Analysis and Information System Security Policies

Establish and maintain comprehensive risk analysis processes and information security policies covering all information systems.

**Requirements:**
- Formal risk assessment methodology
- Asset inventory and classification
- Security policy framework (approved by management body)
- Regular policy review cycles (at least annually)
- Risk appetite and tolerance definitions
- Documented risk treatment plans

### 2. Incident Handling

Implement procedures for detecting, managing, and responding to cybersecurity incidents.

**Requirements:**
- Incident detection capabilities
- Incident classification and triage procedures
- Incident response plans and playbooks
- Incident escalation procedures
- Post-incident review process
- Integration with CSIRT reporting (see Incident Reporting section)

### 3. Business Continuity and Crisis Management

Ensure service continuity during and after cybersecurity incidents.

**Requirements:**
- Business impact analysis (BIA)
- Business continuity plans (BCP)
- Disaster recovery plans (DRP)
- Backup management policies
- Crisis management procedures
- Regular testing of continuity plans (at least annually)
- Recovery time objectives (RTO) and recovery point objectives (RPO)

### 4. Supply Chain Security

Address security risks in relationships with direct suppliers and service providers.

**Requirements:**
- Supplier risk assessment process
- Security requirements in contracts with suppliers
- Monitoring of supplier security posture
- Supplier incident notification requirements
- Assessment of aggregate supply chain risks
- Product/service quality and cybersecurity practices of suppliers

### 5. Security in Network and Information Systems Acquisition, Development, and Maintenance

Integrate security throughout the system lifecycle.

**Requirements:**
- Secure development lifecycle (SDLC) practices
- Vulnerability management procedures
- Security testing (SAST, DAST, penetration testing)
- Patch management processes
- Change management with security review
- Secure configuration management

### 6. Policies and Procedures for Assessing Effectiveness

Evaluate whether cybersecurity risk management measures are effective.

**Requirements:**
- Security metrics and KPIs
- Regular security assessments and audits
- Penetration testing program
- Vulnerability scanning
- Compliance monitoring
- Continuous improvement processes

### 7. Basic Cyber Hygiene Practices and Cybersecurity Training

Ensure all personnel have adequate cybersecurity awareness and skills.

**Requirements:**
- Cybersecurity awareness training for all staff
- Role-based security training for technical staff
- Management body cybersecurity training (mandatory under Article 20)
- Phishing simulation exercises
- Security awareness campaigns
- Training records and effectiveness measurement

### 8. Policies and Procedures Regarding Use of Cryptography and Encryption

Protect data confidentiality and integrity through cryptographic controls.

**Requirements:**
- Cryptography policy
- Encryption standards for data at rest and in transit
- Key management procedures
- Certificate management
- Cryptographic algorithm selection guidance
- Regular review of cryptographic implementations

### 9. Human Resources Security, Access Control Policies, and Asset Management

Manage people, access, and assets securely.

**Requirements:**
- Pre-employment screening and security checks
- Security responsibilities in employment contracts
- Departure procedures (access revocation)
- Role-based access control (RBAC)
- Privileged access management (PAM)
- Asset inventory and ownership
- Acceptable use policies

### 10. Multi-Factor Authentication, Secured Communications, and Emergency Communications

Deploy strong authentication and secure communication channels.

**Requirements:**
- MFA for all remote access and privileged accounts
- MFA for access to critical systems
- Continuous authentication where appropriate
- Encrypted communications (TLS 1.2+ minimum)
- Secure emergency communication channels
- Out-of-band communication capabilities
- Secure voice and video communications

---

## Incident Reporting Requirements

NIS2 introduces a **multi-stage incident reporting regime** for significant incidents. An incident is considered significant if it causes or is capable of causing:

- Severe operational disruption or financial loss
- Considerable material or non-material damage to other persons

### Reporting Timeline

| Stage | Deadline | Content |
|-------|----------|---------|
| **Early warning** | Within **24 hours** of becoming aware | Whether the incident is suspected of being caused by unlawful or malicious acts, whether it could have cross-border impact |
| **Incident notification** | Within **72 hours** of becoming aware | Update of early warning, initial assessment of severity and impact, indicators of compromise where applicable |
| **Intermediate report** | Upon CSIRT/authority request | Status update on incident handling and response |
| **Final report** | Within **1 month** of incident notification | Detailed description of the incident and its root cause, mitigation measures applied and ongoing, cross-border impact if applicable |

### Additional Requirements

- Entities must **inform recipients of their services** without undue delay if the significant incident is likely to adversely affect the provision of those services
- Member States may require entities to use specific platforms or templates
- CSIRTs must provide feedback and guidance within 24 hours of receiving early warning
- Active cyber threats must be reported to recipients of services along with remediation measures

---

## Management Accountability (Article 20)

NIS2 introduces **personal accountability for management bodies** — a significant departure from NIS1.

**Key requirements:**

1. **Approval and oversight**: Management bodies must approve cybersecurity risk management measures and oversee their implementation
2. **Liability**: Management bodies can be held liable for infringements of Article 21
3. **Training**: Members of management bodies must undergo cybersecurity training and encourage similar training for employees
4. **Sufficient knowledge**: Management bodies must have sufficient knowledge and skills to assess cybersecurity risks and management practices

**Consequences of non-compliance:**

- Member States may impose a **temporary prohibition** on natural persons holding management responsibilities at CEO or legal representative level in essential entities
- Administrative fines and other enforcement measures
- Personal liability for management body members who fail to comply

---

## Supply Chain Security Deep-Dive

Supply chain security is one of the most impactful new requirements under NIS2.

### Requirements

Entities must take into account:

1. **Vulnerabilities specific to each direct supplier and service provider**
2. **Overall quality of products and cybersecurity practices** of suppliers, including secure development procedures
3. **Results of coordinated security risk assessments** of critical supply chains (per Article 22)
4. **Supplier contractual arrangements** including:
   - Security requirements and certifications
   - Right to audit
   - Incident notification obligations
   - Sub-contractor security requirements

### Implementation Framework

**Tier 1 — Critical suppliers:**
- Full security assessment before onboarding
- Annual security audits or certification verification (ISO 27001, SOC 2)
- Real-time incident notification requirements
- Right to audit clauses
- Exit strategy and data portability requirements

**Tier 2 — Important suppliers:**
- Security questionnaire and self-assessment
- Periodic security review (biannual)
- Contractual security requirements
- Incident notification within 48 hours

**Tier 3 — Standard suppliers:**
- Basic security questionnaire
- Annual review of security posture
- Standard contractual security clauses

### Coordinated Risk Assessments (Article 22)

The NIS Cooperation Group may carry out coordinated risk assessments of critical supply chains, considering:

- Technical and non-technical risk factors
- Dependencies and potential points of failure
- Risks from non-EU influence on supply chains

---

## Penalties

### Administrative Fines

| Entity Type | Maximum Fine |
|------------|-------------|
| **Essential entities** | **€10,000,000** or **2% of total worldwide annual turnover**, whichever is higher |
| **Important entities** | **€7,000,000** or **1.4% of total worldwide annual turnover**, whichever is higher |

### Other Enforcement Measures

**For essential entities (Article 32):**
- Binding instructions
- Orders to implement security audit recommendations
- Orders to bring measures into compliance
- Temporary suspension of certifications or authorizations
- Temporary prohibition of management responsibilities for responsible natural persons

**For important entities (Article 33):**
- Binding instructions
- Orders to implement security audit recommendations
- Orders to bring measures into compliance
- Administrative fines

### Supervisory Regime Differences

| Aspect | Essential Entities | Important Entities |
|--------|-------------------|-------------------|
| **Supervision** | Ex-ante (proactive) | Ex-post (reactive/complaint-based) |
| **Audits** | Regular security audits | Audits when justified |
| **On-site inspections** | Yes | Upon reasonable request |
| **Management bans** | Yes (temporary) | No |

---

## NIS2 vs NIS1 Comparison

| Aspect | NIS1 (2016/1148) | NIS2 (2022/2555) |
|--------|-------------------|-------------------|
| **Scope** | 7 sectors, ~10K entities | 18 sectors, ~160K entities |
| **Entity classification** | OES and DSP | Essential and Important |
| **Security measures** | General requirements | 10 specific minimum measures |
| **Incident reporting** | No specific timeline | 24h / 72h / 1 month staged |
| **Management accountability** | Not specified | Mandatory training, personal liability |
| **Supply chain** | Not addressed | Explicit requirements |
| **Penalties** | Set by Member States | Harmonized: €10M/2% or €7M/1.4% |
| **Supervision** | Varied | Harmonized ex-ante/ex-post |
| **Peer review** | Limited | Enhanced peer review mechanism |
| **Vulnerability disclosure** | Not addressed | Coordinated vulnerability disclosure |
| **Size threshold** | Member State designation | Clear size-cap rules |
| **Enforcement** | Weak, inconsistent | Strong, harmonized |

---

## Infrastructure Security Checks

### DNS Security

- **DNSSEC implementation** is effectively mandatory for DNS service providers and TLD registries under NIS2
- Validate DNSSEC chain of trust for all zones
- Implement DNS monitoring and anomaly detection
- Consider DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT) for internal resolution
- Monitor for DNS tunneling and exfiltration

### Network Monitoring and Segmentation

- Deploy network monitoring for anomaly detection (Article 21(2)(b))
- Implement network segmentation between critical and non-critical systems
- Monitor east-west traffic within data centers
- Deploy network-based intrusion detection/prevention systems
- Maintain network flow logs for forensic analysis

### Endpoint Detection and Response

- Deploy EDR solutions on all endpoints accessing critical systems
- Configure automated threat detection and response
- Maintain endpoint inventory with health status
- Implement application whitelisting for critical systems
- Regular endpoint compliance scanning

### MFA Enforcement (Article 21(2)(j))

- Deploy MFA for all remote access
- Enforce MFA for privileged accounts
- Implement MFA for access to critical systems and data
- Consider passwordless authentication where feasible
- Support hardware security keys (FIDO2/WebAuthn) for high-risk accounts

### Encryption Requirements

- TLS 1.2 minimum for all external communications; TLS 1.3 preferred
- Encrypt data at rest using AES-256 or equivalent
- Implement end-to-end encryption for sensitive communications
- Deploy certificate management and monitoring
- Regular cryptographic algorithm review

### Vulnerability Disclosure Coordination

- Establish a coordinated vulnerability disclosure (CVD) policy
- Designate a vulnerability disclosure contact
- Participate in ENISA's vulnerability database
- Implement responsible disclosure processes
- Track and remediate disclosed vulnerabilities within defined timelines

### Physical Security for Critical Infrastructure

- Physical access controls for data centers and critical facilities
- Environmental monitoring (temperature, humidity, water detection)
- Surveillance and intrusion detection systems
- Visitor management and escort procedures
- Physical security testing as part of overall resilience testing

---

## Tools

### NIS2 Scope Analyzer

Determines whether an organization falls within NIS2 scope and classifies it as Essential or Important.

```bash
# Analyze scope interactively
python scripts/nis2_scope_analyzer.py --sector energy --sub-sector electricity --employees 500 --turnover 100

# Full analysis with JSON output
python scripts/nis2_scope_analyzer.py --sector health --sub-sector healthcare_providers --employees 75 --turnover 15 --json

# Generate compliance checklist
python scripts/nis2_scope_analyzer.py --sector digital_infrastructure --sub-sector cloud_computing --employees 200 --turnover 50 --checklist

# Load from config file
python scripts/nis2_scope_analyzer.py --config organization.json --json --output scope_report.json
```

**Features:**
- Sector and sub-sector classification against Annex I and Annex II
- Size threshold evaluation (employees, turnover, balance sheet)
- Automatic inclusion detection (DNS providers, TLD registries, etc.)
- Entity type determination (Essential vs Important)
- Applicable obligations summary
- Compliance checklist generation

---

### NIS2 Compliance Checker

Assesses compliance against all 10 minimum security measures with per-measure scoring.

```bash
# Run full compliance check
python scripts/nis2_compliance_checker.py --config assessment.json

# Generate assessment template
python scripts/nis2_compliance_checker.py --template > assessment.json

# Check specific measures only
python scripts/nis2_compliance_checker.py --config assessment.json --measures 1 2 4 --json

# Generate gap analysis report
python scripts/nis2_compliance_checker.py --config assessment.json --output gap_report.json --json
```

**Features:**
- Assessment against all 10 Article 21 minimum measures
- Per-measure compliance scoring (0–100)
- Overall compliance score
- Incident reporting readiness validation
- Supply chain security assessment
- Management accountability verification
- Gap analysis with prioritized remediation recommendations

---

## Reference Guides

### [NIS2 Requirements Guide](references/nis2-requirements-guide.md)

Complete coverage of all 10 minimum security measures with implementation guidance, incident reporting procedures, management accountability requirements, supply chain security framework, and ISO 27001 control mapping.

### [NIS2 Implementation Playbook](references/nis2-implementation-playbook.md)

12-month implementation roadmap with resource requirements, policy templates, technical controls checklist, training requirements, and cost estimation framework.

---

## Compliance Assessment Workflow

### Phase 1: Scope Determination

```
1. Identify sector and sub-sector classification
   → Use NIS2 Scope Analyzer tool
2. Determine entity size (employees, turnover, balance sheet)
3. Check for automatic inclusion criteria
4. Classify as Essential or Important entity
5. Identify applicable Member State transposition requirements
```

### Phase 2: Gap Assessment

```
1. Document current security posture
2. Map existing controls to NIS2 10 minimum measures
   → Use NIS2 Compliance Checker tool
3. Assess incident reporting readiness
4. Evaluate supply chain security maturity
5. Review management accountability compliance
6. Generate gap analysis report
```

### Phase 3: Remediation Planning

```
1. Prioritize gaps by risk and regulatory impact
2. Develop remediation roadmap (see Implementation Playbook)
3. Allocate budget and resources
4. Define project milestones and ownership
5. Establish governance structure
```

### Phase 4: Implementation

```
1. Implement technical controls
2. Develop and approve policies
3. Deploy monitoring and detection capabilities
4. Establish incident reporting procedures
5. Conduct supply chain security assessments
6. Train management body and staff
```

### Phase 5: Continuous Compliance

```
1. Regular compliance assessments (quarterly minimum)
2. Annual management body training refresh
3. Incident response exercises (biannual)
4. Supply chain security reviews (annual)
5. Policy review and update cycles
6. Audit preparation and execution
```

---

## NIS2 Implementation Roadmap

### 12-Month Plan

| Month | Phase | Key Activities |
|-------|-------|---------------|
| 1–2 | **Assessment** | Scope determination, gap analysis, current state documentation |
| 3–4 | **Planning** | Remediation roadmap, budget allocation, governance setup, quick wins |
| 5–6 | **Foundation** | Core policies, risk framework, asset inventory, management training |
| 7–8 | **Implementation** | Technical controls, monitoring deployment, incident response setup |
| 9–10 | **Supply Chain** | Supplier assessments, contractual updates, third-party risk program |
| 11 | **Testing** | Incident response exercises, penetration testing, compliance validation |
| 12 | **Operationalize** | Final audit, continuous monitoring, ongoing compliance program launch |

### Quick Wins (Month 1–3)

1. Enable MFA for all remote access and privileged accounts
2. Document existing security policies
3. Establish incident reporting contact with national CSIRT
4. Begin management body cybersecurity training
5. Create asset inventory of critical systems
6. Review and update backup procedures

### Resource Estimates

| Organization Size | FTE Requirement | Estimated Budget |
|-------------------|----------------|-----------------|
| Medium (50–249) | 1–2 dedicated + project team | €200K–€500K |
| Large (250–999) | 2–4 dedicated + project team | €500K–€1.5M |
| Enterprise (1000+) | 4–8 dedicated + project team | €1.5M–€5M+ |

---

---

## Troubleshooting

| Problem | Likely Cause | Resolution |
|---------|-------------|------------|
| Scope Analyzer returns "out of scope" for an entity that should be in scope | Automatic inclusion criteria not triggered; size thresholds not met | Check for automatic inclusion flags (DNS providers, TLD registries, sole provider). Verify `--turnover` and `--employees` values. Use `--checklist` flag to review all criteria. |
| Compliance Checker scores are unexpectedly low | Assessment JSON has missing or null control responses | Run `--template` to regenerate a fresh assessment template. Ensure every control question has a boolean or score value. |
| Gap report does not cover all 10 measures | `--measures` flag is filtering output | Remove the `--measures` flag to assess all 10 Article 21 measures. Verify the config JSON includes all measure sections. |
| Entity classified as "Important" instead of "Essential" | Sector falls under Annex II rather than Annex I | Review sector/sub-sector classification. Annex I sectors produce Essential entities; Annex II sectors produce Important entities. Size also matters. |
| National transposition requirements unclear | Member State has not yet fully transposed NIS2 | As of early 2026, 13 of 27 EU Member States have incomplete transposition. Check the ECSO NIS2 Transposition Tracker for country-specific status. Apply the directive's baseline requirements. |
| Supply chain assessment section incomplete | Supplier tier classification not provided in config | Populate supplier data with tier levels (Critical/Important/Standard) and include contractual security requirements for each tier. |
| Incident reporting readiness score is zero | No incident handling controls documented in assessment | Complete Measure 2 (Incident Handling) controls in the assessment JSON, including detection capabilities, classification procedures, and CSIRT reporting integration. |

---

## Success Criteria

- All in-scope entities correctly classified as Essential or Important with documented rationale for the classification decision
- Compliance scores of 70% or higher across all 10 minimum security measures within the first assessment cycle, trending toward 90%+ within 12 months
- Incident reporting procedures tested and validated against the 24h/72h/1-month staged timeline, with documented CSIRT contact and reporting templates
- Management body members have completed mandatory cybersecurity training with documented attendance and knowledge assessment records
- Supply chain security program covers 100% of Tier 1 (critical) suppliers with quality agreements, right-to-audit clauses, and incident notification requirements in contracts
- Gap analysis produces a prioritized remediation roadmap with assigned owners, budgets, and milestone dates for every identified gap
- Quarterly compliance reassessments demonstrate measurable improvement with trending metrics reported to management

---

## Scope & Limitations

**In Scope:**
- NIS2 Directive (EU 2022/2555) compliance assessment and gap analysis
- Entity classification (Essential vs Important) per Annex I and Annex II
- All 10 Article 21 minimum security measures assessment
- Incident reporting readiness evaluation against the multi-stage reporting regime
- Supply chain security framework assessment (Tier 1/2/3 suppliers)
- Management accountability verification per Article 20
- Cross-framework mapping to ISO 27001 controls

**Out of Scope:**
- National transposition specifics (varies by Member State; the tools assess against the directive baseline, not country-specific implementing legislation)
- Technical penetration testing or vulnerability scanning (use infrastructure-compliance-auditor for technical checks)
- CER Directive (EU 2022/2557) physical resilience requirements (complementary but separate regulation)
- DORA (EU 2022/2554) requirements for financial sector entities (use dora-compliance-expert for lex specialis)
- Legal advice on penalty exposure or liability (consult qualified legal counsel)
- Real-time infrastructure monitoring or SIEM deployment

---

## Integration Points

| Skill | Integration |
|-------|------------|
| [information-security-manager-iso27001](../information-security-manager-iso27001/) | NIS2 measures map closely to ISO 27001 Annex A controls; use ISO 27001 ISMS as the implementation backbone for NIS2 compliance |
| [infrastructure-compliance-auditor](../infrastructure-compliance-auditor/) | Validate technical controls (DNS, TLS, MFA, encryption, monitoring) that satisfy NIS2 Article 21 requirements |
| [dora-compliance-expert](../dora-compliance-expert/) | DORA is lex specialis for financial sector entities; coordinate NIS2 and DORA assessments to avoid duplication |
| [nist-csf-specialist](../nist-csf-specialist/) | NIST CSF 2.0 functions map to NIS2 measures; use CSF maturity assessor to benchmark cybersecurity posture |
| [soc2-compliance-expert](../soc2-compliance-expert/) | SOC 2 Trust Services Criteria overlap significantly with NIS2 measures; leverage existing SOC 2 evidence |
| [isms-audit-expert](../isms-audit-expert/) | ISO 27001 audit evidence directly supports NIS2 compliance demonstrations |

---

## Tool Reference

### nis2_scope_analyzer.py

Determines NIS2 applicability and entity classification.

| Flag | Required | Description |
|------|----------|-------------|
| `--sector` | Yes (or `--config`) | Sector identifier (e.g., `energy`, `health`, `digital_infrastructure`) |
| `--sub-sector` | Yes (or `--config`) | Sub-sector identifier (e.g., `electricity`, `healthcare_providers`, `cloud_computing`) |
| `--employees` | Yes (or `--config`) | Number of employees in the organization |
| `--turnover` | Yes (or `--config`) | Annual turnover in millions of euros |
| `--config` | No | Path to organization JSON config file (alternative to individual flags) |
| `--json` | No | Output results in JSON format |
| `--checklist` | No | Generate a compliance checklist based on entity classification |
| `--output` | No | Path to write the output report file |

### nis2_compliance_checker.py

Assesses compliance against all 10 Article 21 minimum security measures.

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | Yes (or `--template`) | Path to assessment JSON file with control responses |
| `--template` | No | Generate a blank assessment template (pipe to file with `>`) |
| `--measures` | No | Space-separated list of measure numbers to assess (e.g., `1 2 4`). Omit for all 10. |
| `--json` | No | Output results in JSON format |
| `--output` | No | Path to write the gap analysis report |

---

*Last Updated: March 2026*
*Directive Reference: EU 2022/2555*
*Applicable From: October 17, 2024 (Member State transposition deadline)*

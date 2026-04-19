---
name: gdpr-dsgvo-expert
description: >
  GDPR and German DSGVO compliance automation. Scans codebases for privacy
  risks, generates DPIA documentation, tracks data subject rights requests. Use
  for GDPR compliance assessments, privacy audits, data protection planning,
  DPIA generation, and data subject rights management.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: privacy-compliance
  updated: 2026-03-31
  tags: [gdpr, dsgvo, dpia, data-protection, privacy]
---
# GDPR/DSGVO Expert

Tools and guidance for EU General Data Protection Regulation (GDPR) and German Bundesdatenschutzgesetz (BDSG) compliance.

---

## Table of Contents

- [Tools](#tools)
  - [GDPR Compliance Checker](#gdpr-compliance-checker)
  - [DPIA Generator](#dpia-generator)
  - [Data Subject Rights Tracker](#data-subject-rights-tracker)
- [Reference Guides](#reference-guides)
- [Workflows](#workflows)

---

## Tools

### GDPR Compliance Checker

Scans codebases for potential GDPR compliance issues including personal data patterns and risky code practices.

```bash
# Scan a project directory
python scripts/gdpr_compliance_checker.py /path/to/project

# JSON output for CI/CD integration
python scripts/gdpr_compliance_checker.py . --json --output report.json
```

**Detects:**
- Personal data patterns (email, phone, IP addresses)
- Special category data (health, biometric, religion)
- Financial data (credit cards, IBAN)
- Risky code patterns:
  - Logging personal data
  - Missing consent mechanisms
  - Indefinite data retention
  - Unencrypted sensitive data
  - Disabled deletion functionality

**Output:**
- Compliance score (0-100)
- Risk categorization (critical, high, medium)
- Prioritized recommendations with GDPR article references

---

### DPIA Generator

Generates Data Protection Impact Assessment documentation following Art. 35 requirements.

```bash
# Get input template
python scripts/dpia_generator.py --template > input.json

# Generate DPIA report
python scripts/dpia_generator.py --input input.json --output dpia_report.md
```

**Features:**
- Automatic DPIA threshold assessment
- Risk identification based on processing characteristics
- Legal basis requirements documentation
- Mitigation recommendations
- Markdown report generation

**DPIA Triggers Assessed:**
- Systematic monitoring (Art. 35(3)(c))
- Large-scale special category data (Art. 35(3)(b))
- Automated decision-making (Art. 35(3)(a))
- WP29 high-risk criteria

---

### Data Subject Rights Tracker

Manages data subject rights requests under GDPR Articles 15-22.

```bash
# Add new request
python scripts/data_subject_rights_tracker.py add \
  --type access --subject "John Doe" --email "john@example.com"

# List all requests
python scripts/data_subject_rights_tracker.py list

# Update status
python scripts/data_subject_rights_tracker.py status --id DSR-202601-0001 --update verified

# Generate compliance report
python scripts/data_subject_rights_tracker.py report --output compliance.json

# Generate response template
python scripts/data_subject_rights_tracker.py template --id DSR-202601-0001
```

**Supported Rights:**

| Right | Article | Deadline |
|-------|---------|----------|
| Access | Art. 15 | 30 days |
| Rectification | Art. 16 | 30 days |
| Erasure | Art. 17 | 30 days |
| Restriction | Art. 18 | 30 days |
| Portability | Art. 20 | 30 days |
| Objection | Art. 21 | 30 days |
| Automated decisions | Art. 22 | 30 days |

**Features:**
- Deadline tracking with overdue alerts
- Identity verification workflow
- Response template generation
- Compliance reporting

---

## Reference Guides

### GDPR Compliance Guide
`references/gdpr_compliance_guide.md`

Comprehensive implementation guidance covering:
- Legal bases for processing (Art. 6)
- Special category requirements (Art. 9)
- Data subject rights implementation
- Accountability requirements (Art. 30)
- International transfers (Chapter V)
- Breach notification (Art. 33-34)

### German BDSG Requirements
`references/german_bdsg_requirements.md`

German-specific requirements including:
- DPO appointment threshold (§ 38 BDSG - 20+ employees)
- Employment data processing (§ 26 BDSG)
- Video surveillance rules (§ 4 BDSG)
- Credit scoring requirements (§ 31 BDSG)
- State data protection laws (Landesdatenschutzgesetze)
- Works council co-determination rights

### DPIA Methodology
`references/dpia_methodology.md`

Step-by-step DPIA process:
- Threshold assessment criteria
- WP29 high-risk indicators
- Risk assessment methodology
- Mitigation measure categories
- DPO and supervisory authority consultation
- Templates and checklists

---

## Workflows

### Workflow 1: New Processing Activity Assessment

```
Step 1: Run compliance checker on codebase
        → python scripts/gdpr_compliance_checker.py /path/to/code

Step 2: Review findings and compliance score
        → Address critical and high issues

Step 3: Determine if DPIA required
        → Check references/dpia_methodology.md threshold criteria

Step 4: If DPIA required, generate assessment
        → python scripts/dpia_generator.py --template > input.json
        → Fill in processing details
        → python scripts/dpia_generator.py --input input.json --output dpia.md

Step 5: Document in records of processing activities
```

### Workflow 2: Data Subject Request Handling

```
Step 1: Log request in tracker
        → python scripts/data_subject_rights_tracker.py add --type [type] ...

Step 2: Verify identity (proportionate measures)
        → python scripts/data_subject_rights_tracker.py status --id [ID] --update verified

Step 3: Gather data from systems
        → python scripts/data_subject_rights_tracker.py status --id [ID] --update in_progress

Step 4: Generate response
        → python scripts/data_subject_rights_tracker.py template --id [ID]

Step 5: Send response and complete
        → python scripts/data_subject_rights_tracker.py status --id [ID] --update completed

Step 6: Monitor compliance
        → python scripts/data_subject_rights_tracker.py report
```

### Workflow 3: German BDSG Compliance Check

```
Step 1: Determine if DPO required
        → 20+ employees processing personal data automatically
        → OR processing requires DPIA
        → OR business involves data transfer/market research

Step 2: If employees involved, review § 26 BDSG
        → Document legal basis for employee data
        → Check works council requirements

Step 3: If video surveillance, comply with § 4 BDSG
        → Install signage
        → Document necessity
        → Limit retention

Step 4: Register DPO with supervisory authority
        → See references/german_bdsg_requirements.md for authority list
```

---

## Key GDPR Concepts

### Legal Bases (Art. 6)

- **Consent**: Marketing, newsletters, analytics (must be freely given, specific, informed)
- **Contract**: Order fulfillment, service delivery
- **Legal obligation**: Tax records, employment law
- **Legitimate interests**: Fraud prevention, security (requires balancing test)

### Special Category Data (Art. 9)

Requires explicit consent or Art. 9(2) exception:
- Health data
- Biometric data
- Racial/ethnic origin
- Political opinions
- Religious beliefs
- Trade union membership
- Genetic data
- Sexual orientation

### Data Subject Rights

All rights must be fulfilled within **30 days** (extendable to 90 for complex requests):
- **Access**: Provide copy of data and processing information
- **Rectification**: Correct inaccurate data
- **Erasure**: Delete data (with exceptions for legal obligations)
- **Restriction**: Limit processing while issues are resolved
- **Portability**: Provide data in machine-readable format
- **Object**: Stop processing based on legitimate interests

### German BDSG Additions

| Topic | BDSG Section | Key Requirement |
|-------|--------------|-----------------|
| DPO threshold | § 38 | 20+ employees = mandatory DPO |
| Employment | § 26 | Detailed employee data rules |
| Video | § 4 | Signage and proportionality |
| Scoring | § 31 | Explainable algorithms |

---

## Cross-Reference: CCPA/CPRA US Privacy Comparison

When operating across EU and US jurisdictions, align GDPR compliance with California Consumer Privacy Act (CCPA) as amended by CPRA. Key differences to manage:

| Dimension | GDPR | CCPA/CPRA |
|-----------|------|-----------|
| Scope | Any org processing EU resident data | For-profit businesses meeting revenue/data thresholds |
| Legal basis | 6 lawful bases required (Art. 6) | No legal basis requirement; opt-out model |
| Consent | Opt-in by default | Opt-out (except minors and sensitive data) |
| Data subject rights | Access, rectification, erasure, portability, objection | Know, delete, correct, opt-out of sale/sharing, limit sensitive data use |
| Breach notification | 72 hours to supervisory authority (Art. 33) | "Most expedient time possible" to consumers |
| Enforcement | DPAs with fines up to 4% global turnover | California Privacy Protection Agency (CPPA), $2,500-$7,500 per violation |
| DPO requirement | Mandatory in many cases (Art. 37) | No DPO requirement |
| Children's data | Under 16 requires parental consent (Art. 8) | Under 16 opt-in for sale; under 13 parental consent |

**Practical alignment:** Build a unified privacy program that satisfies the stricter GDPR requirements by default, then layer CCPA/CPRA-specific mechanisms (e.g., "Do Not Sell or Share My Personal Information" link, annual metrics disclosure).

> **See also:** `../ccpa-cpra-specialist/SKILL.md` for full CCPA/CPRA compliance workflows and tools.

---

## Infrastructure Privacy Controls

### Cookie Consent and Tracking

Implement compliant cookie consent per GDPR Art. 6 + ePrivacy Directive:

| Category | Examples | Consent Required | Default State |
|----------|----------|------------------|---------------|
| Strictly Necessary | Session, CSRF, load balancer | No | Active |
| Functional | Language preference, UI settings | Yes | Inactive |
| Analytics | Google Analytics, Matomo, Hotjar | Yes | Inactive |
| Marketing | Facebook Pixel, Google Ads, retargeting | Yes | Inactive |

**Implementation requirements:**
- Banner must block all non-essential cookies until explicit consent
- Pre-checked boxes are NOT valid consent (Planet49 ruling, CJEU C-673/17)
- Consent must be as easy to withdraw as to give
- Record consent proof (timestamp, version, choices made)
- Re-consent on material changes to cookie policy

### Global Privacy Control (GPC) Signal

Per CCPA/CPRA regulations and emerging EU guidance:
- Detect `Sec-GPC: 1` HTTP header and `navigator.globalPrivacyControl` JavaScript API
- Treat GPC as valid opt-out signal for CCPA/CPRA
- For GDPR: GPC can serve as a signal of objection under Art. 21 — evaluate on a case-by-case basis
- Log GPC signal detection and honor it automatically

### Data Localization and Cross-Border Transfers

| Transfer Mechanism | Status (post-Schrems II) | When to Use |
|---------------------|--------------------------|-------------|
| EU Adequacy Decision | Valid | Transfers to adequate countries (e.g., Japan, UK, South Korea, US via DPF) |
| Standard Contractual Clauses (SCCs) | Valid with TIA | Default mechanism for non-adequate countries |
| Binding Corporate Rules (BCRs) | Valid | Intra-group transfers in multinationals |
| EU-US Data Privacy Framework (DPF) | Valid (since July 2023) | US companies certified under DPF |
| Derogations (Art. 49) | Limited use only | Explicit consent, contract necessity — not for systematic transfers |

**Transfer Impact Assessment (TIA) requirements for SCCs:**
1. Map the data flow (what data, to whom, where)
2. Assess recipient country legal framework (surveillance laws, access by authorities)
3. Evaluate supplementary measures needed (encryption, pseudonymization, contractual)
4. Document assessment and review annually

---

## AI-Specific GDPR Requirements

### Automated Decision-Making (Art. 22)

Art. 22 restricts decisions based solely on automated processing that produce legal or similarly significant effects:

| Requirement | Implementation |
|-------------|----------------|
| Right not to be subject to automated decisions | Provide human review mechanism for consequential decisions |
| Right to explanation | Document and explain logic, significance, and consequences |
| Right to contest | Enable data subjects to challenge automated decisions |
| Explicit consent or contract necessity | Secure Art. 22(2) legal basis before deploying |
| Suitable safeguards | Implement human oversight, right to express point of view |

**AI transparency checklist:**
- [ ] Document algorithmic logic in plain language
- [ ] Implement human-in-the-loop for high-stakes decisions (credit, employment, insurance)
- [ ] Provide opt-out mechanism for fully automated decisions
- [ ] Conduct and document bias testing (protected characteristics under Art. 9)
- [ ] Log all automated decisions with reasoning for auditability
- [ ] Include AI decision-making in privacy notice (Art. 13(2)(f), Art. 14(2)(g))

### AI Training Data Requirements

| Requirement | GDPR Basis | Action |
|-------------|------------|--------|
| Lawful basis for training data | Art. 6 | Legitimate interest (with DPIA) or consent |
| Purpose limitation | Art. 5(1)(b) | Training purpose must be compatible with original collection |
| Data minimization | Art. 5(1)(c) | Use minimum data necessary; prefer synthetic/anonymized data |
| Accuracy | Art. 5(1)(d) | Ensure training data is accurate and up-to-date |
| Storage limitation | Art. 5(1)(e) | Define retention for training datasets |
| Special category data | Art. 9 | Explicit consent or Art. 9(2)(j) research exemption for health/biometric data |
| Right to erasure | Art. 17 | Implement mechanism to remove individual data from training sets (or document inability) |
| Data scraping | Art. 14 | Inform data subjects when using publicly available data for training |

---

## Enhanced DPIA Methodology with EU AI Act Integration

### When DPIA + AI Act Conformity Assessment Overlap

For AI systems processing personal data, both GDPR Art. 35 DPIA and EU AI Act conformity assessment may apply:

| AI Risk Level (EU AI Act) | GDPR DPIA Required? | Combined Assessment Approach |
|---------------------------|----------------------|------------------------------|
| Unacceptable (Art. 5) | N/A — prohibited | Do not deploy |
| High-risk (Annex III) | Almost always yes | Joint DPIA + conformity assessment |
| Limited risk (Art. 50) | Evaluate per Art. 35 criteria | DPIA if systematic monitoring or profiling |
| Minimal risk | Evaluate per Art. 35 criteria | Standard DPIA threshold assessment |

### Enhanced DPIA Process for AI Systems

```
Step 1: AI System Classification
        → Classify under EU AI Act risk levels
        → Map to GDPR Art. 35(3) triggers

Step 2: Data Flow and Processing Analysis
        → Document training data sources and legal basis
        → Map inference data flows
        → Identify automated decision points (Art. 22)

Step 3: AI-Specific Risk Assessment
        → Bias and discrimination risk (protected groups)
        → Accuracy and reliability risk
        → Explainability and transparency gaps
        → Data quality and representativeness
        → Model drift and ongoing monitoring needs

Step 4: Fundamental Rights Impact
        → Right to non-discrimination
        → Right to privacy and data protection
        → Freedom of expression (content moderation AI)
        → Right to an effective remedy

Step 5: Combined Mitigation Measures
        → Technical: differential privacy, federated learning, model cards
        → Organizational: AI ethics board, human oversight procedures
        → Contractual: AI-specific DPA clauses with processors
        → Monitoring: continuous bias monitoring, performance drift detection

Step 6: DPO and Supervisory Authority Consultation
        → Consult DPO on combined assessment
        → Prior consultation with SA if high residual risk (Art. 36)
        → Notify national AI authority if high-risk AI system
```

---

## Privacy by Design Technical Controls

### Data Minimization Techniques

| Technique | Description | Use Case |
|-----------|-------------|----------|
| Field-level encryption | Encrypt specific PII fields at rest | Database storage |
| Tokenization | Replace PII with non-reversible tokens | Payment processing, analytics |
| Data masking | Obscure portions of data (e.g., email: j***@example.com) | UI display, logging |
| Aggregation | Process only aggregated/statistical data | Analytics, reporting |
| Purpose-scoped access | Limit data access to specific processing purposes | Multi-purpose systems |
| Automatic expiration | TTL-based data deletion | Session data, temporary processing |

### Pseudonymization Implementation (Recital 26, Art. 4(5))

| Method | Reversibility | Strength | Best For |
|--------|---------------|----------|----------|
| HMAC-based | Reversible with key | Strong | Internal analytics with re-identification need |
| Format-preserving encryption | Reversible with key | Strong | Legacy system compatibility |
| Deterministic hashing (salted) | One-way | Medium | Cross-dataset linkage without PII |
| Random ID mapping | Reversible with lookup table | Strong | Research datasets |

**Key management for pseudonymization:**
- Store re-identification keys separately from pseudonymized data
- Apply strict access controls to key material (minimum two-person rule)
- Document key rotation schedule
- Log all re-identification events

### Encryption Standards

| Layer | Minimum Standard | Recommended |
|-------|------------------|-------------|
| At rest | AES-256 | AES-256-GCM with envelope encryption |
| In transit | TLS 1.2 | TLS 1.3 |
| Database | Transparent Data Encryption (TDE) | Column-level encryption for PII |
| Backups | AES-256 | AES-256 + separate key from production |
| Key management | Hardware-backed (HSM/KMS) | Cloud KMS with customer-managed keys (BYOK) |

---

## Cross-Framework Privacy Mapping

| Requirement | GDPR Article | CCPA/CPRA Section | HIPAA Rule | NIS2 Article |
|-------------|-------------|-------------------|------------|--------------|
| Risk assessment | Art. 35 (DPIA) | §1798.185 (risk assessment regs) | §164.308(a)(1) | Art. 21(2)(a) |
| Breach notification | Art. 33-34 (72 hrs to SA) | §1798.150 (to consumers) | §164.404-408 (60 days) | Art. 23 (24 hrs early warning) |
| Data minimization | Art. 5(1)(c) | §1798.100(c) (collection limitation) | §164.502(b) (minimum necessary) | Art. 21(2)(e) |
| Encryption | Art. 32(1)(a) | Implicit (reasonable security) | §164.312(a)(2)(iv) (addressable) | Art. 21(2)(e) |
| Access controls | Art. 32(1)(b) | Implicit (reasonable security) | §164.312(a)(1) (access control) | Art. 21(2)(d) |
| Incident response | Art. 33-34 | §1798.150 | §164.308(a)(6) | Art. 21(2)(b) |
| Supply chain security | Art. 28 (processor agreements) | §1798.140(ag) (service provider contracts) | §164.308(b) (BAAs) | Art. 21(2)(d) |
| Governance/accountability | Art. 5(2), Art. 24 | §1798.185 (audit regs) | §164.308(a)(1) | Art. 20 (governance) |
| Right to delete/erasure | Art. 17 | §1798.105 | Limited (retention rules) | N/A |
| Data portability | Art. 20 | §1798.130(a)(2) | N/A | N/A |

> **Cross-references:** See `../information-security-manager-iso27001/SKILL.md` for ISO 27001 security controls, and `../mdr-745-specialist/SKILL.md` for healthcare device data protection under MDR.

---

## Cross-Framework Privacy Integration

### GDPR ↔ CCPA/CPRA Comparison

| Aspect | GDPR | CCPA/CPRA |
|--------|------|-----------|
| Scope | Any org processing EU residents' data | $25M+ revenue, 100K+ consumers, or 50%+ revenue from selling PI |
| Legal Basis | 6 legal bases required (Art. 6) | Opt-out model (no legal basis needed for collection) |
| Consent | Opt-in required | Opt-out for sale/sharing |
| Right to Delete | Art. 17 | §1798.105 |
| Data Portability | Art. 20 | §1798.130 |
| Penalties | Up to €20M or 4% global turnover | $2,500-$7,500 per violation |
| DPO Required | Yes (in many cases) | No |
| DPIA Required | Yes (high risk processing) | Risk assessments (CPRA) |

### AI-Specific GDPR Requirements

- **Automated Decision-Making (Art. 22):** Right not to be subject to decisions based solely on automated processing with legal/significant effects
- **AI Training Data:** Legitimate interest or consent required; purpose limitation applies to model training
- **Profiling:** Requires explicit consent for automated profiling with significant effects
- **EU AI Act Integration:** High-risk AI systems processing personal data require DPIA per Art. 35 GDPR
- **Cross-reference:** See `eu-ai-act-specialist` for AI-specific compliance

### Infrastructure Privacy Controls

- **Cookie Consent:** TCF 2.2 compliant consent management platform (CMP)
- **Global Privacy Control (GPC):** Must honor GPC browser signals (also CCPA requirement)
- **Data Localization:** EU data residency requirements, Schrems II adequacy decisions
- **Cross-Border Transfers:** Standard Contractual Clauses (SCCs), adequacy decisions, binding corporate rules
- **Privacy by Design Controls:** Data minimization, pseudonymization, encryption at rest/transit, access logging

### Cross-Framework Mapping

| Control | GDPR | CCPA | HIPAA | NIS2 |
|---------|------|------|-------|------|
| Privacy Notice | Art. 13-14 | §1798.100 | Privacy Practices | — |
| Data Subject Rights | Art. 15-22 | §1798.100-125 | Access/Amendment | — |
| Breach Notification | Art. 33-34 | §1798.150 | §164.404-408 | Art. 23 |
| DPO/Privacy Officer | Art. 37-39 | — | Privacy Officer | — |
| Risk Assessment | Art. 35 (DPIA) | Risk Assessment | §164.308(a)(1) | Art. 21 |
| Encryption | Art. 32 | Reasonable Security | §164.312(a)(2)(iv) | Art. 21.2.h |
| Training | Art. 39.1.b | — | §164.308(a)(5) | Art. 21.2.g |

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| Compliance checker reports critical findings for special category data | Code processes health, biometric, or religious data without explicit consent or Art. 9(2) exception | Identify all special category data processing; secure explicit consent or document applicable Art. 9(2) exception; implement field-level encryption for sensitive fields |
| DPIA generator determines assessment required but organization has no DPIA process | Processing triggers Art. 35(3) criteria (systematic monitoring, large-scale special categories, or automated decision-making) | Follow the DPIA methodology in `references/dpia_methodology.md`; generate template with `dpia_generator.py --template`; consult DPO before proceeding; consider prior consultation with supervisory authority if high residual risk (Art. 36) |
| Data subject rights requests consistently exceed 30-day deadline | Manual fulfillment without tracking system, unclear data location, or complex verification requirements | Deploy `data_subject_rights_tracker.py` for automated deadline monitoring; map all personal data locations using data inventory; streamline identity verification to proportionate measures |
| Cross-border transfer mechanism invalidated or uncertain | Reliance on deprecated mechanism or Transfer Impact Assessment not completed for SCCs | Review current adequacy decisions (UK, Japan, South Korea, US via DPF); for SCCs, complete Transfer Impact Assessment per Schrems II requirements; document supplementary measures (encryption, pseudonymization) |
| Cookie consent banner flagged as non-compliant | Pre-checked boxes, cookie wall blocking access, or reject button harder to find than accept | Implement TCF 2.2 compliant CMP; ensure all non-essential cookies blocked until explicit consent; make reject as prominent as accept (per Planet49 ruling, CJEU C-673/17); record consent proof |
| GDPR compliance checker detects personal data in application logs | Application logs contain email addresses, IP addresses, or user identifiers | Implement log sanitization to mask or pseudonymize personal data before storage; configure logging frameworks to exclude PII fields; set log retention limits aligned with purpose |
| AI system processing personal data lacks Art. 22 safeguards | Automated decision-making produces legal or significant effects without human review mechanism | Implement human-in-the-loop for high-stakes decisions; provide right to explanation and right to contest; document algorithmic logic in plain language; include AI decision-making in privacy notice per Art. 13(2)(f) |

---

## Success Criteria

- **Compliance score of 80+ on codebase scan** -- indicating no critical personal data exposure issues, with all high-risk patterns addressed and documented
- **All data subject rights requests fulfilled within 30 days** -- tracked via `data_subject_rights_tracker.py` with identity verification completed, response templates generated, and compliance reports showing zero overdue requests
- **DPIA completed for all high-risk processing activities** -- covering Art. 35(3) triggers, WP29 criteria, risk mitigation measures, and DPO consultation; prior SA consultation documented where required
- **Records of Processing Activities (Art. 30) maintained and current** -- covering all processing activities with purposes, legal bases, data categories, recipients, retention periods, and transfer mechanisms
- **Cross-border transfer mechanisms validated** -- adequacy decisions, SCCs with TIA, or BCRs in place for all international data flows, reviewed annually
- **Cookie consent implementation compliant** -- non-essential cookies blocked until explicit consent, reject as easy as accept, consent proof recorded with timestamp and version, GPC signal honored
- **DPO appointed and registered where required** -- including German BDSG Section 38 threshold (20+ employees processing personal data automatically), with supervisory authority notification

---

## Scope & Limitations

**In Scope:**
- Codebase scanning for personal data patterns and risky processing practices
- DPIA generation following Art. 35 requirements with threshold assessment and risk mitigation
- Data subject rights request tracking (Art. 15-22) with deadline monitoring and response templates
- German BDSG-specific requirements (DPO threshold, employment data, video surveillance, credit scoring)
- Cross-border transfer mechanism assessment (adequacy decisions, SCCs, BCRs, DPF)
- AI-specific GDPR requirements (Art. 22 automated decisions, training data governance, profiling)
- Cross-framework privacy mapping (GDPR, CCPA/CPRA, HIPAA, NIS2)

**Out of Scope:**
- Legal advice on specific legal basis selection or legitimate interest balancing tests -- consult DPO and legal counsel
- Supervisory authority notification or interaction for breach reporting (Art. 33-34)
- Implementation of cookie consent management platforms or consent management code
- GDPR representative appointment logistics for non-EU organizations (Art. 27)
- Binding Corporate Rules (BCR) application or approval process
- German Landesdatenschutzgesetze (state-level data protection laws) beyond general guidance

**Important Notes:**
- GDPR enforcement fines reached EUR 2.3 billion in 2025, a 38% year-over-year increase; healthcare violations spiked with average penalties of EUR 203,000
- The EU AI Act creates dual obligations for AI systems processing personal data -- both DPIA (GDPR Art. 35) and conformity assessment (AI Act) may apply simultaneously
- Dark patterns in consent interfaces are under heightened enforcement scrutiny; regulators are penalizing cookie walls, manipulative UI, and buried reject options

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `ccpa-cpra-privacy-expert` | Unified privacy program covering both GDPR and CCPA/CPRA; cross-framework mapping | When organization processes data of both EU residents and California consumers |
| `eu-ai-act-specialist` | Combined DPIA + AI Act conformity assessment for high-risk AI systems processing personal data | When AI system triggers both GDPR Art. 35 DPIA and EU AI Act high-risk classification |
| `information-security-manager-iso27001` | ISO 27001 security controls support GDPR Art. 32 security of processing requirements | When implementing technical and organizational measures for personal data protection |
| `infrastructure-compliance-auditor` | Technical privacy controls validation (encryption, access controls, logging, data masking) | When assessing infrastructure supporting GDPR privacy-by-design requirements |
| `dora-compliance-expert` | DORA complements GDPR for financial sector ICT systems processing personal data | When financial entity must align DORA ICT security with GDPR data protection requirements |

---

## Tool Reference

### gdpr_compliance_checker.py

Scans codebases for potential GDPR compliance issues including personal data patterns and risky code practices.

| Flag | Required | Description |
|------|----------|-------------|
| `<project_dir>` | Yes | Path to project directory to scan |
| `--json` | No | Output results in JSON format for CI/CD integration |
| `--output <file>` | No | Export report to specified file path |

**Detects:** Email, phone, IP address, credit card, IBAN, German ID patterns; special category data (health, biometric, religion); risky code patterns (logging PII, missing consent, indefinite retention, unencrypted sensitive data, disabled deletion). **Output:** Compliance score (0-100), risk categorization (critical/high/medium), and prioritized recommendations with GDPR article references.

### dpia_generator.py

Generates Data Protection Impact Assessment documentation following Art. 35 requirements.

| Flag | Required | Description |
|------|----------|-------------|
| `--template` | No | Generate blank DPIA input template to stdout |
| `--input <file>` | Yes (unless `--template` or `--interactive`) | Path to JSON processing activity description |
| `--output <file>` | No | Export DPIA report to specified file path (markdown format) |
| `--interactive` | No | Launch interactive mode for guided DPIA creation |

**Features:** Automatic DPIA threshold assessment against Art. 35(3) triggers and WP29 criteria, risk identification based on processing characteristics, legal basis documentation, mitigation recommendations, and markdown report generation.

### data_subject_rights_tracker.py

Manages data subject rights requests under GDPR Articles 15-22 with deadline tracking and response templates.

| Subcommand | Description |
|------------|-------------|
| `add` | Add new request (`--type`, `--subject`, `--email` required) |
| `list` | List all tracked requests |
| `status` | View or update request status (`--id` required, `--update` to change status) |
| `report` | Generate compliance report (`--output` for file export) |
| `template` | Generate response template for specific request (`--id` required) |

| Flag | Description |
|------|-------------|
| `--type <right>` | Right type: `access`, `rectification`, `erasure`, `restriction`, `portability`, `objection`, `automated` |
| `--subject <name>` | Data subject name |
| `--email <email>` | Data subject email address |
| `--id <request_id>` | Request identifier (e.g., `DSR-202601-0001`) |
| `--update <status>` | New status: `received`, `verified`, `in_progress`, `completed`, `denied`, `extended` |
| `--output <file>` | Export report or template to specified file path |

**Features:** 30-day deadline tracking with overdue alerts, identity verification workflow, response template generation per right type, and compliance reporting with metrics.

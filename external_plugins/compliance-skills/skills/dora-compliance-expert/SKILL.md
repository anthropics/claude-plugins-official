---
name: dora-compliance-expert
description: >
  DORA (EU 2022/2554) digital operational resilience compliance automation for
  financial entities. Assesses readiness against all 5 DORA pillars, classifies
  ICT incidents, validates third-party risk management, and generates resilience
  testing plans. Use for DORA compliance assessments, ICT risk management,
  incident classification, third-party ICT oversight, and digital operational
  resilience testing.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: financial-resilience
  updated: 2026-03-31
  tags: [dora, ict-risk, resilience-testing, financial-services]
---
# DORA Compliance Expert

Tools and guidance for Regulation (EU) 2022/2554 on digital operational resilience for the financial sector (Digital Operational Resilience Act — DORA).

---

## Table of Contents

- [DORA Overview](#dora-overview)
- [Scope](#scope)
- [Five Pillars Deep-Dive](#five-pillars-deep-dive)
- [Penalties and Enforcement](#penalties-and-enforcement)
- [DORA Implementation Roadmap](#dora-implementation-roadmap)
- [Infrastructure Checks](#infrastructure-checks)
- [Tools](#tools)
- [Reference Guides](#reference-guides)

---

## DORA Overview

The **Digital Operational Resilience Act (Regulation EU 2022/2554)** establishes a comprehensive framework for ICT risk management in the EU financial sector. It entered into force on January 16, 2023, and has been **applicable since January 17, 2025**.

**Key objectives:**

- Ensure financial entities can withstand, respond to, and recover from all types of ICT-related disruptions and threats
- Harmonize ICT risk management requirements across the financial sector
- Establish an oversight framework for critical ICT third-party service providers
- Promote information sharing on cyber threats within the financial sector

**Legal nature:** Unlike NIS2 (a directive requiring national transposition), DORA is a **regulation** — directly applicable in all EU Member States without transposition.

**Relationship to other frameworks:**

| Framework | Relationship |
|-----------|-------------|
| NIS2 Directive | DORA is lex specialis (specific law) for financial sector; NIS2 applies residually |
| GDPR | DORA complements GDPR for security of ICT systems processing personal data |
| EBA Guidelines on ICT | DORA supersedes prior EBA guidelines on ICT and security risk management |
| PSD2 | DORA enhances and extends PSD2 operational resilience requirements |
| MiCA | Crypto-asset service providers are in scope of both MiCA and DORA |
| ISO 27001 | DORA requirements map to ISO 27001 controls; certification supports compliance |

**Regulatory Technical Standards (RTS) and Implementing Technical Standards (ITS):**

DORA is supplemented by detailed RTS/ITS developed by the European Supervisory Authorities (ESAs: EBA, ESMA, EIOPA). Key RTS/ITS cover:

- ICT risk management framework details
- Incident classification criteria and reporting formats
- Threat-led penetration testing (TLPT) methodology
- ICT third-party register format
- Oversight framework procedures

---

## Scope

DORA applies to **20 types of financial entities** and their **critical ICT third-party service providers**.

### Financial Entities in Scope

| # | Entity Type | Examples |
|---|------------|---------|
| 1 | Credit institutions | Banks, building societies |
| 2 | Payment institutions | Payment service providers |
| 3 | Account information service providers | Open banking providers |
| 4 | Electronic money institutions | E-money issuers |
| 5 | Investment firms | Broker-dealers, portfolio managers |
| 6 | Crypto-asset service providers | Crypto exchanges, custodians |
| 7 | Issuers of asset-referenced tokens | Stablecoin issuers |
| 8 | Central securities depositories | CSDs |
| 9 | Central counterparties | CCPs |
| 10 | Trading venues | Stock exchanges, MTFs, OTFs |
| 11 | Trade repositories | Transaction reporting repositories |
| 12 | Managers of alternative investment funds | Hedge fund managers, PE managers |
| 13 | Management companies (UCITS) | Mutual fund managers |
| 14 | Data reporting service providers | ARMs, APAs |
| 15 | Insurance and reinsurance undertakings | Insurance companies |
| 16 | Insurance intermediaries | Insurance brokers (except SMEs) |
| 17 | Institutions for occupational retirement provision | Pension funds |
| 18 | Credit rating agencies | S&P, Moody's, Fitch, etc. |
| 19 | Administrators of critical benchmarks | LIBOR/EURIBOR administrators |
| 20 | Crowdfunding service providers | Investment crowdfunding platforms |

### Proportionality Principle

DORA applies proportionately based on the entity's:
- Size and overall risk profile
- Nature, scale, and complexity of services, activities, and operations
- Systemic importance

**Simplified ICT risk management framework** is available for:
- Small and non-interconnected investment firms
- Payment institutions exempted under PSD2
- Institutions exempted under Directive 2013/36/EU
- Electronic money institutions exempted under EMD2
- Small IORPs

### Critical ICT Third-Party Service Providers

The ESAs designate **critical ICT third-party service providers (CTPPs)** based on:
- Systemic impact of the services on financial entities
- Systemic character or importance of financial entities relying on the provider
- Degree of substitutability of the provider
- Number of Member States in which the provider operates

CTPPs are subject to the **Direct Oversight Framework** by the Lead Overseer (one of the ESAs).

---

## Five Pillars Deep-Dive

### Pillar 1: ICT Risk Management (Chapter II, Articles 5–16)

The cornerstone of DORA. Financial entities must establish a comprehensive ICT risk management framework.

#### Governance and Organization (Article 5)

The **management body** bears ultimate responsibility for ICT risk management:

- Define, approve, oversee, and be responsible for the implementation of the ICT risk management framework
- Define appropriate risk tolerance level for ICT risk
- Approve the digital operational resilience strategy
- Allocate adequate budget for ICT risk management
- Approve and review the ICT business continuity policy and ICT response and recovery plans
- Be informed at least once a year on findings of ICT risk reviews

**Organizational requirements:**
- Designate an ICT risk management function (second line of defense)
- Ensure adequate separation of ICT risk management, control, and internal audit functions
- Establish clear roles and responsibilities for all ICT-related functions
- Implement reporting lines ensuring the management body receives timely information

#### ICT Risk Management Framework (Article 6)

Entities must establish, maintain, and implement a sound, comprehensive, and well-documented ICT risk management framework that:

- Ensures a high level of digital operational resilience
- Is documented and reviewed at least annually (or after major ICT incidents)
- Includes a digital operational resilience strategy
- Defines how the framework supports the entity's business strategy
- Sets clear information security objectives
- Defines ICT risk tolerance levels
- Commits to a continuous improvement process

**Digital Operational Resilience Strategy must include:**
- Methods for addressing ICT risk
- Explanation of how the ICT risk management framework supports the business strategy
- ICT risk tolerance level
- Key information security objectives
- Overview of ICT reference architecture and changes needed
- Mechanisms for detecting ICT anomalies
- ICT third-party risk strategy
- Digital operational resilience testing approach
- Communication strategy for incident disclosure

#### ICT Systems, Protocols, and Tools (Article 7)

Requirements for ICT systems and infrastructure:
- Use and maintain updated ICT systems, protocols, and tools that are adequate to support critical operations
- Monitor effectiveness of ICT systems
- Identify all sources of ICT risk (including environmental risks and physical threats)
- Ensure appropriate network security management
- Implement mechanisms for detecting anomalous activities

#### Identification (Article 8)

- Identify, classify, and adequately document all ICT-supported business functions, information assets, and ICT assets
- Identify all sources of ICT risk, particularly cyber threats
- Map the interconnections and interdependencies with ICT third-party providers
- Perform ICT risk assessments at least annually (and after major changes)
- Identify assets and systems critical to business operations

#### Protection and Prevention (Article 9)

- Implement ICT security policies, procedures, protocols, and tools
- Continuously monitor and control the security and functioning of ICT systems
- Design network connection resilience mechanisms
- Deploy strong authentication mechanisms (MFA, Article 9(4))
- Implement ICT change management policies
- Apply software patching policies
- Implement data and system access policies based on least privilege

#### Detection (Article 10)

- Put in place mechanisms to promptly detect anomalous activities
- Detect network performance issues and ICT-related incidents
- Deploy multiple layers of controls (including automated alerting)
- Implement detection mechanisms that enable a fast response
- Allocate sufficient resources for monitoring trading activities

#### Response and Recovery (Article 11)

- Implement a comprehensive ICT business continuity policy
- Develop ICT response and recovery plans
- Activate response plans upon identification of ICT incidents
- Estimate preliminary impacts, damages, and losses
- Set communication and crisis management actions
- Execute ICT response and recovery procedures as appropriate

Specific requirements:
- Record all ICT-related incidents and significant cyber threats
- Activate containment measures and restoration of operations
- Implement backup and restoration policies and procedures
- When restoring data from backups, maintain the integrity and confidentiality of data

#### Backup and Restoration (Article 12)

- Establish backup policies specifying scope, frequency, and retention
- Restore backup data on separate ICT systems (not directly connected to source)
- Regularly test backup procedures and restoration capabilities
- When restoring data, ensure integrity checks are performed
- Maintain redundant ICT capacities equipped with sufficient resources

#### Learning and Evolving (Article 13)

- Gather information on vulnerabilities, cyber threats, and ICT-related incidents
- Review ICT-related incidents after recovery (post-incident reviews)
- Implement findings of post-incident reviews and digital operational resilience testing
- Monitor effectiveness of the ICT risk management framework
- Deliver mandatory annual ICT security awareness training for all staff
- Develop ICT security awareness programs for non-ICT staff

#### Communication (Article 14)

- Develop crisis communication plans for internal and external stakeholders
- Designate at least one spokesperson to communicate externally during incidents
- Define communication policies for responsible disclosure of ICT-related incidents
- Inform relevant clients and the public when appropriate

---

### Pillar 2: ICT-Related Incident Management (Chapter III, Articles 17–23)

#### Incident Management Process (Article 17)

Financial entities must:
- Define, establish, and implement an ICT-related incident management process
- Put in place early warning indicators to trigger detection
- Establish procedures to identify, track, log, categorize, and classify ICT-related incidents
- Assign roles and responsibilities for different incident types/scenarios
- Define plans for communication to staff, external stakeholders, media, and competent authorities

#### Classification of ICT-Related Incidents (Article 18)

Entities must classify incidents based on these criteria:

| Criterion | Description |
|-----------|------------|
| **Number of clients/counterparts affected** | Scale of impact on external parties |
| **Duration** | Length of the incident |
| **Geographic spread** | Jurisdictions and Member States affected |
| **Data losses** | Availability, authenticity, integrity, or confidentiality of data |
| **Criticality of services affected** | Impact on critical or important functions |
| **Economic impact** | Direct and indirect financial costs |

**Major incident** determination: An incident is classified as major if it meets the thresholds defined in the RTS on incident classification.

#### Reporting Obligations (Article 19)

| Stage | Deadline | Content |
|-------|----------|---------|
| **Initial notification** | Within **4 hours** of classifying as major (or 24 hours from detection) | Basic facts, initial classification, estimated impact |
| **Intermediate report** | Within **72 hours** of initial notification | Updated information, severity, root cause assessment, recovery status |
| **Final report** | Within **1 month** of intermediate report | Root cause analysis, complete impact assessment, mitigation measures, lessons learned |

**Additional requirements:**
- Entities must inform their clients without undue delay about major ICT-related incidents that affect their financial interests
- Entities must report to the competent authority using specified templates
- Competent authorities may request additional information at any time

#### Voluntary Reporting (Article 19(2))

Entities may voluntarily report:
- Significant cyber threats (even if they have not resulted in an incident)
- Near-misses that could have caused a major incident

#### Centralized Reporting (Article 20)

The ESAs develop common templates and procedures for incident reporting to reduce burden and ensure consistency.

---

### Pillar 3: Digital Operational Resilience Testing (Chapter IV, Articles 24–27)

#### General Requirements (Article 24)

All financial entities must establish, maintain, and review a digital operational resilience testing program as an integral part of their ICT risk management framework.

#### Basic Testing (Article 25)

All entities must perform, at a minimum:

| Test Type | Frequency | Description |
|-----------|-----------|------------|
| **Vulnerability assessments and scans** | Regular (at least annually) | Automated and manual vulnerability identification |
| **Open-source analyses** | Regular | Assessment of open-source software risks |
| **Network security assessments** | Annual minimum | Network architecture, configuration, traffic analysis |
| **Gap analyses** | Annual minimum | Comparison of current controls vs requirements |
| **Physical security reviews** | Periodic | Data center, office, and facility security |
| **Questionnaires and scanning software** | Regular | Compliance checking and configuration verification |
| **Source code reviews** | Where applicable | Security-focused code review for in-house applications |
| **Scenario-based tests** | Annual | Tabletop exercises, simulations |
| **Compatibility testing** | As needed | Testing for system updates and changes |
| **Performance testing** | Regular | Load and stress testing for critical systems |
| **End-to-end testing** | Regular | Testing of complete business process chains |
| **Penetration testing** | Annual minimum | Simulated attack testing |

#### Advanced Testing — Threat-Led Penetration Testing (Article 26)

**Applicable to:** Entities identified by competent authorities based on systemic importance, ICT risk profile, and criticality of services.

**TLPT requirements:**

- Based on the TIBER-EU framework
- Covers critical or important functions mapped to services, business processes, and ICT
- Conducted at least every 3 years
- Scope is determined by the financial entity, validated by the competent authority
- Must include live production systems
- The management body must approve the scope

**TLPT methodology:**

1. **Scoping phase:** Identify critical functions and supporting ICT infrastructure
2. **Threat intelligence phase:** Gather threat intelligence specific to the entity's sector and geography
3. **Red team phase:** Execute realistic attack scenarios against production systems
4. **Closure phase:** Report findings, remediation planning
5. **Purple team phase:** Collaborative exercises between red team (attackers) and blue team (defenders)

**Key rules:**
- Conducted by external testers with appropriate qualifications and independence
- Internal testers may participate under specific conditions
- Test results must be validated by competent authority
- Remediation plans must be produced and implemented
- Summary results must be shared with the competent authority

#### Purple Teaming

DORA introduces purple teaming as a key element:
- Collaborative exercise between red team and blue team
- Red team shares tactics, techniques, and procedures (TTPs) used
- Blue team reviews detection and response capabilities
- Joint identification of gaps and improvement areas
- Mandatory as part of the TLPT closure phase

---

### Pillar 4: ICT Third-Party Risk Management (Chapter V, Articles 28–44)

#### General Principles (Article 28)

Financial entities must:
- Manage ICT third-party risk as an integral component of ICT risk management
- Be responsible at all times for compliance, regardless of outsourcing
- Define strategy on ICT third-party risk (part of the digital resilience strategy)
- Maintain and update a register of information relating to all contractual arrangements on ICT services

#### Preliminary Assessment (Article 28(4))

Before entering into a contractual arrangement, entities must:
- Identify and assess all relevant risks (including concentration risk)
- Assess whether the arrangement covers critical or important functions
- Conduct appropriate due diligence on prospective ICT third-party providers
- Identify and assess conflicts of interest
- Verify the ICT third-party provider's ability to comply with applicable regulations

#### Key Contractual Provisions (Article 30)

Contracts with ICT third-party service providers must include:

| Provision | Description |
|-----------|------------|
| **Clear service descriptions** | Complete description of all services, including SLAs |
| **Location requirements** | Where data will be processed and stored, including sub-processing |
| **Data protection provisions** | Measures ensuring availability, authenticity, integrity, and confidentiality |
| **Service level commitments** | Quantitative and qualitative performance targets |
| **Assistance obligations** | ICT provider must assist with ICT incidents affecting the entity |
| **Cooperation with authorities** | Provider must cooperate with competent authorities and resolution authorities |
| **Termination rights** | Clear termination rights, including for performance failures and regulatory changes |
| **Transition and exit provisions** | Adequate transition periods and assistance for orderly transfer of services |
| **Participation in TLPT** | ICT provider must participate in entity's threat-led penetration testing |
| **Audit rights** | Full access and audit rights, including on-site inspections of the ICT provider |
| **Unrestricted right to monitor** | Right to continuously monitor provider's performance |
| **Exit strategies** | Mandatory exit strategies for critical or important function outsourcing |

**For critical or important functions**, additional contractual requirements apply:
- More detailed service level descriptions
- Notice periods and reporting obligations for material developments
- Full access to performance and security data
- ICT provider must implement and test business continuity plans
- Provider must provide staff training on ICT security awareness

#### Register of ICT Third-Party Arrangements (Article 28(3))

Entities must maintain a register containing:
- All contractual arrangements with ICT third-party providers
- Distinction between critical/important and non-critical functions
- Entity identification details (LEI, type, group structure)
- Service details (type, start date, end date, governing law, data processing locations)
- Sub-contractor chain information
- Exit strategy information

The register must be reported to competent authorities upon request.

#### Exit Strategies (Article 28(8))

For critical or important functions, entities must:
- Develop exit strategies that are comprehensive, documented, and tested
- Ensure sufficient transition arrangements that avoid disruption or degradation of services
- Consider alternative solutions and transition plans
- Enable recovery of data and applications

#### Oversight Framework for Critical ICT Third-Party Providers (Articles 31–44)

The ESAs designate CTPPs and assign a Lead Overseer. The oversight framework includes:

- Direct supervision powers over CTPPs
- On-site inspections of CTPPs
- Power to request information and issue recommendations
- Annual oversight plans
- CTPPs must cooperate with the Lead Overseer
- Non-compliance may result in periodic penalty payments

#### Concentration Risk (Article 29)

Entities must:
- Identify and assess risks arising from concentrating ICT service arrangements on a single provider
- Assess whether planned ICT outsourcing leads to material concentration risk
- Consider the substitutability of the ICT third-party provider
- Develop multi-vendor strategies where appropriate

---

### Pillar 5: Information Sharing (Chapter VI, Article 45)

#### Voluntary Cyber Threat Intelligence Sharing

Financial entities **may** exchange amongst themselves cyber threat intelligence information including:
- Indicators of compromise (IoCs)
- Tactics, techniques, and procedures (TTPs)
- Cybersecurity alerts and configuration tools
- Tools and methods for detecting cyberattacks

#### Requirements for Sharing Arrangements

- Sharing must aim to enhance digital operational resilience
- Must be within trusted communities of financial entities
- Arrangements must respect business confidentiality and data protection
- Must protect personal data in accordance with GDPR
- Sharing may be enabled through information sharing and analysis centers (ISACs)

#### Notification Requirements

Entities must notify competent authorities of their participation in information-sharing arrangements.

---

## Penalties and Enforcement

### Administrative Penalties

DORA delegates penalty-setting to Member States and competent authorities. The regulation empowers authorities to impose:

- Administrative penalties and remedial measures proportionate to the infringement
- Periodic penalty payments to compel compliance
- Public statements identifying the entity and the nature of the infringement
- Orders to cease conduct and to desist from repetition
- Temporary or permanent prohibition of certain activities

### Enforcement Powers

Competent authorities have powers to:
- Require access to any document, data, or information
- Conduct on-site inspections
- Require remediation within a specified timeframe
- Suspend or restrict activities
- Impose administrative penalties

### CTPP Oversight Penalties

For critical ICT third-party service providers:
- The Lead Overseer may issue recommendations
- Non-compliance with recommendations may lead to periodic penalty payments
- Maximum penalty: 1% of average daily worldwide turnover per day, for up to 6 months

---

## DORA Implementation Roadmap

### 9-Month Plan

| Month | Phase | Key Activities |
|-------|-------|---------------|
| 1 | **Assessment** | Map ICT risk landscape, identify applicable DORA requirements, gap analysis against 5 pillars |
| 2 | **Framework Design** | Design ICT risk management framework, define governance structure, establish policies |
| 3 | **ICT Risk Management** | Implement risk identification, protection, detection, and response procedures |
| 4 | **Incident Management** | Deploy incident classification, establish reporting procedures, prepare templates |
| 5 | **Third-Party Risk** | Build ICT third-party register, assess critical providers, update contracts |
| 6 | **Third-Party Risk (cont.)** | Complete contractual updates, develop exit strategies, assess concentration risk |
| 7 | **Resilience Testing** | Design testing program, execute basic tests (vulnerability scanning, gap analysis) |
| 8 | **Advanced Testing** | Conduct penetration testing, scenario-based exercises, TLPT preparation (if applicable) |
| 9 | **Validation** | Internal audit, remediation, management body reporting, continuous improvement setup |

### Quick Wins (Month 1–2)

1. Establish ICT risk management governance (management body accountability)
2. Begin building the ICT third-party register
3. Review and update incident response procedures for DORA timelines (4h/72h/1mo)
4. Ensure management body receives regular ICT risk reporting
5. Verify MFA deployment for critical systems
6. Document existing BCP/DRP for ICT systems

---

## Infrastructure Checks

### ICT Asset Inventory

- Maintain a comprehensive register of all ICT assets (hardware, software, network, cloud)
- Classify assets by criticality and map to business functions
- Include dependencies on ICT third-party providers
- Update inventory upon any changes to ICT infrastructure

### Network Resilience Testing

- Annual network security assessments
- Network architecture review and segmentation validation
- DDoS resilience testing for public-facing services
- Redundant network path verification
- Network monitoring and anomaly detection validation

### Data Center Redundancy

- Active-active or active-passive redundancy for critical systems
- Geographic separation of primary and secondary data centers
- Automated failover mechanisms tested regularly
- Power and cooling redundancy verification
- Physical security assessment of data centers

### Business Continuity Testing

- Annual BCP exercise for all critical business functions
- ICT disaster recovery testing covering failover and restoration
- Scenario-based testing (cyber incident, natural disaster, provider failure)
- Recovery time and recovery point validation against targets
- Post-exercise improvement tracking

### Disaster Recovery Capabilities

- Documented DRP for all critical ICT systems
- Backup restoration tested on separate environments
- Immutable backup storage for ransomware resilience
- Communication plans for disaster scenarios
- Coordination procedures with ICT third-party providers

### Third-Party Dependency Mapping

- Map all ICT third-party providers to business functions
- Identify critical dependencies and single points of failure
- Assess concentration risk across providers
- Document sub-contractor chains for critical services
- Verify provider business continuity capabilities

---

## Tools

### DORA Readiness Checker

Assesses organizational readiness against all 5 DORA pillars with per-pillar scoring.

```bash
# Generate assessment template
python scripts/dora_readiness_checker.py --template > assessment.json

# Run full readiness assessment
python scripts/dora_readiness_checker.py --config assessment.json

# Assess specific pillars only
python scripts/dora_readiness_checker.py --config assessment.json --pillars 1 3 4 --json

# Generate report with JSON output
python scripts/dora_readiness_checker.py --config assessment.json --output readiness_report.json --json
```

**Features:**
- Assessment against all 5 DORA pillars
- Per-pillar readiness scoring (0–100)
- Overall readiness score
- ICT risk management framework validation
- Incident management readiness check
- Third-party risk management assessment
- Resilience testing program evaluation
- Gap analysis with prioritized remediation recommendations

---

### DORA Incident Classifier

Classifies ICT incidents per DORA criteria and determines reporting obligations.

```bash
# Classify an incident interactively
python scripts/dora_incident_classifier.py --clients-affected 5000 --duration-hours 4 --data-loss yes --services-critical yes --economic-impact 500000

# Classify from JSON input
python scripts/dora_incident_classifier.py --config incident.json --json

# Generate incident notification template
python scripts/dora_incident_classifier.py --config incident.json --generate-template --output notification.json
```

**Features:**
- Incident classification per Article 18 criteria
- Major incident determination
- Reporting deadline calculation (4h initial, 72h intermediate, 1 month final)
- Incident notification template generation
- Severity scoring and impact assessment

---

## Reference Guides

### [DORA Five Pillars Guide](references/dora-five-pillars-guide.md)

Complete implementation guidance for all 5 DORA pillars with ISO 27001 control mapping, financial-sector-specific requirements, and RTS/ITS references.

### [DORA Third-Party Management Guide](references/dora-third-party-management.md)

ICT third-party register template, contractual requirements checklist, exit strategy framework, concentration risk assessment methodology, and critical provider oversight.

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| Readiness score unexpectedly low on Pillar 1 (ICT Risk Management) | Management body has not formally approved the ICT risk management framework | Ensure the management body signs off on the framework, digital resilience strategy, and ICT risk tolerance level per Article 5; document board meeting minutes |
| Incident classification tool returns "major" for minor service interruptions | Threshold parameters set too conservatively or default values used | Review classification criteria against actual RTS thresholds; adjust `--clients-affected`, `--duration-hours`, and `--economic-impact` inputs to match your entity's context |
| Third-party register incomplete despite significant outsourcing | ICT service arrangements not systematically tracked or sub-contractor chains undocumented | Inventory all contractual ICT arrangements; use the register template from `references/dora-third-party-management.md`; include sub-processing chains and data processing locations |
| Resilience testing program scored as non-compliant | Only basic vulnerability scanning performed; no scenario-based or penetration testing | Design a comprehensive testing program per Article 25 covering all 12 test types; schedule annual penetration testing and scenario-based exercises; plan for TLPT if designated by competent authority |
| Pillar 5 (Information Sharing) shows zero compliance | Organization has not joined any cyber threat intelligence sharing arrangement | Evaluate participation in an ISAC (Information Sharing and Analysis Center) relevant to your financial sub-sector; notify competent authority of participation per Article 45 |
| Exit strategies missing for critical ICT third-party providers | Contracts lack termination, transition, and data recovery provisions | Update all contracts for critical functions to include comprehensive exit strategies per Article 28(8); test transition plans and document alternative provider options |
| Proportionality assessment unclear | Organization unsure whether simplified framework applies | Assess entity size, risk profile, and systemic importance per DORA proportionality principle; small and non-interconnected firms may qualify for simplified requirements |

---

## Success Criteria

- **Overall readiness score of 75+ across all 5 pillars** -- indicating the organization can demonstrate compliance with core DORA requirements to competent authorities
- **ICT risk management framework formally approved by the management body** -- with documented digital operational resilience strategy, risk tolerance levels, and annual review cycle
- **Incident classification and reporting procedures operational** -- with capability to submit initial notification within 4 hours of major incident classification and intermediate report within 72 hours
- **Complete ICT third-party register maintained** -- covering all contractual arrangements, distinguishing critical/important functions, with entity identification, service details, and sub-contractor chains
- **Resilience testing program covers all 12 required test types** -- with annual penetration testing, scenario-based exercises, and TLPT preparation (if applicable) per Articles 24-27
- **Exit strategies documented and tested for all critical ICT providers** -- with comprehensive transition arrangements, alternative provider identification, and data recovery procedures
- **Annual ICT security awareness training delivered to all staff** -- with records maintained and specialized training for ICT and security personnel per Article 13

---

## Scope & Limitations

**In Scope:**
- Readiness assessment against all 5 DORA pillars with per-pillar scoring
- ICT incident classification per Article 18 criteria with major incident determination
- Reporting deadline calculation (4-hour initial, 72-hour intermediate, 1-month final)
- Incident notification template generation for competent authority submissions
- Third-party risk management guidance including register template and contractual requirements
- Resilience testing program design covering basic and advanced (TLPT) testing
- Gap analysis with prioritized remediation recommendations

**Out of Scope:**
- Actual penetration testing execution or vulnerability scanning -- this skill provides planning and assessment frameworks, not testing tools
- Direct interaction with competent authorities or ESAs (EBA, ESMA, EIOPA)
- Legal determination of entity scope (whether your organization falls under DORA's 20 entity types) -- consult regulatory counsel
- CTPP (Critical Third-Party Provider) oversight framework compliance -- applicable only to ESA-designated providers
- Real-time ICT monitoring or SIEM implementation -- use `infrastructure-compliance-auditor` for technical security controls

**Important Notes:**
- DORA became applicable January 17, 2025; regulators are treating 2025 as a transition year but enforcement is expected to intensify in 2026
- Non-compliance penalties can reach up to 2% of total annual worldwide turnover or 1% of average daily global turnover for up to 6 months (for CTPPs)

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `information-security-manager-iso27001` | ISO 27001 controls map directly to DORA Pillar 1 requirements; ISO 27001 certification supports DORA compliance evidence | When building ICT risk management framework aligned with both ISO 27001 and DORA |
| `nis2-directive-specialist` | DORA is lex specialis for financial sector; NIS2 applies residually; coordinate incident reporting timelines | When financial entity also falls under NIS2 scope for non-financial ICT services |
| `infrastructure-compliance-auditor` | Technical infrastructure checks validate DORA Pillar 1 (protection, detection) and Pillar 3 (resilience testing) controls | When assessing actual infrastructure security posture against DORA requirements |
| `nist-csf-specialist` | NIST CSF 2.0 functions map to DORA pillars; useful for organizations with US operations | When building a unified resilience framework across US and EU requirements |

---

## Tool Reference

### dora_readiness_checker.py

Assesses organizational readiness against all 5 DORA pillars with per-pillar scoring and gap analysis.

| Flag | Required | Description |
|------|----------|-------------|
| `--config <file>` | Yes (unless `--template`) | Path to JSON assessment configuration file |
| `--template` | No | Generate blank assessment template to stdout |
| `--pillars <nums>` | No | Assess specific pillars only (e.g., `--pillars 1 3 4`) |
| `--json` | No | Output results in JSON format for automation |
| `--output <file>` | No | Export report to specified file path |

**Output:** Overall readiness score (0-100), per-pillar readiness scores, ICT risk management framework validation, incident management readiness, third-party risk assessment, resilience testing evaluation, and prioritized remediation recommendations.

### dora_incident_classifier.py

Classifies ICT incidents per DORA Article 18 criteria and determines reporting obligations.

| Flag | Required | Description |
|------|----------|-------------|
| `--config <file>` | No | Path to JSON incident description file |
| `--template` | No | Generate blank incident input template to stdout |
| `--clients-affected <num>` | No | Number of clients/financial counterparts affected |
| `--duration-hours <num>` | No | Duration of the incident in hours |
| `--data-loss <yes/no>` | No | Whether data loss occurred (availability, integrity, or confidentiality) |
| `--services-critical <yes/no>` | No | Whether critical or important functions were affected |
| `--economic-impact <num>` | No | Estimated economic impact in EUR |
| `--json` | No | Output results in JSON format |
| `--generate-template` | No | Generate incident notification template for competent authority |
| `--output <file>` | No | Export report or template to specified file path |

**Output:** Incident severity scoring per Article 18 criteria, major incident determination, reporting deadline calculation (initial 4h, intermediate 72h, final 1 month), and notification template generation.

---

*Last Updated: March 2026*
*Regulation Reference: EU 2022/2554*
*Applicable From: January 17, 2025*

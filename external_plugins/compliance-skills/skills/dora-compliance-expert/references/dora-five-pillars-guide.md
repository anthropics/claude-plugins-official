# DORA Five Pillars — Implementation Guide

Complete implementation guidance for all 5 pillars of the Digital Operational Resilience Act (EU 2022/2554), with ISO 27001 control mapping, financial-sector-specific requirements, and RTS/ITS references.

---

## Table of Contents

- [Pillar 1: ICT Risk Management](#pillar-1-ict-risk-management)
- [Pillar 2: ICT-Related Incident Management](#pillar-2-ict-related-incident-management)
- [Pillar 3: Digital Operational Resilience Testing](#pillar-3-digital-operational-resilience-testing)
- [Pillar 4: ICT Third-Party Risk Management](#pillar-4-ict-third-party-risk-management)
- [Pillar 5: Information Sharing](#pillar-5-information-sharing)
- [ISO 27001 Control Mapping](#iso-27001-control-mapping)
- [RTS/ITS References](#rtsits-references)

---

## Pillar 1: ICT Risk Management

### Articles 5–16 Implementation

#### Governance Framework (Article 5)

**Implementation steps:**

1. **Management body accountability**
   - Document management body responsibilities for ICT risk in the entity's governance framework
   - Include ICT risk management as a standing agenda item in board/management meetings
   - Ensure the management body defines and approves the ICT risk tolerance level
   - Allocate dedicated budget for ICT risk management (separate line item)

2. **Organizational structure**
   - Appoint a Chief Information Security Officer (CISO) or equivalent with direct reporting line to management body
   - Establish an ICT risk management function (second line of defense)
   - Ensure separation between ICT risk management, ICT operations/control, and internal audit
   - Define RACI matrix for all ICT-related functions

3. **Digital operational resilience strategy (Article 6(8))**

   The strategy must include:
   - Explanation of how ICT risk management supports the business strategy
   - ICT risk tolerance level and key information security objectives
   - Description of the ICT reference architecture and changes needed
   - Mechanisms for detecting and responding to ICT anomalies
   - ICT third-party risk strategy
   - Digital operational resilience testing approach
   - Communication strategy for ICT incident disclosure

   **Financial sector specificity:** The strategy must consider the entity's interconnectedness with the broader financial system, systemic importance, and potential cascading effects.

#### ICT Systems and Tools (Article 7)

- Deploy systems, protocols, and tools that are adequate in design and updated
- Invest in ICT capacity proportionate to business needs and risk profile
- Implement reliability, capacity, and business continuity as design principles
- Document all ICT systems supporting critical or important functions

#### Identification (Article 8)

- Identify and classify all ICT-supported business functions, roles, and assets
- Map interdependencies among ICT assets and between entity and third-party providers
- Maintain updated network topology and data flow documentation
- Identify assets and services supporting critical/important functions
- Perform ICT risk assessments annually and after significant changes

**Financial sector specificity:** Financial entities must specifically map dependencies relevant to financial stability, payment systems, and settlement processes.

#### Protection and Prevention (Article 9)

Key requirements:
- Continuous monitoring and control of ICT system security
- Network connection resilience (redundant paths, failover)
- MFA for access to critical systems (Article 9(4))
- Strong authentication mechanisms
- ICT change management with security review
- Software patching policies with defined timelines
- Least privilege access control

**Financial sector specificity:** Payment systems, trading platforms, and settlement systems require enhanced protection measures due to real-time availability requirements and financial impact of disruption.

#### Detection (Article 10)

- Multiple layers of detection controls
- Automated alerting mechanisms
- Sufficient resources and capabilities for monitoring trading activities
- Detection mechanisms that enable multi-stage attack identification
- Log collection from all critical systems with adequate retention

#### Response and Recovery (Articles 11–12)

- ICT business continuity policy covering all critical functions
- Response and recovery plans tested annually
- Backup policies with:
  - Defined scope, frequency, and retention
  - Restoration on separate, independent systems
  - Integrity verification after restoration
  - Redundant ICT capacities with adequate resources

**Financial sector specificity:** Recovery objectives must consider market hours, settlement cycles, and regulatory reporting deadlines. Payment systems may require near-zero RPO.

#### Learning and Evolving (Article 13)

- Mandatory post-incident reviews for all significant incidents
- Vulnerability and threat intelligence gathering
- Annual ICT security awareness training for all staff (mandatory)
- ICT security awareness programs for non-ICT personnel
- Implementation of findings from testing and post-incident analysis

#### Communication (Article 14)

- Crisis communication plans for both internal and external stakeholders
- At least one designated spokesperson for external crisis communication
- Responsible disclosure policies for ICT-related incidents
- Coordination with competent authorities during incidents

---

## Pillar 2: ICT-Related Incident Management

### Articles 17–23 Implementation

#### Building the Incident Management Process (Article 17)

**Step 1: Detection and identification**
- Deploy early warning indicators across all critical systems
- SIEM integration with financial-sector-specific use cases
- Automated correlation of events from multiple sources
- Integration with threat intelligence feeds relevant to financial sector

**Step 2: Classification (Article 18)**

Classify every incident using all six criteria:

| Criterion | Data Required | Source |
|-----------|--------------|--------|
| Clients/counterparts affected | Customer count, counterparty count | CRM, trading systems |
| Duration | Start time, resolution time | Incident management system |
| Geographic spread | Affected jurisdictions | Service monitoring, customer data |
| Data losses | Type and volume of data affected | Forensic analysis, DLP systems |
| Service criticality | Mapping of affected systems to business functions | Business service catalog |
| Economic impact | Direct costs, indirect costs, regulatory costs | Finance, risk management |

**Step 3: Major incident determination**

An incident is major when it meets thresholds defined in the RTS on incident classification criteria (delegated to ESAs). Key indicators:
- Significant number of clients unable to access financial services
- Extended duration affecting critical functions
- Cross-border impact affecting financial stability
- Loss or compromise of financially sensitive data
- Substantial economic impact (direct and indirect)

**Step 4: Reporting timeline**

```
Detection → Classification → Initial (4h) → Intermediate (72h) → Final (1 month)
     |            |                |                |                    |
   ASAP      ASAP after       4h from          72h from            1 month from
            detection      classification    initial report     intermediate report
                          (max 24h from
                           detection)
```

**Step 5: Client notification**
- Determine if clients' financial interests are affected
- Notify without undue delay using appropriate channels
- Include description of incident, impact, and remedial measures

#### Reporting Templates

**Initial notification content:**
- Entity identification (name, LEI, entity type)
- Incident reference and classification date/time
- Brief description
- Affected services and functions
- Initial impact assessment
- Suspected cause (malicious/non-malicious)

**Intermediate report content:**
- Updated severity and impact assessment
- Root cause assessment (if determined)
- Recovery status and timeline
- Indicators of compromise
- Additional measures implemented

**Final report content:**
- Complete timeline
- Detailed root cause analysis
- Full impact assessment (financial, operational, data, reputational)
- Mitigation measures applied and ongoing
- Lessons learned and improvement actions

---

## Pillar 3: Digital Operational Resilience Testing

### Articles 24–27 Implementation

#### Testing Program Design

**Program structure:**

| Test Category | Frequency | Scope | Applicable Entities |
|--------------|-----------|-------|-------------------|
| Vulnerability scanning | Continuous/weekly | All systems | All |
| Network security assessment | Annual | Network infrastructure | All |
| Gap analysis | Annual | Controls vs requirements | All |
| Scenario-based testing | Annual | Critical functions | All |
| Penetration testing | Annual | Critical systems | All |
| Source code review | Per release/annual | In-house applications | All with in-house development |
| Open-source analysis | Per release/continuous | OSS dependencies | All using OSS |
| Physical security review | Annual | Data centers, offices | All |
| TLPT | Every 3 years | Critical functions (production) | Designated entities only |

#### Basic Testing Requirements (Article 25)

All financial entities must perform:

1. **Vulnerability assessments and scans**
   - External vulnerability scanning at least weekly
   - Internal scanning at least monthly
   - Web application scanning for all public-facing applications
   - Remediation tracking with defined SLAs

2. **Network security assessments**
   - Architecture review and segmentation validation
   - Firewall rule review and optimization
   - Network traffic analysis for anomalies
   - Wireless network security assessment

3. **Gap analyses**
   - Compare current controls against DORA requirements
   - Map to RTS/ITS technical standards
   - Identify and prioritize remediation actions

4. **Scenario-based tests**
   - Cyber attack scenarios (ransomware, APT, DDoS)
   - Third-party provider failure scenarios
   - Multi-event scenarios (cascading failures)
   - Crisis communication exercises
   - Include management body participation in major scenarios

5. **Penetration testing**
   - External network penetration testing
   - Web application penetration testing
   - Internal network penetration testing
   - Social engineering testing (phishing, vishing)
   - Mobile application testing (if applicable)

6. **Source code reviews**
   - SAST integrated into CI/CD pipelines
   - Manual security code review for critical changes
   - Open-source dependency analysis (SCA)
   - License compliance checking for OSS

#### TLPT — Threat-Led Penetration Testing (Article 26)

**Applicability:** Only entities designated by competent authorities based on systemic importance and risk profile.

**TLPT process based on TIBER-EU:**

```
Phase 1: Scoping (4-6 weeks)
├── Identify critical/important functions
├── Map supporting ICT infrastructure
├── Define scope boundaries with competent authority
└── Management body approval

Phase 2: Threat Intelligence (4-6 weeks)
├── Sector-specific threat landscape analysis
├── Entity-specific threat assessment
├── Attack scenario development
└── TTP (Tactics, Techniques, Procedures) selection

Phase 3: Red Team Testing (8-12 weeks)
├── Execute realistic attack scenarios
├── Target production systems (live environment)
├── Multiple attack vectors
├── Document all activities and findings
└── Maintain strict operational security

Phase 4: Closure (4-6 weeks)
├── Red team debrief and reporting
├── Blue team review (detection and response assessment)
├── Purple team exercises (collaborative analysis)
├── Remediation plan development
├── Management body presentation
└── Summary report to competent authority
```

**Purple teaming requirements:**
- Red team shares TTPs, tools, and attack paths
- Blue team assesses detection coverage for each TTP
- Joint gap identification for detection and response
- Collaborative improvement recommendations
- Documentation of purple team findings and remediation

**Key TLPT rules:**
- Must be conducted by qualified external testers
- Internal testers may participate under specific conditions
- Tests must cover live production systems
- Results must be validated by the competent authority
- Remediation of findings is mandatory
- Summary must be shared with the competent authority

---

## Pillar 4: ICT Third-Party Risk Management

### Articles 28–44 Implementation

#### Lifecycle Management

```
Assessment → Contracting → Onboarding → Monitoring → Review → Exit/Renewal
     |            |            |            |           |          |
  Due diligence  DORA-compliant  Security    Ongoing    Annual    Exit
  Risk assessment  provisions   integration  SLA/security review  strategy
  Concentration   Article 30    verification monitoring          execution
  risk check
```

#### Pre-Engagement Assessment

**Due diligence checklist:**

- [ ] Provider financial stability assessment
- [ ] Provider security certifications (ISO 27001, SOC 2, etc.)
- [ ] Provider business continuity capabilities
- [ ] Geographic location of data processing and storage
- [ ] Sub-contractor chain transparency
- [ ] Regulatory compliance status
- [ ] Conflict of interest evaluation
- [ ] Concentration risk assessment
- [ ] Substitutability analysis
- [ ] Reference checks from other financial entity clients

#### Contract Management

**Mandatory contractual provisions (Article 30):**

For all ICT service arrangements:
1. Clear and complete service descriptions with SLAs
2. Data processing locations (including sub-processing)
3. Data availability, authenticity, integrity, and confidentiality measures
4. Quantitative and qualitative performance targets
5. Provider assistance obligations during ICT incidents
6. Cooperation requirements with competent and resolution authorities
7. Termination rights (including for performance failure and regulatory change)
8. Transition and exit provisions
9. TLPT participation requirements
10. Full audit and access rights (including on-site inspections)
11. Unrestricted right to monitor performance

For critical or important functions (Article 30(3), additional):
12. Detailed service level descriptions
13. Notice periods and reporting for material developments
14. Full access to performance and security data
15. Mandatory BCP testing by provider
16. ICT security awareness training for provider staff
17. Provider participation in entity's security testing

#### Ongoing Monitoring

- Track SLA compliance continuously
- Monitor provider security posture (certifications, incidents, vulnerabilities)
- Review sub-contractor changes
- Assess provider financial health annually
- Verify data processing location compliance
- Monitor regulatory changes affecting the arrangement

#### Exit Strategy Framework

For critical/important function arrangements:

1. **Trigger conditions**
   - Provider material breach of contract
   - Provider insolvency or financial instability
   - Regulatory requirement to exit
   - Concentration risk exceeding tolerance
   - Provider designated as CTPP with restrictions

2. **Transition planning**
   - Identify alternative providers or insourcing options
   - Define data migration procedures
   - Document system integration requirements
   - Establish transition timeline (typically 6-18 months)
   - Test transition procedures before they are needed

3. **Data management**
   - Data extraction and portability requirements
   - Data format and structure specifications
   - Secure deletion verification from outgoing provider
   - Continuity of data integrity during migration

---

## Pillar 5: Information Sharing

### Article 45 Implementation

#### Setting Up Sharing Arrangements

1. **Identify relevant sharing communities**
   - Financial sector ISACs (e.g., FS-ISAC, European FI-ISAC)
   - National CERT/CSIRT communities
   - Sector-specific threat intelligence sharing groups
   - Vendor-operated threat intelligence platforms

2. **Establish governance**
   - Define what can be shared (IoCs, TTPs, strategic intelligence)
   - Establish data handling procedures (TLP protocol)
   - Ensure GDPR compliance for any personal data in threat data
   - Protect business confidentiality and competition-sensitive information

3. **Operationalize**
   - Integrate threat intelligence feeds into SIEM/SOC
   - Establish processes to analyze and act on received intelligence
   - Contribute back to the community with sanitized threat data
   - Report participation to competent authority

---

## ISO 27001 Control Mapping

### Complete DORA to ISO 27001:2022 Mapping

| DORA Article | Topic | ISO 27001:2022 Controls |
|-------------|-------|------------------------|
| Art. 5 | Governance | Cl.5.1 (Leadership), Cl.5.2 (Policy), Cl.5.3 (Roles) |
| Art. 6 | ICT risk management framework | Cl.4.1-4.4 (Context), Cl.6.1 (Risk assessment), Cl.8 (Operation) |
| Art. 7 | ICT systems and tools | A.8.9 (Configuration), A.8.20 (Networks), A.8.26 (Application security) |
| Art. 8 | Identification | A.5.9-5.12 (Asset management), Cl.6.1.2 (Risk identification) |
| Art. 9 | Protection and prevention | A.5.15-5.18 (Access control), A.8.5 (Authentication), A.8.8 (Vulnerability), A.8.9 (Configuration), A.8.20-8.22 (Network security) |
| Art. 10 | Detection | A.8.15 (Logging), A.8.16 (Monitoring) |
| Art. 11 | Response and recovery | A.5.24-5.27 (Incident management), A.5.29-5.30 (Business continuity) |
| Art. 12 | Backup and restoration | A.8.13 (Backup), A.8.14 (Redundancy) |
| Art. 13 | Learning and evolving | Cl.10.1-10.2 (Improvement), A.5.27 (Lessons learned), A.6.3 (Awareness) |
| Art. 14 | Communication | A.5.5-5.6 (Communication), A.5.24 (IR planning) |
| Art. 17 | Incident management process | A.5.24 (IR planning), A.5.25 (Assessment and decision) |
| Art. 18 | Classification | A.5.25 (Assessment and decision) |
| Art. 19 | Reporting | A.5.26 (Response to incidents) |
| Art. 24-25 | Basic testing | Cl.9.1 (Monitoring), A.8.8 (Vulnerability management) |
| Art. 26 | TLPT | No direct equivalent (DORA-specific) |
| Art. 28 | Third-party risk | A.5.19-5.23 (Supplier management) |
| Art. 29 | Concentration risk | A.5.21 (ICT supply chain) |
| Art. 30 | Contractual provisions | A.5.20 (Addressing security in supplier agreements) |
| Art. 45 | Information sharing | A.5.7 (Threat intelligence) |

### Gap Analysis for ISO 27001 Certified Organizations

Organizations with ISO 27001 certification typically have **50-65% of DORA requirements** covered. Key gaps:

1. **DORA-specific governance requirements** — Management body must directly approve and oversee ICT risk management (not just delegate)
2. **Incident reporting timelines** — 4-hour initial notification is significantly more aggressive than ISO 27001 requirements
3. **TLPT** — No equivalent in ISO 27001; requires threat intelligence-based red teaming against production systems
4. **ICT third-party register** — DORA requires a structured register of all ICT arrangements with specific fields
5. **Concentration risk** — Explicit requirement to assess and manage ICT provider concentration
6. **Exit strategies** — Mandatory documented and tested exit strategies for critical function outsourcing
7. **Financial sector specificity** — Recovery objectives tied to market hours, settlement cycles, and financial stability considerations

---

## RTS/ITS References

### Key Regulatory Technical Standards

| RTS/ITS | Topic | DORA Article | Status |
|---------|-------|-------------|--------|
| RTS on ICT risk management framework | Details of the ICT risk management framework | Art. 15 | Final |
| RTS on simplified ICT risk management | Simplified framework for certain entities | Art. 16(3) | Final |
| RTS on incident classification | Criteria for classifying major ICT incidents | Art. 18(3) | Final |
| ITS on incident reporting | Templates and procedures for reporting | Art. 20 | Final |
| RTS on TLPT | Threat-led penetration testing requirements | Art. 26(11) | Final |
| RTS on ICT third-party register | Format for the register of information | Art. 28(9) | Final |
| RTS on contractual provisions | Standard contractual clauses | Art. 30(4) | Final |
| RTS on oversight framework | Procedures for critical ICT provider oversight | Art. 41 | Final |
| RTS on subcontracting | Conditions for subcontracting critical functions | Art. 30(5) | Final |

**Note:** Consult the EBA, ESMA, and EIOPA websites for the latest versions of all RTS/ITS, as technical standards continue to be refined through the regulatory process.

---

*Last Updated: March 2026*
*Regulation Reference: EU 2022/2554*

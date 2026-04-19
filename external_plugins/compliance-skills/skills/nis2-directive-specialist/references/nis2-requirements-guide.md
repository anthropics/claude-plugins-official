# NIS2 Requirements Guide

Comprehensive reference for implementing all requirements of the NIS2 Directive (EU 2022/2555), including the 10 minimum security measures, incident reporting procedures, management accountability, and supply chain security.

---

## Table of Contents

- [10 Minimum Security Measures — Implementation Guidance](#10-minimum-security-measures--implementation-guidance)
- [Incident Reporting Procedures](#incident-reporting-procedures)
- [Management Accountability Requirements](#management-accountability-requirements)
- [Supply Chain Security Framework](#supply-chain-security-framework)
- [ISO 27001 Control Mapping](#iso-27001-control-mapping)

---

## 10 Minimum Security Measures — Implementation Guidance

### Measure 1: Risk Analysis and Information System Security Policies

**Article Reference:** Article 21(2)(a)

**What is required:**
- Formal, documented risk assessment methodology covering all information systems
- Comprehensive asset inventory with classification and ownership
- Information security policy framework approved by the management body
- Regular review and update cycle for policies and risk assessments

**Implementation steps:**

1. **Establish risk assessment methodology**
   - Select a recognized framework (ISO 27005, NIST SP 800-30, OCTAVE, FAIR)
   - Define risk identification, analysis, evaluation, and treatment processes
   - Document risk appetite and tolerance thresholds approved by management
   - Define criteria for "significant" risks requiring treatment

2. **Build asset inventory**
   - Identify all information systems, hardware, software, data stores, and network components
   - Assign ownership for each asset
   - Classify assets by criticality and data sensitivity
   - Maintain automated discovery and inventory updates

3. **Develop policy framework**
   - Create an overarching information security policy (top-level commitment)
   - Develop topic-specific policies: access control, cryptography, physical security, operations security, communications security, system acquisition/development, supplier relationships, incident management, business continuity, compliance
   - Ensure management body formally approves each policy
   - Establish a policy exception process

4. **Implement review cycles**
   - Annual policy review (minimum) or upon significant changes
   - Quarterly risk assessment updates for critical systems
   - Annual comprehensive risk reassessment
   - Document all review outcomes and actions

**Evidence to maintain:**
- Risk assessment methodology document
- Risk register with treatment plans
- Asset inventory with last-updated dates
- Signed policy approval records
- Policy review meeting minutes

---

### Measure 2: Incident Handling

**Article Reference:** Article 21(2)(b)

**What is required:**
- Detection capabilities across all information systems
- Incident classification and triage procedures
- Response plans and playbooks for key scenarios
- Post-incident analysis and lessons learned

**Implementation steps:**

1. **Deploy detection capabilities**
   - SIEM for log correlation and alerting
   - Network intrusion detection/prevention systems (NIDS/NIPS)
   - Endpoint detection and response (EDR) on all endpoints
   - Application-level monitoring and anomaly detection
   - Email security gateway with phishing detection

2. **Define classification and triage**
   - Establish severity levels (Critical, High, Medium, Low, Informational)
   - Define classification criteria: impact on services, data affected, geographic scope, financial impact
   - Create decision trees for triage
   - Define escalation paths for each severity level

3. **Develop response playbooks**
   - Ransomware response playbook
   - Data breach response playbook
   - DDoS attack response playbook
   - Insider threat response playbook
   - Supply chain compromise playbook
   - Advanced persistent threat (APT) playbook

4. **Establish 24/7 response capability**
   - SOC or on-call rotation covering all hours
   - Defined communication channels for incident escalation
   - Contact lists for internal teams, management, CSIRT, legal, PR
   - War room procedures for major incidents

5. **Implement post-incident review**
   - Mandatory post-incident review for all Medium+ incidents
   - Root cause analysis methodology (5-Why, Fishbone)
   - Lessons learned documentation
   - Tracking of improvement actions to completion

**Evidence to maintain:**
- Incident response policy and procedures
- Playbook documents for each scenario
- On-call schedule and escalation matrix
- Incident log with classification, response timeline, and outcomes
- Post-incident review reports

---

### Measure 3: Business Continuity and Crisis Management

**Article Reference:** Article 21(2)(c)

**What is required:**
- Business impact analysis (BIA)
- Business continuity plans (BCP) and disaster recovery plans (DRP)
- Backup management with tested restoration
- Regular testing of all plans

**Implementation steps:**

1. **Conduct Business Impact Analysis**
   - Identify all critical business functions and supporting systems
   - Determine maximum tolerable downtime for each function
   - Set Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)
   - Assess financial, operational, reputational, and regulatory impact of disruption

2. **Develop Business Continuity Plans**
   - Create BCPs for each critical business function
   - Define roles and responsibilities during continuity events
   - Establish alternate work locations and communication procedures
   - Document manual workarounds for critical processes

3. **Develop Disaster Recovery Plans**
   - Create DRPs for each critical system
   - Define failover procedures (automated and manual)
   - Document system restoration sequences (dependency-aware)
   - Establish data validation and integrity checks post-recovery

4. **Implement backup management**
   - Automated backups aligned with RPO requirements
   - 3-2-1 backup strategy: 3 copies, 2 media types, 1 offsite
   - Immutable backups for ransomware protection
   - Regular backup integrity verification

5. **Test plans regularly**
   - Annual full-scale BCP/DRP exercise
   - Biannual tabletop exercises for crisis scenarios
   - Quarterly backup restoration tests
   - Document test results and improvement actions

**Evidence to maintain:**
- Business Impact Analysis document
- BCP and DRP documents
- Backup configuration and schedule documentation
- Backup restoration test records
- BCP/DRP exercise reports and improvement tracking

---

### Measure 4: Supply Chain Security

**Article Reference:** Article 21(2)(d)

**What is required:**
- Supplier risk assessment process
- Security requirements in contracts
- Ongoing monitoring of supplier security
- Assessment of aggregate supply chain risks

**Implementation steps:**

1. **Establish supplier classification**
   - Tier 1 (Critical): Direct access to sensitive systems/data, essential to operations
   - Tier 2 (Important): Limited access, important but not essential
   - Tier 3 (Standard): No direct access, limited business impact

2. **Conduct supplier risk assessments**
   - Pre-onboarding security assessment (questionnaire, certification check, audit)
   - Risk scoring based on access level, data exposure, service criticality
   - Annual reassessment for Tier 1, biannual for Tier 2
   - Automated continuous monitoring where available

3. **Define contractual requirements**
   - Security baseline requirements proportionate to tier
   - Incident notification obligations (24h for Tier 1, 48h for Tier 2)
   - Right to audit clause
   - Sub-processor and sub-contractor notification and approval
   - Data protection and confidentiality
   - Exit and transition provisions

4. **Monitor aggregate risks**
   - Identify concentration risks (single points of failure)
   - Assess geographic and geopolitical risks
   - Evaluate technology stack dependencies
   - Review vendor financial stability

**Evidence to maintain:**
- Supplier register with tier classification
- Supplier risk assessment records
- Contract templates with security clauses
- Supplier audit reports
- Supply chain risk assessment reports

---

### Measure 5: Security in Acquisition, Development, and Maintenance

**Article Reference:** Article 21(2)(e)

**What is required:**
- Secure development lifecycle (SDLC)
- Vulnerability management
- Patch management
- Change management with security review

**Implementation steps:**

1. **Implement secure SDLC**
   - Security requirements gathering at design phase
   - Threat modeling for new systems and significant changes
   - Secure coding standards and developer training
   - Static application security testing (SAST) in CI/CD
   - Dynamic application security testing (DAST) before release
   - Security-focused code reviews

2. **Establish vulnerability management**
   - Regular vulnerability scanning (weekly external, monthly internal)
   - Vulnerability prioritization using CVSS + business context
   - Defined remediation SLAs: Critical 24-72h, High 1-2 weeks, Medium 1 month, Low quarterly
   - Tracking and reporting on vulnerability metrics

3. **Implement patch management**
   - Patch identification and assessment process
   - Emergency patch procedures for zero-day vulnerabilities
   - Scheduled patch windows with change management approval
   - Rollback procedures for failed patches

4. **Enforce change management**
   - All changes reviewed for security impact
   - Separation of development, testing, and production environments
   - Approval workflows for production changes
   - Configuration management and drift detection

**Evidence to maintain:**
- SDLC documentation and security gates
- Vulnerability scan reports and remediation records
- Patch management records
- Change management logs with security reviews

---

### Measure 6: Assessing Effectiveness

**Article Reference:** Article 21(2)(f)

**What is required:**
- Cybersecurity metrics and KPIs
- Regular security assessments and audits
- Penetration testing
- Continuous improvement process

**Implementation steps:**

1. **Define cybersecurity metrics**
   - Mean time to detect (MTTD)
   - Mean time to respond (MTTR)
   - Patch compliance rate
   - Vulnerability count trends (open/closed)
   - Phishing simulation click rates
   - Security training completion rates
   - Incidents by severity and type

2. **Conduct regular assessments**
   - Annual internal security audit covering all 10 measures
   - External security audit at least biennially (annually for essential entities)
   - Compliance gap assessments against NIS2 requirements
   - Control effectiveness testing

3. **Implement penetration testing**
   - Annual external penetration test (network and web application)
   - Internal penetration testing for critical systems
   - Social engineering assessments
   - Red team exercises for mature organizations

4. **Drive continuous improvement**
   - Management review of security metrics (quarterly minimum)
   - Formal corrective action process for audit findings
   - Security improvement roadmap aligned with risk register
   - Benchmarking against industry standards and peers

**Evidence to maintain:**
- Security dashboard and metrics reports
- Internal and external audit reports
- Penetration test reports and remediation tracking
- Management review minutes and improvement actions

---

### Measure 7: Cyber Hygiene and Training

**Article Reference:** Article 21(2)(g)

**What is required:**
- Cybersecurity awareness training for all personnel
- Management body cybersecurity training (mandatory)
- Role-based training for technical staff
- Phishing simulations and effectiveness measurement

**Implementation steps:**

1. **General awareness training**
   - Mandatory at onboarding, annual refresher
   - Topics: phishing, social engineering, password hygiene, data handling, physical security, reporting procedures
   - Format: interactive e-learning modules with quiz assessment
   - Minimum passing score: 80%

2. **Management body training**
   - Dedicated cybersecurity training for board and executive members
   - Topics: cyber risk landscape, NIS2 obligations, management liability, incident oversight, cybersecurity investment decisions
   - Frequency: at onboarding, then annually
   - This is mandatory under Article 20(2)

3. **Technical role-based training**
   - Secure coding training for developers
   - Incident response training for SOC/IR teams
   - Cloud security training for infrastructure teams
   - Security architecture training for architects

4. **Simulated exercises**
   - Quarterly phishing simulations
   - Targeted campaigns for high-risk departments (finance, executive, HR)
   - Remedial training for repeat clickers
   - Track trends over time

**Evidence to maintain:**
- Training program documentation
- Completion records for all personnel
- Quiz scores and pass rates
- Phishing simulation reports
- Management body training certificates

---

### Measure 8: Cryptography and Encryption

**Article Reference:** Article 21(2)(h)

**What is required:**
- Cryptography policy
- Encryption for data at rest and in transit
- Key management procedures
- Regular review of cryptographic implementations

**Implementation steps:**

1. **Develop cryptography policy**
   - Approved algorithms: AES-256 for symmetric, RSA-2048+ or ECDSA P-256+ for asymmetric
   - Minimum TLS version: 1.2 (1.3 preferred)
   - Prohibited algorithms: DES, 3DES, RC4, MD5, SHA-1 (for security purposes)
   - Use cases requiring encryption (data classification driven)

2. **Encrypt data at rest**
   - Database encryption (transparent data encryption or column-level)
   - File system encryption for sensitive data
   - Backup encryption
   - Full disk encryption for endpoints

3. **Encrypt data in transit**
   - TLS 1.2+ for all external communications
   - TLS for internal service-to-service communications
   - VPN with strong encryption for remote access
   - Certificate pinning where appropriate

4. **Implement key management**
   - Key generation using cryptographically secure random number generators
   - Key storage in HSMs or secure key management services
   - Key rotation schedule (annual minimum, or per use case)
   - Key revocation and destruction procedures

5. **Review implementations**
   - Annual review of cryptographic algorithm choices against current guidance (ENISA, NIST)
   - TLS configuration testing (SSL Labs grade A minimum)
   - Certificate expiry monitoring
   - Migration plans for deprecated algorithms

**Evidence to maintain:**
- Cryptography policy document
- Key management procedures
- TLS configuration audit results
- Certificate inventory with expiry dates
- Cryptographic review records

---

### Measure 9: Human Resources Security, Access Control, and Asset Management

**Article Reference:** Article 21(2)(i)

**What is required:**
- Pre-employment security checks
- Role-based access control (RBAC) with least privilege
- Privileged access management (PAM)
- Asset inventory with ownership
- Secure departure procedures

**Implementation steps:**

1. **Human resources security**
   - Background checks proportionate to role sensitivity
   - Security clauses in employment contracts
   - Confidentiality/NDA agreements
   - Clear definition of security responsibilities per role
   - Exit interviews with security component

2. **Access control**
   - Implement RBAC with documented role-permission matrices
   - Enforce least privilege principle
   - Automated provisioning and deprovisioning tied to HR systems
   - Access request and approval workflows
   - Regular access reviews (quarterly for critical systems, biannual for others)

3. **Privileged access management**
   - PAM solution for credential vaulting and session management
   - Just-in-time (JIT) access for administrative tasks
   - Session recording for privileged access to critical systems
   - Separate administrative accounts from daily-use accounts
   - Break-glass procedures for emergency access

4. **Asset management**
   - Automated discovery and inventory of all assets
   - Asset classification by criticality and data sensitivity
   - Asset ownership assignment and accountability
   - End-of-life and disposal procedures for hardware and data
   - Acceptable use policies for organizational assets

5. **Departure procedures**
   - Immediate notification from HR to IT upon termination
   - Access revocation within 24 hours (immediately for involuntary termination)
   - Return of physical assets (laptops, keys, badges, tokens)
   - Remote wipe capability for mobile devices
   - Transfer of data ownership

**Evidence to maintain:**
- Background check records (per retention policy)
- Role-permission matrix
- Access review reports
- PAM deployment and session logs
- Asset inventory with ownership records
- Departure checklists with completion dates

---

### Measure 10: MFA, Secured Communications, and Emergency Communications

**Article Reference:** Article 21(2)(j)

**What is required:**
- Multi-factor authentication for remote, privileged, and critical system access
- End-to-end encrypted communications
- Secured emergency communication channels
- Out-of-band communication capabilities

**Implementation steps:**

1. **Deploy MFA**
   - All remote access (VPN, cloud services, email)
   - All privileged and administrative accounts
   - Access to critical systems and sensitive data
   - Single sign-on (SSO) with MFA for all enterprise applications
   - Support FIDO2/WebAuthn hardware keys for high-risk accounts
   - Phishing-resistant MFA where feasible

2. **Secured communications**
   - Encrypted email for sensitive communications (S/MIME or PGP)
   - Encrypted instant messaging for business communications
   - Encrypted file sharing with access controls
   - Secure video conferencing platforms

3. **Emergency communications**
   - Out-of-band communication channel (satellite phones, separate network)
   - Emergency contact lists accessible offline
   - Pre-established communication protocols for crisis scenarios
   - Regular testing of emergency communication channels

**Evidence to maintain:**
- MFA deployment records and coverage metrics
- MFA exception register (with risk acceptance)
- Emergency communication procedures
- Emergency communication test records

---

## Incident Reporting Procedures

### Overview

Under Article 23, entities must report significant incidents to the CSIRT or competent authority using a multi-stage process. An incident is significant if it:

- Has caused or is capable of causing severe operational disruption of services or financial loss
- Has affected or is capable of affecting other natural or legal persons by causing considerable material or non-material damage

### Early Warning (Within 24 Hours)

**Trigger:** Upon becoming aware of a significant incident

**Content requirements:**
- Whether the incident is suspected of being caused by unlawful or malicious acts
- Whether the incident could have a cross-border impact
- Brief factual description

**Template fields:**
- Reporting entity identification (name, NIS2 registration)
- Date and time of detection
- Date and time of incident occurrence (if known)
- Brief description of the incident
- Suspected malicious/unlawful activity: Yes / No / Unknown
- Potential cross-border impact: Yes / No / Unknown
- Contact person for follow-up

### Incident Notification (Within 72 Hours)

**Trigger:** 72 hours from becoming aware of the significant incident

**Content requirements:**
- Update to the early warning information
- Initial assessment of the incident severity and impact
- Indicators of compromise (IoC) where applicable

**Template fields:**
- Reference to early warning (case ID)
- Updated description of the incident
- Systems and services affected
- Number of users/entities affected
- Geographic scope
- Severity assessment (Critical / High / Medium)
- Root cause assessment (if known at this stage)
- Indicators of compromise (IPs, domains, hashes, signatures)
- Mitigation measures implemented

### Intermediate Report (Upon Request)

**Trigger:** Upon request from CSIRT or competent authority

**Content requirements:**
- Status update on incident handling and response
- Additional details as requested

### Final Report (Within 1 Month)

**Trigger:** No later than one month after the incident notification

**Content requirements:**
- Detailed description of the incident, including severity and impact
- Type of threat or root cause that likely triggered the incident
- Applied and ongoing mitigation measures
- Cross-border impact (if applicable)

**Template fields:**
- Complete incident timeline
- Root cause analysis results
- Full impact assessment (operational, financial, data, reputational)
- Detailed description of mitigation measures
- Lessons learned
- Improvement actions planned
- Cross-border impact details (affected Member States, entities)

---

## Management Accountability Requirements

### Article 20 Obligations

**Management body** refers to the governing body of the entity (board of directors, executive management, or equivalent).

### Approval and Oversight (Article 20(1))

The management body must:
- **Approve** the cybersecurity risk management measures adopted under Article 21
- **Oversee** the implementation of those measures
- **Be liable** for infringements of Article 21

**Implementation guidance:**
- Cybersecurity measures must be a formal board/management agenda item
- Management body must receive regular reports on cybersecurity posture
- Approval should be documented in meeting minutes
- A named member should have oversight responsibility for cybersecurity

### Training (Article 20(2))

Members of the management body must:
- **Undergo training** to gain sufficient knowledge and skills to identify cybersecurity risks
- **Assess cybersecurity risk management practices** and their impact on services
- **Encourage** similar training for employees on a regular basis

**Recommended training topics:**
- Current cyber threat landscape relevant to the entity's sector
- NIS2 obligations and management liability
- Cybersecurity risk assessment fundamentals
- Incident response oversight responsibilities
- Cybersecurity investment and resource allocation
- Supply chain cybersecurity risks

### Enforcement Implications

For **essential entities**, Member States may impose:
- Temporary prohibition on natural persons responsible from exercising managerial functions at CEO or legal representative level
- This is a significant personal consequence unique to NIS2

---

## Supply Chain Security Framework

### Tier-Based Approach

**Tier 1 — Critical Suppliers**
(Direct access to sensitive systems, essential to core operations)

| Requirement | Detail |
|-------------|--------|
| Pre-onboarding | Full security assessment (audit or equivalent) |
| Certification | ISO 27001 or SOC 2 Type II required |
| Contracts | Full security clauses, right to audit, SLAs |
| Incident notification | Within 24 hours |
| Reviews | Annual security audit or certification check |
| Monitoring | Continuous (security rating services, threat intelligence) |
| Exit strategy | Documented transition plan, data return/destruction |

**Tier 2 — Important Suppliers**
(Limited access, important but not essential)

| Requirement | Detail |
|-------------|--------|
| Pre-onboarding | Security questionnaire and self-assessment |
| Certification | ISO 27001 or SOC 2 preferred, not mandatory |
| Contracts | Security requirements, incident notification, NDA |
| Incident notification | Within 48 hours |
| Reviews | Biannual security review |
| Monitoring | Periodic (annual questionnaire refresh) |

**Tier 3 — Standard Suppliers**
(No direct access, limited impact)

| Requirement | Detail |
|-------------|--------|
| Pre-onboarding | Basic security questionnaire |
| Contracts | Standard security clauses, NDA |
| Reviews | Annual self-assessment |

### Contractual Security Requirements

Essential clauses for Tier 1 and Tier 2 supplier contracts:

1. **Security baseline:** Supplier must maintain security measures at least equivalent to industry standards
2. **Incident notification:** Supplier must notify of any security incident affecting the entity's data or services within defined timeline
3. **Right to audit:** Entity may audit or commission audit of supplier's security controls
4. **Sub-processor notification:** Supplier must notify and obtain approval before engaging sub-processors
5. **Data protection:** Compliance with applicable data protection requirements
6. **Business continuity:** Supplier must maintain BCP/DRP for services provided
7. **Termination and transition:** Data return, deletion, and transition assistance obligations
8. **Compliance:** Supplier must comply with applicable NIS2 requirements

---

## ISO 27001 Control Mapping

### NIS2 Measure to ISO 27001:2022 Control Mapping

| NIS2 Measure | ISO 27001:2022 Controls |
|-------------|------------------------|
| **M1:** Risk analysis and policies | A.5.1 (Policies), A.5.2 (Roles), A.5.9-5.11 (Asset management), Cl.6.1 (Risk assessment), Cl.8.2-8.3 (Risk treatment) |
| **M2:** Incident handling | A.5.24 (IR planning), A.5.25 (Assessment), A.5.26 (Response), A.5.27 (Learning), A.8.16 (Monitoring) |
| **M3:** Business continuity | A.5.29 (ICT readiness), A.5.30 (ICT for BC), A.8.13 (Backup), A.8.14 (Redundancy) |
| **M4:** Supply chain security | A.5.19 (Supplier policy), A.5.20 (Addressing security), A.5.21 (ICT supply chain), A.5.22 (Monitoring), A.5.23 (Cloud services) |
| **M5:** Acquisition, development, maintenance | A.8.8 (Vulnerability management), A.8.9 (Configuration), A.8.25 (Secure development), A.8.26 (Application security), A.8.27 (Secure architecture), A.8.28 (Secure coding), A.8.29 (Security testing), A.8.31 (Separation), A.8.32 (Change management) |
| **M6:** Assessing effectiveness | Cl.9.1 (Monitoring/measurement), Cl.9.2 (Internal audit), Cl.9.3 (Management review), Cl.10.1-10.2 (Improvement) |
| **M7:** Cyber hygiene and training | A.6.3 (Awareness/training), A.6.8 (Information security event reporting) |
| **M8:** Cryptography and encryption | A.8.24 (Use of cryptography) |
| **M9:** HR security, access control, asset management | A.6.1 (Screening), A.6.2 (Terms), A.6.4 (Disciplinary), A.6.5 (Termination), A.5.15 (Access control), A.5.16-5.18 (Identity management), A.8.2 (Privileged access), A.8.3 (Access restriction), A.8.5 (Authentication) |
| **M10:** MFA, secured and emergency communications | A.8.5 (Secure authentication), A.5.14 (Information transfer), A.8.20 (Networks security), A.8.21 (Web services security), A.8.24 (Cryptography) |

### Gap Analysis Approach

For organizations already ISO 27001 certified:

1. Map existing ISO 27001 controls to NIS2 measures using the table above
2. Identify NIS2-specific requirements not fully covered by ISO 27001:
   - Specific incident reporting timelines (24h/72h/1 month)
   - Management body training and personal liability
   - Supply chain security at the level of detail required
   - Emergency communication channels
3. Conduct gap assessment for these areas
4. Develop remediation plan for identified gaps

Organizations with ISO 27001 certification typically have **60-70% of NIS2 requirements** already addressed. Key gaps are usually in incident reporting timelines, management accountability, supply chain depth, and emergency communication.

---

*Last Updated: March 2026*
*Directive Reference: EU 2022/2555, Articles 20-23*

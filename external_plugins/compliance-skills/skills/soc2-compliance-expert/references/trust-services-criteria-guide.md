# Trust Services Criteria Complete Reference Guide

Comprehensive reference for all SOC 2 Trust Services Criteria (TSC) as defined by AICPA in TSP Section 100, based on the COSO 2013 Internal Control Framework.

---

## TSC Structure Overview

The Trust Services Criteria are organized into:

- **Common Criteria (CC1-CC9):** Required for every SOC 2 audit (Security category)
- **Additional Criteria:** Optional categories chosen based on service commitments
  - **A1:** Availability
  - **PI1:** Processing Integrity
  - **C1:** Confidentiality
  - **P1:** Privacy

The Common Criteria map directly to the five COSO components:
1. Control Environment (CC1)
2. Communication and Information (CC2)
3. Risk Assessment (CC3)
4. Monitoring Activities (CC4)
5. Control Activities (CC5)

Plus three additional areas unique to TSC:
6. Logical and Physical Access Controls (CC6)
7. System Operations (CC7)
8. Change Management (CC8)
9. Risk Mitigation (CC9)

---

## CC1: Control Environment

### CC1.1 - COSO Principle 1: Integrity and Ethical Values

**Control Objective:** The entity demonstrates a commitment to integrity and ethical values.

**Implementation Guidance:**
- Establish a code of conduct/ethics policy covering expected behavior, conflicts of interest, and reporting mechanisms
- Require annual employee acknowledgment of code of conduct
- Include code of conduct in new hire onboarding
- Define consequences for violations
- Provide anonymous reporting mechanism (ethics hotline or online portal)

**Evidence Requirements:**
- Code of conduct policy document (current version with approval date)
- Employee acknowledgment records (100% completion)
- New hire onboarding checklist showing code of conduct review
- Ethics hotline configuration and usage reports
- Disciplinary action records related to violations (if any, redacted)

**Common Audit Questions:**
- "Can you provide the current code of conduct policy?"
- "What percentage of employees have acknowledged the code of conduct?"
- "How are violations reported and investigated?"
- "When was the code of conduct last reviewed and updated?"

**Typical Findings:**
- Code of conduct not reviewed/updated in over 2 years
- Missing acknowledgments for contractors or part-time employees
- No anonymous reporting mechanism available
- New hires not acknowledging code within first week

### CC1.2 - COSO Principle 2: Board Independence and Oversight

**Control Objective:** The board of directors demonstrates independence from management and exercises oversight.

**Implementation Guidance:**
- Establish a governance committee or board-level oversight for information security
- Document committee charter with security oversight responsibilities
- Schedule quarterly security briefings to board/committee
- Ensure at least one board member has cybersecurity expertise or appoint an external advisor
- Board reviews and approves information security policy annually

**Evidence Requirements:**
- Board/committee charter document
- Meeting minutes showing security discussions (quarterly minimum)
- Board member qualifications/expertise documentation
- Annual information security policy approval by board
- Security metrics presented to board

**Common Audit Questions:**
- "How does the board exercise oversight of the security program?"
- "How frequently does the board receive security updates?"
- "Does the board review and approve the information security policy?"

**Typical Findings:**
- No documented board oversight of security program
- Security briefings to board less than quarterly
- No board member with security expertise
- Board minutes do not reflect security discussions

### CC1.3 - COSO Principle 3: Organizational Structure

**Control Objective:** Management establishes structures, reporting lines, and appropriate authorities and responsibilities.

**Implementation Guidance:**
- Create and maintain organizational chart showing security reporting structure
- Define CISO/security lead role with appropriate authority
- Document RACI matrix for security functions
- Ensure security team has adequate staffing and budget
- Establish clear escalation paths

**Evidence Requirements:**
- Organizational chart (current)
- CISO/security lead job description
- Security team structure and headcount
- RACI matrix for security functions
- Security budget documentation

**Common Audit Questions:**
- "Who is responsible for the information security program?"
- "Does the security leader report to executive management?"
- "How is the security function resourced?"

**Typical Findings:**
- No dedicated security lead or CISO role
- Security leader reports too low in organization
- Inadequate security staffing relative to company size
- RACI matrix not documented or outdated

### CC1.4 - COSO Principle 4: Commitment to Competence

**Control Objective:** The entity demonstrates a commitment to attract, develop, and retain competent individuals.

**Implementation Guidance:**
- Conduct background checks for all employees with access to sensitive data
- Define competency requirements for security-critical roles
- Provide ongoing security training and professional development
- Evaluate employee performance including security responsibilities
- Maintain succession plans for key security roles

**Evidence Requirements:**
- Background check policy
- Background check completion log (sample)
- Security training records
- Job descriptions with competency requirements
- Professional development records for security team

**Common Audit Questions:**
- "What background checks are performed for new hires?"
- "How do you ensure security staff maintain relevant certifications?"
- "What security training is provided to employees?"

**Typical Findings:**
- Background checks not performed for all roles with data access
- No ongoing professional development for security team
- Security training limited to annual awareness (no role-specific training)

### CC1.5 - COSO Principle 5: Accountability

**Control Objective:** The entity holds individuals accountable for their internal control responsibilities.

**Implementation Guidance:**
- Include security responsibilities in performance evaluations
- Define and enforce consequences for policy violations
- Track security-related KPIs per team/department
- Publish security metrics dashboards
- Recognize and reward security-positive behaviors

**Evidence Requirements:**
- Performance evaluation templates showing security criteria
- Disciplinary policy for security violations
- Security metrics by department
- Security champion program (if applicable)

**Common Audit Questions:**
- "How are employees held accountable for security responsibilities?"
- "What happens when someone violates the security policy?"

**Typical Findings:**
- Performance evaluations do not include security criteria
- No documented consequences for policy violations
- Security accountability limited to IT/security team only

---

## CC2: Communication and Information

### CC2.1 - Internal Communication

**Control Objective:** The entity internally generates and uses relevant, quality information to support the functioning of internal controls.

**Implementation Guidance:**
- Distribute information security policy to all employees
- Maintain centralized policy portal accessible to all employees
- Send regular security updates and bulletins
- Communicate security incident learnings organization-wide
- Maintain internal security wiki or knowledge base

**Evidence Requirements:**
- Policy distribution records
- Policy portal URL and access logs
- Security newsletter/bulletin examples
- Internal communication about security incidents
- Onboarding materials including security information

**Common Audit Questions:**
- "How are security policies communicated to employees?"
- "How do employees know where to find security policies?"
- "How are lessons from security incidents shared?"

**Typical Findings:**
- Policies stored in shared drive but not proactively distributed
- No regular security communications beyond annual training
- New employees not informed of security policies during onboarding

### CC2.2 - External Communication

**Control Objective:** The entity communicates with external parties regarding matters affecting the functioning of internal controls.

**Implementation Guidance:**
- Publish privacy policy on website
- Maintain public-facing security page or trust center
- Document customer notification procedures for security incidents
- Provide service level agreements with security commitments
- Maintain vulnerability disclosure/responsible disclosure program

**Evidence Requirements:**
- Published privacy policy (URL)
- Security page or trust center (URL)
- Customer incident notification procedures
- SLA documentation
- Vulnerability disclosure policy (if applicable)

**Common Audit Questions:**
- "How do you communicate your security commitments to customers?"
- "What is your customer notification process for security incidents?"
- "Do you have a public vulnerability disclosure program?"

**Typical Findings:**
- No public-facing security page or trust center
- Privacy policy outdated or missing required elements
- No documented customer notification procedure for incidents
- Vulnerability disclosure program not established

### CC2.3 - System Description

**Control Objective:** The entity produces and maintains an accurate system description.

**Implementation Guidance:**
- Author comprehensive system description (Section III of SOC 2 report)
- Include all five components: infrastructure, software, people, procedures, data
- Document system boundaries and data flows
- Identify complementary user entity controls (CUECs)
- Identify complementary subservice organization controls (CSOCs)
- Update system description for significant changes

**Evidence Requirements:**
- System description document (current version)
- Data flow diagrams
- Network architecture diagrams
- System boundary definition document
- CUEC and CSOC documentation
- Change log for system description updates

**Common Audit Questions:**
- "Can you walk me through the system description?"
- "What are the boundaries of the system in scope?"
- "Which subservice organizations are you relying on?"
- "What controls do you expect your customers to implement?"

**Typical Findings:**
- System description missing or significantly outdated
- Data flow diagrams do not reflect current architecture
- Subservice organizations not identified or documented
- CUECs not defined

---

## CC3: Risk Assessment

### CC3.1 - Risk Identification and Assessment

**Control Objective:** The entity specifies objectives with sufficient clarity to enable the identification and assessment of risks relating to objectives.

**Implementation Guidance:**
- Conduct formal risk assessment at least annually
- Maintain risk register with likelihood, impact, and risk treatment
- Use standardized risk scoring methodology (qualitative or quantitative)
- Cover all risk domains: technology, operational, compliance, strategic
- Engage stakeholders from across the organization in risk identification
- Document risk appetite and tolerance levels

**Evidence Requirements:**
- Annual risk assessment report
- Risk register (current)
- Risk methodology documentation
- Risk acceptance sign-offs
- Stakeholder participation records

**Common Audit Questions:**
- "When was the last risk assessment performed?"
- "Who participates in the risk assessment process?"
- "How do you score and prioritize risks?"
- "How are risk treatment decisions made and documented?"

**Typical Findings:**
- Risk assessment not performed in current year
- Risk register incomplete or not maintained
- No formal risk scoring methodology
- Risk acceptance not signed off by appropriate management

### CC3.2 - Fraud Risk Assessment

**Control Objective:** The entity considers the potential for fraud in assessing risks to the achievement of objectives.

**Implementation Guidance:**
- Include fraud risk scenarios in annual risk assessment
- Analyze segregation of duties for fraud prevention
- Assess management override risks
- Consider insider threat scenarios
- Evaluate data manipulation risks
- Implement fraud detection controls

**Evidence Requirements:**
- Fraud risk assessment document
- Segregation of duties matrix
- Anti-fraud control documentation
- Insider threat program documentation (if applicable)

**Common Audit Questions:**
- "How do you assess fraud risk?"
- "What segregation of duties controls are in place?"
- "How do you mitigate management override risks?"

**Typical Findings:**
- No formal fraud risk assessment performed
- Segregation of duties analysis not documented
- Insider threat not considered in risk assessment

### CC3.3 - Change Risk Assessment

**Control Objective:** The entity considers changes that could significantly impact the system of internal controls.

**Implementation Guidance:**
- Assess risks from significant organizational changes
- Monitor regulatory and compliance landscape changes
- Evaluate risks from new technologies or products
- Assess risks from personnel changes (key person dependencies)
- Review risks from third-party relationship changes

**Evidence Requirements:**
- Change impact assessment records
- Regulatory monitoring evidence
- New technology risk assessments
- Key person dependency analysis

**Common Audit Questions:**
- "How do you identify and assess risks from significant changes?"
- "How do you monitor changes in the regulatory landscape?"
- "What key person dependencies exist and how are they mitigated?"

**Typical Findings:**
- No formal process for assessing change-related risks
- Regulatory monitoring ad hoc rather than systematic
- Key person dependencies not identified

---

## CC4: Monitoring Activities

### CC4.1 - Ongoing Monitoring and Separate Evaluations

**Control Objective:** The entity selects, develops, and performs ongoing and separate evaluations to ascertain whether controls are present and functioning.

**Implementation Guidance:**

**Ongoing Monitoring:**
- Deploy SIEM for continuous security event monitoring
- Implement cloud security posture management (CSPM)
- Configure automated compliance scanning
- Establish security metrics dashboards with KPIs/KRIs
- Deploy continuous vulnerability scanning

**Separate Evaluations:**
- Conduct internal security audits at least annually
- Commission external penetration testing annually (quarterly for critical systems)
- Perform control self-assessments by process owners
- Conduct tabletop exercises for incident response
- Engage third-party assessments as needed

**Evidence Requirements:**
- SIEM configuration and alert rules
- Security metrics dashboards
- Internal audit reports and schedules
- Penetration test reports (with remediation status)
- Vulnerability scan results (monthly)
- Control self-assessment results
- Tabletop exercise records

**Common Audit Questions:**
- "How do you continuously monitor the effectiveness of controls?"
- "What security metrics do you track?"
- "When was the last penetration test performed and what were the results?"
- "How frequently do you conduct internal security audits?"

**Typical Findings:**
- No centralized SIEM or security monitoring
- Penetration testing not performed in current period
- Internal audits not covering all control domains
- Security metrics not tracked or reported to management

### CC4.2 - Deficiency Communication and Remediation

**Control Objective:** The entity evaluates and communicates internal control deficiencies in a timely manner.

**Implementation Guidance:**
- Classify findings by severity (critical, high, medium, low)
- Assign remediation owners and target dates
- Track remediation progress in ticketing system
- Report to management monthly on open findings
- Escalate critical/high findings to executive management
- Conduct root cause analysis for all high/critical findings

**Evidence Requirements:**
- Finding tracker/register with status
- Remediation evidence for closed findings
- Management reports on finding status
- Root cause analysis records
- Escalation evidence for critical findings

**Common Audit Questions:**
- "How are control deficiencies tracked and remediated?"
- "What are the remediation SLAs by severity?"
- "How are findings reported to management?"
- "Are there any overdue remediations?"

**Typical Findings:**
- No formal finding tracking system
- Missing remediation SLAs or SLAs not met
- Findings not reported to management regularly
- Root cause analysis not performed

---

## CC5: Control Activities

### CC5.1 - Control Activity Design

**Control Objective:** The entity selects and develops control activities that contribute to the mitigation of risks.

**Implementation Guidance:**
- Map controls to identified risks (risk-control matrix)
- Design controls as preventive, detective, or corrective
- Consider automated controls where feasible
- Document control design rationale
- Implement compensating controls where primary controls have limitations

**Evidence Requirements:**
- Risk-control mapping matrix
- Control design documentation
- Automated control configurations
- Compensating control justifications

### CC5.2 - Technology General Controls

**Control Objective:** The entity selects and develops general control activities over technology.

**Implementation Guidance:**
- Establish IT general controls (ITGCs) program covering:
  - Logical access to programs and data
  - Program change management
  - Program development lifecycle
  - Computer operations

**Evidence Requirements:**
- ITGC framework documentation
- Access control procedures for IT systems
- Change management procedures
- SDLC documentation
- Computer operations procedures

### CC5.3 - Policy Deployment

**Control Objective:** The entity deploys control activities through policies and procedures.

**Implementation Guidance:**
- Maintain centralized policy management system
- Establish annual policy review and approval cycle
- Track policy acknowledgments from all employees
- Implement version control for all policy documents
- Define exception management process

**Evidence Requirements:**
- Policy management system configuration
- Policy documents with version history
- Annual review and approval records
- Employee acknowledgment tracking
- Exception request and approval records

**Common Audit Questions:**
- "Where are policies maintained and how are they distributed?"
- "When were policies last reviewed and approved?"
- "What is your policy exception process?"
- "Do all employees acknowledge receiving and reading policies?"

**Typical Findings:**
- Policies not reviewed within last 12 months
- Missing employee acknowledgments
- No version control on policy documents
- Exception process not documented or not followed

---

## CC6: Logical and Physical Access Controls

### CC6.1 - Logical Access Security

**Control Objective:** The entity implements logical access security software, infrastructure, and architectures.

**Implementation Guidance:**
- Deploy centralized identity provider (IdP) with SSO
- Enforce multi-factor authentication for all users
- Implement role-based access control (RBAC)
- Configure password policies (minimum 12 characters, complexity)
- Set session timeouts (15 min for sensitive, 30 min general)
- Implement account lockout after 5 failed attempts

**Evidence Requirements:**
- IdP configuration (SSO, MFA policies)
- MFA enrollment report (100% coverage)
- Password policy configuration
- Session timeout configuration
- Account lockout policy configuration
- RBAC role definitions

**Common Audit Questions:**
- "How is access to the system authenticated?"
- "Is MFA enforced for all users?"
- "What password requirements are enforced?"
- "How are sessions managed and timed out?"

**Typical Findings:**
- MFA not enforced for all users or all applications
- SMS-based MFA still permitted
- Password policy below minimum requirements
- Session timeouts not configured or too long
- SSO not deployed for all SaaS applications

### CC6.2 - Access Provisioning

**Control Objective:** Access to system components is provisioned based on authorization.

**Implementation Guidance:**
- Implement formal access request workflow
- Require manager approval for all access requests
- Provision access based on role (not individual)
- Use SCIM for automated provisioning where supported
- Maintain role definitions and access matrices

**Evidence Requirements:**
- Access request ticket samples (with approvals)
- Role definitions and access matrices
- SCIM provisioning configuration
- Onboarding access provisioning checklist

### CC6.3 - Access Reviews and Modification

**Control Objective:** Access to system components is reviewed and modified periodically.

**Implementation Guidance:**
- Quarterly access reviews for privileged access
- Semi-annual access reviews for standard access
- Quarterly service account access reviews
- Immediate access modification for role changes
- Document review results including access changes made

**Evidence Requirements:**
- Access review completion records (with dates, reviewer, results)
- Access changes made as a result of reviews
- Service account review records
- Role change access modification records

**Common Audit Questions:**
- "How frequently are access reviews performed?"
- "Who performs the reviews?"
- "What actions are taken based on review results?"
- "Can you provide evidence of completed reviews during the audit period?"

**Typical Findings:**
- Access reviews not performed per scheduled frequency
- Reviews performed but no evidence of access changes/remediation
- Service accounts not included in access reviews
- Reviewer independence not maintained (self-reviews)

### CC6.4 - Physical Access

**Control Objective:** The entity restricts physical access to facilities and protected information assets.

**Implementation Guidance:**
- Badge access system for office and data center
- Visitor management (sign-in, escort, sign-out)
- Environmental controls (fire, HVAC, water detection)
- CCTV at entry/exit points (90-day retention)
- Separate data center access from general office access

**Evidence Requirements:**
- Badge access system logs (sample period)
- Visitor sign-in logs
- CCTV configuration and retention settings
- Environmental monitoring configuration
- Data center access list

### CC6.5 - Access Removal on Termination

**Control Objective:** Access to system components is removed when no longer needed.

**Implementation Guidance:**
- Same-day access removal upon termination
- Automated deprovisioning via HRIS-IdP integration
- Offboarding checklist covering all access points
- Equipment return tracking
- Account verification after deprovisioning

**Evidence Requirements:**
- Offboarding checklist (completed samples)
- HRIS termination to IdP deactivation timing evidence
- Equipment return records
- Post-deprovisioning verification evidence

**Common Audit Questions:**
- "What is your process when an employee leaves?"
- "How quickly is access removed after termination?"
- "Is deprovisioning automated or manual?"
- "How do you verify all access has been removed?"

**Typical Findings:**
- Access removal not same-day (multi-day delays)
- Manual deprovisioning leading to missed accounts
- No verification after deprovisioning
- Application-specific accounts not revoked (only IdP disabled)

### CC6.6 - Network Protection

**Control Objective:** The entity protects boundaries of the system against unauthorized access.

**Implementation Guidance:**
- Firewall with deny-by-default rules
- Web Application Firewall (WAF) on all public endpoints
- Network segmentation between environments
- VPN or Zero Trust Network Access for remote access
- Intrusion detection/prevention systems

### CC6.7 - Data Transmission Encryption

**Control Objective:** The entity protects data during transmission.

**Implementation Guidance:**
- TLS 1.2 minimum (TLS 1.3 preferred)
- AEAD cipher suites only (AES-GCM, ChaCha20-Poly1305)
- HSTS with preload
- Certificate management with automated renewal
- Internal service-to-service encryption (mTLS where applicable)

### CC6.8 - Malware Prevention

**Control Objective:** The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software.

**Implementation Guidance:**
- Deploy EDR on all endpoints
- Application whitelisting for sensitive systems
- Email security gateway with malware scanning
- Web filtering for known malicious domains
- USB/removable media restrictions

---

## CC7: System Operations

### CC7.1 - Vulnerability Management

**Control Objective:** The entity detects and monitors system vulnerabilities.

**Implementation Guidance:**
- Monthly vulnerability scanning (internal and external)
- Annual penetration testing (quarterly for critical systems)
- Container image scanning on every build
- Dependency/SCA scanning on every build
- Web application security testing with each major release
- Defined remediation SLAs by severity:
  - Critical: 24 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

**Evidence Requirements:**
- Monthly scan results (internal and external)
- Penetration test report (annual)
- Remediation tracking with SLA compliance
- Container/dependency scan configurations
- Vulnerability metrics (open count trends, SLA compliance rates)

**Common Audit Questions:**
- "How frequently do you scan for vulnerabilities?"
- "What are your remediation SLAs?"
- "What is your current SLA compliance rate?"
- "When was the last penetration test and what were the results?"

**Typical Findings:**
- Scanning frequency below monthly
- Remediation SLAs not defined or not met
- Penetration testing not performed in current year
- Container images not scanned before deployment
- No dependency scanning in CI/CD pipeline

### CC7.2 - Security Monitoring

**Control Objective:** The entity monitors system components and the operation of those components for anomalies.

**Implementation Guidance:**
- Deploy SIEM with centralized log aggregation
- Ingest logs from all critical systems
- Define alert rules for security events
- Establish 24/7 monitoring capability (SOC or managed)
- Monitor for: failed authentication, privilege escalation, configuration changes, data exfiltration indicators

**Evidence Requirements:**
- SIEM configuration and log source inventory
- Alert rules documentation
- Sample alert response evidence
- Log retention configuration (minimum 90 days, 365 recommended)
- Monitoring coverage assessment

### CC7.3 - Incident Response

**Control Objective:** The entity evaluates security events to determine whether they constitute security incidents.

**Implementation Guidance:**
- Document incident response plan with severity levels
- Define incident commander and escalation paths
- Establish communication templates
- Conduct quarterly tabletop exercises
- Track MTTD (Mean Time to Detect), MTTR (Mean Time to Respond)
- Post-incident review within 5 business days

**Evidence Requirements:**
- Incident response plan (current, approved)
- Severity level definitions
- Escalation matrix
- Tabletop exercise records (quarterly)
- Incident tickets and post-mortem reports
- MTTD/MTTR metrics

### CC7.4 - Business Continuity

**Control Objective:** The entity develops and implements business continuity plans.

See A1 criteria below for detailed guidance.

### CC7.5 - Recovery

**Control Objective:** The entity recovers from identified security incidents.

**Implementation Guidance:**
- Document recovery procedures per system tier
- Define RTO/RPO per system classification
- Test recovery procedures at least annually
- Maintain up-to-date runbooks
- Practice disaster recovery failover

---

## CC8: Change Management

### CC8.1 - Change Authorization and Management

**Control Objective:** The entity authorizes, designs, develops, configures, documents, tests, approves, and implements changes to meet its objectives.

**Implementation Guidance:**
1. Change request with business justification
2. Impact assessment (security, performance, compliance)
3. Peer code review (minimum 1 reviewer, 2 for critical systems)
4. Testing in non-production environment
5. Approval from authorized change authority
6. Deployment with rollback plan
7. Post-deployment validation
8. Change record closure

**Emergency Changes:**
- Defined criteria for emergency classification
- Abbreviated approval (single authorized approver)
- Post-implementation review within 48 hours
- Retroactive documentation
- Trend tracking for frequency

**Evidence Requirements:**
- Change management policy/procedure
- Change tickets with full lifecycle (request, review, approval, test, deploy, close)
- Code review evidence (PR approvals in git platform)
- Branch protection configuration
- CI/CD pipeline configuration showing gates
- Emergency change records with post-hoc review
- Change Advisory Board (CAB) meeting records (if applicable)

**Common Audit Questions:**
- "Walk me through your change management process."
- "Can you show me a sample of change tickets with approvals?"
- "How do you handle emergency changes?"
- "What testing is performed before production deployment?"
- "Who can approve changes?"

**Typical Findings:**
- Changes deployed without documented approval
- Code reviews not consistently performed
- Testing evidence not captured
- Emergency change process not defined or overused
- No separation between development and production environments
- Rollback plans not documented

---

## CC9: Risk Mitigation

### CC9.1 - Vendor Risk Management

**Control Objective:** The entity identifies, assesses, and manages risks associated with vendors and business partners.

**Implementation Guidance:**
- Maintain vendor inventory with risk classification
- Conduct security due diligence before onboarding
- Collect and review SOC 2 reports from critical vendors annually
- Include security requirements in contracts (DPA, SLA, audit rights)
- Monitor vendor security posture continuously (where possible)
- Maintain current subprocessor list

**Evidence Requirements:**
- Vendor inventory with risk tiering
- Vendor risk assessment questionnaires (completed)
- Vendor SOC 2 reports (reviewed)
- Contract samples showing security requirements
- Subprocessor list (current)
- Vendor reassessment schedule and completion records

**Common Audit Questions:**
- "How do you assess vendor security risk?"
- "Which vendors are classified as critical?"
- "Do you review vendor SOC 2 reports?"
- "What contractual security requirements do you impose?"

**Typical Findings:**
- No vendor risk classification or tiering
- SOC 2 reports not collected or reviewed for critical vendors
- Contracts missing security requirements or DPA
- Vendor assessments not performed annually
- Subprocessor list not maintained

### CC9.2 - Business Disruption Risk

**Control Objective:** The entity assesses and manages risks associated with business disruptions.

**Implementation Guidance:**
- Obtain cyber liability insurance
- Review insurance coverage annually against risk profile
- Document business interruption insurance
- Maintain risk transfer register
- Evaluate insurance adequacy after significant changes

**Evidence Requirements:**
- Cyber insurance certificate (current)
- Coverage summary
- Annual coverage review documentation
- Business interruption insurance evidence

---

## A1: Availability

### A1.1 - Capacity and Performance

**Control Objective:** The entity maintains, monitors, and evaluates current processing capacity and use of system components.

**Implementation Guidance:**
- Monitor CPU, memory, storage, and network utilization
- Configure auto-scaling with defined limits
- Set alerting thresholds (70%, 85%, 95%)
- Conduct annual capacity planning review
- Forecast growth based on historical trends

**Evidence Requirements:**
- Monitoring dashboards (current utilization)
- Auto-scaling configuration
- Alerting threshold configuration
- Annual capacity planning document
- Growth forecasting analysis

### A1.2 - Disaster Recovery and Continuity

**Control Objective:** The entity authorizes, designs, develops, implements, operates, approves, maintains, and monitors environmental protections, software, data backup, and recovery infrastructure.

**Implementation Guidance:**
- Document DR plan with system-specific recovery procedures
- Define RTO/RPO per system tier
- Deploy multi-region or multi-AZ architecture for Tier 1 systems
- Configure automated failover for critical systems
- Maintain DR site in geographically separate region
- Conduct Business Impact Analysis (BIA)

**Evidence Requirements:**
- DR plan (current, approved)
- BIA results
- RTO/RPO definitions by system
- Multi-region architecture evidence
- Failover configuration documentation

### A1.3 - Recovery Testing

**Control Objective:** The entity tests recovery plan procedures supporting system recovery.

**Implementation Guidance:**
- Full DR failover test: Annual minimum
- Backup restoration test: Monthly
- Tabletop exercise: Semi-annual
- Communication tree test: Semi-annual
- Document test results with RTO/RPO achievement
- Track and remediate test failures

**Evidence Requirements:**
- DR failover test results (with RTO/RPO achieved vs target)
- Monthly backup restoration test results
- Tabletop exercise records
- Remediation records for test failures

**Common Audit Questions:**
- "When was the last DR failover test?"
- "Were RTO/RPO targets met during the last test?"
- "How often do you test backup restoration?"
- "What issues were identified in the last DR test and how were they addressed?"

**Typical Findings:**
- DR testing not performed in current period
- Backup restoration not tested regularly
- RTO/RPO targets not met during testing (with no remediation)
- DR plan outdated or not reflecting current architecture
- Tabletop exercises not conducted

---

## PI1: Processing Integrity

### PI1.1 - Completeness, Accuracy, Timeliness

**Control Objective:** The entity uses procedures to ensure system processing is complete, accurate, timely, and authorized.

**Implementation Guidance:**
- Input validation at all data entry points
- Processing checksums and hash verification
- Batch processing reconciliation (record counts, control totals)
- Transaction sequencing guarantees
- Processing authorization controls
- SLA monitoring for timeliness

**Evidence Requirements:**
- Input validation documentation
- Reconciliation procedures and results
- Processing SLA monitoring
- Authorization workflow configuration

### PI1.2-PI1.5 - Error Handling, Validation, Authorization, Quality

**Implementation Guidance:**
- Comprehensive error handling with classification codes
- Automated retry with exponential backoff
- Dead letter queues for failed messages
- Error notification and escalation
- Output reconciliation and verification
- Data quality monitoring dashboards

**Evidence Requirements:**
- Error handling procedures
- Dead letter queue configuration
- Error trend reports
- Output reconciliation records
- Data quality metrics

---

## C1: Confidentiality

### C1.1 - Data Classification and Protection

**Control Objective:** The entity identifies and maintains confidential information.

**Implementation Guidance:**
- Define classification levels: Public, Internal, Confidential, Restricted
- Create handling procedures per level
- Apply encryption: AES-256 at rest, TLS 1.2+ in transit
- Use HSM for production encryption keys
- Implement key rotation (annual minimum, 90 days for high-sensitivity)
- DLP controls for data exfiltration prevention

**Evidence Requirements:**
- Data classification policy
- Data asset inventory with classifications
- Encryption configuration (at rest and in transit)
- Key management configuration and rotation evidence
- DLP policy configuration (if applicable)

### C1.2 - Data Disposal

**Control Objective:** The entity disposes of confidential information to meet objectives.

**Implementation Guidance:**
- Define retention schedule by data category
- Implement automated retention enforcement
- Cryptographic erasure for cloud storage
- NIST 800-88 or DOD 5220.22-M for physical media
- Certificate of destruction from vendors
- Include backup data in retention scope

**Evidence Requirements:**
- Data retention schedule
- Automated enforcement configuration
- Disposal/destruction records
- Certificates of destruction
- Backup data retention documentation

---

## P1: Privacy

### P1.1 - Privacy Notice

**Implementation Guidance:**
- Clear, conspicuous privacy notice on website
- Cover: data collected, purposes, sharing, rights, retention, contact
- Cookie consent mechanism (opt-in for EU, opt-out for US)
- Update for material changes with notification

### P1.2 - Choice and Consent

**Implementation Guidance:**
- Granular consent options
- Consent withdrawal as easy as granting
- Consent records with timestamp and policy version
- Age verification for minors
- Double opt-in for marketing

### P1.3 - Collection Limitation

**Implementation Guidance:**
- Data minimization review for each collection point
- Document justification for each data element
- Eliminate unnecessary data collection
- Privacy by design in product development

### P1.4 - Use, Retention, and Disposal

**Implementation Guidance:**
- Purpose limitation documentation
- Retention schedule by data category
- Automated enforcement
- Legal hold capability
- Disposal verification

### P1.5 - Access (Data Subject Rights)

**Implementation Guidance:**
- DSR intake mechanism (web form, email)
- Identity verification procedures
- 30-day response SLA
- Support: access, correction, deletion, portability, restriction, objection
- Automated DSR fulfillment where possible

### P1.6 - Disclosure to Third Parties

**Implementation Guidance:**
- DPA with all processors
- Subprocessor list maintenance
- Customer notification of subprocessor changes
- Cross-border transfer mechanisms (SCCs, adequacy decisions)

### P1.7 - Quality

**Implementation Guidance:**
- Data accuracy procedures
- Self-service correction mechanisms
- Periodic data quality audits

### P1.8 - Monitoring and Enforcement

**Implementation Guidance:**
- Privacy Impact Assessments (PIAs) for new processing
- Annual privacy program review
- Privacy compliance metrics
- Privacy incident tracking

---

## Auditor Sample Selection Guide

Auditors typically select samples as follows:

| Control Frequency | Population Size | Typical Sample Size |
|-------------------|----------------|---------------------|
| Multiple times daily | >250 | 25-40 |
| Daily | 365 | 25-30 |
| Weekly | 52 | 10-15 |
| Monthly | 12 | 5-8 |
| Quarterly | 4 | 2-3 |
| Semi-annual | 2 | 2 |
| Annual | 1 | 1 |

**Key Consideration:** If ANY sample item fails, the auditor may:
1. Expand the sample size
2. Report an exception in the SOC 2 report
3. Qualify the opinion (if pervasive)

This means controls must operate consistently throughout the entire observation period, not just when evidence is collected.

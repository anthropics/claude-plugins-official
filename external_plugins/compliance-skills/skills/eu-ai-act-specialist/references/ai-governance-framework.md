# AI Governance Framework

Comprehensive reference for establishing AI governance structures aligned with EU AI Act (Regulation EU 2024/1689) requirements. Covers organizational design, ethics oversight, model lifecycle governance, incident management, and conformity assessment procedures.

---

## Table of Contents

- [AI Governance Organizational Structure](#ai-governance-organizational-structure)
- [AI Ethics Board](#ai-ethics-board)
- [AI Registry and Inventory Management](#ai-registry-and-inventory-management)
- [Model Lifecycle Governance](#model-lifecycle-governance)
- [Responsible AI Principles — Legal Requirements Mapping](#responsible-ai-principles--legal-requirements-mapping)
- [AI Incident Management](#ai-incident-management)
- [Conformity Assessment Procedures](#conformity-assessment-procedures)
- [CE Marking Process for AI Systems](#ce-marking-process-for-ai-systems)

---

## AI Governance Organizational Structure

### Recommended Governance Model

Organizations deploying AI systems subject to the EU AI Act should establish a three-tier governance structure:

```
TIER 1: STRATEGIC GOVERNANCE
┌─────────────────────────────────────────────────┐
│  Board of Directors / Executive Leadership       │
│  - Overall accountability for AI strategy        │
│  - Risk appetite and tolerance setting           │
│  - Resource allocation for AI compliance         │
└──────────────────────┬──────────────────────────┘
                       │
TIER 2: OVERSIGHT AND ADVISORY
┌──────────────────────┴──────────────────────────┐
│  AI Ethics Board / AI Governance Committee       │
│  - Policy development and review                 │
│  - Ethical review of high-risk AI systems        │
│  - Fundamental rights impact oversight           │
│  - Exception and escalation decisions            │
└──────────────────────┬──────────────────────────┘
                       │
TIER 3: OPERATIONAL GOVERNANCE
┌──────────────────────┴──────────────────────────┐
│  AI Compliance Function                          │
│  ┌───────────────────────────────────────────┐  │
│  │ AI Compliance Officer / Team              │  │
│  │ - Risk classification                     │  │
│  │ - Conformity assessment coordination      │  │
│  │ - Post-market monitoring                  │  │
│  │ - Regulatory liaison                      │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ AI Technical Governance                   │  │
│  │ - Data governance (Art. 10)               │  │
│  │ - Technical documentation (Art. 11)       │  │
│  │ - Model validation and testing            │  │
│  │ - Bias detection and fairness testing     │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ AI Risk Management                        │  │
│  │ - Risk identification and evaluation      │  │
│  │ - Control measure design                  │  │
│  │ - Incident management                     │  │
│  │ - Human oversight implementation          │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Key Roles and Responsibilities

| Role | Responsibility | AI Act Reference |
|------|---------------|------------------|
| **AI Compliance Officer** | Overall AI Act compliance oversight, regulatory liaison, classification decisions | Art. 17 (QMS), Art. 43 (conformity assessment) |
| **Data Governance Lead** | Training data quality, bias examination, representativeness analysis | Art. 10 |
| **AI Risk Manager** | Risk management system, risk evaluation, control measures | Art. 9 |
| **Human Oversight Coordinator** | Oversight personnel selection, training, procedure design | Art. 14 |
| **Technical Documentation Manager** | Technical file creation, maintenance, updates | Art. 11 |
| **Post-Market Monitoring Lead** | Monitoring system operation, incident reporting, data analysis | Art. 72, 73 |
| **AI Ethics Advisor** | Ethical review, fundamental rights impact assessment, bias review | Art. 27 |
| **AI Security Officer** | Cybersecurity measures, adversarial threat protection | Art. 15 |
| **AI Literacy Coordinator** | Training program design and delivery | Art. 4 |

### Governance Documentation Requirements

| Document | Purpose | Owner | Review Frequency |
|----------|---------|-------|-----------------|
| AI Governance Policy | Top-level governance framework and principles | AI Compliance Officer | Annual |
| AI System Inventory | Register of all AI systems with classifications | AI Compliance Officer | Continuous |
| AI Risk Management Policy | Risk appetite, methodology, escalation | AI Risk Manager | Annual |
| AI Data Governance Policy | Data quality, bias, representativeness standards | Data Governance Lead | Annual |
| AI Ethics Policy | Ethical principles and review procedures | AI Ethics Board | Annual |
| AI Incident Response Plan | Incident detection, classification, response, reporting | Post-Market Monitoring Lead | Annual |
| AI Literacy Program | Training curriculum and delivery plan | AI Literacy Coordinator | Semi-annual |
| Conformity Assessment Procedures | Assessment pathways and evidence requirements | AI Compliance Officer | As needed |

---

## AI Ethics Board

### Purpose

The AI Ethics Board provides independent oversight and advisory guidance on the ethical dimensions of AI system development and deployment. While not explicitly required by the AI Act, an ethics board is a best practice that supports compliance with fundamental rights obligations, bias prevention, and responsible AI deployment.

### Composition

| Member | Expertise | Role |
|--------|-----------|------|
| Independent Chair | Ethics, law, or governance | Chairs meetings, breaks ties, signs off on reviews |
| Legal Counsel | AI regulation, data protection, fundamental rights | Legal interpretation, regulatory guidance |
| Technical Expert | AI/ML engineering, data science | Technical feasibility assessment, bias analysis review |
| Domain Expert | Sector-specific knowledge (healthcare, finance, etc.) | Use-case context, impact assessment |
| External Ethicist | Applied ethics, philosophy of technology | Ethical framework application, societal impact |
| User/Affected Person Representative | End-user or affected community perspective | Impact from the perspective of those affected |
| Data Protection Officer | GDPR, data privacy | Personal data processing oversight |

### Operating Procedures

**Meetings:** Quarterly regular meetings; ad-hoc meetings for urgent reviews

**Quorum:** Minimum of 4 members including Chair and at least one external member

**Review triggers:**
- New high-risk AI system proposed for development
- Significant change to an existing high-risk AI system
- Bias detection findings requiring mitigation decisions
- Fundamental rights impact assessment results
- Serious incident involving an AI system
- Ethical concern raised by any employee (whistleblower pathway)

**Decisions:**
- Advisory recommendations (non-binding but must be addressed with documented rationale)
- Escalation to Board of Directors for strategic decisions
- Authority to recommend halting deployment pending investigation

### Ethical Review Process

```
1. SUBMISSION
   └── Project team submits AI Ethics Review Request
       Including: system description, risk classification,
       FRIA (if applicable), bias analysis results

2. SCREENING (5 business days)
   └── Ethics Board secretariat reviews for completeness
       ├── Complete → Schedule for review
       └── Incomplete → Return with guidance

3. REVIEW (15 business days)
   └── Board members review documentation
       └── Meeting to discuss findings and concerns

4. DETERMINATION
   ├── APPROVED — proceed with noted conditions
   ├── APPROVED WITH CONDITIONS — proceed after addressing conditions
   ├── DEFERRED — additional information or analysis required
   └── NOT APPROVED — significant ethical concerns; do not proceed

5. FOLLOW-UP
   └── Monitor conditions and report back at defined intervals
```

---

## AI Registry and Inventory Management

### AI System Registry

Maintain a comprehensive registry of all AI systems in the organization. This supports the EU database registration requirement (Art. 49) and internal governance.

### Registry Fields

| Field | Description | Required |
|-------|-------------|----------|
| **System ID** | Unique internal identifier | Yes |
| **System Name** | Human-readable name | Yes |
| **Version** | Current version | Yes |
| **Description** | Functional description | Yes |
| **Provider** | Internal team or external vendor | Yes |
| **Risk Classification** | Unacceptable / High / Limited / Minimal | Yes |
| **Annex III Category** | If applicable, which Annex III category | If high-risk |
| **Art. 6(3) Exception** | Whether exception was claimed and rationale | If Annex III |
| **Intended Purpose** | Specific use case | Yes |
| **Deployment Status** | Development / Testing / Staging / Production / Retired | Yes |
| **Deployment Date** | Date placed on market or put into service | If deployed |
| **EU Deployment** | Whether deployed or producing outputs used in EU | Yes |
| **Affected Persons** | Categories of persons affected | Yes |
| **Decision Impact** | Advisory / Automated with review / Fully automated | Yes |
| **Data Types** | Personal / Special category / Non-personal | Yes |
| **Model Type** | Classification, regression, NLP, computer vision, etc. | Yes |
| **Conformity Assessment** | Status and path (internal / third-party) | If high-risk |
| **CE Marking** | Whether applied | If high-risk |
| **EU Database ID** | Registration number in EU database | If registered |
| **Post-Market Monitoring** | Monitoring plan reference | If high-risk |
| **Responsible Person** | Internal compliance owner | Yes |
| **Ethics Review** | Status and reference | If high-risk |
| **Last Review Date** | Date of last compliance review | Yes |
| **Next Review Date** | Scheduled next review | Yes |

### Inventory Management Process

```
1. DISCOVERY
   └── Identify all AI systems across the organization
       ├── Procurement records (vendor AI systems)
       ├── IT system inventory
       ├── Development team records
       └── Shadow AI detection (unofficial AI tool usage)

2. REGISTRATION
   └── Enter each AI system into the registry
       └── Complete all required fields

3. CLASSIFICATION
   └── Apply risk classification (use ai_risk_classifier.py)
       └── Document classification rationale

4. ONGOING MANAGEMENT
   ├── New systems: Register before development begins
   ├── Changes: Update registry on any significant change
   ├── Retirement: Mark as retired, retain records
   └── Reviews: Quarterly review of all active systems

5. REPORTING
   ├── Management dashboard: Active systems by risk level
   ├── Compliance status: Gap analysis per system
   └── Board reporting: Summary metrics and risk posture
```

### Shadow AI Detection

Organizations must also detect and manage unofficial AI system usage:

| Detection Method | Description |
|-----------------|-------------|
| Network monitoring | Detect API calls to AI services (OpenAI, Anthropic, Google, etc.) |
| Procurement review | Review software subscriptions for AI tools |
| Employee surveys | Periodic surveys about AI tool usage |
| IT policy enforcement | Acceptable use policies for AI tools |
| Data flow analysis | Detect organizational data flowing to AI services |

---

## Model Lifecycle Governance

### Lifecycle Stages

```
┌─────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐
│ CONCEPT  │ -> │ DEVELOP   │ -> │ VALIDATE │ -> │ DEPLOY     │ -> │ MONITOR   │
│ & DESIGN │    │ & TRAIN   │    │ & TEST   │    │ & OPERATE  │    │ & MAINTAIN│
└─────────┘    └───────────┘    └──────────┘    └────────────┘    └───────────┘
                                                                        │
                                                                        v
                                                                  ┌───────────┐
                                                                  │ RETIRE    │
                                                                  └───────────┘
```

### Stage 1: Concept and Design

| Activity | Governance Control | AI Act Reference |
|----------|-------------------|------------------|
| Define intended purpose | Document and get approval | Art. 13 |
| Risk classification | Classify using decision tree | Art. 6 |
| Ethics review (high-risk) | Submit to AI Ethics Board | Best practice |
| FRIA (public bodies) | Complete before design | Art. 27 |
| Data requirements | Define data needs and governance plan | Art. 10 |
| Resource allocation | Budget for compliance activities | Art. 17 |

**Gate criteria:** Risk classification completed and documented; ethics review approved (if high-risk); resource plan approved.

### Stage 2: Develop and Train

| Activity | Governance Control | AI Act Reference |
|----------|-------------------|------------------|
| Data collection and preparation | Follow data governance policy | Art. 10 |
| Bias examination | Run bias detection on training data | Art. 10(2)(f) |
| Model training | Document architecture, parameters, choices | Art. 11 |
| Risk identification | Identify known and foreseeable risks | Art. 9 |
| Technical documentation | Begin drafting technical file | Art. 11 |

**Gate criteria:** Bias examination completed; risks identified and documented; technical documentation initiated.

### Stage 3: Validate and Test

| Activity | Governance Control | AI Act Reference |
|----------|-------------------|------------------|
| Performance testing | Test against defined metrics and thresholds | Art. 9(7) |
| Fairness testing | Test outcomes across demographic groups | Art. 10(2)(f) |
| Robustness testing | Test with noisy, adversarial, and edge-case inputs | Art. 15 |
| Security testing | Test for AI-specific vulnerabilities | Art. 15 |
| Human oversight testing | Verify oversight mechanisms function correctly | Art. 14 |
| Logging verification | Verify automatic logging captures required data | Art. 12 |

**Gate criteria:** All tests passed or accepted with documented rationale; risk management measures verified; technical documentation complete.

### Stage 4: Deploy and Operate

| Activity | Governance Control | AI Act Reference |
|----------|-------------------|------------------|
| Conformity assessment | Complete internal control or third-party assessment | Art. 43 |
| CE marking | Affix before placing on market | Art. 48 |
| EU database registration | Register before deployment | Art. 49 |
| Deploy instructions for use | Provide to all deployers | Art. 13 |
| Activate monitoring | Start post-market monitoring system | Art. 72 |
| Train oversight personnel | Ensure competency of human overseers | Art. 14 |
| Inform workers | Notify workers subject to AI system | Art. 26(7) |

**Gate criteria:** Conformity assessment completed; CE marking applied; EU database registration confirmed; monitoring active.

### Stage 5: Monitor and Maintain

| Activity | Governance Control | AI Act Reference |
|----------|-------------------|------------------|
| Performance monitoring | Continuous performance and drift tracking | Art. 72 |
| Bias monitoring | Ongoing fairness metric tracking | Art. 10, 72 |
| Incident management | Detect, classify, respond, report incidents | Art. 73 |
| Risk management updates | Update risk assessment with new data | Art. 9 |
| Model retraining | Governed retraining process with validation | Art. 9, 10, 11 |
| Documentation updates | Keep technical documentation current | Art. 11 |
| Periodic review | Regular compliance review | Art. 17 |

**Triggers for re-assessment:**
- Significant model performance degradation
- Bias metric exceeding defined thresholds
- Serious incident reported
- Change in intended purpose or deployment context
- Material change to the model (retraining, architecture change)
- Regulatory guidance update

### Stage 6: Retirement

| Activity | Governance Control |
|----------|-------------------|
| Retirement decision | Documented rationale for retirement |
| Data retention | Retain logs and documentation per retention policy |
| EU database update | Update registration to reflect retirement |
| Notification | Inform deployers and affected parties |
| Knowledge transfer | Document lessons learned |
| Archive | Archive technical documentation per retention requirements |

---

## Responsible AI Principles — Legal Requirements Mapping

### Mapping Ethical Principles to Legal Obligations

| Responsible AI Principle | EU AI Act Legal Requirement | Articles |
|--------------------------|---------------------------|----------|
| **Transparency** | System transparency; instructions for use; AI interaction disclosure | Art. 13, Art. 50 |
| **Fairness and Non-discrimination** | Data governance; bias examination and mitigation; representative datasets | Art. 10(2)(f)(g) |
| **Accountability** | QMS accountability framework; record-keeping; traceability | Art. 12, Art. 17 |
| **Safety** | Risk management system; accuracy, robustness, cybersecurity | Art. 9, Art. 15 |
| **Human Agency** | Human oversight; automation bias safeguards; intervention mechanisms | Art. 14 |
| **Privacy** | Data governance; GDPR alignment; special category data safeguards | Art. 10(5), GDPR |
| **Societal Wellbeing** | Fundamental rights impact assessment; prohibited practices | Art. 5, Art. 27 |
| **Explainability** | Transparency to deployers; interpretable outputs | Art. 13, Art. 14 |
| **Robustness** | Accuracy and robustness requirements; adversarial resilience | Art. 15 |
| **Sustainability** | Energy reporting for GPAI; voluntary codes of conduct | Art. 55(1)(e), Art. 95 |

---

## AI Incident Management

### Incident Classification

| Severity | Definition | Response Time | Reporting |
|----------|-----------|---------------|-----------|
| **Critical** | Serious incident — death, serious damage to health, serious and irreversible disruption to critical infrastructure, serious breach of fundamental rights | Immediate response | Report to market surveillance authority within 15 days (Art. 73) |
| **High** | Near-miss serious incident or significant malfunction with potential for serious consequences | Within 4 hours | Internal escalation; assess if Art. 73 reporting required |
| **Medium** | Malfunction affecting performance but not meeting serious incident criteria | Within 24 hours | Internal documentation; provider notification |
| **Low** | Minor anomaly, degraded performance within acceptable bounds | Within 1 week | Internal logging; trend monitoring |

### Serious Incident Definition (Art. 3(49))

An incident or malfunctioning of an AI system that directly or indirectly leads to any of the following:
1. Death or serious damage to the health of a person
2. Serious and irreversible disruption of the management or operation of critical infrastructure
3. Breach of obligations under Union law intended to protect fundamental rights
4. Serious damage to property or the environment

### Incident Response Process

```
1. DETECTION
   ├── Automated monitoring alerts
   ├── Human oversight personnel reports
   ├── Deployer incident reports
   ├── Affected person complaints
   └── External reports (authorities, media)

2. TRIAGE (within 1 hour)
   ├── Classify severity (Critical / High / Medium / Low)
   ├── Assign incident owner
   ├── Determine if serious incident (Art. 3(49))
   └── Activate appropriate response team

3. CONTAINMENT (immediate for Critical/High)
   ├── Assess need to halt system operation
   ├── Implement immediate corrective measures
   ├── Preserve evidence and logs
   └── Secure affected data

4. INVESTIGATION
   ├── Root cause analysis
   ├── Impact assessment (persons affected, scope, severity)
   ├── Review risk management adequacy
   ├── Assess whether system still meets requirements
   └── Identify systemic issues

5. REPORTING (within 15 days for serious incidents)
   ├── Report to market surveillance authority (Art. 73)
   │   ├── Authorities of ALL member states where incident occurred
   │   ├── Include: description, corrective actions, known details
   │   └── Follow up with additional information as available
   ├── Report to notified body (if applicable)
   └── Notify deployers

6. CORRECTIVE ACTION
   ├── Implement corrective measures
   ├── Update risk management system
   ├── Update technical documentation
   ├── Retrain model if needed (with governance controls)
   └── Communicate changes to deployers

7. CLOSURE AND LEARNING
   ├── Verify corrective actions are effective
   ├── Update post-market monitoring system
   ├── Document lessons learned
   ├── Update AI literacy training if needed
   └── Close incident record
```

### Incident Documentation Requirements

| Field | Description |
|-------|-------------|
| Incident ID | Unique identifier |
| Detection date/time | When incident was detected |
| Occurrence date/time | When incident occurred (if different) |
| AI System | System name, version, registration number |
| Severity classification | Critical / High / Medium / Low |
| Serious incident? | Yes/No per Art. 3(49) criteria |
| Description | What happened |
| Root cause | Identified or suspected root cause |
| Affected persons | Number and categories of affected persons |
| Impact | Health, safety, fundamental rights, property, environment |
| Containment actions | Immediate actions taken |
| Corrective actions | Remediation measures |
| Reporting | Authorities notified, dates, references |
| Status | Open / Under investigation / Corrective action / Closed |
| Closure date | When incident was closed |
| Lessons learned | Insights for preventing recurrence |

---

## Conformity Assessment Procedures

### Internal Control Procedure (Annex VI)

For high-risk AI systems where internal control is sufficient (Annex III categories 2-8, with harmonised standards applied):

```
PHASE 1: PREPARATION (months 1-3)
├── 1.1 Establish/verify QMS meets Art. 17 requirements
├── 1.2 Verify all Chapter III Section 2 requirements are implemented
├── 1.3 Compile technical documentation (Art. 11, Annex IV)
├── 1.4 Complete all testing (accuracy, robustness, cybersecurity, fairness)
└── 1.5 Designate person(s) responsible for conformity assessment

PHASE 2: INTERNAL ASSESSMENT (months 3-5)
├── 2.1 Review technical documentation for completeness and accuracy
├── 2.2 Verify risk management system (Art. 9)
│   ├── Risks identified, evaluated, and controlled
│   ├── Testing completed against defined metrics
│   └── Residual risks acceptable
├── 2.3 Verify data governance (Art. 10)
│   ├── Data quality criteria met
│   ├── Bias examined and mitigated
│   └── Special category data handled properly
├── 2.4 Verify record-keeping (Art. 12)
│   ├── Automatic logging implemented
│   └── Retention periods defined
├── 2.5 Verify transparency (Art. 13)
│   ├── Instructions for use complete
│   └── All required information included
├── 2.6 Verify human oversight (Art. 14)
│   ├── Oversight level appropriate
│   ├── Mechanisms functional
│   └── Automation bias safeguards in place
├── 2.7 Verify accuracy, robustness, cybersecurity (Art. 15)
│   ├── Performance metrics meet targets
│   ├── Robustness tested
│   └── Cybersecurity measures proportionate
├── 2.8 Verify QMS (Art. 17)
│   └── All QMS elements documented and implemented
└── 2.9 Document assessment findings and conclusions

PHASE 3: DECLARATION (month 5-6)
├── 3.1 Prepare EU Declaration of Conformity (Art. 47)
│   ├── Provider name and address
│   ├── AI system identification
│   ├── Declaration of conformity with AI Act
│   ├── Reference to harmonised standards applied
│   ├── Signed by authorized representative
│   └── Date and place of issuance
├── 3.2 Affix CE marking (Art. 48)
├── 3.3 Register in EU database (Art. 49)
└── 3.4 Retain documentation for 10 years

PHASE 4: POST-MARKET (ongoing)
├── 4.1 Implement post-market monitoring system (Art. 72)
├── 4.2 Maintain documentation updates
├── 4.3 Report serious incidents within 15 days (Art. 73)
├── 4.4 Re-assess conformity on significant changes
└── 4.5 Annual compliance review
```

### Third-Party Assessment Procedure (Annex VII)

For biometric identification systems (Annex III category 1) and cases where harmonised standards are insufficient:

```
PHASE 1: PREPARATION (months 1-4)
├── 1.1 Complete all Phase 1 steps from internal control procedure
├── 1.2 Select notified body
│   ├── Check notified body competence and scope
│   ├── Verify designation covers the AI system type
│   └── Agree on timeline and scope of assessment
└── 1.3 Prepare submission package for notified body

PHASE 2: QMS ASSESSMENT BY NOTIFIED BODY (months 4-8)
├── 2.1 Submit QMS documentation to notified body
├── 2.2 Notified body reviews:
│   ├── QMS documentation completeness
│   ├── QMS implementation (may include on-site audit)
│   ├── Representative sample of AI system development records
│   └── Evidence of QMS effectiveness
├── 2.3 Notified body determination:
│   ├── QMS certificate issued → proceed to Phase 3
│   └── Corrective action required → address and re-submit
└── 2.4 QMS certificate issued (valid for specified period)

PHASE 3: TECHNICAL DOCUMENTATION ASSESSMENT (months 6-10)
├── 3.1 Submit complete technical documentation to notified body
├── 3.2 Notified body reviews:
│   ├── Technical documentation completeness (Annex IV)
│   ├── System compliance with requirements (Art. 9-15)
│   ├── Data governance and bias examination results
│   ├── Testing and validation results
│   └── Human oversight design
├── 3.3 Notified body may:
│   ├── Request additional testing
│   ├── Conduct independent testing
│   ├── Review source code or training data (subject to confidentiality)
│   └── Interview development team
├── 3.4 Notified body determination:
│   ├── EU type-examination certificate issued → proceed to Phase 4
│   └── Non-conformity identified → address and re-submit
└── 3.5 Type-examination certificate issued (valid for specified period)

PHASE 4: DECLARATION AND MARKING (months 10-12)
├── 4.1 Prepare EU Declaration of Conformity
│   ├── Reference both QMS certificate and type-examination certificate
│   └── Include notified body identification number
├── 4.2 Affix CE marking with notified body identification number
├── 4.3 Register in EU database
└── 4.4 Retain documentation for 10 years

PHASE 5: ONGOING SURVEILLANCE (annual)
├── 5.1 Notified body periodic surveillance audits
├── 5.2 Notify notified body of any planned significant changes
├── 5.3 Obtain approval before implementing significant changes
├── 5.4 Maintain QMS and technical documentation
└── 5.5 Report serious incidents to notified body
```

### Selecting the Correct Assessment Path

| System Category | Default Path | Conditions for Alternative |
|----------------|-------------|--------------------------|
| Annex III, point 1 (biometrics) | Third-party (Annex VII) | No alternative — third-party required |
| Annex III, points 2-8 | Internal control (Annex VI) | Third-party required if harmonised standards not applied or do not fully cover requirements |
| Annex I products (safety components) | Per product legislation | Follow the applicable product conformity assessment |
| GPAI models | No conformity assessment per se | Compliance demonstration to AI Office |

---

## CE Marking Process for AI Systems

### CE Marking Requirements (Art. 48)

| Requirement | Detail |
|-------------|--------|
| **Visibility** | CE marking must be visible on the AI system, its packaging, or accompanying documentation |
| **Legibility** | Must be clearly legible (minimum 5mm height per Regulation 765/2008 unless impractical) |
| **Indelibility** | Must be indelible — cannot be easily removed |
| **Notified body number** | If third-party assessment performed, include the notified body's four-digit identification number |
| **Timing** | Must be affixed BEFORE placing on the market |
| **Single marking** | One CE marking per system — covers both product legislation and AI Act if applicable |

### CE Marking Process

```
1. CONFIRM ELIGIBILITY
   └── System has completed conformity assessment (Annex VI or VII)

2. PREPARE DECLARATION
   └── EU Declaration of Conformity signed per Art. 47

3. DESIGN MARKING
   ├── Standard CE marking format
   ├── Add notified body number (if applicable): CE XXXX
   └── Determine placement (system, packaging, or documentation)

4. APPLY MARKING
   ├── For software: In the system UI, About screen, or documentation
   ├── For hardware: Physical marking on the device
   ├── For digital-only: In documentation and EU database entry
   └── Ensure visibility, legibility, indelibility

5. REGISTER
   └── Update EU database registration with CE marking status

6. MAINTAIN
   ├── Ensure marking remains valid throughout system lifetime
   ├── Re-assess if significant changes are made
   └── Remove if conformity can no longer be ensured
```

### Declaration of Conformity Content (Art. 47)

The EU Declaration of Conformity must contain:

| Element | Description |
|---------|-------------|
| Provider details | Name and address of the provider |
| AI system identification | System name, type, version, serial number or batch identifier |
| Conformity statement | Statement that the AI system is in conformity with the AI Act |
| Standards | References to harmonised standards or common specifications applied |
| Notified body | Name, number, and certificate references (if applicable) |
| Additional legislation | Reference to any other applicable EU legislation |
| Signature | Signed by a person authorised to bind the provider |
| Date and place | Date and place of issue |
| Responsible person | Name, position, and contact details of the person signing |

---

**Last Updated:** March 2026
**Regulation Reference:** Regulation (EU) 2024/1689 — EU Artificial Intelligence Act

---
name: quality-manager-qms-iso13485
description: >
  ISO 13485 Quality Management System implementation and maintenance for medical
  device organizations. Provides QMS design, documentation control, internal
  auditing, CAPA management, and certification support.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: quality-management
  updated: 2026-03-31
  tags:
    - iso-13485
    - qms
    - design-control
    - supplier-qualification
    - medical-device
---
# Quality Manager - QMS ISO 13485 Specialist

ISO 13485:2016 Quality Management System implementation, maintenance, and certification support for medical device organizations.

---

## Table of Contents

- [QMS Implementation Workflow](#qms-implementation-workflow)
- [Document Control Workflow](#document-control-workflow)
- [Internal Audit Workflow](#internal-audit-workflow)
- [Process Validation Workflow](#process-validation-workflow)
- [Supplier Qualification Workflow](#supplier-qualification-workflow)
- [QMS Process Reference](#qms-process-reference)
- [Decision Frameworks](#decision-frameworks)
- [Tools and References](#tools-and-references)

---

## QMS Implementation Workflow

Implement ISO 13485:2016 compliant quality management system from gap analysis through certification.

### Workflow: Initial QMS Implementation

1. Conduct gap analysis against ISO 13485:2016 requirements
2. Document current state vs. required state for each clause
3. Prioritize gaps by:
   - Regulatory criticality
   - Risk to product safety
   - Resource requirements
4. Develop implementation roadmap with milestones
5. Establish Quality Manual per Clause 4.2.2:
   - QMS scope with justified exclusions
   - Process interactions
   - Procedure references
6. Create required documented procedures:
   - Document control (4.2.3)
   - Record control (4.2.4)
   - Internal audit (8.2.4)
   - Nonconforming product (8.3)
   - Corrective action (8.5.2)
   - Preventive action (8.5.3)
7. Deploy processes with training
8. **Validation:** Gap analysis complete; Quality Manual approved; all required procedures documented and trained

### Gap Analysis Matrix

| Clause | Requirement | Current State | Gap | Priority | Action |
|--------|-------------|---------------|-----|----------|--------|
| 4.2.2 | Quality Manual | Not documented | Major | High | Create QM |
| 4.2.3 | Document control | Informal | Moderate | High | Formalize SOP |
| 5.6 | Management review | Ad hoc | Major | High | Establish schedule |
| 7.3 | Design control | Partial | Moderate | Medium | Complete procedures |
| 8.2.4 | Internal audit | None | Major | High | Create program |

### QMS Structure

| Level | Document Type | Purpose | Example |
|-------|---------------|---------|---------|
| 1 | Quality Manual | QMS overview, policy | QM-001 |
| 2 | Procedures | How processes work | SOP-02-001 |
| 3 | Work Instructions | Task-level detail | WI-06-012 |
| 4 | Records | Evidence of conformity | Training records |

### Required Procedure List

| Clause | Procedure | Minimum Content |
|--------|-----------|-----------------|
| 4.2.3 | Document Control | Approval, review, distribution, obsolete control |
| 4.2.4 | Record Control | Identification, storage, retention, disposal |
| 8.2.4 | Internal Audit | Program, auditor qualification, reporting |
| 8.3 | Nonconforming Product | Identification, segregation, disposition |
| 8.5.2 | Corrective Action | Investigation, root cause, effectiveness |
| 8.5.3 | Preventive Action | Risk identification, implementation, verification |

---

## Document Control Workflow

Establish and maintain document control per ISO 13485 Clause 4.2.3.

### Workflow: Document Creation and Approval

1. Identify need for new document or revision
2. Assign document number per numbering convention:
   - Format: `[TYPE]-[AREA]-[SEQUENCE]-[REV]`
   - Example: `SOP-02-001-01`
3. Draft document using approved template
4. Route for review to subject matter experts
5. Collect and address review comments
6. Obtain required approvals based on document type
7. Update Document Master List
8. **Validation:** Document numbered correctly; all reviewers signed; Master List updated

### Document Numbering Convention

| Prefix | Document Type | Approval Authority |
|--------|---------------|-------------------|
| QM | Quality Manual | Management Rep + CEO |
| POL | Policy | Department Head + QA |
| SOP | Procedure | Process Owner + QA |
| WI | Work Instruction | Supervisor + QA |
| TF | Template/Form | Process Owner |
| SPEC | Specification | Engineering + QA |

### Area Codes

| Code | Area | Examples |
|------|------|----------|
| 01 | Quality Management | Quality Manual, policy |
| 02 | Document Control | This procedure |
| 03 | Training | Competency procedures |
| 04 | Design | Design control |
| 05 | Purchasing | Supplier management |
| 06 | Production | Manufacturing |
| 07 | Quality Control | Inspection, testing |
| 08 | CAPA | Corrective actions |

### Document Change Control

| Change Type | Approval Level | Examples |
|-------------|----------------|----------|
| Administrative | Document Control | Typos, formatting |
| Minor | Process Owner + QA | Clarifications |
| Major | Full review cycle | Process changes |
| Emergency | Expedited + retrospective | Safety issues |

### Document Review Schedule

| Document Type | Review Period | Trigger for Unscheduled Review |
|---------------|---------------|-------------------------------|
| Quality Manual | Annual | Organizational change |
| Procedures | Annual | Audit finding, regulation change |
| Work Instructions | 2 years | Process change |
| Forms | 2 years | User feedback |

---

## Internal Audit Workflow

Plan and execute internal audits per ISO 13485 Clause 8.2.4.

### Workflow: Annual Audit Program

1. Identify processes and areas requiring audit coverage
2. Assess risk factors for audit frequency:
   - Previous audit findings
   - Regulatory changes
   - Process changes
   - Complaint trends
3. Assign qualified auditors (independent of area audited)
4. Develop annual audit schedule
5. Obtain management approval
6. Communicate schedule to process owners
7. Track completion and reschedule as needed
8. **Validation:** All processes covered; auditors qualified and independent; schedule approved

### Workflow: Individual Audit Execution

1. Prepare audit plan with scope, criteria, and schedule
2. Notify auditee minimum 1 week prior
3. Review procedures and previous audit results
4. Prepare audit checklist
5. Conduct opening meeting
6. Collect evidence through:
   - Document review
   - Record sampling
   - Process observation
   - Personnel interviews
7. Classify findings:
   - Major NC: Absence or breakdown of system
   - Minor NC: Single lapse or deviation
   - Observation: Risk of future NC
8. Conduct closing meeting
9. Issue audit report within 5 business days
10. **Validation:** All checklist items addressed; findings supported by evidence; report distributed

### Audit Program Template

| Audit # | Process | Clauses | Q1 | Q2 | Q3 | Q4 | Auditor |
|---------|---------|---------|----|----|----|----|---------|
| IA-001 | Document Control | 4.2.3, 4.2.4 | X | | | | [Name] |
| IA-002 | Management Review | 5.6 | | X | | | [Name] |
| IA-003 | Design Control | 7.3 | | X | | | [Name] |
| IA-004 | Production | 7.5 | | | X | | [Name] |
| IA-005 | CAPA | 8.5.2, 8.5.3 | | | | X | [Name] |

### Auditor Qualification Requirements

| Criterion | Requirement |
|-----------|-------------|
| Training | ISO 13485 awareness + auditor training |
| Experience | Minimum 1 audit as observer |
| Independence | Not auditing own work area |
| Competence | Understanding of audited process |

### Finding Classification Guide

| Classification | Criteria | Response Time |
|----------------|----------|---------------|
| Major NC | System absence, total breakdown, regulatory violation | 30 days for CAPA |
| Minor NC | Single instance, partial compliance | 60 days for CAPA |
| Observation | Potential risk, improvement opportunity | Track in next audit |

---

## Process Validation Workflow

Validate special processes per ISO 13485 Clause 7.5.6.

### Workflow: Process Validation Protocol

1. Identify processes requiring validation:
   - Output cannot be verified by inspection
   - Deficiencies appear only in use
   - Sterilization, welding, sealing, software
2. Form validation team with subject matter experts
3. Write validation protocol including:
   - Process description and parameters
   - Equipment and materials
   - Acceptance criteria
   - Statistical approach
4. Execute Installation Qualification (IQ):
   - Verify equipment installed correctly
   - Document equipment specifications
5. Execute Operational Qualification (OQ):
   - Test parameter ranges
   - Verify process control
6. Execute Performance Qualification (PQ):
   - Run production conditions
   - Verify output meets requirements
7. Write validation report with conclusions
8. **Validation:** IQ/OQ/PQ complete; acceptance criteria met; validation report approved

### Validation Documentation Requirements

| Phase | Content | Evidence |
|-------|---------|----------|
| Protocol | Objectives, methods, criteria | Approved protocol |
| IQ | Equipment verification | Installation records |
| OQ | Parameter verification | Test results |
| PQ | Performance verification | Production data |
| Report | Summary, conclusions | Approval signatures |

### Revalidation Triggers

| Trigger | Action Required |
|---------|-----------------|
| Equipment change | Assess impact, revalidate affected phases |
| Parameter change | OQ and PQ minimum |
| Material change | Assess impact, PQ minimum |
| Process failure | Full revalidation |
| Periodic | Per validation schedule (typically 3 years) |

### Special Process Examples

| Process | Validation Standard | Critical Parameters |
|---------|--------------------|--------------------|
| EO Sterilization | ISO 11135 | Temperature, humidity, EO concentration, time |
| Steam Sterilization | ISO 17665 | Temperature, pressure, time |
| Radiation Sterilization | ISO 11137 | Dose, dose uniformity |
| Sealing | Internal | Temperature, pressure, dwell time |
| Welding | ISO 11607 | Heat, pressure, speed |

---

## Supplier Qualification Workflow

Evaluate and approve suppliers per ISO 13485 Clause 7.4.

### Workflow: New Supplier Qualification

1. Identify supplier category:
   - Category A: Critical (affects safety/performance)
   - Category B: Major (affects quality)
   - Category C: Minor (indirect impact)
2. Request supplier information:
   - Quality certifications
   - Product specifications
   - Quality history
3. Evaluate supplier based on:
   - Quality system (ISO certification)
   - Technical capability
   - Quality history
   - Financial stability
4. For Category A suppliers:
   - Conduct on-site audit
   - Require quality agreement
5. Calculate qualification score
6. Make approval decision:
   - >80: Approved
   - 60-80: Conditional approval
   - <60: Not approved
7. Add to Approved Supplier List
8. **Validation:** Evaluation criteria scored; qualification records complete; supplier categorized

### Supplier Evaluation Criteria

| Criterion | Weight | Scoring |
|-----------|--------|---------|
| Quality System | 30% | ISO 13485=30, ISO 9001=20, Documented=10, None=0 |
| Quality History | 25% | Reject rate: <1%=25, 1-3%=15, >3%=0 |
| Delivery | 20% | On-time: >95%=20, 90-95%=10, <90%=0 |
| Technical Capability | 15% | Exceeds=15, Meets=10, Marginal=5 |
| Financial Stability | 10% | Strong=10, Adequate=5, Questionable=0 |

### Supplier Category Requirements

| Category | Qualification | Monitoring | Agreement |
|----------|---------------|------------|-----------|
| A - Critical | On-site audit | Annual review | Quality agreement |
| B - Major | Questionnaire | Semi-annual review | Quality requirements |
| C - Minor | Assessment | Issue-based | Standard terms |

### Supplier Performance Metrics

| Metric | Target | Calculation |
|--------|--------|-------------|
| Accept Rate | >98% | (Accepted lots / Total lots) × 100 |
| On-Time Delivery | >95% | (On-time / Total orders) × 100 |
| Response Time | <5 days | Average days to resolve issues |
| Documentation | 100% | (Complete CoCs / Required CoCs) × 100 |

---

## QMS Process Reference

### ISO 13485 Clause Structure

| Clause | Title | Key Requirements |
|--------|-------|-----------------|
| 4.1 | General Requirements | Process identification, interaction, outsourcing |
| 4.2 | Documentation | Quality Manual, procedures, records |
| 5.1-5.5 | Management Responsibility | Commitment, policy, objectives, organization |
| 5.6 | Management Review | Inputs, outputs, records |
| 6.1-6.4 | Resource Management | Personnel, infrastructure, environment |
| 7.1 | Product Realization Planning | Quality plan, risk management |
| 7.2 | Customer Requirements | Determination, review, communication |
| 7.3 | Design and Development | Planning, inputs, outputs, review, V&V, transfer, changes |
| 7.4 | Purchasing | Supplier control, purchasing info, verification |
| 7.5 | Production | Control, cleanliness, validation, identification, traceability |
| 7.6 | Monitoring Equipment | Calibration, control |
| 8.1 | Measurement Planning | Monitoring and analysis planning |
| 8.2 | Monitoring | Feedback, complaints, reporting, audits, process, product |
| 8.3 | Nonconforming Product | Control, disposition |
| 8.4 | Data Analysis | Trend analysis |
| 8.5 | Improvement | CAPA |

### Management Review Required Inputs (Clause 5.6.2)

| Input | Source | Prepared By |
|-------|--------|-------------|
| Audit results | Internal and external audits | QA Manager |
| Customer feedback | Complaints, surveys | Customer Quality |
| Process performance | Process metrics | Process Owners |
| Product conformity | Inspection data, NCs | QC Manager |
| CAPA status | CAPA system | CAPA Officer |
| Previous actions | Prior review records | QMR |
| Changes affecting QMS | Regulatory, organizational | RA Manager |
| Recommendations | All sources | All Managers |

### Record Retention Requirements

| Record Type | Minimum Retention | Regulatory Basis |
|-------------|-------------------|------------------|
| Device Master Record | Life of device + 2 years | 21 CFR 820.181 |
| Device History Record | Life of device + 2 years | 21 CFR 820.184 |
| Design History File | Life of device + 2 years | 21 CFR 820.30 |
| Complaint Records | Life of device + 2 years | 21 CFR 820.198 |
| Training Records | Employment + 3 years | Best practice |
| Audit Records | 7 years | Best practice |
| CAPA Records | 7 years | Best practice |
| Calibration Records | Equipment life + 2 years | Best practice |

---

## Decision Frameworks

### Exclusion Justification (Clause 4.2.2)

| Clause | Permissible Exclusion | Justification Required |
|--------|----------------------|------------------------|
| 6.4.2 | Contamination control | Product not affected by contamination |
| 7.3 | Design and development | Organization does not design products |
| 7.5.2 | Product cleanliness | No cleanliness requirements |
| 7.5.3 | Installation | No installation activities |
| 7.5.4 | Servicing | No servicing activities |
| 7.5.5 | Sterile products | No sterile products |

### Nonconformity Disposition Decision Tree

```
Nonconforming Product Identified
            │
            ▼
    Can it be reworked?
            │
       Yes──┴──No
        │       │
        ▼       ▼
    Is rework     Can it be used
    procedure     as is?
    available?        │
        │        Yes──┴──No
    Yes─┴─No     │       │
     │    │     ▼       ▼
     ▼    ▼  Concession  Scrap or
  Rework  Create    approval    return to
  per SOP  rework    needed?    supplier
          procedure     │
                    Yes─┴─No
                     │    │
                     ▼    ▼
                 Customer  Use as is
                 approval  with MRB
                          approval
```

### CAPA Initiation Criteria

| Source | Automatic CAPA | Evaluate for CAPA |
|--------|----------------|-------------------|
| Customer complaint | Safety-related | All others |
| External audit | Major NC | Minor NC |
| Internal audit | Major NC | Repeat minor NC |
| Product NC | Field failure | Trend exceeds threshold |
| Process deviation | Safety impact | Repeated deviations |

---

## Tools and References

### Scripts

| Tool | Purpose | Usage |
|------|---------|-------|
| [qms_audit_checklist.py](scripts/qms_audit_checklist.py) | Generate audit checklists by clause or process | `python qms_audit_checklist.py --help` |

**Audit Checklist Generator Features:**
- Generate clause-specific checklists (e.g., `--clause 7.3`)
- Generate process-based checklists (e.g., `--process design-control`)
- Full system audit checklist (`--audit-type system`)
- Text or JSON output formats
- Interactive mode for guided selection

### References

| Document | Content |
|----------|---------|
| [iso13485-clause-requirements.md](references/iso13485-clause-requirements.md) | Detailed requirements for each ISO 13485:2016 clause with audit questions |
| [qms-process-templates.md](references/qms-process-templates.md) | Ready-to-use templates for document control, audit, CAPA, supplier, training |

### Quick Reference: Mandatory Documented Procedures

| Procedure | Clause | Key Elements |
|-----------|--------|--------------|
| Document Control | 4.2.3 | Approval, distribution, obsolete control |
| Record Control | 4.2.4 | Identification, retention, disposal |
| Internal Audit | 8.2.4 | Program, auditor qualification, reporting |
| NC Product Control | 8.3 | Identification, segregation, disposition |
| Corrective Action | 8.5.2 | Root cause, implementation, verification |
| Preventive Action | 8.5.3 | Risk identification, implementation |

---

## Related Skills

| Skill | Integration Point |
|-------|-------------------|
| [quality-manager-qmr](../quality-manager-qmr/) | Management review, quality policy |
| [capa-officer](../capa-officer/) | CAPA system management |
| [qms-audit-expert](../qms-audit-expert/) | Advanced audit techniques |
| [quality-documentation-manager](../quality-documentation-manager/) | DHF, DMR, DHR management |
| [risk-management-specialist](../risk-management-specialist/) | ISO 14971 integration |

---

## ISO 13485:2016 Alignment with FDA QMSR

### QMSR Transition Impact on ISO 13485 QMS

With the FDA's QMSR (effective February 2, 2026) incorporating ISO 13485:2016 by reference, organizations already ISO 13485 certified gain significant advantages:

| Area | Pre-QMSR (Dual System) | Post-QMSR (Unified) |
|------|----------------------|---------------------|
| Quality Manual | Separate FDA QSR and ISO 13485 references | Single Quality Manual referencing ISO 13485 |
| Design controls | 820.30 + ISO 13485 Clause 7.3 (mapped) | ISO 13485 Clause 7.3 (primary) |
| CAPA | 820.100 + ISO 13485 Clause 8.5 | ISO 13485 Clause 8.5 (primary) |
| Document control | 820.40 + ISO 13485 Clause 4.2 | ISO 13485 Clause 4.2 (primary) |
| Purchasing | 820.50 + ISO 13485 Clause 7.4 | ISO 13485 Clause 7.4 (primary) |
| Audits | Separate FDA and ISO audit tracks | Single audit satisfying both |

### FDA-Retained Requirements Beyond ISO 13485

Even under QMSR, certain FDA-specific requirements remain. The QMS must address:

| FDA Requirement | CFR Reference | ISO 13485 Gap | Action |
|----------------|---------------|---------------|--------|
| Complaint handling (medical device reports) | 21 CFR 820.198 | Clause 8.2.2 covers complaints but not FDA MDR reporting specifics | Add FDA MDR reporting procedure to complaint handling SOP |
| Corrections and removals | 21 CFR 806 | No direct equivalent | Maintain separate procedure for FDA reporting of corrections/removals |
| Unique Device Identification | 21 CFR 830 | No UDI clause in ISO 13485 | Add UDI procedures to labeling/identification processes |
| Electronic records and signatures | 21 CFR Part 11 | No electronic signature requirements | Implement Part 11 compliance for electronic QMS |

### QMSR Gap Analysis Checklist

- [ ] Map all existing QSR SOPs to ISO 13485 clause numbers
- [ ] Identify FDA-retained requirements not covered by ISO 13485
- [ ] Update Quality Manual scope and references
- [ ] Retrain staff on ISO 13485 terminology (e.g., "design output" terminology alignment)
- [ ] Update supplier quality agreements to reference QMSR
- [ ] Revise internal audit checklist to combined ISO 13485 + FDA requirements
- [ ] Verify complaint handling addresses both ISO 13485 Clause 8.2.2 and 21 CFR 820.198
- [ ] Conduct mock audit against QMSR requirements

---

## Digital QMS Implementation

### Electronic Document Management System (eDMS) Requirements

| Requirement | Implementation | Regulatory Basis |
|-------------|---------------|------------------|
| Document version control | Automatic versioning with audit trail | ISO 13485 Clause 4.2.3 |
| Electronic approval workflows | Role-based approval routing with e-signatures | 21 CFR Part 11, Annex 11 |
| Access controls | Role-based permissions, segregation of duties | ISO 13485 Clause 4.2.3(c) |
| Audit trail | Immutable record of all changes with timestamp, user, reason | 21 CFR Part 11 §11.10(e) |
| Backup and recovery | Regular backups with tested restore procedures | ISO 13485 Clause 4.2.4 |
| Training records integration | Link document access to training completion | ISO 13485 Clause 6.2 |
| Obsolete document control | Automatic removal from use with archival | ISO 13485 Clause 4.2.3(e) |

### Electronic Signatures

| Signature Type | Use Case | Technical Requirement |
|---------------|----------|----------------------|
| Electronic signature | Document approval, batch release, CAPA closure | Linked to individual, date/time stamped, meaning included |
| Digital signature | High-assurance: design reviews, regulatory submissions | PKI-based, certificate authority, tamper-evident |
| Biometric signature | Optional for high-security processes | Fingerprint or similar biometric linked to identity |

### Audit Trail Requirements

| Element | Description | Example |
|---------|-------------|---------|
| Who | User identity (not shared accounts) | jane.smith@company.com |
| What | Action performed | "Approved SOP-02-001 Rev 3" |
| When | Date and time (UTC or with timezone) | 2026-03-09T14:30:00Z |
| Why | Reason for change (required for modifications) | "Updated per CAPA-2026-003 findings" |
| Previous value | Old content (for modifications) | Automatic diff/version comparison |

---

## Cross-Reference: 21 CFR Part 11 / Annex 11

### 21 CFR Part 11 Requirements for Electronic Records

| Requirement | Section | QMS Implementation |
|-------------|---------|-------------------|
| Validation | §11.10(a) | Validate eQMS software per GAMP 5 methodology |
| Audit trail | §11.10(e) | Computer-generated, timestamped, immutable audit trail |
| System access controls | §11.10(d) | Unique user IDs, passwords, role-based access |
| Authority checks | §11.10(g) | Only authorized individuals can use specific functions |
| Device checks | §11.10(h) | Verify source of data input |
| Personnel qualification | §11.10(i) | Training on system use and Part 11 requirements |
| Electronic signatures | §11.50, §11.100 | Unique to individual, not reusable, linked to records |
| Open vs. closed systems | §11.30 vs. §11.10 | Determine system type; open systems need encryption |

### Annex 11 (EU GMP) Requirements

| Requirement | Section | QMS Implementation |
|-------------|---------|-------------------|
| Risk management | §1 | Apply risk-based approach to computerized system validation |
| Personnel | §2 | Designated system owner and trained users |
| Supplier assessment | §3 | Assess eQMS vendor quality and compliance capability |
| Validation | §4-5 | IQ/OQ/PQ for eQMS, validation plan and report |
| Data | §6-9 | Data integrity, accuracy checks, data storage |
| Printouts | §8 | Ability to generate clear, legible copies of electronic records |
| Audit trail | §9 | Record of all GMP-relevant changes |
| Change and configuration management | §10-11 | Controlled change process for system modifications |
| Security | §12 | Physical and logical security controls |
| Incident management | §13 | Procedure for reporting and managing system incidents |
| Electronic signatures | §14 | Equivalent legal standing to handwritten signatures |
| Batch release | §15 | Electronic batch release with appropriate controls |
| Business continuity | §16 | Contingency procedures for system unavailability |
| Archiving | §17 | Long-term accessibility and readability of archived data |

---

## Remote Audit Considerations (Post-COVID)

### Remote Audit Methodology

| Audit Element | On-Site Approach | Remote Equivalent |
|-------------|-----------------|-------------------|
| Document review | Physical review of controlled copies | Screen-sharing of eDMS, live navigation |
| Record sampling | Pull physical records from files | Live database queries via screen-share |
| Process observation | Walk the production floor | Live video tour, camera-equipped devices |
| Personnel interviews | Face-to-face | Video conference with individual sessions |
| Equipment verification | Physical inspection | Live video with zoom capability |
| Evidence collection | Photocopies, photographs | Screenshots, screen recordings, exported PDFs |

### Remote Audit Best Practices

| Practice | Description |
|----------|-------------|
| Pre-audit documentation | Share document packages 2 weeks before audit via secure portal |
| Technology testing | Test video conferencing, screen-sharing, and secure file transfer before audit |
| Audit plan adaptation | Allow 20-30% more time for remote activities vs. on-site |
| Secure communication | Use encrypted channels for all audit communications and evidence transfer |
| Real-time evidence | Prefer live demonstrations over pre-recorded material |
| Breakout rooms | Use separate video sessions for confidential interviews |
| Audit trail of the audit | Record audit sessions (with agreement) for reference |

### Hybrid Audit Model

| Activity | Recommended Mode | Rationale |
|----------|-----------------|-----------|
| Opening/closing meetings | Remote | Efficient, schedule-friendly |
| Document and record review | Remote | Full eDMS access, efficient sampling |
| Process observation (manufacturing) | On-site | Cannot verify physical processes remotely |
| Cleanroom/controlled environment | On-site | Environmental conditions require physical presence |
| Software system review | Remote | Screen-sharing is equivalent or better |
| Management interview | Either | Remote is acceptable |
| Supplier audit (critical) | On-site | Physical verification essential |

---

## Cross-Reference: ISO 42001 for AI-Enabled Medical Devices

### ISO 42001 (AI Management System) Integration with ISO 13485

For medical device organizations developing AI-enabled products, ISO 42001:2023 provides an AI management system framework:

| ISO 42001 Clause | ISO 13485 Integration Point | Combined Requirement |
|-----------------|---------------------------|---------------------|
| 4. Context of the organization | Clause 4.1 (General requirements) | Extend QMS scope to include AI-specific processes |
| 5. Leadership | Clause 5 (Management responsibility) | AI governance within quality policy and objectives |
| 6. Planning (AI risk assessment) | Clause 7.1 (Risk management planning) | Extend ISO 14971 risk management to AI-specific risks |
| 7. Support (AI competence) | Clause 6.2 (Human resources) | Add AI/ML competency requirements to training matrix |
| 8. Operation (AI lifecycle) | Clause 7.3 (Design and development) | Integrate AI development lifecycle into design controls |
| 9. Performance evaluation | Clause 8 (Measurement, analysis) | Add AI performance metrics to quality monitoring |
| 10. Improvement | Clause 8.5 (CAPA) | Include AI-related incidents in CAPA scope |

### AI Lifecycle Integration with Design Controls

```
ISO 13485 Design Control (Cl. 7.3)     ISO 42001 AI Lifecycle
─────────────────────────────────       ─────────────────────
Design Input (7.3.3)                    AI System Requirements
    ↓                                       ↓
Design Output (7.3.4)                   Data Collection & Preparation
    ↓                                   Model Architecture & Training
    ↓                                       ↓
Design Review (7.3.5)                   AI Model Validation Review
    ↓                                       ↓
Design Verification (7.3.6)            Model Verification (accuracy, bias)
    ↓                                       ↓
Design Validation (7.3.7)             Clinical Validation (real-world performance)
    ↓                                       ↓
Design Transfer (7.3.8)               Model Deployment & Monitoring
    ↓                                       ↓
Design Changes (7.3.9)                Model Retraining & Update Control
```

---

## Supplier Qualification for Software/Cloud Providers

### Cloud Service Provider Qualification

| Qualification Criterion | Assessment Method | Minimum Requirement |
|------------------------|-------------------|---------------------|
| Information security | ISO 27001 certificate or SOC 2 Type II report | Current certification for relevant scope |
| Data residency | Contractual agreement + architecture review | Data stored in jurisdictions compliant with regulations |
| Availability SLA | Service agreement review | 99.9% uptime minimum for critical systems |
| Backup and recovery | Architecture review + test results | RPO < 4 hours, RTO < 8 hours for critical systems |
| Incident notification | Contract clause review | Notification within 24 hours of security incident |
| Audit rights | Contract clause | Right to audit or receive audit reports |
| Regulatory compliance | Vendor compliance documentation | GxP-qualified environments (if applicable) |
| Exit strategy | Data portability assessment | Documented data export capability in standard formats |

### Software Supplier Assessment

| Assessment Area | Category A (Critical) | Category B (Major) | Category C (Minor) |
|----------------|----------------------|--------------------|--------------------|
| Quality system | ISO 13485 or ISO 9001 required | ISO 9001 preferred | Documented processes |
| Development process | IEC 62304 compliance evidence | SDLC documentation | Basic version control |
| Cybersecurity | IEC 81001-5-1 compliance | Security testing evidence | Basic security practices |
| Change management | Formal change control with notification | Release notes and notification | Version tracking |
| Validation support | IQ/OQ/PQ documentation provided | Functional test documentation | User documentation |
| Incident handling | SLA-based response with root cause | Defined support process | Best-effort support |

---

## CAPA Integration with Cybersecurity Incidents

### Cybersecurity Incident as CAPA Trigger

| Incident Type | CAPA Required? | Response Actions |
|-------------|----------------|-----------------|
| Patient data breach | Yes — automatic | Contain → investigate → notify (GDPR 72h, HIPAA 60 days) → CAPA |
| Device vulnerability (exploitable) | Yes — automatic | Patch → verify → communicate → CAPA for root cause |
| Device vulnerability (not exploitable) | Evaluate | Risk assessment → mitigate if feasible → track |
| Malware on manufacturing system | Yes — automatic | Isolate → clean → verify product integrity → CAPA |
| Unauthorized access to QMS | Yes — automatic | Revoke access → assess impact → verify record integrity → CAPA |
| Supplier security incident | Evaluate | Assess impact on device/data → CAPA if product affected |

### Cybersecurity CAPA Process

```
Step 1: Incident Detection and Containment
        → Activate incident response plan
        → Contain threat and preserve evidence
        → Assess impact on product safety and quality

Step 2: Investigation (Root Cause Analysis)
        → Technical forensic analysis
        → 5 Whys + attack chain reconstruction
        → Identify QMS process failures that enabled the incident
        → Assess whether product quality was affected

Step 3: Corrective Actions
        → Technical: patch vulnerability, update security controls
        → Process: update SOPs, access controls, monitoring
        → People: security awareness training
        → Product: assess need for field safety corrective action (FSCA)

Step 4: Preventive Actions
        → Threat modeling review for similar attack vectors
        → Security control gap analysis
        → Supply chain security review (if applicable)
        → Update cybersecurity risk assessment

Step 5: Effectiveness Verification
        → Penetration testing to verify fix
        → Monitoring for recurrence (90-day window)
        → Review of updated security metrics
        → Close CAPA with evidence of effectiveness

Step 6: Regulatory Reporting (if required)
        → MDR vigilance report (if patient safety affected)
        → FDA MedWatch report (if applicable)
        → GDPR breach notification (if personal data involved)
        → NIS2 incident report (if essential entity)
```

> **Cross-references:** See `../information-security-manager-iso27001/SKILL.md` for ISO 27001 incident response procedures, `../fda-consultant-specialist/SKILL.md` for FDA QMSR alignment, and `../risk-management-specialist/SKILL.md` for cybersecurity risk integration with ISO 14971.

---

## ISO 13485 Enhanced — QMSR, Digital QMS & Cross-Framework Integration

### ISO 13485:2016 Alignment with FDA QMSR

With FDA's Quality Management System Regulation (QMSR) effective Feb 2026:

- **Direct Alignment:** FDA now recognizes ISO 13485:2016 as the quality system standard
- **Single QMS:** Organizations can maintain one QMS for both FDA and EU market access
- **Gap Analysis:** Identify differences between current QSR procedures and ISO 13485 requirements
- **Transition Plan:** Map QSR 21 CFR 820 sections to ISO 13485 clauses, update procedures
- **Cross-reference:** See `fda-consultant-specialist` for detailed FDA requirements

### Digital QMS Implementation

- **Electronic Document Control:** Validated electronic document management system (eDMS)
- **Electronic Signatures:** 21 CFR Part 11 / EU Annex 11 compliant e-signatures
- **Audit Trail:** Automated, timestamped, immutable record of all document changes
- **Cloud QMS Platforms:** Qualification requirements for SaaS QMS solutions (IQ/OQ/PQ)
- **Cross-reference:** See `quality-documentation-manager` for Part 11 compliance

### Remote Audit Considerations

- **Hybrid Audits:** Combination of on-site and remote activities (ISO 19011 guidance)
- **Technology Requirements:** Secure video conferencing, screen sharing, document access
- **Limitations:** Physical process observations may require on-site verification
- **Notified Body Acceptance:** Most NBs accept hybrid audits for surveillance and recertification

### AI-Enabled Medical Device QMS

- **ISO 42001 Integration:** For organizations developing AI-enabled medical devices
- **Data Governance:** Training data quality per ISO 42001 Annex A.7 within QMS
- **Model Lifecycle:** AI model versioning and change control within existing QMS processes
- **Cross-reference:** See `iso42001-ai-management` for AI management system requirements

### Supplier Qualification for Software/Cloud Providers

- **Cloud Service Providers:** Qualification checklist (SOC 2, ISO 27001, data residency, SLAs)
- **Open Source Software:** Risk assessment for OSS components (licensing, maintenance, vulnerabilities)
- **SaaS Tools:** Validation requirements for SaaS platforms used in QMS processes
- **SBOM Management:** Track software components across the supply chain

---

## Troubleshooting

| Problem | Likely Cause | Resolution |
|---------|-------------|------------|
| Audit checklist generator returns empty output | Clause number not recognized | Use exact clause numbers from ISO 13485:2016 (e.g., `7.3`, `4.2.3`, `8.5.2`). Run with `--interactive` to see all available clauses. |
| System audit checklist is very large | `--audit-type system` includes all clauses | For targeted audits, use `--clause` or `--process` flags to generate focused checklists. System audits intentionally cover the full standard. |
| Gap analysis matrix shows all clauses as "Major" gaps | Assessment conducted against a greenfield organization | Prioritize gaps by regulatory criticality and product safety impact. Address Clauses 4.2, 7.3, 8.2.4, 8.3, and 8.5 first as these require mandatory documented procedures. |
| QMSR transition mapping unclear | QSR sections not aligned to ISO 13485 clauses | The QMSR (effective Feb 2, 2026) incorporates ISO 13485 by reference. Map QSR 21 CFR 820 sub-parts to ISO 13485 clauses using the QMSR Gap Analysis Checklist in this skill. |
| Supplier qualification score borderline (60-80) | Supplier meets some criteria but has gaps | Issue conditional approval with documented improvement requirements and a defined reassessment date. Increase monitoring frequency until the supplier exceeds the 80-point threshold. |
| Process validation protocol incomplete | IQ/OQ/PQ phases not clearly separated | Each qualification phase must have distinct objectives, acceptance criteria, and documented results. Use the Validation Documentation Requirements table as a template for protocol structure. |
| Design control audit questions not applicable | Organization does not perform design activities | ISO 13485 permits exclusion of Clause 7.3 if the organization does not design products. Document the exclusion justification in the Quality Manual per Clause 4.2.2. |

---

## Success Criteria

- QMS gap analysis completed against all ISO 13485:2016 clauses with documented current state, gap severity, priority, and remediation actions
- All 6 mandatory documented procedures established, trained, and effective (document control, record control, internal audit, NC product, corrective action, preventive action)
- Quality Manual approved with justified clause exclusions, process interactions documented, and scope clearly defined
- QMSR transition completed: all QSR SOPs mapped to ISO 13485 clauses, FDA-retained requirements addressed, internal audit checklist updated for combined ISO 13485 + FDA requirements
- Supplier qualification program operational with category-based assessment (A/B/C), documented scoring, and approved supplier list maintained
- Process validation completed for all special processes (IQ/OQ/PQ documented with approved protocols and reports)
- Certification audit passed with zero Major nonconformities and a plan to address any Minor findings within 60 days

---

## Scope & Limitations

**In Scope:**
- ISO 13485:2016 QMS implementation from gap analysis through certification
- Document control system design (numbering, approval, change control, review schedules)
- Internal audit program planning and execution per Clause 8.2.4
- Process validation methodology (IQ/OQ/PQ) per Clause 7.5.6
- Supplier qualification and monitoring per Clause 7.4
- FDA QMSR transition planning and gap analysis
- Digital QMS implementation (eDMS, Part 11, Annex 11 requirements)
- Remote and hybrid audit methodology
- AI-enabled medical device QMS considerations (ISO 42001 integration)

**Out of Scope:**
- Clinical evaluation or clinical investigation management (use regulatory-affairs-head for clinical evidence strategy)
- Product-specific design control execution (the skill provides the design control framework, not product-specific design inputs/outputs)
- Sterilization validation protocol development (requires product-specific expertise per ISO 11135/11137/17665)
- Regulatory submission preparation (use fda-consultant-specialist or mdr-745-specialist)
- Post-market surveillance program execution (use risk-management-specialist for post-production risk monitoring)
- IT infrastructure or cybersecurity implementation (use infrastructure-compliance-auditor for technical security)

---

## Integration Points

| Skill | Integration |
|-------|------------|
| [quality-manager-qmr](../quality-manager-qmr/) | QMR oversees QMS effectiveness; management review inputs include QMS process performance metrics |
| [capa-officer](../capa-officer/) | CAPA system (Clause 8.5) is a core QMS process; CAPA effectiveness feeds into management review |
| [qms-audit-expert](../qms-audit-expert/) | Internal audit program (Clause 8.2.4) evaluates QMS processes; audit findings drive CAPA and improvement |
| [quality-documentation-manager](../quality-documentation-manager/) | Document and record control (Clause 4.2) provides the documentation foundation for the entire QMS |
| [risk-management-specialist](../risk-management-specialist/) | ISO 14971 risk management integrates with design control (Clause 7.3) and product realization planning (Clause 7.1) |
| [fda-consultant-specialist](../fda-consultant-specialist/) | QMSR alignment requires mapping FDA-specific requirements (MDR reporting, UDI, Part 11) beyond ISO 13485 |
| [regulatory-affairs-head](../regulatory-affairs-head/) | Regulatory strategy informs QMS scope, market-specific requirements, and certification timelines |

---

## Tool Reference

### qms_audit_checklist.py

Generates ISO 13485:2016 audit checklists by clause, process, or full system audit.

| Flag | Required | Description |
|------|----------|-------------|
| `--clause` | No | ISO 13485 clause number to generate a clause-specific checklist (e.g., `7.3`, `4.2.3`, `8.5.2`) |
| `--process` | No | Process name for a process-based checklist (e.g., `design-control`, `purchasing`, `capa`) |
| `--audit-type` | No | Audit type: `system` for a full-system checklist covering all clauses |
| `--output` | No | Output format: `json` for structured output, omit for human-readable text |
| `--interactive` | No | Launch interactive mode for guided clause/process selection |

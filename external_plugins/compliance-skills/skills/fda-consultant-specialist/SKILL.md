---
name: fda-consultant-specialist
description: >
  FDA regulatory consultant for medical device companies. Provides 510(k)/PMA/De
  Novo pathway guidance, QSR (21 CFR 820) compliance, HIPAA assessments, and
  device cybersecurity. Use when user mentions FDA submission, 510(k), PMA, De
  Novo, QSR, premarket, predicate device, substantial equivalence, HIPAA medical
  device, or FDA cybersecurity.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: fda-compliance
  updated: 2026-03-31
  tags: [fda, 510k, pma, qsr, hipaa, cybersecurity]
---
# FDA Consultant Specialist

FDA regulatory consulting for medical device manufacturers covering submission pathways, Quality System Regulation (QSR), HIPAA compliance, and device cybersecurity requirements.

## Table of Contents

- [FDA Pathway Selection](#fda-pathway-selection)
- [510(k) Submission Process](#510k-submission-process)
- [QSR Compliance](#qsr-compliance)
- [HIPAA for Medical Devices](#hipaa-for-medical-devices)
- [Device Cybersecurity](#device-cybersecurity)
- [Resources](#resources)

---

## FDA Pathway Selection

Determine the appropriate FDA regulatory pathway based on device classification and predicate availability.

### Decision Framework

```
Predicate device exists?
├── YES → Substantially equivalent?
│   ├── YES → 510(k) Pathway
│   │   ├── No design changes → Abbreviated 510(k)
│   │   ├── Manufacturing only → Special 510(k)
│   │   └── Design/performance → Traditional 510(k)
│   └── NO → PMA or De Novo
└── NO → Novel device?
    ├── Low-to-moderate risk → De Novo
    └── High risk (Class III) → PMA
```

### Pathway Comparison

| Pathway | When to Use | Timeline | Cost |
|---------|-------------|----------|------|
| 510(k) Traditional | Predicate exists, design changes | 90 days | $21,760 |
| 510(k) Special | Manufacturing changes only | 30 days | $21,760 |
| 510(k) Abbreviated | Guidance/standard conformance | 30 days | $21,760 |
| De Novo | Novel, low-moderate risk | 150 days | $134,676 |
| PMA | Class III, no predicate | 180+ days | $425,000+ |

### Pre-Submission Strategy

1. Identify product code and classification
2. Search 510(k) database for predicates
3. Assess substantial equivalence feasibility
4. Prepare Q-Sub questions for FDA
5. Schedule Pre-Sub meeting if needed

**Reference:** See [fda_submission_guide.md](references/fda_submission_guide.md) for pathway decision matrices and submission requirements.

---

## 510(k) Submission Process

### Workflow

```
Phase 1: Planning
├── Step 1: Identify predicate device(s)
├── Step 2: Compare intended use and technology
├── Step 3: Determine testing requirements
└── Checkpoint: SE argument feasible?

Phase 2: Preparation
├── Step 4: Complete performance testing
├── Step 5: Prepare device description
├── Step 6: Document SE comparison
├── Step 7: Finalize labeling
└── Checkpoint: All required sections complete?

Phase 3: Submission
├── Step 8: Assemble submission package
├── Step 9: Submit via eSTAR
├── Step 10: Track acknowledgment
└── Checkpoint: Submission accepted?

Phase 4: Review
├── Step 11: Monitor review status
├── Step 12: Respond to AI requests
├── Step 13: Receive decision
└── Verification: SE letter received?
```

### Required Sections (21 CFR 807.87)

| Section | Content |
|---------|---------|
| Cover Letter | Submission type, device ID, contact info |
| Form 3514 | CDRH premarket review cover sheet |
| Device Description | Physical description, principles of operation |
| Indications for Use | Form 3881, patient population, use environment |
| SE Comparison | Side-by-side comparison with predicate |
| Performance Testing | Bench, biocompatibility, electrical safety |
| Software Documentation | Level of concern, hazard analysis (IEC 62304) |
| Labeling | IFU, package labels, warnings |
| 510(k) Summary | Public summary of submission |

### Common RTA Issues

| Issue | Prevention |
|-------|------------|
| Missing user fee | Verify payment before submission |
| Incomplete Form 3514 | Review all fields, ensure signature |
| No predicate identified | Confirm K-number in FDA database |
| Inadequate SE comparison | Address all technological characteristics |

---

## QSR Compliance

Quality System Regulation (21 CFR Part 820) requirements for medical device manufacturers.

### Key Subsystems

| Section | Title | Focus |
|---------|-------|-------|
| 820.20 | Management Responsibility | Quality policy, org structure, management review |
| 820.30 | Design Controls | Input, output, review, verification, validation |
| 820.40 | Document Controls | Approval, distribution, change control |
| 820.50 | Purchasing Controls | Supplier qualification, purchasing data |
| 820.70 | Production Controls | Process validation, environmental controls |
| 820.100 | CAPA | Root cause analysis, corrective actions |
| 820.181 | Device Master Record | Specifications, procedures, acceptance criteria |

### Design Controls Workflow (820.30)

```
Step 1: Design Input
└── Capture user needs, intended use, regulatory requirements
    Verification: Inputs reviewed and approved?

Step 2: Design Output
└── Create specifications, drawings, software architecture
    Verification: Outputs traceable to inputs?

Step 3: Design Review
└── Conduct reviews at each phase milestone
    Verification: Review records with signatures?

Step 4: Design Verification
└── Perform testing against specifications
    Verification: All tests pass acceptance criteria?

Step 5: Design Validation
└── Confirm device meets user needs in actual use conditions
    Verification: Validation report approved?

Step 6: Design Transfer
└── Release to production with DMR complete
    Verification: Transfer checklist complete?
```

### CAPA Process (820.100)

1. **Identify**: Document nonconformity or potential problem
2. **Investigate**: Perform root cause analysis (5 Whys, Fishbone)
3. **Plan**: Define corrective/preventive actions
4. **Implement**: Execute actions, update documentation
5. **Verify**: Confirm implementation complete
6. **Effectiveness**: Monitor for recurrence (30-90 days)
7. **Close**: Management approval and closure

**Reference:** See [qsr_compliance_requirements.md](references/qsr_compliance_requirements.md) for detailed QSR implementation guidance.

---

## HIPAA for Medical Devices

HIPAA requirements for devices that create, store, transmit, or access Protected Health Information (PHI).

### Applicability

| Device Type | HIPAA Applies |
|-------------|---------------|
| Standalone diagnostic (no data transmission) | No |
| Connected device transmitting patient data | Yes |
| Device with EHR integration | Yes |
| SaMD storing patient information | Yes |
| Wellness app (no diagnosis) | Only if stores PHI |

### Required Safeguards

```
Administrative (§164.308)
├── Security officer designation
├── Risk analysis and management
├── Workforce training
├── Incident response procedures
└── Business associate agreements

Physical (§164.310)
├── Facility access controls
├── Workstation security
└── Device disposal procedures

Technical (§164.312)
├── Access control (unique IDs, auto-logoff)
├── Audit controls (logging)
├── Integrity controls (checksums, hashes)
├── Authentication (MFA recommended)
└── Transmission security (TLS 1.2+)
```

### Risk Assessment Steps

1. Inventory all systems handling ePHI
2. Document data flows (collection, storage, transmission)
3. Identify threats and vulnerabilities
4. Assess likelihood and impact
5. Determine risk levels
6. Implement controls
7. Document residual risk

**Reference:** See [hipaa_compliance_framework.md](references/hipaa_compliance_framework.md) for implementation checklists and BAA templates.

---

## Device Cybersecurity

FDA cybersecurity requirements for connected medical devices.

### Premarket Requirements

| Element | Description |
|---------|-------------|
| Threat Model | STRIDE analysis, attack trees, trust boundaries |
| Security Controls | Authentication, encryption, access control |
| SBOM | Software Bill of Materials (CycloneDX or SPDX) |
| Security Testing | Penetration testing, vulnerability scanning |
| Vulnerability Plan | Disclosure process, patch management |

### Device Tier Classification

**Tier 1 (Higher Risk):**
- Connects to network/internet
- Cybersecurity incident could cause patient harm

**Tier 2 (Standard Risk):**
- All other connected devices

### Postmarket Obligations

1. Monitor NVD and ICS-CERT for vulnerabilities
2. Assess applicability to device components
3. Develop and test patches
4. Communicate with customers
5. Report to FDA per guidance

### Coordinated Vulnerability Disclosure

```
Researcher Report
    ↓
Acknowledgment (48 hours)
    ↓
Initial Assessment (5 days)
    ↓
Fix Development
    ↓
Coordinated Public Disclosure
```

**Reference:** See [device_cybersecurity_guidance.md](references/device_cybersecurity_guidance.md) for SBOM format examples and threat modeling templates.

---

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `fda_submission_tracker.py` | Track 510(k)/PMA/De Novo submission milestones and timelines |
| `qsr_compliance_checker.py` | Assess 21 CFR 820 compliance against project documentation |
| `hipaa_risk_assessment.py` | Evaluate HIPAA safeguards in medical device software |

### references/

| File | Content |
|------|---------|
| `fda_submission_guide.md` | 510(k), De Novo, PMA submission requirements and checklists |
| `qsr_compliance_requirements.md` | 21 CFR 820 implementation guide with templates |
| `hipaa_compliance_framework.md` | HIPAA Security Rule safeguards and BAA requirements |
| `device_cybersecurity_guidance.md` | FDA cybersecurity requirements, SBOM, threat modeling |
| `fda_capa_requirements.md` | CAPA process, root cause analysis, effectiveness verification |

### Usage Examples

```bash
# Track FDA submission status
python scripts/fda_submission_tracker.py /path/to/project --type 510k

# Assess QSR compliance
python scripts/qsr_compliance_checker.py /path/to/project --section 820.30

# Run HIPAA risk assessment
python scripts/hipaa_risk_assessment.py /path/to/project --category technical
```

---

## FDA QMSR — Quality Management System Regulation

### Transition from QSR (21 CFR 820) to QMSR

The FDA finalized the Quality Management System Regulation (QMSR) in January 2024, replacing the legacy Quality System Regulation (QSR) with ISO 13485:2016 alignment. The rule became effective **February 2, 2026**.

| Aspect | Legacy QSR (21 CFR 820) | QMSR (Effective Feb 2026) |
|--------|------------------------|---------------------------|
| Framework | FDA-specific prescriptive requirements | Incorporates ISO 13485:2016 by reference |
| Design controls | 820.30 (FDA-specific) | ISO 13485 Clause 7.3 |
| CAPA | 820.100 | ISO 13485 Clause 8.5 |
| Document control | 820.40 | ISO 13485 Clause 4.2 |
| Management responsibility | 820.20 | ISO 13485 Clause 5 |
| Purchasing controls | 820.50 | ISO 13485 Clause 7.4 |

**Key differences under QMSR:**
- ISO 13485:2016 is incorporated by reference as the primary QMS standard
- FDA retains certain device-specific requirements not covered by ISO 13485 (e.g., complaint handling per 21 CFR 820.198)
- Organizations already ISO 13485 certified have a significant head start
- No separate FDA registration for QMS — single system serves both ISO and FDA

### QMSR Transition Checklist

- [ ] Gap analysis: ISO 13485:2016 vs. current QSR compliance
- [ ] Update Quality Manual to reference ISO 13485 clause structure
- [ ] Map existing SOPs to ISO 13485 clauses
- [ ] Address FDA-specific retained requirements (complaint handling, MDR reporting)
- [ ] Train staff on ISO 13485 terminology and structure
- [ ] Update supplier agreements to reference new regulatory framework
- [ ] Conduct internal audit against QMSR requirements
- [ ] Update design history files to ISO 13485 Clause 7.3 format

---

## AI/ML-Based Software as Medical Device (SaMD)

### FDA AI/ML SaMD Framework

| Category | Description | FDA Pathway |
|----------|-------------|-------------|
| Locked algorithm | Algorithm does not change after deployment | Standard 510(k)/De Novo/PMA |
| Adaptive algorithm (PCCP) | Algorithm learns and changes with use | Predetermined Change Control Plan |
| Continuously learning | Real-time adaptation from new data | Case-by-case; PCCP required |

### AI/ML SaMD Submission Requirements

```
AI/ML SaMD Submission Package
├── Algorithm description and architecture
├── Training data characterization
│   ├── Data sources and collection methods
│   ├── Demographics and representativeness
│   ├── Data quality and labeling methodology
│   └── Training/validation/test split rationale
├── Performance evaluation
│   ├── Pre-specified performance goals
│   ├── Standalone performance metrics (sensitivity, specificity, AUC)
│   ├── Subgroup analysis (age, sex, race, site)
│   └── Real-world performance data (if available)
├── Reference standard justification
├── Predetermined Change Control Plan (if adaptive)
├── Human factors / user interface
├── Cybersecurity documentation
└── Software documentation per IEC 62304
```

### Good Machine Learning Practice (GMLP) Principles

1. Multi-disciplinary expertise throughout product lifecycle
2. Good software engineering and security practices
3. Representative training and test datasets
4. Independent test datasets separate from training
5. Reference datasets based on best available methods
6. Model design tailored to available data and intended use
7. Focus on performance of human-AI team
8. Clinical study testing demonstrates real-world performance
9. Users provided clear, essential information
10. Deployed models monitored for performance with retraining managed

---

## Predetermined Change Control Plan (PCCP) for AI/ML Devices

### PCCP Structure

| Section | Content | Evidence |
|---------|---------|----------|
| Description of modifications | Types of changes the algorithm will make | Change specification document |
| Modification protocol | How changes will be developed and tested | Validation protocol |
| Impact assessment | How each change type affects safety and effectiveness | Risk analysis per change type |
| Performance monitoring | Ongoing real-world performance tracking | Monitoring plan with metrics |
| Update verification | How each update will be verified before deployment | Verification and validation plan |
| Transparency | How users will be notified of changes | Communication plan |

### PCCP Change Categories

| Category | Example | Verification Level |
|----------|---------|-------------------|
| Performance improvement | Retrained model with additional data | Automated testing + clinical validation |
| Input adaptation | New imaging modality support | Full V&V cycle |
| Output modification | New risk categories or confidence levels | Clinical study |
| Architecture change | Model architecture update | New submission (510(k)/PMA supplement) |

---

## Enhanced Cybersecurity Requirements (PATCH Act)

The PATCH Act (effective March 2023, codified in FD&C Act §524B) requires:

| Requirement | Details | Evidence |
|-------------|---------|----------|
| Cybersecurity plan | Submit plan to monitor, identify, and address vulnerabilities | Premarket submission section |
| SBOM | Software Bill of Materials including commercial, open-source, off-the-shelf components | CycloneDX or SPDX format |
| Patch/update capability | Design device to be patchable throughout lifecycle | Architecture documentation |
| Coordinated vulnerability disclosure | Establish and maintain CVD process | Published security policy |
| Postmarket updates | Provide patches and updates in a reasonably justified cycle | Patch management plan |

### Cybersecurity Documentation for Premarket Submissions

```
Cybersecurity Premarket Package
├── Security risk assessment
│   ├── Threat model (STRIDE or equivalent)
│   ├── Security risk analysis per AAMI TIR57
│   └── Attack surface analysis
├── Security architecture
│   ├── Security controls implementation
│   ├── Cryptographic architecture
│   └── Network architecture and trust boundaries
├── SBOM (Software Bill of Materials)
│   ├── All software components (commercial, open-source, custom)
│   ├── Version information
│   └── Known vulnerability status
├── Security testing
│   ├── Static analysis (SAST)
│   ├── Dynamic analysis (DAST)
│   ├── Penetration testing report
│   ├── Fuzz testing results
│   └── Vulnerability scanning results
├── Lifecycle security plan
│   ├── Patch management process
│   ├── End-of-life/end-of-support plan
│   └── Customer communication plan
└── Coordinated vulnerability disclosure policy
```

---

## Cross-Reference: EU AI Act for AI Medical Devices

AI-enabled medical devices must comply with both FDA requirements and EU AI Act when marketed in both jurisdictions:

| Aspect | FDA Approach | EU AI Act Approach | Harmonization Strategy |
|--------|-------------|-------------------|----------------------|
| Risk classification | SaMD risk framework (IMDRF) | Annex III high-risk (medical devices) | Map to both frameworks; use higher standard |
| Transparency | Labeling requirements | Art. 13 transparency obligations | Unified transparency documentation |
| Data governance | GMLP principles | Art. 10 data and data governance | Comprehensive data quality program |
| Human oversight | Human factors per IEC 62366 | Art. 14 human oversight | Integrated human factors + oversight design |
| Post-market | Real-world performance monitoring | Art. 72 post-market monitoring | Single monitoring system serving both |
| Technical documentation | FDA premarket submission | Annex IV technical documentation | Unified technical file |

> **See also:** `../mdr-745-specialist/SKILL.md` for EU MDR classification of AI/ML medical devices and `../risk-management-specialist/SKILL.md` for ISO 14971 risk management for AI devices.

---

## Updated 510(k) Electronic Submission Requirements (eSTAR)

### eSTAR Mandate

As of October 1, 2023, FDA requires all 510(k) submissions to use the eSTAR template format. Paper submissions are no longer accepted.

| eSTAR Requirement | Details |
|-------------------|---------|
| Template | FDA eSTAR template (fillable PDF) |
| Format | Structured data fields + attachments |
| Attachments | PDF/A format, bookmarked, OCR-searchable |
| File naming | FDA naming convention required |
| Submission portal | CDRH Customer Collaboration Portal or FDA ESG |
| Maximum file size | 100MB per individual file; no total limit |

### eSTAR Section Mapping

| eSTAR Section | Content | Common Deficiencies |
|---------------|---------|---------------------|
| Administrative | Cover letter, user fee, truthful/accurate statement | Missing signatures, incorrect fee |
| Device Description | Complete device description with images/diagrams | Insufficient detail, missing accessories |
| Substantial Equivalence | Predicate comparison table | Incomplete comparison criteria |
| Performance Testing | All test reports with summaries | Missing acceptance criteria, incomplete protocols |
| Software | Level of concern, hazard analysis, architecture | Outdated IEC 62304 compliance |
| Biocompatibility | ISO 10993 evaluation or testing | Missing risk assessment, incomplete contact analysis |
| Sterility | Sterilization validation summary | Missing reprocessing instructions (reusable devices) |
| Labeling | Device labels, IFU, patient materials | Non-compliant with 21 CFR 801 |
| EMC/Electrical Safety | IEC 60601-1 compliance | Missing particular standards |
| Clinical | Clinical data summary (if applicable) | Insufficient clinical evidence for new indications |

---

## Cross-Framework: FDA ↔ MDR ↔ ISO 13485 Mapping

| Process Area | FDA (QMSR/QSR) | EU MDR 2017/745 | ISO 13485:2016 |
|-------------|-----------------|-----------------|----------------|
| Quality management system | 21 CFR 820 / QMSR | Annex IX, Annex XI | Clause 4 |
| Management responsibility | 820.20 / ISO 13485 Cl. 5 | Annex IX §2.2 | Clause 5 |
| Design controls | 820.30 / ISO 13485 Cl. 7.3 | Annex II §6.1, GSPR | Clause 7.3 |
| Document control | 820.40 / ISO 13485 Cl. 4.2 | Annex IX §2.3 | Clause 4.2 |
| Purchasing | 820.50 / ISO 13485 Cl. 7.4 | Annex IX §2.4 | Clause 7.4 |
| Production | 820.70 / ISO 13485 Cl. 7.5 | Annex IX §2.5 | Clause 7.5 |
| CAPA | 820.100 / ISO 13485 Cl. 8.5 | Art. 83 (PMS), Art. 89 (FSCA) | Clause 8.5 |
| Risk management | 820.30(g) / ISO 14971 | Annex I (GSPR), ISO 14971 | Clause 7.1 |
| Clinical evidence | 820.30(f) / clinical data | Annex XIV (clinical evaluation) | N/A (separate) |
| Post-market | 820.198 / MDR/MedWatch | Art. 83-86 (PMS), Art. 87-92 (vigilance) | Clause 8.2.1-8.2.3 |
| Labeling | 21 CFR 801 | Art. 10-13, Annex I Ch. III | N/A (separate) |
| UDI | 21 CFR 830 (FDA UDI) | Art. 27-29 (UDI-DI/PI) | N/A (separate) |
| Cybersecurity | §524B FD&C (PATCH Act) | MDCG 2019-16 | N/A (separate) |
| AI/ML devices | AI/ML SaMD framework + PCCP | EU AI Act + MDR | ISO 13485 + ISO 42001 |

> **Cross-references:** See `../quality-manager-qms-iso13485/SKILL.md` for ISO 13485 implementation aligned with QMSR, and `../mdr-745-specialist/SKILL.md` for EU MDR technical documentation requirements.

---

## FDA Regulatory Updates & Cross-Framework Integration

### FDA QMSR — Quality Management System Regulation

The FDA is aligning 21 CFR Part 820 with ISO 13485:2016 through the Quality Management System Regulation (QMSR), effective February 2, 2026:

- **Key Change:** QSR (21 CFR 820) replaced by ISO 13485 as the recognized quality system standard
- **Impact:** Manufacturers must comply with ISO 13485:2016 instead of QSR-specific requirements
- **Design Controls:** ISO 13485 Clause 7.3 replaces 820.30
- **CAPA:** ISO 13485 Clause 8.5 replaces 820.90/820.100
- **Transition:** FDA accepting both QSR and QMSR during transition period

### AI/ML-Based Software as Medical Device (SaMD)

- **Predetermined Change Control Plan (PCCP):** Required for AI/ML devices that learn and adapt
- **Good Machine Learning Practice (GMLP):** FDA's 10 guiding principles for AI/ML in medical devices
- **Transparency:** Clear labeling of AI/ML-based functionality and limitations
- **Real-World Performance:** Post-market monitoring of AI model performance drift
- **Cross-reference:** See `eu-ai-act-specialist` for EU AI Act requirements for AI medical devices

### Enhanced Cybersecurity Requirements (PATCH Act)

- **Premarket Submissions:** Cybersecurity documentation required for all connected devices
- **Software Bill of Materials (SBOM):** Mandatory for all premarket submissions
- **Coordinated Vulnerability Disclosure:** Required policy for all connected device manufacturers
- **Postmarket Patches:** Cybersecurity patches exempt from 510(k) requirements
- **Cross-reference:** See `infrastructure-compliance-auditor` for technical cybersecurity checks

### Cross-Framework Mapping (FDA ↔ MDR ↔ ISO 13485)

| Area | FDA (QSR/QMSR) | EU MDR 2017/745 | ISO 13485:2016 |
|------|----------------|-----------------|----------------|
| Design Controls | 820.30 / QMSR | Annex II | Clause 7.3 |
| Risk Management | 820.30(g) | Annex I GSPR | ISO 14971 |
| Clinical Evidence | 820.30(f) | Annex XIV | Clause 7.3.7 |
| CAPA | 820.90/100 | Art. 83, 89 | Clause 8.5 |
| Post-Market | 822, MDR | Chapter VII | Clause 8.2.1 |
| Cybersecurity | FDA Guidance | MDCG 2019-16 | IEC 62443 |
| AI/ML | PCCP Framework | EU AI Act | ISO 42001 |

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| 510(k) submission returned as RTA (Refuse to Accept) | Missing user fee, incomplete Form 3514, no predicate identified, or inadequate SE comparison | Review the RTA checklist per FDA guidance; verify payment, complete all eSTAR fields, confirm K-number in FDA database, and address all technological characteristics in SE comparison |
| QSR compliance checker shows gaps in design controls (820.30) | Design History File incomplete or not aligned with ISO 13485 Clause 7.3 under QMSR | Map existing DHF to ISO 13485 Clause 7.3 structure; ensure design inputs, outputs, reviews, verification, and validation are documented with traceability |
| HIPAA risk assessment returns low score for technical safeguards | Missing encryption at rest/transit, no MFA implementation, or audit logging not enabled | Implement AES-256 encryption at rest, TLS 1.2+ in transit, MFA for all users with ePHI access, and comprehensive audit logging; run `hipaa_risk_assessment.py` with `--category technical` to validate |
| FDA AI request (Additional Information) received during 510(k) review | Performance testing insufficient, SE argument incomplete, or software documentation gaps | Respond within 180 days; address each question specifically; supplement with additional test data, clinical evidence, or software documentation per IEC 62304 |
| QMSR transition gap analysis reveals significant differences | Organization structured QMS around legacy 21 CFR 820 rather than ISO 13485 | Conduct systematic gap analysis mapping 820 subsections to ISO 13485 clauses; prioritize complaint handling (retained FDA requirement), risk-based evidence across all processes, and updated Quality Manual |
| Cybersecurity documentation rejected in premarket submission | SBOM incomplete, threat model missing, or coordinated vulnerability disclosure policy not published | Generate comprehensive SBOM in CycloneDX or SPDX format; complete STRIDE threat model per AAMI TIR57; publish CVD policy; document patch management lifecycle plan |
| AI/ML SaMD submission lacks Predetermined Change Control Plan | Adaptive algorithm deployed without PCCP framework | Develop PCCP covering modification types, validation protocol, impact assessment, performance monitoring, and user notification plan; include all four change categories with appropriate verification levels |

---

## Success Criteria

- **510(k) submission accepted on first attempt** -- zero RTA deficiencies, with all eSTAR sections complete, user fee verified, predicate identified, and SE comparison addressing all technological characteristics
- **QSR/QMSR compliance score above 85%** -- as measured by `qsr_compliance_checker.py`, with all critical subsections (design controls, CAPA, document control) showing evidence of implementation
- **HIPAA technical safeguards fully implemented** -- AES-256 encryption at rest, TLS 1.2+ in transit, MFA enforced, audit controls active, and automatic logoff configured for all systems handling ePHI
- **FDA submission timeline targets met** -- 510(k) traditional within 90 days, De Novo within 150 days, PMA within 180 days, tracked via `fda_submission_tracker.py` milestones
- **QMSR transition completed** -- Quality Manual references ISO 13485 clause structure, all SOPs mapped, FDA-specific retained requirements addressed, and internal audit conducted against QMSR requirements
- **Cybersecurity documentation complete for all connected devices** -- SBOM, threat model, security testing reports, vulnerability disclosure policy, and patch management plan included in premarket submissions

---

## Scope & Limitations

**In Scope:**
- FDA regulatory pathway selection (510(k), De Novo, PMA) with decision framework and comparison
- 510(k) submission process including eSTAR requirements, SE comparison, and RTA prevention
- Quality System Regulation (21 CFR 820) and QMSR (ISO 13485:2016 alignment) compliance assessment
- HIPAA Security Rule safeguard evaluation for medical device software
- Device cybersecurity requirements including SBOM, threat modeling, and PATCH Act compliance
- AI/ML SaMD framework including PCCP, GMLP principles, and training data characterization
- Cross-framework mapping between FDA, EU MDR, and ISO 13485

**Out of Scope:**
- Preparation or writing of actual FDA submission documents -- this skill provides frameworks and gap analysis, not document authoring
- Clinical trial design, execution, or statistical analysis for PMA clinical data
- FDA establishment registration, device listing, or UDI system implementation
- Post-market surveillance reporting (MDR, MedWatch) beyond process guidance
- De novo classification request scientific review preparation
- Direct interaction with FDA reviewers or Pre-Submission (Q-Sub) meeting facilitation

**Important Notes:**
- The QMSR became effective February 2, 2026 -- all manufacturers must now comply with ISO 13485:2016 as incorporated by reference, with FDA-specific retained requirements
- The Quality System Inspection Technique (QSIT) has been withdrawn and replaced with updated inspection procedures under Compliance Program 7382.850
- Risk-based thinking is now expected across all QMS processes under QMSR, not just design controls

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `quality-manager-qms-iso13485` | ISO 13485 QMS implementation aligned with QMSR; process management and supplier qualification | When implementing QMS satisfying both ISO 13485 certification and FDA QMSR requirements |
| `mdr-745-specialist` | Cross-framework mapping for dual US/EU market submissions; technical documentation alignment | When medical device requires both FDA clearance/approval and EU MDR CE marking |
| `capa-officer` | CAPA process management per ISO 13485 Clause 8.5 (replacing legacy 820.100 under QMSR) | When managing corrective and preventive actions within the FDA quality system |
| `risk-management-specialist` | ISO 14971 risk management integrated with design controls and cybersecurity risk assessment | When conducting risk analysis for premarket submissions per 820.30(g) and AAMI TIR57 |
| `eu-ai-act-specialist` | Cross-jurisdictional AI/ML compliance for devices marketed in both US and EU | When AI-enabled medical device requires both FDA PCCP framework and EU AI Act conformity assessment |
| `infrastructure-compliance-auditor` | Technical cybersecurity validation for connected device security controls | When documenting cybersecurity architecture and SBOM for premarket submissions |

---

## Tool Reference

### fda_submission_tracker.py

Tracks FDA submission milestones and calculates regulatory timelines for 510(k), De Novo, and PMA pathways.

| Flag | Required | Description |
|------|----------|-------------|
| `<project_dir>` | Yes | Path to project directory containing submission documents |
| `--type <pathway>` | No | Submission type: `510k` (default), `de_novo`, `pma`, `pma_supplement` |
| `--json` | No | Output results in JSON format |

**Output:** Milestone tracking with completion status, timeline calculations against FDA review goals, phase progress (planning, preparation, submission, review, decision), and overdue milestone alerts.

### qsr_compliance_checker.py

Assesses compliance with 21 CFR Part 820 / QMSR by analyzing project documentation for evidence of implementation.

| Flag | Required | Description |
|------|----------|-------------|
| `<project_dir>` | Yes | Path to project directory containing QMS documentation |
| `--section <section>` | No | Check specific QSR section (e.g., `820.30` for design controls, `820.100` for CAPA) |
| `--json` | No | Output results in JSON format |

**Output:** Per-section compliance status, evidence found (document patterns and keyword matches), compliance percentage, gap identification with required evidence descriptions.

### hipaa_risk_assessment.py

Evaluates HIPAA Security Rule safeguards for medical device software and connected devices.

| Flag | Required | Description |
|------|----------|-------------|
| `<project_dir>` | Yes | Path to project directory for assessment |
| `--category <cat>` | No | Assess specific category: `administrative`, `physical`, `technical`, or all (default) |
| `--json` | No | Output results in JSON format |

**Output:** Per-safeguard compliance status across administrative (Section 164.308), physical (Section 164.310), and technical (Section 164.312) categories, with weighted scoring, evidence detection, and remediation recommendations.

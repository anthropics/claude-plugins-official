---
name: mdr-745-specialist
description: >
  EU MDR 2017/745 compliance specialist for medical device classification,
  technical documentation, clinical evidence, and post-market surveillance.
  Covers Annex VIII classification rules, Annex II/III technical files, Annex
  XIV clinical evaluation, and EUDAMED integration.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: medical-device-regulation
  updated: 2026-03-31
  tags: [eu-mdr, medical-device, gspr, eudamed, udi]
---
# MDR 2017/745 Specialist

EU MDR compliance patterns for medical device classification, technical documentation, and clinical evidence.

---

## Table of Contents

- [Device Classification Workflow](#device-classification-workflow)
- [Technical Documentation](#technical-documentation)
- [Clinical Evidence](#clinical-evidence)
- [Post-Market Surveillance](#post-market-surveillance)
- [EUDAMED and UDI](#eudamed-and-udi)
- [Reference Documentation](#reference-documentation)
- [Tools](#tools)

---

## Device Classification Workflow

Classify device under MDR Annex VIII:

1. Identify device duration (transient, short-term, long-term)
2. Determine invasiveness level (non-invasive, body orifice, surgical)
3. Assess body system contact (CNS, cardiac, other)
4. Check if active device (energy dependent)
5. Apply classification rules 1-22
6. For software, apply MDCG 2019-11 algorithm
7. Document classification rationale
8. **Validation:** Classification confirmed with Notified Body

### Classification Matrix

| Factor | Class I | Class IIa | Class IIb | Class III |
|--------|---------|-----------|-----------|-----------|
| Duration | Any | Short-term | Long-term | Long-term |
| Invasiveness | Non-invasive | Body orifice | Surgical | Implantable |
| System | Any | Non-critical | Critical organs | CNS/cardiac |
| Risk | Lowest | Low-medium | Medium-high | Highest |

### Software Classification (MDCG 2019-11)

| Information Use | Condition Severity | Class |
|-----------------|-------------------|-------|
| Informs decision | Non-serious | IIa |
| Informs decision | Serious | IIb |
| Drives/treats | Critical | III |

### Classification Examples

**Example 1: Absorbable Surgical Suture**
- Rule 8 (implantable, long-term)
- Duration: > 30 days (absorbed)
- Contact: General tissue
- Classification: **Class IIb**

**Example 2: AI Diagnostic Software**
- Rule 11 + MDCG 2019-11
- Function: Diagnoses serious condition
- Classification: **Class IIb**

**Example 3: Cardiac Pacemaker**
- Rule 8 (implantable)
- Contact: Central circulatory system
- Classification: **Class III**

---

## Technical Documentation

Prepare technical file per Annex II and III:

1. Create device description (variants, accessories, intended purpose)
2. Develop labeling (Article 13 requirements, IFU)
3. Document design and manufacturing process
4. Complete GSPR compliance matrix
5. Prepare benefit-risk analysis
6. Compile verification and validation evidence
7. Integrate risk management file (ISO 14971)
8. **Validation:** Technical file reviewed for completeness

### Technical File Structure

```
ANNEX II TECHNICAL DOCUMENTATION
├── Device description and UDI-DI
├── Label and instructions for use
├── Design and manufacturing info
├── GSPR compliance matrix
├── Benefit-risk analysis
├── Verification and validation
└── Clinical evaluation report
```

### GSPR Compliance Checklist

| Requirement | Evidence | Status |
|-------------|----------|--------|
| Safe design (GSPR 1-3) | Risk management file | ☐ |
| Chemical properties (GSPR 10.1) | Biocompatibility report | ☐ |
| Infection risk (GSPR 10.2) | Sterilization validation | ☐ |
| Software requirements (GSPR 17) | IEC 62304 documentation | ☐ |
| Labeling (GSPR 23) | Label artwork, IFU | ☐ |

### Conformity Assessment Routes

| Class | Route | NB Involvement |
|-------|-------|----------------|
| I | Annex II self-declaration | None |
| Is/Im | Annex II + IX/XI | Sterile/measuring aspects |
| IIa | Annex II + IX or XI | Product or QMS |
| IIb | Annex IX + X or X + XI | Type exam + production |
| III | Annex IX + X | Full QMS + type exam |

---

## Clinical Evidence

Develop clinical evidence strategy per Annex XIV:

1. Define clinical claims and endpoints
2. Conduct systematic literature search
3. Appraise clinical data quality
4. Assess equivalence (technical, biological, clinical)
5. Identify evidence gaps
6. Determine if clinical investigation required
7. Prepare Clinical Evaluation Report (CER)
8. **Validation:** CER reviewed by qualified evaluator

### Evidence Requirements by Class

| Class | Minimum Evidence | Investigation |
|-------|------------------|---------------|
| I | Risk-benefit analysis | Not typically required |
| IIa | Literature + post-market | May be required |
| IIb | Systematic literature review | Often required |
| III | Comprehensive clinical data | Required (Article 61) |

### Clinical Evaluation Report Structure

```
CER CONTENTS
├── Executive summary
├── Device scope and intended purpose
├── Clinical background (state of the art)
├── Literature search methodology
├── Data appraisal and analysis
├── Safety and performance conclusions
├── Benefit-risk determination
└── PMCF plan summary
```

### Qualified Evaluator Requirements

- Medical degree or equivalent healthcare qualification
- 4+ years clinical experience in relevant field
- Training in clinical evaluation methodology
- Understanding of MDR requirements

---

## Post-Market Surveillance

Establish PMS system per Chapter VII:

1. Develop PMS plan (Article 84)
2. Define data collection methods
3. Establish complaint handling procedures
4. Create vigilance reporting process
5. Plan Periodic Safety Update Reports (PSUR)
6. Integrate with PMCF activities
7. Define trend analysis and signal detection
8. **Validation:** PMS system audited annually

### PMS System Components

| Component | Requirement | Frequency |
|-----------|-------------|-----------|
| PMS Plan | Article 84 | Maintain current |
| PSUR | Class IIa and higher | Per class schedule |
| PMCF Plan | Annex XIV Part B | Update with CER |
| PMCF Report | Annex XIV Part B | Annual (Class III) |
| Vigilance | Articles 87-92 | As events occur |

### PSUR Schedule

| Class | Frequency |
|-------|-----------|
| Class III | Annual |
| Class IIb implantable | Annual |
| Class IIb | Every 2 years |
| Class IIa | When necessary |

### Serious Incident Reporting

| Timeline | Requirement |
|----------|-------------|
| 2 days | Serious public health threat |
| 10 days | Death or serious deterioration |
| 15 days | Other serious incidents |

---

## EUDAMED and UDI

Implement UDI system per Article 27:

1. Obtain issuing entity code (GS1, HIBCC, ICCBBA)
2. Assign UDI-DI to each device variant
3. Assign UDI-PI (production identifier)
4. Apply UDI carrier to labels (AIDC + HRI)
5. Register actor in EUDAMED
6. Register devices in EUDAMED
7. Upload certificates when available
8. **Validation:** UDI verified on sample labels

### EUDAMED Modules

| Module | Content | Actor |
|--------|---------|-------|
| Actor | Company registration | Manufacturer, AR |
| UDI/Device | Device and variant data | Manufacturer |
| Certificates | NB certificates | Notified Body |
| Clinical Investigation | Study registration | Sponsor |
| Vigilance | Incident reports | Manufacturer |
| Market Surveillance | Authority actions | Competent Authority |

### UDI Label Requirements

Required elements per Article 13:

- [ ] UDI-DI (device identifier)
- [ ] UDI-PI (production identifier) for Class II+
- [ ] AIDC format (barcode/RFID)
- [ ] HRI format (human-readable)
- [ ] Manufacturer name and address
- [ ] Lot/serial number
- [ ] Expiration date (if applicable)

---

## Reference Documentation

### MDR Classification Guide

`references/mdr-classification-guide.md` contains:

- Complete Annex VIII classification rules (Rules 1-22)
- Software classification per MDCG 2019-11
- Worked classification examples
- Conformity assessment route selection

### Clinical Evidence Requirements

`references/clinical-evidence-requirements.md` contains:

- Clinical evidence framework and hierarchy
- Literature search methodology
- Clinical Evaluation Report structure
- PMCF plan and evaluation report guidance

### Technical Documentation Templates

`references/technical-documentation-templates.md` contains:

- Annex II and III content requirements
- Design History File structure
- GSPR compliance matrix template
- Declaration of Conformity template
- Notified Body submission checklist

---

## Tools

### MDR Gap Analyzer

```bash
# Quick gap analysis
python scripts/mdr_gap_analyzer.py --device "Device Name" --class IIa

# JSON output for integration
python scripts/mdr_gap_analyzer.py --device "Device Name" --class III --output json

# Interactive assessment
python scripts/mdr_gap_analyzer.py --interactive
```

Analyzes device against MDR requirements, identifies compliance gaps, generates prioritized recommendations.

**Output includes:**
- Requirements checklist by category
- Gap identification with priorities
- Critical gap highlighting
- Compliance roadmap recommendations

---

## Notified Body Interface

### Selection Criteria

| Factor | Considerations |
|--------|----------------|
| Designation scope | Covers your device type |
| Capacity | Timeline for initial audit |
| Geographic reach | Markets you need to access |
| Technical expertise | Experience with your technology |
| Fee structure | Transparency, predictability |

### Pre-Submission Checklist

- [ ] Technical documentation complete
- [ ] GSPR matrix fully addressed
- [ ] Risk management file current
- [ ] Clinical evaluation report complete
- [ ] QMS (ISO 13485) certified
- [ ] Labeling and IFU finalized
- [ ] **Validation:** Internal gap assessment complete

---

## MDCG Guidance Documents Update (2024-2025)

### Key MDCG Guidance Documents

| Document | Title | Status | Key Impact |
|----------|-------|--------|------------|
| MDCG 2024-1 | Transition provisions under MDR Art. 120 | Final (2024) | Extended transition deadlines for legacy devices |
| MDCG 2024-6 | Clinical evidence needed for medical devices previously CE marked under Directives | Final (2024) | Reduced clinical evidence burden for well-established devices |
| MDCG 2023-4 Rev.1 | Notified Body capacity and availability | Revised (2024) | NB capacity monitoring and optimization |
| MDCG 2022-18 Rev.1 | Software qualification and classification under MDR | Revised (2024) | Updated software classification algorithm |
| MDCG 2020-1 Rev.1 | Clinical evaluation — equivalence | Revised (2024) | Refined equivalence demonstration requirements |
| MDCG 2019-16 Rev.1 | Cybersecurity for medical devices | Revised (2024) | Enhanced cybersecurity requirements for connected devices |
| MDCG 2019-11 Rev.1 | Qualification and classification of software | Active | Software as medical device classification |

### MDR Transition Timeline (Post-Amendment Regulation 2023/607)

| Device Category | Transition Deadline | Conditions |
|----------------|--------------------|-----------|
| Class III and implantable | 26 May 2026 | Valid MDD/AIMDD certificate + QMS application to NB by 26 May 2024 |
| Class IIb | 31 December 2027 | Valid certificate + QMS application to NB |
| Class IIa and Class I (sterile/measuring) | 31 December 2028 | Valid certificate + QMS application to NB |
| Class I (up-classified under MDR) | 31 December 2028 | Previously exempt from NB involvement |

**Conditions for extended deadlines:**
- Device continues to comply with MDD/AIMDD
- No significant changes in design or intended purpose
- No unacceptable safety or performance risk
- Manufacturer has applied to Notified Body for MDR conformity assessment before applicable deadline

---

## Software as Medical Device Under MDR (MDCG 2019-11 Rev.1)

### Software Qualification Decision

```
Is the software a medical device?
        │
        ▼
Does the software perform an action on data?
        │
    Yes─┴─No → NOT a medical device (data storage/communication only)
     │
     ▼
Is the action for the benefit of individual patients?
        │
    Yes─┴─No → NOT a medical device (population health/admin)
     │
     ▼
Is the action one of: treatment, diagnosis, monitoring, prediction?
        │
    Yes─┴─No → NOT a medical device (lifestyle/wellness)
     │
     ▼
QUALIFIES AS MEDICAL DEVICE SOFTWARE → Apply classification rules
```

### Software Classification Under MDR

| Decision Factor | Class IIa | Class IIb | Class III |
|----------------|-----------|-----------|-----------|
| Provides information to inform clinical management | Non-serious conditions | Serious conditions | N/A |
| Drives clinical management or diagnoses | N/A | Non-serious conditions | Serious or critical conditions |
| Monitors physiological processes | Non-vital parameters | Vital parameters (not immediate danger) | Vital parameters (immediate danger) |

### Software Lifecycle Requirements Under MDR

| MDR Requirement | IEC 62304 Mapping | Documentation |
|----------------|-------------------|---------------|
| GSPR 17.1 (repeatability, reliability) | Software development process | Software development plan |
| GSPR 17.2 (state of the art) | Software architecture | Architecture design document |
| GSPR 17.3 (minimum IT requirements) | System requirements | IT environment specification |
| GSPR 17.4 (foreseeable misuse) | Risk management | Software risk analysis |
| Annex II §6.5 (software verification) | Software testing | Test plans and reports |
| Annex I §23.4 (labeling for software) | Release documentation | Software release notes |

---

## AI/ML Medical Devices Under MDR

### AI/ML Classification Considerations

| AI/ML Capability | MDR Classification Impact | Regulatory Consideration |
|-----------------|--------------------------|-------------------------|
| AI-assisted detection | Typically Class IIa-IIb (Rule 11) | Must demonstrate clinical performance per intended use |
| AI-driven diagnosis | Typically Class IIb-III (Rule 11) | Requires clinical investigation for novel indications |
| AI treatment optimization | Typically Class IIb-III (Rule 11 + specific rules) | Benefit-risk analysis must account for AI uncertainty |
| Continuously learning AI | Classification per highest risk output | Post-market monitoring must track algorithm evolution |

### AI/ML-Specific Technical Documentation

In addition to standard Annex II requirements, AI/ML devices must document:

| Section | Content | MDCG Reference |
|---------|---------|----------------|
| Algorithm description | Architecture, training approach, feature engineering | MDCG 2019-11, IMDRF SaMD WG |
| Training data | Sources, demographics, size, labeling methodology, quality | MDCG 2020-1 (equivalence) |
| Validation methodology | Test dataset independence, performance metrics, subgroup analysis | Annex XIV |
| Clinical performance | Sensitivity, specificity, AUC, PPV, NPV per intended population | CER requirements |
| Change management | How algorithm updates are validated and deployed | GSPR 17 |
| Explainability | How the AI's output can be understood by intended users | GSPR 23 (labeling) |

### EU AI Act Interaction with MDR

| EU AI Act Requirement | MDR Equivalent | Combined Approach |
|----------------------|----------------|-------------------|
| High-risk classification (Annex III, Point 10) | Annex VIII classification rules | Both classifications apply; meet stricter requirement |
| Conformity assessment (Art. 43) | Annex IX/X/XI assessment | MDR conformity assessment satisfies AI Act (Art. 120) |
| Technical documentation (Annex IV) | Annex II technical documentation | Extend MDR technical file with AI Act-specific elements |
| Risk management (Art. 9) | ISO 14971 + GSPR | ISO 14971 satisfies both when AI risks are included |
| Data governance (Art. 10) | GSPR 17 + Annex XIV | Add AI-specific data governance to clinical evaluation |
| Post-market monitoring (Art. 72) | Chapter VII PMS | Single PMS system covering both AI Act and MDR |

> **See also:** `../risk-management-specialist/SKILL.md` for AI-specific risk management under ISO 14971, and `../fda-consultant-specialist/SKILL.md` for FDA's AI/ML SaMD framework and PCCP.

---

## Eudamed Implementation Status and Requirements

### Eudamed Module Deployment Status (as of 2025)

| Module | Status | Mandatory Date | Content |
|--------|--------|----------------|---------|
| Actor Registration | Operational | Available now | Economic operator registration |
| UDI/Device Registration | Operational | 6 months after Eudamed fully functional | Device and UDI-DI data |
| Notified Body and Certificates | Operational | Available now | Certificate data upload by NBs |
| Clinical Investigations | Operational | Available now | Study registration and reporting |
| Vigilance | Partially operational | 24 months after fully functional | Incident reports, FSCAs, trend reports |
| Market Surveillance | In development | 18 months after fully functional | CA market surveillance activities |

**Key consideration:** Until Eudamed is declared fully functional by the European Commission, manufacturers must use existing national systems (e.g., BfArM in Germany, ANSM in France) for vigilance reporting.

### Eudamed Registration Requirements for Manufacturers

| Data Element | Required For | Update Frequency |
|-------------|-------------|-----------------|
| SRN (Single Registration Number) | All manufacturers | On change |
| Authorized representative details | Non-EU manufacturers | On change |
| Device identification (UDI-DI) | All devices placed on market | Before first placing on market |
| Basic UDI-DI | Device model/family grouping | Before first placing on market |
| GMDN code | Device nomenclature | On initial registration |
| Risk class | Classification per Annex VIII | On initial registration |
| NB certificate reference | Class IIa and above | When certificate issued |
| Clinical investigation registration | Interventional studies | Before study start |

---

## UDI-DI and UDI-PI Detailed Requirements

### UDI-DI (Device Identifier) — Static Information

| Element | Description | Example |
|---------|-------------|---------|
| Device identifier | Unique code for device model/version | 04069876543219 (GS1 GTIN) |
| Issuing entity | GS1, HIBCC, ICCBBA, or IFA | Selected by manufacturer |
| Device model | Specific device configuration | "CardioMonitor X200" |
| Device version | Software version (for SaMD) | "v3.1.0" |
| Applicable regulations | MDR or IVDR reference | MDR 2017/745 |
| Risk class | Per Annex VIII | Class IIa |
| Basic UDI-DI | Grouping identifier for device family | 04069876500001 |

### UDI-PI (Production Identifier) — Variable Information

| PI Element | When Required | Format |
|-----------|---------------|--------|
| Lot/batch number | When tracking by lot | Lot: ABC123 |
| Serial number | When individual tracking required (Class III, implantable) | SN: 2024-00001 |
| Manufacturing date | When relevant to safety | Mfg: 2024-06-15 |
| Expiry date | When device has shelf life | Exp: 2026-06-15 |
| Software version | SaMD and software-driven devices | SW: v3.1.0 |

### UDI Carrier Requirements

| Carrier Type | Format | Where Applied |
|-------------|--------|---------------|
| AIDC (barcode/2D code) | GS1 DataMatrix, GS1-128, HIBC | Device label, package label |
| HRI (human-readable) | Plain text interpretation of AIDC | Adjacent to AIDC on label |
| RFID | GS1 EPC/RFID | Optional, in addition to AIDC |

**Labeling placement rules:**
- UDI on each level of packaging (unit, intermediate, case)
- For reusable devices requiring sterilization: UDI on device itself (direct marking)
- Class III implantable: UDI on device or packaging that remains with patient record
- UDI must survive device lifecycle (including reprocessing cycles for reusable devices)

### UDI Database Submission Timeline

| Device Class | Submission Deadline |
|-------------|-------------------|
| Class III and implantable | Before placing on the market |
| Class IIb | Before placing on the market |
| Class IIa | Before placing on the market |
| Class I | Before placing on the market |

> **Note:** All timelines are contingent on Eudamed being declared fully functional. Until then, manufacturers should pre-register in Eudamed (available modules) and maintain data readiness.

---

## Cross-Reference: NIS2 for Critical Infrastructure (Healthcare)

Healthcare organizations manufacturing or deploying medical devices may be classified as essential entities under NIS2:

| NIS2 Requirement | MDR Impact | Action for Manufacturers |
|-----------------|-----------|--------------------------|
| Art. 21: Cybersecurity risk management | MDCG 2019-16 cybersecurity guidance | Align device cybersecurity with organizational NIS2 compliance |
| Art. 23: Incident reporting (24h/72h) | Art. 87-92 vigilance reporting | Unified incident reporting covering both device and infrastructure incidents |
| Art. 21(2)(d): Supply chain security | Art. 11 authorized representatives, supply chain | Assess cybersecurity of device component suppliers |
| Art. 20: Governance and accountability | Art. 10 manufacturer obligations | Senior management oversight of both NIS2 and MDR compliance |

> **See also:** `../information-security-manager-iso27001/SKILL.md` for ISO 27001 alignment with NIS2 requirements.

---

## MDR Updates & Cross-Framework Integration

### Latest MDCG Guidance Documents

- **MDCG 2019-11 Rev.1:** Qualification and classification of software — updated algorithm for SaMD
- **MDCG 2020-1 Rev.1:** Clinical evaluation (Annex XIV) — updated methodologies
- **MDCG 2024-8:** EU AI Act interaction with MDR for AI-enabled medical devices
- **MDCG 2023-4:** Legacy devices and Article 120 transition provisions

### AI/ML Medical Devices Under MDR

- **Classification:** AI/ML-based SaMD typically Class IIa or higher (Rule 11)
- **Clinical Evidence:** Must demonstrate AI algorithm clinical performance (sensitivity, specificity, AUC)
- **Continuous Learning:** PCCP-equivalent under MDR for adaptive AI devices
- **Post-Market:** Enhanced PMCF for AI devices monitoring real-world algorithm performance
- **EU AI Act Interaction:** High-risk AI medical devices subject to BOTH MDR and EU AI Act
- **Cross-reference:** See `eu-ai-act-specialist` for AI Act obligations

### NIS2 Impact on Healthcare

- Healthcare entities are "Essential Entities" under NIS2 Directive
- Medical device manufacturers may be "Important Entities"
- NIS2 cybersecurity requirements supplement MDR cybersecurity expectations
- **Cross-reference:** See `nis2-directive-specialist` for NIS2 compliance

### EUDAMED Implementation Status

- **Actor Registration Module:** Operational — all economic operators must register
- **UDI/Device Registration Module:** Operational — mandatory device registration
- **Notified Body Module:** Operational — certificate information
- **Clinical Investigation Module:** Available
- **Vigilance Module:** Under development
- **Market Surveillance Module:** Under development

### UDI Detailed Requirements

- **UDI-DI (Device Identifier):** Unique to device model — used for EUDAMED registration
- **UDI-PI (Production Identifier):** Identifies production unit — lot, serial, expiry, manufacturing date
- **Issuing Entities:** GS1, HIBCC, ICCBBA, IFA
- **Carrier Types:** AIDC (barcode/2D) + HRI (human readable)
- **Implant Card:** Required for Class III implantable devices (UDI + patient information)

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| Device classification unclear -- rules yield different results | Multiple classification rules apply; highest class must be selected per MDR Article 51(7) | Apply all applicable rules from Annex VIII (Rules 1-22); use the implementing rule that gives the highest classification; for software, apply MDCG 2019-11 Rev.1 algorithm; document rationale for each rule considered |
| Notified Body rejects technical file for incompleteness | GSPR compliance matrix gaps, missing clinical evaluation, or insufficient risk management documentation | Review GSPR checklist in this skill; ensure Annex II technical file structure is complete; verify CER meets Annex XIV requirements; confirm ISO 14971 risk management file is current and comprehensive |
| EUDAMED registration delays blocking market access | Module not operational or manufacturer SRN not obtained | Check current EUDAMED module status; obtain SRN via actor registration module (operational); use national systems for vigilance reporting until Eudamed Vigilance module is fully functional |
| Clinical evidence insufficient for Class IIb/III device | Equivalence route rejected by NB or clinical investigation not planned | Reassess equivalence per MDCG 2020-1 Rev.1 (technical, biological, clinical equivalence with access to data); if equivalence fails, plan clinical investigation per Article 61; consider MDCG 2024-6 for reduced evidence burden on well-established devices |
| MDR transition deadline approaching with NB application pending | Limited NB capacity (approximately 40 designated EU-wide as of 2025) | Verify transition deadline for your device class (Class III: May 2026, Class IIb: Dec 2027, Class IIa: Dec 2028); ensure QMS application was submitted to NB by applicable deadline; maintain MDD/AIMDD compliance during transition |
| UDI labeling rejected by NB or competent authority | UDI-DI/UDI-PI format incorrect, AIDC carrier unreadable, or missing elements | Verify all required UDI elements per Article 27; ensure AIDC format (GS1 DataMatrix preferred) is scannable; include HRI adjacent to barcode; for reusable devices, apply direct marking that survives reprocessing |
| AI/ML medical device faces dual regulatory obligations | Device classified under both MDR and EU AI Act as high-risk | Assess both MDR Annex VIII classification and EU AI Act Annex III categorization; MDR conformity assessment may satisfy AI Act per Art. 120; extend technical documentation with AI-specific elements per MDCG 2024-8 |

---

## Success Criteria

- **Device correctly classified with documented rationale** -- classification per Annex VIII with all applicable rules evaluated, highest class selected, and rationale documented for NB review
- **Complete technical file per Annex II structure** -- device description, labeling/IFU, design and manufacturing info, GSPR compliance matrix, benefit-risk analysis, verification and validation, and clinical evaluation report all present and current
- **GSPR compliance matrix fully addressed** -- all applicable General Safety and Performance Requirements mapped to evidence with cross-references to risk management file, biocompatibility reports, sterilization validation, software documentation, and labeling
- **Clinical evaluation report meets Annex XIV requirements** -- literature search methodology documented, data appraised and analyzed, safety and performance conclusions stated, benefit-risk determined, and PMCF plan included
- **PMS system operational** -- PMS plan per Article 84, complaint handling procedures, vigilance reporting process, PSUR schedule defined by class, and PMCF activities integrated with CER
- **UDI system fully implemented** -- UDI-DI assigned per device variant, UDI-PI applied (lot/serial/dates), AIDC and HRI carriers on all packaging levels, EUDAMED registration complete (when applicable)
- **MDR gap analysis shows zero critical gaps** -- as measured by `mdr_gap_analyzer.py`, with all requirements addressed or in-progress with documented timeline

---

## Scope & Limitations

**In Scope:**
- Device classification per MDR Annex VIII (Rules 1-22) including software classification per MDCG 2019-11 Rev.1
- Technical documentation structure and requirements per Annex II and Annex III
- GSPR compliance matrix with evidence mapping
- Clinical evidence strategy including equivalence assessment, CER structure, and PMCF planning
- Post-market surveillance system design including PMS plan, PSUR schedule, and vigilance reporting timelines
- EUDAMED and UDI system implementation guidance
- Conformity assessment route selection by device class
- MDR transition timeline tracking (post-Amendment Regulation 2023/607)
- AI/ML medical device considerations including EU AI Act interaction

**Out of Scope:**
- Clinical investigation protocol design, execution, or statistical analysis
- Biocompatibility testing per ISO 10993 (beyond evidence mapping in GSPR)
- Sterilization validation per ISO 11135/11137 (beyond evidence mapping)
- Notified Body selection, engagement, or commercial negotiation
- Quality Management System implementation -- use `quality-manager-qms-iso13485` for ISO 13485 QMS
- Risk management process implementation -- use `risk-management-specialist` for ISO 14971

**Important Notes:**
- EUDAMED's first four modules became mandatory from May 28, 2026; manufacturers must have SRN and device registrations ready
- Only approximately 40 Notified Bodies are designated EU-wide as of 2025, creating capacity constraints; early NB engagement is critical
- The European Commission published updated transition timelines in December 2025 extending deadlines for certain device categories
- Manufacturers must adopt recently harmonized standards with no formal transition period (Decision EU 2025/2078)

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `fda-consultant-specialist` | Cross-framework mapping for dual US/EU market; FDA QMSR aligns with ISO 13485 used by MDR | When device requires both FDA clearance/approval and EU MDR CE marking |
| `quality-manager-qms-iso13485` | ISO 13485 QMS is prerequisite for MDR conformity assessment (Annex IX, XI) | When establishing or auditing QMS for MDR compliance |
| `risk-management-specialist` | ISO 14971 risk management file is core component of MDR technical documentation | When developing risk management file, FMEA, and benefit-risk analysis |
| `eu-ai-act-specialist` | AI medical devices subject to both MDR and EU AI Act; classification and conformity assessment interaction | When AI-enabled medical device requires dual regulatory compliance |
| `capa-officer` | CAPA process supports MDR vigilance obligations and FSCA implementation | When post-market surveillance identifies safety or performance issues requiring corrective action |
| `infrastructure-compliance-auditor` | Cybersecurity validation per MDCG 2019-16 Rev.1 for connected medical devices | When connected device requires cybersecurity documentation for technical file |

---

## Tool Reference

### mdr_gap_analyzer.py

Analyzes device against MDR requirements, identifies compliance gaps, and generates prioritized recommendations.

| Flag | Required | Description |
|------|----------|-------------|
| `--device <name>` | Yes (unless `--interactive`) | Device name for gap analysis |
| `--class <class>` | Yes (unless `--interactive`) | Device classification: `I`, `Is`, `Im`, `IIa`, `IIb`, `III` |
| `--output <format>` | No | Output format: `json` for machine-readable output; default is human-readable text |
| `--interactive` | No | Launch interactive assessment mode with guided questions |

**Analysis Categories:** Technical documentation (Annex II), GSPR compliance, clinical evidence (Annex XIV), post-market surveillance (Chapter VII), UDI/EUDAMED, labeling (Article 13), quality management system, risk management, and conformity assessment route.

**Output:** Requirements checklist with per-item status (Not Started/In Progress/Complete/N/A), gap identification with priority (Critical/High/Medium/Low), critical gap highlighting, completion percentage, and compliance roadmap recommendations.

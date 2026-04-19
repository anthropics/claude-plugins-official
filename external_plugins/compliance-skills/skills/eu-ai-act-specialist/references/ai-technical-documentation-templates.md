# AI Technical Documentation Templates

Production-ready templates for EU AI Act (Regulation EU 2024/1689) compliance documentation. Covers all required documentation for high-risk AI systems, GPAI models, and deployer obligations.

---

## Table of Contents

- [Template 1: AI System Description](#template-1-ai-system-description)
- [Template 2: Risk Management System Documentation](#template-2-risk-management-system-documentation)
- [Template 3: Data Governance Documentation](#template-3-data-governance-documentation)
- [Template 4: Testing and Validation Report](#template-4-testing-and-validation-report)
- [Template 5: Human Oversight Procedures](#template-5-human-oversight-procedures)
- [Template 6: Post-Market Monitoring Plan](#template-6-post-market-monitoring-plan)
- [Template 7: Incident Reporting Template](#template-7-incident-reporting-template)
- [Template 8: Fundamental Rights Impact Assessment](#template-8-fundamental-rights-impact-assessment)

---

## Template 1: AI System Description

```
═══════════════════════════════════════════════════════════════════
AI SYSTEM TECHNICAL DESCRIPTION
Regulation (EU) 2024/1689 — Art. 11, Annex IV
═══════════════════════════════════════════════════════════════════

Document ID:        [TDS-XXXX-VX.X]
System Name:        [Name]
System Version:     [X.X.X]
Provider:           [Legal entity name]
Date:               [DD/MM/YYYY]
Classification:     [HIGH-RISK / LIMITED / MINIMAL]
Annex III Category: [Category number and title, if applicable]
Document Status:    [Draft / Under Review / Approved / Superseded]
Approved By:        [Name, Title]

───────────────────────────────────────────────────────────────────
1. GENERAL DESCRIPTION
───────────────────────────────────────────────────────────────────

1.1 Provider Information
    - Legal name:
    - Registered address:
    - Contact person:
    - Contact email:
    - Contact phone:
    - EU Authorised Representative (if non-EU provider):

1.2 AI System Identification
    - Trade name / brand:
    - Model / type designation:
    - Version / build:
    - Hardware/software platform:
    - EU Database registration number:

1.3 Intended Purpose
    - Primary intended purpose:
    - Specific use cases:
    - Target deployer profile:
    - Geographic scope of deployment:
    - Deployment environment:

1.4 Persons Affected
    - Categories of natural persons affected:
    - Estimated number of affected persons:
    - Vulnerable groups that may be affected:
    - Nature of impact on affected persons:

1.5 Contraindications and Foreseeable Misuse
    - Known contraindications (when NOT to use):
    - Foreseeable misuse scenarios:
    - Safeguards against misuse:
    - Prohibited uses:

───────────────────────────────────────────────────────────────────
2. TECHNICAL ARCHITECTURE
───────────────────────────────────────────────────────────────────

2.1 System Architecture Overview
    - Architecture diagram: [Reference to diagram]
    - Component list:
      Component 1: [Name, function, technology]
      Component 2: [Name, function, technology]
    - External dependencies:
    - Integration points:

2.2 AI Model Specification
    - Model type: [CNN, Transformer, XGBoost, ensemble, etc.]
    - Model architecture: [Detailed architecture description]
    - Number of parameters:
    - Input modalities: [text, image, tabular, audio, video, etc.]
    - Output type: [classification, regression, generation, etc.]
    - Output format: [probability scores, labels, text, etc.]
    - Inference latency: [typical, p95, p99]
    - Computational requirements:
      Training: [GPU type, count, time]
      Inference: [CPU/GPU requirements, memory]

2.3 Key Design Choices
    | Design Decision | Choice Made | Rationale | Alternatives Considered |
    |-----------------|-------------|-----------|------------------------|
    |                 |             |           |                        |

2.4 Software and Dependencies
    - Programming language(s):
    - ML framework:
    - Key libraries and versions:
    - Operating system:
    - Containerization (if applicable):

───────────────────────────────────────────────────────────────────
3. TRAINING AND DATA
───────────────────────────────────────────────────────────────────

3.1 Training Data
    - Data sources:
    - Data volume: [number of samples, data size]
    - Data collection period:
    - Data collection method:
    - Geographic origin of data:
    - Languages:

3.2 Data Characteristics
    - Feature descriptions:
      | Feature | Type | Description | Range/Values |
      |---------|------|-------------|-------------|
      |         |      |             |             |
    - Label / target variable:
    - Label distribution:

3.3 Data Preparation
    - Cleaning procedures:
    - Annotation process:
    - Labelling methodology:
    - Quality assurance for labels:
    - Data augmentation (if applied):
    - Train/validation/test split ratios:
    - Stratification method:

3.4 Data Governance (Art. 10 Summary)
    - Bias examination results: [Reference to full report]
    - Representativeness assessment:
    - Special category data: [Yes/No; if yes, safeguards]
    - Data governance documentation: [Reference to full document]

───────────────────────────────────────────────────────────────────
4. PERFORMANCE AND LIMITATIONS
───────────────────────────────────────────────────────────────────

4.1 Performance Metrics
    | Metric | Overall | Group 1 | Group 2 | Group N |
    |--------|---------|---------|---------|---------|
    |        |         |         |         |         |

4.2 Performance Conditions
    - Optimal operating conditions:
    - Degraded performance conditions:
    - Failure conditions:

4.3 Known Limitations
    - Technical limitations:
    - Data limitations:
    - Environmental limitations:
    - Edge cases with degraded performance:

4.4 Benchmarking
    - Benchmark datasets used:
    - Comparison with state of the art:
    - Comparison with human performance (if relevant):

───────────────────────────────────────────────────────────────────
5. RISK CLASSIFICATION
───────────────────────────────────────────────────────────────────

5.1 Classification Determination
    - AI Act classification: [HIGH-RISK / LIMITED / MINIMAL]
    - Annex III category (if applicable):
    - Art. 6(3) exception analysis (if applicable):
    - Classification rationale:

5.2 Applicable Obligations
    | Obligation | Article | Compliance Status |
    |-----------|---------|-------------------|
    |           |         |                   |

5.3 Cross-References
    - Risk Management System: [Document reference]
    - Data Governance: [Document reference]
    - Human Oversight Procedures: [Document reference]
    - Post-Market Monitoring Plan: [Document reference]

───────────────────────────────────────────────────────────────────
6. CHANGE HISTORY
───────────────────────────────────────────────────────────────────

    | Version | Date | Author | Changes | Impact Assessment |
    |---------|------|--------|---------|-------------------|
    |         |      |        |         |                   |

───────────────────────────────────────────────────────────────────
7. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Technical Lead |  |  |  |
    | AI Compliance Officer |  |  |  |
    | Quality Manager |  |  |  |
```

---

## Template 2: Risk Management System Documentation

```
═══════════════════════════════════════════════════════════════════
RISK MANAGEMENT SYSTEM — AI SYSTEM
Regulation (EU) 2024/1689 — Art. 9
═══════════════════════════════════════════════════════════════════

Document ID:        [RMS-XXXX-VX.X]
AI System:          [System name and version]
Risk Management Lead: [Name, Title]
Date:               [DD/MM/YYYY]
Review Date:        [DD/MM/YYYY]
Document Status:    [Draft / Under Review / Approved]

───────────────────────────────────────────────────────────────────
1. SCOPE AND OBJECTIVES
───────────────────────────────────────────────────────────────────

1.1 Scope
    - AI system(s) covered:
    - Lifecycle phases covered:
    - Boundaries and exclusions:

1.2 Objectives
    - Identify and manage risks to health, safety, and fundamental rights
    - Ensure residual risks are acceptable
    - Maintain risk management throughout system lifecycle
    - Comply with Art. 9 requirements

1.3 Methodology
    - Risk identification method: [FMEA, HAZOP, FTA, brainstorming, etc.]
    - Risk evaluation criteria:
    - Risk acceptability criteria:
    - Review and update triggers:

───────────────────────────────────────────────────────────────────
2. RISK IDENTIFICATION
───────────────────────────────────────────────────────────────────

2.1 Intended Use Risks

    | Risk ID | Hazard | Harm | Affected Persons | Source |
    |---------|--------|------|------------------|--------|
    | R-001   |        |      |                  |        |
    | R-002   |        |      |                  |        |

2.2 Foreseeable Misuse Risks

    | Risk ID | Misuse Scenario | Hazard | Harm | Affected Persons |
    |---------|----------------|--------|------|------------------|
    | R-M001  |                |        |      |                  |

2.3 Fundamental Rights Risks

    | Risk ID | Right Affected | Risk Description | Affected Groups |
    |---------|---------------|------------------|-----------------|
    | R-FR001 | Non-discrimination |              |                 |
    | R-FR002 | Privacy        |                  |                 |
    | R-FR003 | Freedom of expression |           |                 |

───────────────────────────────────────────────────────────────────
3. RISK EVALUATION
───────────────────────────────────────────────────────────────────

3.1 Probability Scale
    | Level | Probability | Description |
    |-------|-------------|-------------|
    | 1     | Rare        | Less than 1 in 10,000 uses |
    | 2     | Unlikely    | 1 in 1,000 to 1 in 10,000 |
    | 3     | Possible    | 1 in 100 to 1 in 1,000 |
    | 4     | Likely      | 1 in 10 to 1 in 100 |
    | 5     | Very likely | More than 1 in 10 |

3.2 Severity Scale
    | Level | Severity | Description |
    |-------|----------|-------------|
    | 1     | Negligible | Minor inconvenience, easily reversible |
    | 2     | Minor    | Temporary harm, recoverable without intervention |
    | 3     | Moderate | Significant harm, requires intervention to recover |
    | 4     | Serious  | Serious harm to health, safety, or rights |
    | 5     | Critical | Death, permanent disability, irreversible rights violation |

3.3 Risk Matrix
    | Probability \ Severity | Negligible | Minor | Moderate | Serious | Critical |
    |----------------------|------------|-------|----------|---------|----------|
    | Very likely          | Medium     | High  | High     | Unacceptable | Unacceptable |
    | Likely               | Low        | Medium| High     | High    | Unacceptable |
    | Possible             | Low        | Medium| Medium   | High    | High     |
    | Unlikely             | Low        | Low   | Medium   | Medium  | High     |
    | Rare                 | Low        | Low   | Low      | Medium  | Medium   |

3.4 Risk Evaluation Results

    | Risk ID | Probability | Severity | Risk Level | Acceptable? |
    |---------|-------------|----------|------------|-------------|
    | R-001   |             |          |            |             |

───────────────────────────────────────────────────────────────────
4. RISK CONTROL MEASURES
───────────────────────────────────────────────────────────────────

    | Risk ID | Control Measure | Type | Implementation | Verification | Status |
    |---------|----------------|------|----------------|-------------|--------|
    | R-001   |                | [Elimination/Reduction/Protection] |  |  |  |

    Control type hierarchy (most to least preferred):
    1. Elimination — remove the source of risk
    2. Reduction — reduce probability or severity
    3. Protection — safeguards, warnings, training

───────────────────────────────────────────────────────────────────
5. RESIDUAL RISK ASSESSMENT
───────────────────────────────────────────────────────────────────

5.1 Individual Residual Risks

    | Risk ID | Residual Probability | Residual Severity | Residual Level | Acceptable? |
    |---------|---------------------|-------------------|----------------|-------------|
    | R-001   |                     |                   |                |             |

5.2 Overall Residual Risk

    - Overall residual risk determination: [Acceptable / Not acceptable]
    - Risk-benefit analysis:
      Benefits: [Description of system benefits]
      Residual risks: [Summary of remaining risks]
      Determination: [Benefits outweigh residual risks / Do not outweigh]
    - Comparison with state of the art:

5.3 Information for Safety
    - Residual risks communicated in instructions for use:
    - Training requirements for deployers:
    - Limitations highlighted:

───────────────────────────────────────────────────────────────────
6. TESTING
───────────────────────────────────────────────────────────────────

6.1 Pre-Market Testing

    | Test ID | Test Description | Metrics | Threshold | Result | Pass/Fail |
    |---------|-----------------|---------|-----------|--------|-----------|
    |         |                 |         |           |        |           |

6.2 Real-World Conditions Testing (if applicable)
    - Test environment description:
    - Test duration:
    - Test population:
    - Results summary:

───────────────────────────────────────────────────────────────────
7. REVIEW AND UPDATE PLAN
───────────────────────────────────────────────────────────────────

    - Scheduled review frequency: [Annually / Semi-annually / Quarterly]
    - Update triggers:
      [ ] Serious incident reported
      [ ] Post-market monitoring data indicates new risk
      [ ] Significant system change (retraining, new data, new context)
      [ ] New regulatory guidance or harmonised standard
      [ ] Deployer feedback indicating issues
    - Review record:

    | Review Date | Reviewer | Changes Made | Rationale |
    |-------------|----------|-------------|-----------|
    |             |          |             |           |

───────────────────────────────────────────────────────────────────
8. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Risk Management Lead |  |  |  |
    | AI Compliance Officer |  |  |  |
    | Technical Lead |  |  |  |
```

---

## Template 3: Data Governance Documentation

```
═══════════════════════════════════════════════════════════════════
DATA GOVERNANCE DOCUMENTATION — AI SYSTEM
Regulation (EU) 2024/1689 — Art. 10
═══════════════════════════════════════════════════════════════════

Document ID:        [DGD-XXXX-VX.X]
AI System:          [System name and version]
Data Governance Lead: [Name, Title]
Date:               [DD/MM/YYYY]
Document Status:    [Draft / Under Review / Approved]

───────────────────────────────────────────────────────────────────
1. DATA OVERVIEW
───────────────────────────────────────────────────────────────────

1.1 Dataset Inventory

    | Dataset | Purpose | Source | Volume | Period | Format |
    |---------|---------|--------|--------|--------|--------|
    | Training |        |        |        |        |        |
    | Validation |      |        |        |        |        |
    | Testing  |        |        |        |        |        |

1.2 Data Types
    - Personal data processed: [Yes/No]
    - Special category data (Art. 9 GDPR): [Yes/No]
    - If special category: justification for processing:
    - Safeguards for special category data:

───────────────────────────────────────────────────────────────────
2. DESIGN CHOICES (Art. 10(2)(a))
───────────────────────────────────────────────────────────────────

2.1 Data Collection Design
    - Why these data sources were chosen:
    - Data sources rejected and reasons:
    - Sampling methodology:
    - Collection timeframe rationale:
    - Geographic scope rationale:

2.2 Labelling Strategy
    - Labelling methodology:
    - Number of annotators:
    - Inter-annotator agreement:
    - Quality assurance process:
    - Labelling guidelines: [Reference]

───────────────────────────────────────────────────────────────────
3. DATA PREPARATION (Art. 10(2)(b))
───────────────────────────────────────────────────────────────────

3.1 Processing Steps

    | Step | Process | Tool/Method | Parameters | Quality Check |
    |------|---------|-------------|-----------|---------------|
    | 1    | Cleaning |            |           |               |
    | 2    | Filtering |           |           |               |
    | 3    | Annotation |          |           |               |
    | 4    | Enrichment |          |           |               |
    | 5    | Aggregation |         |           |               |

3.2 Data Quality Metrics

    | Metric | Value | Threshold | Pass/Fail |
    |--------|-------|-----------|-----------|
    | Completeness |  |          |           |
    | Accuracy     |  |          |           |
    | Consistency  |  |          |           |
    | Timeliness   |  |          |           |
    | Duplication rate | |       |           |

───────────────────────────────────────────────────────────────────
4. ASSUMPTIONS (Art. 10(2)(c))
───────────────────────────────────────────────────────────────────

    - What the data is meant to measure:
    - What the data is meant to represent:
    - Assumptions about data-to-reality mapping:
    - Known gaps between data and real-world distribution:
    - Limitations of the data:

───────────────────────────────────────────────────────────────────
5. SUFFICIENCY AND REPRESENTATIVENESS (Art. 10(2)(e)(f))
───────────────────────────────────────────────────────────────────

5.1 Data Sufficiency
    - Total samples: [number]
    - Sufficiency assessment methodology:
    - Learning curve analysis (if performed):
    - Conclusion on sufficiency:

5.2 Representativeness Analysis

    | Attribute | Dataset Distribution | Population Distribution | Ratio | Assessment |
    |-----------|---------------------|------------------------|-------|------------|
    |           |                     |                        |       |            |

    - Population reference source:
    - Overall representativeness assessment:
    - Gaps identified:
    - Mitigation for gaps:

───────────────────────────────────────────────────────────────────
6. BIAS EXAMINATION (Art. 10(2)(f))
───────────────────────────────────────────────────────────────────

6.1 Bias Analysis Methodology
    - Tools used: [e.g., ai_bias_detector.py]
    - Protected attributes examined:
    - Metrics calculated:
    - Thresholds applied:

6.2 Bias Analysis Results

    | Attribute | Metric | Value | Threshold | Pass/Fail | Severity |
    |-----------|--------|-------|-----------|-----------|----------|
    |           |        |       |           |           |          |

6.3 Proxy Variable Analysis

    | Feature | Protected Attribute | Correlation | Risk Level |
    |---------|-------------------|-------------|------------|
    |         |                   |             |            |

6.4 Bias Examination Conclusion
    - Summary of findings:
    - Overall bias risk assessment:
    - Reference to full bias detection report:

───────────────────────────────────────────────────────────────────
7. BIAS MITIGATION (Art. 10(2)(g))
───────────────────────────────────────────────────────────────────

    | Bias Finding | Mitigation Measure | Type | Effectiveness | Residual Bias |
    |-------------|-------------------|------|---------------|---------------|
    |             |                   | [Pre/In/Post-processing] |         |               |

    - Mitigation verification results:
    - Residual bias assessment:
    - Residual bias acceptance rationale:

───────────────────────────────────────────────────────────────────
8. SPECIAL CATEGORY DATA (Art. 10(5))
───────────────────────────────────────────────────────────────────

    (Complete only if special category data is processed)

    - Special categories processed: [race, political opinions, religious
      beliefs, trade union membership, genetic data, biometric data, health
      data, sex life, sexual orientation]
    - Strict necessity justification:
    - Specific purpose: [bias detection and correction]
    - Safeguards implemented:
      [ ] Encryption at rest and in transit
      [ ] Access controls (list authorized persons)
      [ ] Purpose limitation enforcement
      [ ] Data minimization applied
      [ ] Retention limitation defined
      [ ] DPIA completed
    - Legal basis:

───────────────────────────────────────────────────────────────────
9. DATA MANAGEMENT
───────────────────────────────────────────────────────────────────

    - Storage location:
    - Access controls:
    - Retention period:
    - Deletion procedure:
    - Version control:
    - Data lineage tracking:

───────────────────────────────────────────────────────────────────
10. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Data Governance Lead |  |  |  |
    | Data Protection Officer |  |  |  |
    | AI Compliance Officer |  |  |  |
```

---

## Template 4: Testing and Validation Report

```
═══════════════════════════════════════════════════════════════════
TESTING AND VALIDATION REPORT — AI SYSTEM
Regulation (EU) 2024/1689 — Art. 9(7), Art. 15
═══════════════════════════════════════════════════════════════════

Document ID:        [TVR-XXXX-VX.X]
AI System:          [System name and version]
Test Lead:          [Name, Title]
Test Period:        [Start date — End date]
Document Status:    [Draft / Under Review / Approved]

───────────────────────────────────────────────────────────────────
1. TEST PLAN SUMMARY
───────────────────────────────────────────────────────────────────

1.1 Objectives
    - Verify system meets accuracy requirements (Art. 15)
    - Verify robustness against errors and adversarial inputs (Art. 15)
    - Verify cybersecurity measures (Art. 15)
    - Validate risk management measures (Art. 9)
    - Verify fairness across demographic groups (Art. 10)

1.2 Test Environment
    - Hardware:
    - Software:
    - Configuration:
    - Differences from production environment:

1.3 Test Data
    - Test dataset description:
    - Test dataset size:
    - Test data source:
    - Relationship to training data: [Independent / Holdout / Cross-validated]

───────────────────────────────────────────────────────────────────
2. ACCURACY TESTING (Art. 15(1))
───────────────────────────────────────────────────────────────────

2.1 Overall Performance

    | Metric | Value | Threshold | Pass/Fail |
    |--------|-------|-----------|-----------|
    | Accuracy |     |           |           |
    | Precision |    |           |           |
    | Recall   |     |           |           |
    | F1 Score |     |           |           |
    | AUC-ROC  |     |           |           |
    | [Other]  |     |           |           |

2.2 Performance by Demographic Group

    | Group | Metric 1 | Metric 2 | Metric 3 | Threshold | Pass/Fail |
    |-------|----------|----------|----------|-----------|-----------|
    |       |          |          |          |           |           |

2.3 Performance by Use Case / Scenario

    | Scenario | Metric | Value | Threshold | Pass/Fail |
    |----------|--------|-------|-----------|-----------|
    |          |        |       |           |           |

2.4 Accuracy Conclusions
    - Overall accuracy assessment:
    - Performance variations across groups:
    - Accuracy level to declare in instructions for use:

───────────────────────────────────────────────────────────────────
3. ROBUSTNESS TESTING (Art. 15(2)(3))
───────────────────────────────────────────────────────────────────

3.1 Input Error Resilience

    | Error Type | Test Method | Degradation | Acceptable? |
    |-----------|-------------|-------------|-------------|
    | Missing values |        |             |             |
    | Noisy input |           |             |             |
    | Out-of-range values |   |             |             |
    | Corrupted input |       |             |             |
    | Wrong format |          |             |             |

3.2 Edge Case Testing

    | Edge Case | Input Description | Expected Behaviour | Actual Behaviour | Pass/Fail |
    |-----------|------------------|-------------------|-----------------|-----------|
    |           |                  |                   |                 |           |

3.3 Fail-Safe Behaviour

    | Failure Scenario | Expected Fail-Safe | Actual Behaviour | Pass/Fail |
    |-----------------|-------------------|-----------------|-----------|
    |                 |                   |                 |           |

3.4 Redundancy Verification

    | Component | Redundancy Measure | Test Method | Result |
    |-----------|-------------------|-------------|--------|
    |           |                   |             |        |

───────────────────────────────────────────────────────────────────
4. CYBERSECURITY TESTING (Art. 15(4)(5))
───────────────────────────────────────────────────────────────────

4.1 Data Poisoning Resistance

    | Attack Type | Test Method | Result | Mitigation |
    |------------|-------------|--------|------------|
    | Label flipping |         |        |            |
    | Backdoor insertion |     |        |            |
    | Data injection |         |        |            |

4.2 Adversarial Example Resistance

    | Attack Method | Perturbation Level | Success Rate | Mitigation |
    |--------------|-------------------|-------------|------------|
    | FGSM         |                   |             |            |
    | PGD          |                   |             |            |
    | [Other]      |                   |             |            |

4.3 Model Integrity

    | Test | Method | Result | Pass/Fail |
    |------|--------|--------|-----------|
    | Model tampering detection |  |    |           |
    | Model extraction resistance | |   |           |
    | Membership inference resistance | | |         |

4.4 Infrastructure Security

    | Control | Test Method | Result | Pass/Fail |
    |---------|-------------|--------|-----------|
    | API authentication |    |        |           |
    | Data encryption |       |        |           |
    | Access logging |        |        |           |
    | Network segmentation |  |        |           |

───────────────────────────────────────────────────────────────────
5. FAIRNESS TESTING (Art. 10)
───────────────────────────────────────────────────────────────────

5.1 Fairness Metrics

    | Attribute | Demographic Parity | Equalized Odds | Predictive Parity | Pass/Fail |
    |-----------|-------------------|----------------|-------------------|-----------|
    |           |                   |                |                   |           |

5.2 Disparate Impact Analysis

    | Attribute | Advantaged Group | Disadvantaged Group | Impact Ratio | Pass/Fail |
    |-----------|-----------------|---------------------|-------------|-----------|
    |           |                 |                     |             |           |

5.3 Fairness Conclusions
    - Overall fairness assessment:
    - Residual disparities:
    - Mitigation measures applied:

───────────────────────────────────────────────────────────────────
6. OVERALL TEST CONCLUSIONS
───────────────────────────────────────────────────────────────────

    - Total tests executed:
    - Tests passed:
    - Tests failed:
    - Overall determination: [PASS / CONDITIONAL PASS / FAIL]
    - Conditions (if conditional pass):
    - Recommended actions:

───────────────────────────────────────────────────────────────────
7. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Test Lead |  |  |  |
    | AI Compliance Officer |  |  |  |
    | Quality Manager |  |  |  |
```

---

## Template 5: Human Oversight Procedures

```
═══════════════════════════════════════════════════════════════════
HUMAN OVERSIGHT PROCEDURES — AI SYSTEM
Regulation (EU) 2024/1689 — Art. 14
═══════════════════════════════════════════════════════════════════

Document ID:        [HOP-XXXX-VX.X]
AI System:          [System name and version]
Oversight Level:    [Human-in-the-loop / Human-on-the-loop / Human-in-command]
Date:               [DD/MM/YYYY]
Document Status:    [Draft / Under Review / Approved]

───────────────────────────────────────────────────────────────────
1. OVERSIGHT DESIGN
───────────────────────────────────────────────────────────────────

1.1 Oversight Level Determination
    - Selected level: [Human-in-the-loop / Human-on-the-loop / Human-in-command]
    - Rationale for selection:
    - Risk factors considered:
    - Decision impact assessment:

1.2 Oversight Architecture
    - Where in the decision pipeline oversight occurs:
    - What decisions require human approval:
    - What decisions can proceed automatically:
    - Confidence threshold for automatic processing (if applicable):
    - Escalation criteria:

───────────────────────────────────────────────────────────────────
2. OVERSIGHT PERSONNEL
───────────────────────────────────────────────────────────────────

2.1 Roles

    | Role | Responsibility | Authority Level | Required Number |
    |------|---------------|-----------------|-----------------|
    | Primary Overseer |   |                 |                 |
    | Backup Overseer |    |                 |                 |
    | Escalation Authority | |               |                 |

2.2 Required Competencies

    | Competency | Description | Assessment Method |
    |-----------|-------------|-------------------|
    | Domain knowledge |     |                   |
    | AI system understanding | |                |
    | Output interpretation |  |                 |
    | Bias awareness |       |                   |
    | Decision authority |   |                   |

2.3 Training Requirements

    | Training Module | Duration | Frequency | Certification |
    |----------------|----------|-----------|---------------|
    | System operation |        |           |               |
    | Output interpretation |   |           |               |
    | Override procedures |     |           |               |
    | Bias awareness |         |           |               |
    | Incident reporting |     |           |               |

2.4 Training Records
    - Training records maintained by:
    - Training effectiveness assessment method:
    - Recertification period:

───────────────────────────────────────────────────────────────────
3. MONITORING PROCEDURES
───────────────────────────────────────────────────────────────────

3.1 Monitoring Interface
    - Dashboard description:
    - Key indicators displayed:
    - Alert mechanism:
    - Real-time vs batch monitoring:

3.2 Key Performance Indicators

    | KPI | Description | Threshold | Alert Level |
    |-----|------------|-----------|------------|
    |     |            |           |            |

3.3 Review Procedures
    - Review frequency: [Real-time / Hourly / Daily / Weekly]
    - Sample review rate: [percentage of decisions reviewed]
    - Review documentation requirements:
    - Quality assurance for reviews:

───────────────────────────────────────────────────────────────────
4. INTERVENTION PROCEDURES
───────────────────────────────────────────────────────────────────

4.1 Override Mechanism
    - How to override a system decision:
    - Override authority levels:
    - Override documentation requirements:
    - Override logging:

4.2 Stop / Shutdown Procedure
    - Emergency stop mechanism: [Button location / Command / API]
    - Graceful shutdown procedure:
    - Emergency shutdown procedure:
    - System state after shutdown:
    - Restart procedure:

4.3 Decision Reversal Process
    - How to reverse a system decision:
    - Time window for reversal:
    - Notification to affected persons:
    - Documentation requirements:

4.4 Escalation Path

    | Trigger | Escalation To | Response Time | Action |
    |---------|--------------|---------------|--------|
    |         |              |               |        |

───────────────────────────────────────────────────────────────────
5. AUTOMATION BIAS SAFEGUARDS (Art. 14(4)(b))
───────────────────────────────────────────────────────────────────

5.1 Safeguards Implemented

    | Safeguard | Description | Implementation |
    |-----------|-------------|----------------|
    | Mandatory review | Overseers must actively confirm decisions | |
    | Randomized verification | Random subset requires independent verification | |
    | Confidence display | System confidence shown alongside decisions | |
    | Dissenting information | Counter-evidence actively presented | |
    | Rotation | Overseers rotated to prevent complacency | |
    | Calibration exercises | Regular exercises comparing AI vs correct answers | |

5.2 Effectiveness Measurement
    - How automation bias is measured:
    - Override rate monitoring:
    - Correlation between AI confidence and human agreement:
    - Periodic assessment schedule:

───────────────────────────────────────────────────────────────────
6. RECORD-KEEPING
───────────────────────────────────────────────────────────────────

    - Oversight actions logged: [Yes]
    - Override decisions logged with rationale: [Yes]
    - Review outcomes documented: [Yes]
    - Incident reports linked: [Yes]
    - Retention period:
    - Storage location:

───────────────────────────────────────────────────────────────────
7. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Oversight Coordinator |  |  |  |
    | AI Compliance Officer |  |  |  |
```

---

## Template 6: Post-Market Monitoring Plan

```
═══════════════════════════════════════════════════════════════════
POST-MARKET MONITORING PLAN — AI SYSTEM
Regulation (EU) 2024/1689 — Art. 72
═══════════════════════════════════════════════════════════════════

Document ID:        [PMP-XXXX-VX.X]
AI System:          [System name and version]
Monitoring Lead:    [Name, Title]
Date:               [DD/MM/YYYY]
Document Status:    [Draft / Under Review / Approved]

───────────────────────────────────────────────────────────────────
1. MONITORING SCOPE
───────────────────────────────────────────────────────────────────

    - AI system(s) covered:
    - Monitoring start date:
    - Geographic scope:
    - Number of deployers:
    - Estimated number of affected persons:

───────────────────────────────────────────────────────────────────
2. DATA COLLECTION
───────────────────────────────────────────────────────────────────

2.1 Data Sources

    | Source | Data Type | Collection Method | Frequency |
    |--------|-----------|------------------|-----------|
    | System logs | Performance metrics | Automated | Continuous |
    | Deployer feedback | Incident reports, complaints | Manual | As received |
    | User feedback | Satisfaction, accuracy | Survey | Quarterly |
    | Market surveillance | Authority communications | Manual | As received |
    | Scientific literature | New risks, state of art | Manual review | Semi-annual |
    | Media monitoring | Public reports, incidents | Automated | Continuous |

2.2 Performance Metrics Monitored

    | Metric | Baseline | Alert Threshold | Critical Threshold | Frequency |
    |--------|----------|----------------|-------------------|-----------|
    | Accuracy |         |                |                   |           |
    | Fairness |         |                |                   |           |
    | Drift   |          |                |                   |           |
    | Latency |          |                |                   |           |
    | Error rate |       |                |                   |           |

───────────────────────────────────────────────────────────────────
3. ANALYSIS PROCEDURES
───────────────────────────────────────────────────────────────────

    - Performance trend analysis: [Method, frequency]
    - Bias monitoring analysis: [Method, frequency]
    - Drift detection: [Method, frequency]
    - Root cause analysis for anomalies: [Method]
    - Cross-system interaction analysis: [Method]

───────────────────────────────────────────────────────────────────
4. RISK MANAGEMENT INTEGRATION
───────────────────────────────────────────────────────────────────

    - Trigger for risk management update:
    - Process for updating risk assessment with new data:
    - Feedback loop to development team:
    - Change management for system modifications:

───────────────────────────────────────────────────────────────────
5. INCIDENT REPORTING (Art. 73)
───────────────────────────────────────────────────────────────────

    - Serious incident definition: [Reference Art. 3(49)]
    - Reporting deadline: 15 days from awareness
    - Reporting authority: [Market surveillance authority]
    - Report format: [Reference to Incident Reporting Template]
    - Responsible person:
    - Escalation procedure:

───────────────────────────────────────────────────────────────────
6. CORRECTIVE ACTIONS
───────────────────────────────────────────────────────────────────

    | Trigger | Corrective Action | Timeline | Authority |
    |---------|------------------|----------|-----------|
    | Performance below threshold | Investigation + remediation | 30 days | Monitoring Lead |
    | Bias exceeding threshold | Bias mitigation + revalidation | 60 days | Data Governance Lead |
    | Serious incident | Immediate corrective action | Immediate | AI Compliance Officer |
    | Regulatory non-compliance | Compliance remediation | Per authority | AI Compliance Officer |

───────────────────────────────────────────────────────────────────
7. REPORTING
───────────────────────────────────────────────────────────────────

    | Report | Audience | Frequency | Content |
    |--------|----------|-----------|---------|
    | Monitoring dashboard | Operations team | Real-time | KPIs, alerts |
    | Monthly monitoring report | AI Compliance | Monthly | Trends, incidents, actions |
    | Management review | Leadership | Quarterly | Summary, risks, recommendations |
    | Annual post-market report | Authority (if required) | Annual | Comprehensive review |

───────────────────────────────────────────────────────────────────
8. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Monitoring Lead |  |  |  |
    | AI Compliance Officer |  |  |  |
    | Quality Manager |  |  |  |
```

---

## Template 7: Incident Reporting Template

```
═══════════════════════════════════════════════════════════════════
AI SYSTEM INCIDENT REPORT
Regulation (EU) 2024/1689 — Art. 73
═══════════════════════════════════════════════════════════════════

REPORTING DEADLINE: 15 days from becoming aware of serious incident

───────────────────────────────────────────────────────────────────
1. INCIDENT IDENTIFICATION
───────────────────────────────────────────────────────────────────

    Incident ID:          [IR-XXXX]
    Report Date:          [DD/MM/YYYY]
    Date of Awareness:    [DD/MM/YYYY]
    Date of Occurrence:   [DD/MM/YYYY]
    Reporting Deadline:   [DD/MM/YYYY — 15 days from awareness]
    Report Type:          [ ] Initial  [ ] Follow-up  [ ] Final
    Report Status:        [Submitted / Acknowledged / Under review]

───────────────────────────────────────────────────────────────────
2. REPORTER INFORMATION
───────────────────────────────────────────────────────────────────

    Reporter Role:        [ ] Provider  [ ] Deployer  [ ] Authorised Rep
    Organisation:         [Legal name]
    Contact Person:       [Name]
    Contact Email:        [Email]
    Contact Phone:        [Phone]
    Address:              [Address]

───────────────────────────────────────────────────────────────────
3. AI SYSTEM IDENTIFICATION
───────────────────────────────────────────────────────────────────

    System Name:          [Name]
    System Version:       [Version]
    Provider:             [Provider name]
    EU Database ID:       [Registration number]
    Risk Classification:  [HIGH-RISK]
    Annex III Category:   [Category number]
    CE Marking:           [ ] Yes  [ ] No
    Notified Body:        [Name and number, if applicable]

───────────────────────────────────────────────────────────────────
4. INCIDENT DESCRIPTION
───────────────────────────────────────────────────────────────────

4.1 Summary
    [Clear, concise description of what happened]

4.2 Serious Incident Classification
    The incident involves: (select all that apply)
    [ ] Death of a natural person
    [ ] Serious damage to health of a natural person
    [ ] Serious and irreversible disruption of critical infrastructure
    [ ] Breach of fundamental rights obligations
    [ ] Serious damage to property
    [ ] Serious damage to the environment

4.3 Detailed Description
    - Sequence of events:
    - AI system behaviour during incident:
    - System inputs at time of incident:
    - System outputs at time of incident:
    - Human oversight actions taken:
    - Environmental conditions:

4.4 Root Cause (known or suspected)
    [ ] Model error / incorrect prediction
    [ ] Data quality issue
    [ ] System malfunction / software bug
    [ ] Adversarial attack / manipulation
    [ ] Misuse by deployer / user
    [ ] Environmental factor
    [ ] Unknown
    Description:

───────────────────────────────────────────────────────────────────
5. IMPACT ASSESSMENT
───────────────────────────────────────────────────────────────────

5.1 Persons Affected
    - Number of persons affected:
    - Categories of affected persons:
    - Vulnerable groups affected:
    - Severity of harm:

5.2 Geographic Scope
    - Member states where incident occurred:
    - Member states where system is deployed:

5.3 Ongoing Risk
    - Is the risk ongoing? [ ] Yes  [ ] No
    - Likelihood of recurrence:
    - Number of similar systems potentially affected:

───────────────────────────────────────────────────────────────────
6. IMMEDIATE CORRECTIVE ACTIONS
───────────────────────────────────────────────────────────────────

    | Action | Date Implemented | Status | Effectiveness |
    |--------|-----------------|--------|---------------|
    |        |                 |        |               |

    System status: [ ] Operating normally  [ ] Operating with restrictions
                   [ ] Suspended  [ ] Withdrawn from market

───────────────────────────────────────────────────────────────────
7. PLANNED CORRECTIVE ACTIONS
───────────────────────────────────────────────────────────────────

    | Action | Target Date | Responsible | Status |
    |--------|------------|-------------|--------|
    |        |            |             |        |

───────────────────────────────────────────────────────────────────
8. NOTIFICATIONS
───────────────────────────────────────────────────────────────────

    | Authority / Body | Date Notified | Reference Number |
    |-----------------|---------------|-----------------|
    | Market surveillance authority ([Country]) |  |  |
    | Notified body (if applicable) |  |  |
    | Data protection authority (if personal data) |  |  |
    | Deployers |  |  |

───────────────────────────────────────────────────────────────────
9. ATTACHMENTS
───────────────────────────────────────────────────────────────────

    [ ] System logs from incident period
    [ ] Error reports
    [ ] Photographs / screenshots
    [ ] Witness statements
    [ ] Medical reports (if applicable)
    [ ] Technical analysis report
    [ ] Other: ____________

───────────────────────────────────────────────────────────────────
10. DECLARATION
───────────────────────────────────────────────────────────────────

    I confirm that the information provided is accurate and complete
    to the best of my knowledge.

    Name:
    Title:
    Signature:
    Date:
```

---

## Template 8: Fundamental Rights Impact Assessment

```
═══════════════════════════════════════════════════════════════════
FUNDAMENTAL RIGHTS IMPACT ASSESSMENT (FRIA)
Regulation (EU) 2024/1689 — Art. 27
═══════════════════════════════════════════════════════════════════

Required for: Deployers that are public bodies or private entities
              providing public services, using high-risk AI systems

Document ID:        [FRIA-XXXX-VX.X]
AI System:          [System name and version]
Deployer:           [Organisation name]
Assessment Lead:    [Name, Title]
Date:               [DD/MM/YYYY]
Document Status:    [Draft / Under Review / Approved / Submitted]

───────────────────────────────────────────────────────────────────
1. DEPLOYER PROCESSES (Art. 27(1)(a))
───────────────────────────────────────────────────────────────────

1.1 Description of Use
    - Business process where AI system is used:
    - Role of AI system in the process:
    - Decision types supported by the system:
    - Human involvement in decision process:
    - Volume of decisions processed:

1.2 Operational Context
    - Department / unit using the system:
    - Geographic deployment:
    - Regulatory context:
    - Public service nature of the use:

───────────────────────────────────────────────────────────────────
2. USAGE PARAMETERS (Art. 27(1)(b))
───────────────────────────────────────────────────────────────────

    - Period of intended use: [Start date — End date / Ongoing]
    - Frequency of use: [Continuous / Daily / Weekly / As needed]
    - Volume: [Number of decisions per period]
    - Geographic scope: [Cities / Regions / National]

───────────────────────────────────────────────────────────────────
3. AFFECTED PERSONS AND GROUPS (Art. 27(1)(c))
───────────────────────────────────────────────────────────────────

3.1 Categories of Affected Persons

    | Category | Estimated Number | Vulnerability Factors | Exposure Level |
    |----------|-----------------|----------------------|----------------|
    |          |                 |                      | [High/Med/Low] |

3.2 Specific Groups Likely to Be Affected

    | Group | Why Affected | Potential Disproportionate Impact | Mitigation |
    |-------|-------------|----------------------------------|------------|
    | Children / minors |  |  |  |
    | Elderly persons |    |  |  |
    | Persons with disabilities | |  |  |
    | Ethnic minorities |  |  |  |
    | Low-income persons | |  |  |
    | Migrants / refugees | |  |  |
    | [Other groups]     |  |  |  |

───────────────────────────────────────────────────────────────────
4. SPECIFIC RISKS OF HARM (Art. 27(1)(d))
───────────────────────────────────────────────────────────────────

4.1 Fundamental Rights Risk Assessment

    | Right | Risk Description | Affected Groups | Likelihood | Severity | Risk Level |
    |-------|-----------------|-----------------|------------|----------|------------|
    | **Human dignity** (Art. 1 CFR) |  |  |  |  |  |
    | **Right to life** (Art. 2 CFR) |  |  |  |  |  |
    | **Integrity of the person** (Art. 3 CFR) |  |  |  |  |  |
    | **Respect for private life** (Art. 7 CFR) |  |  |  |  |  |
    | **Protection of personal data** (Art. 8 CFR) |  |  |  |  |  |
    | **Non-discrimination** (Art. 21 CFR) |  |  |  |  |  |
    | **Equality between women and men** (Art. 23 CFR) |  |  |  |  |  |
    | **Rights of the child** (Art. 24 CFR) |  |  |  |  |  |
    | **Integration of persons with disabilities** (Art. 26 CFR) |  |  |  |  |  |
    | **Right to an effective remedy** (Art. 47 CFR) |  |  |  |  |  |
    | **Right to good administration** (Art. 41 CFR) |  |  |  |  |  |
    | **Freedom of expression** (Art. 11 CFR) |  |  |  |  |  |
    | **Freedom of assembly** (Art. 12 CFR) |  |  |  |  |  |
    | **Right to education** (Art. 14 CFR) |  |  |  |  |  |
    | **Workers' rights** (Art. 27-32 CFR) |  |  |  |  |  |
    | **Consumer protection** (Art. 38 CFR) |  |  |  |  |  |

    CFR = Charter of Fundamental Rights of the European Union

4.2 Cumulative and Systemic Risks
    - Risk of cumulative impact across multiple uses:
    - Risk of systemic discrimination:
    - Risk of chilling effects on rights exercise:

───────────────────────────────────────────────────────────────────
5. HUMAN OVERSIGHT MEASURES (Art. 27(1)(e))
───────────────────────────────────────────────────────────────────

    - Oversight level implemented:
    - Oversight personnel qualifications:
    - Override procedures:
    - Escalation procedures:
    - Automation bias safeguards:
    - Assessment of oversight adequacy:

───────────────────────────────────────────────────────────────────
6. RISK MITIGATION MEASURES (Art. 27(1)(f))
───────────────────────────────────────────────────────────────────

    | Risk Identified | Mitigation Measure | Implementation Status | Effectiveness |
    |----------------|-------------------|----------------------|---------------|
    |                |                   |                      |               |

    - Additional safeguards for vulnerable groups:
    - Accessibility measures:
    - Information provided to affected persons:
    - Alternative (non-AI) pathway available: [ ] Yes  [ ] No
      If yes, describe:

───────────────────────────────────────────────────────────────────
7. GOVERNANCE AND COMPLAINTS (Art. 27(1)(g))
───────────────────────────────────────────────────────────────────

7.1 Governance Mechanisms
    - Internal governance structure for AI use:
    - Decision-making authority for AI deployment:
    - Regular review schedule:
    - Accountability framework:

7.2 Complaint Mechanisms
    - How affected persons can raise concerns:
    - Complaint handling process:
    - Timeline for complaint resolution:
    - Appeal mechanism:
    - Contact information for complaints:

7.3 Redress
    - How affected persons can seek redress:
    - Types of redress available:
    - Information provided to affected persons about rights:

───────────────────────────────────────────────────────────────────
8. CONCLUSIONS AND DETERMINATION
───────────────────────────────────────────────────────────────────

    - Overall fundamental rights risk level:
      [ ] Low — risks adequately mitigated
      [ ] Medium — residual risks exist with mitigation in place
      [ ] High — significant residual risks; additional measures needed
      [ ] Unacceptable — deployment should not proceed

    - Determination: [ ] Proceed with deployment
                     [ ] Proceed with conditions
                     [ ] Do not proceed

    - Conditions (if applicable):

    - Review and update schedule:

───────────────────────────────────────────────────────────────────
9. MARKET SURVEILLANCE AUTHORITY SUBMISSION
───────────────────────────────────────────────────────────────────

    - Authority name:
    - Submission date:
    - Submission method:
    - Reference number:
    - Authority response (if received):

───────────────────────────────────────────────────────────────────
10. APPROVALS
───────────────────────────────────────────────────────────────────

    | Role | Name | Signature | Date |
    |------|------|-----------|------|
    | Assessment Lead |  |  |  |
    | Legal Counsel |  |  |  |
    | Data Protection Officer |  |  |  |
    | Senior Leadership |  |  |  |
```

---

**Regulation Reference:** Regulation (EU) 2024/1689 — EU Artificial Intelligence Act

**Last Updated:** March 2026

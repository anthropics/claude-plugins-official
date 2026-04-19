---
name: eu-ai-act-specialist
description: >
  EU AI Act (Regulation EU 2024/1689) compliance specialist. Use when
  classifying AI systems by risk tier, assessing provider or deployer
  obligations, evaluating GPAI model compliance, running conformity assessments,
  performing bias detection and fairness testing, building AI governance
  programs, or preparing for EU AI Act enforcement deadlines. Covers the full
  regulatory lifecycle from system inventory through post-market monitoring.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: ai-governance
  updated: 2026-03-31
  tags: [eu-ai-act, ai-governance, risk-classification, gpai, conformity]
---
# EU AI Act Compliance Specialist

Production-ready compliance patterns for Regulation (EU) 2024/1689 -- the EU Artificial Intelligence Act. Covers risk classification, provider/deployer obligations, GPAI model requirements, conformity assessment, and AI governance.

---

## AI System Inventory and Classification Workflow

The agent classifies AI systems under the EU AI Act's risk-based framework and maps applicable obligations.

### Workflow: Classify and Map Obligations

1. **Inventory all AI systems** -- for each system, document: name, provider/developer, description, intended purpose, deployment status, affected persons, geographic scope, data processed, and decision impact level.
2. **Apply classification decision tree** to each system:
   - Does it meet the Art. 3(1) definition of an AI system? If no, document exclusion.
   - Does it fall under a prohibited practice (Art. 5)? If yes, flag as UNACCEPTABLE RISK -- must be discontinued.
   - Is it a safety component of an Annex I product? If yes, HIGH-RISK (product legislation path).
   - Does it fall under an Annex III category? If yes, apply Art. 6(3) exception analysis. If exception does not apply, HIGH-RISK.
   - Does Art. 50 transparency obligation apply? If yes, LIMITED RISK. Otherwise, MINIMAL RISK.
3. **Map obligations** based on classification -- assign compliance owners for each obligation.
4. **Run gap analysis** using `scripts/ai_compliance_checker.py` to identify compliance gaps.
5. **Prioritize remediation** by deadline urgency, penalty severity, and number of affected persons.
6. **Validation checkpoint:** Every AI system classified; prohibited practices flagged for immediate action; high-risk systems have assigned compliance owners and remediation timelines.

### Example: AI System Classification Output

```json
{
  "system_name": "Resume Screener v2.1",
  "provider": "Internal ML Team",
  "intended_purpose": "Screen job applications and rank candidates for recruiter review",
  "ai_act_classification": "HIGH-RISK",
  "classification_rationale": "Annex III Category 4 - Employment: AI for recruitment and screening of job applicants",
  "art_6_3_exception": false,
  "exception_rationale": "System directly influences which candidates proceed to interview stage - not a narrow procedural task",
  "applicable_obligations": [
    "Risk management system (Art. 9)",
    "Data governance (Art. 10)",
    "Technical documentation (Art. 11)",
    "Record-keeping / automatic logging (Art. 12)",
    "Transparency and information to deployers (Art. 13)",
    "Human oversight (Art. 14)",
    "Accuracy, robustness, cybersecurity (Art. 15)",
    "Quality management system (Art. 17)",
    "Conformity assessment (Art. 43)",
    "CE marking (Art. 48)",
    "EU database registration (Art. 49)",
    "Post-market monitoring (Art. 72)"
  ],
  "compliance_deadline": "2026-08-02",
  "assigned_owner": "Head of AI Governance"
}
```

---

## Risk Classification System

The AI Act uses a risk-based approach with four tiers.

### Tier 1: Prohibited Practices (Art. 5) -- Banned from 2 February 2025

| Prohibited Practice | Article |
|---------------------|---------|
| Social scoring by public authorities | Art. 5(1)(c) |
| Real-time remote biometric identification in public spaces (with narrow exceptions) | Art. 5(1)(h) |
| Emotion recognition in workplace and education (except medical/safety) | Art. 5(1)(f) |
| Individual predictive policing based solely on profiling | Art. 5(1)(d) |
| Exploitation of vulnerabilities (age, disability, social/economic situation) | Art. 5(1)(b) |
| Subliminal manipulation causing significant harm | Art. 5(1)(a) |
| Untargeted facial image scraping for recognition databases | Art. 5(1)(e) |
| Biometric categorization by sensitive attributes (race, religion, etc.) | Art. 5(1)(g) |

### Tier 2: High-Risk AI Systems (Art. 6, Annex III)

An AI system is high-risk if it falls under Annex III categories OR is a safety component of a product covered by Annex I harmonization legislation.

**Annex III Categories:**

| # | Category | Examples |
|---|----------|----------|
| 1 | Biometric identification and categorization | Remote biometric ID, emotion recognition |
| 2 | Critical infrastructure management | Road traffic, water/gas/electricity supply, digital infrastructure |
| 3 | Education and vocational training | Admissions, learning outcome evaluation, test monitoring |
| 4 | Employment and workers management | Recruitment/screening, promotion/termination, performance monitoring |
| 5 | Essential private and public services | Creditworthiness, insurance risk, public assistance eligibility |
| 6 | Law enforcement | Polygraph, deepfake detection, crime analytics |
| 7 | Migration, asylum, border control | Asylum risk assessment, visa/permit examination |
| 8 | Administration of justice | Judicial fact-finding, election influence |

### Tier 3: Limited Risk -- Transparency Obligations (Art. 50)

| System Type | Transparency Requirement |
|-------------|------------------------|
| Chatbots / AI interacting with persons | Inform person they are interacting with AI |
| Emotion recognition / biometric categorization | Inform exposed persons of system operation |
| Deepfakes / AI-generated content | Disclose AI generation; machine-readable labelling |
| AI-generated text on public interest matters | Disclose AI generation unless editorially reviewed |

### Tier 4: Minimal Risk

No mandatory requirements. Voluntary codes of conduct encouraged (Art. 95).

---

## Provider Obligations for High-Risk AI

Providers of high-risk AI systems must comply with all of the following:

| # | Obligation | Article | Key Requirement |
|---|-----------|---------|-----------------|
| 1 | Risk Management System | Art. 9 | Continuous iterative process throughout lifecycle; test against defined metrics |
| 2 | Data Governance | Art. 10 | Training/validation/testing datasets meet quality, representativeness, and bias criteria |
| 3 | Technical Documentation | Art. 11 | Drawn up before market placement; kept up to date throughout lifecycle |
| 4 | Record-Keeping / Logging | Art. 12 | Automatic recording of events enabling traceability |
| 5 | Transparency | Art. 13 | Instructions for use with capabilities, limitations, and oversight measures |
| 6 | Human Oversight | Art. 14 | Human-in-the-loop, on-the-loop, or in-command depending on risk |
| 7 | Accuracy, Robustness, Cybersecurity | Art. 15 | Appropriate levels declared and maintained; adversarial resilience |
| 8 | Quality Management System | Art. 17 | Documented QMS covering design, development, testing, data management, post-market |
| 9 | Conformity Assessment | Art. 43 | Internal control (Annex VI) or third-party assessment (Annex VII) |
| 10 | CE Marking | Art. 48 | Affix CE marking before market placement |
| 11 | EU Database Registration | Art. 49 | Register in EU database before market placement |
| 12 | Post-Market Monitoring | Art. 72 | Active systematic data collection; serious incident reporting within 15 days |

---

## Deployer Obligations (Art. 26)

| Obligation | Detail |
|-----------|--------|
| Use per instructions | Operate per provider's instructions for use |
| Human oversight | Assign competent, trained, authorized oversight personnel |
| Input data relevance | Ensure input data is relevant and representative |
| Monitoring | Monitor operation; inform provider of risks/incidents |
| Record-keeping | Keep auto-generated logs (minimum 6 months) |
| Inform workers | Notify workers/representatives before deployment of high-risk AI |
| DPIA | Carry out GDPR Art. 35 data protection impact assessment when required |
| Fundamental Rights Impact Assessment | Required for public bodies / private entities providing public services (Art. 27) |

---

## General-Purpose AI Models (GPAI)

### GPAI Provider Obligations (Art. 53) -- Effective 2 August 2025

| Obligation | Detail |
|-----------|--------|
| Technical documentation | Maintain documentation of model training/testing process |
| Information for downstream | Provide sufficient info for downstream AI system providers |
| Copyright compliance | Comply with EU copyright law; honor opt-out mechanisms |
| Training data summary | Publish detailed summary of training content per AI Office template |
| EU representative | Non-EU providers must appoint EU-based representative |

### Systemic Risk GPAI Models (Art. 51, 55)

Classified as systemic risk if: high impact capabilities, AI Office designation, or trained with >10^25 FLOPs (rebuttable presumption).

**Additional obligations:** Model evaluation with adversarial testing, red-teaming proportionate to risk, systemic risk assessment and mitigation, incident tracking and reporting, cybersecurity protection, energy consumption reporting.

---

## Conformity Assessment Workflow

The agent guides organizations through conformity assessment for high-risk AI systems.

### Workflow: Internal Control (Annex VI)

1. **Establish QMS** per Art. 17 -- document design, development, testing, data management, and post-market monitoring processes.
2. **Compile technical documentation** per Art. 11 -- system description, development process, risk management, data governance, performance metrics.
3. **Implement all Chapter III Section 2 requirements** -- verify each obligation is addressed.
4. **Conduct internal assessment:**
   - Verify risk management system addresses all identified risks (Art. 9)
   - Verify data governance meets Art. 10 requirements
   - Verify technical documentation is complete and current (Art. 11)
   - Verify logging capability (Art. 12)
   - Verify transparency and instructions for use (Art. 13)
   - Verify human oversight design (Art. 14)
   - Verify accuracy, robustness, cybersecurity (Art. 15)
   - Confirm QMS covers all required elements (Art. 17)
5. **Sign EU Declaration of Conformity** (Art. 47), affix CE marking (Art. 48), register in EU database (Art. 49).
6. **Implement post-market monitoring** (Art. 72) and maintain documentation updates.
7. **Validation checkpoint:** All 12 provider obligations verified; declaration signed; CE marking affixed; EU database registration complete; post-market monitoring operational.

### Workflow: Third-Party Assessment (Annex VII)

Required for biometric identification systems (Annex III point 1) and cases where harmonized standards are insufficient.

1. **Complete all internal control steps** above.
2. **Select and engage notified body** with relevant AI system expertise.
3. **QMS assessment** -- notified body reviews and assesses QMS; issues certificate or requires corrective action; annual surveillance.
4. **Technical documentation assessment** -- notified body reviews documentation, tests system, issues type-examination certificate.
5. **Sign EU Declaration of Conformity** with notified body identification number on CE marking.
6. **Maintain ongoing compliance** -- notified body surveillance, notify of significant changes, maintain all documentation.
7. **Validation checkpoint:** Notified body certificates issued; CE marking with NB number affixed; ongoing surveillance scheduled.

---

## Bias Detection and Fairness Testing

The agent performs bias detection per Art. 10 data governance requirements.

### Workflow: Bias Testing

1. **Define protected attributes** -- age, gender, ethnicity, disability, religion, and other relevant characteristics for the system's context.
2. **Analyze data distribution** -- check representation ratios (target: 0.8-1.25 vs. population), class imbalance ratios (>0.5), and coverage of all known groups.
3. **Evaluate outcome fairness** using these metrics:
   - Demographic parity: P(positive outcome) equal across groups (within 80% / four-fifths rule)
   - Equalized odds: TPR and FPR equal across groups (within 80%)
   - Predictive parity: PPV equal across groups (within 80%)
   - Calibration: Predicted probabilities accurate for all groups (within 5pp)
4. **Identify proxy variables** -- check for features correlated with protected attributes.
5. **Implement mitigation** -- data augmentation, re-sampling, re-weighting, adversarial debiasing, threshold adjustment, or reject option classification as appropriate.
6. **Validate** -- re-run analysis to confirm improvement.
7. **Document** -- record all findings, measures taken, and residual bias levels in technical documentation.
8. **Validation checkpoint:** All protected attributes tested; fairness metrics within thresholds or residual bias documented with justification; mitigation measures recorded.

### Example: Bias Detection Command

```bash
# Analyze dataset statistics for bias indicators
python scripts/ai_bias_detector.py --input dataset_stats.json \
  --protected-attributes gender,age_group,ethnicity

# Output as JSON for integration with compliance documentation
python scripts/ai_bias_detector.py --input dataset_stats.json --json
```

---

## Implementation Timeline

| Date | Milestone | Key Requirements |
|------|-----------|-----------------|
| 1 Aug 2024 | Entry into force | Regulation published |
| 2 Feb 2025 | Prohibited practices + AI literacy | Art. 5 prohibitions; Art. 4 AI literacy |
| 2 Aug 2025 | GPAI obligations + governance | Art. 53, 55 GPAI obligations; AI Office operational |
| 2 Aug 2026 | **Full application** | All remaining: high-risk, deployer, transparency, conformity, CE marking |
| 2 Aug 2027 | Extended deadline | Certain Annex I Section B high-risk safety components |

### Penalties (Art. 99)

| Violation Type | Maximum Fine | % Global Turnover |
|---------------|-------------|-------------------|
| Prohibited AI practices | EUR 35 million | 7% (whichever higher) |
| High-risk non-compliance | EUR 15 million | 3% (whichever higher) |
| Misleading information to authorities | EUR 7.5 million | 1% (whichever higher) |

SMEs and startups receive proportionate treatment (lower of absolute or percentage).

---

## AI Model Documentation Templates

### Template: AI System Description

```
AI SYSTEM DESCRIPTION
=====================
System Name:
Version:
Provider:
Date:

1. GENERAL INFORMATION
   - Intended purpose:
   - Target users (deployers):
   - Affected persons:
   - Geographic scope:
   - AI Act classification:
   - Annex III category (if applicable):

2. TECHNICAL ARCHITECTURE
   - Model type:
   - Input data modalities:
   - Output description:
   - Key design choices and rationale:

3. TRAINING AND DATA
   - Training data sources:
   - Data volume and characteristics:
   - Data preparation methods:
   - Bias examination results:

4. PERFORMANCE
   - Accuracy metrics:
   - Robustness testing results:
   - Known limitations:
   - Performance across demographic groups:

5. HUMAN OVERSIGHT
   - Oversight level: [human-in-the-loop / on-the-loop / in-command]
   - Override mechanism:
   - Automation bias safeguards:
```

### Template: Risk Management Documentation

```
RISK MANAGEMENT SYSTEM -- AI SYSTEM
====================================
System Name:
Version:
Risk Management Lead:
Date:

1. RISK IDENTIFICATION
   | Risk ID | Description | Likelihood | Severity | Risk Level |
   |---------|-------------|------------|----------|------------|
   | R-001   |             |            |          |            |

2. RISK CONTROL MEASURES
   | Risk ID | Measure | Type | Verification | Status |
   |---------|---------|------|-------------|--------|
   | R-001   |         |      |             |        |

3. RESIDUAL RISK ASSESSMENT
   - Acceptability determination:
   - Overall risk-benefit analysis:

4. POST-MARKET DATA INTEGRATION
   - Review frequency:
   - Trigger conditions for update:
```

---

## Tools

### AI Risk Classifier

```bash
# Classify AI system from JSON description
python scripts/ai_risk_classifier.py --input system_description.json

# Classify from inline JSON
python scripts/ai_risk_classifier.py --inline '{
  "name": "Resume Screener",
  "description": "AI system that screens job applications and ranks candidates",
  "domain": "employment",
  "uses_biometrics": false,
  "decision_type": "automated_with_review",
  "affected_persons": "job applicants",
  "eu_deployment": true
}'

# JSON output for programmatic use
python scripts/ai_risk_classifier.py --input system.json --json
```

### AI Compliance Checker

```bash
# Full compliance check with gap analysis
python scripts/ai_compliance_checker.py --input compliance_status.json

# Check deployer obligations only
python scripts/ai_compliance_checker.py --input compliance_status.json --role deployer

# JSON output with remediation steps
python scripts/ai_compliance_checker.py --input compliance_status.json --json
```

### AI Bias Detector

```bash
# Analyze dataset for bias indicators mapped to Art. 10
python scripts/ai_bias_detector.py --input dataset_stats.json

# Specify protected attributes explicitly
python scripts/ai_bias_detector.py --input dataset_stats.json \
  --protected-attributes gender,age_group,ethnicity --json
```

---

## Reference Documentation

| Document | Path | Description |
|----------|------|-------------|
| Classification Guide | `references/ai-act-classification-guide.md` | Complete Annex III categories, decision trees, prohibited practices, GPAI classification |
| Governance Framework | `references/ai-governance-framework.md` | Organizational structure, ethics board, model lifecycle, conformity assessment procedures |
| Documentation Templates | `references/ai-technical-documentation-templates.md` | Full templates for system description, risk management, data governance, testing, oversight, post-market monitoring, incident reporting, FRIA |

---

---

## Troubleshooting

| Problem | Possible Cause | Resolution |
|---------|---------------|------------|
| AI system classified as HIGH-RISK but organization believes it qualifies for Art. 6(3) exception | Exception analysis incomplete or domain mapping incorrect | Re-evaluate against all Art. 6(3) exception criteria; the system must perform a narrow procedural task, improve the result of a previously completed human activity, or be purely preparatory; document rationale with legal review |
| Bias detector reports disparate impact but model performs well overall | Aggregated metrics mask subgroup disparities; four-fifths rule violation on specific protected attributes | Analyze per-group positive outcome rates using `--protected-attributes` flag; implement targeted mitigation (re-sampling, threshold adjustment) for affected groups; document residual bias with justification |
| Compliance checker returns low score despite extensive documentation | Documentation exists but key compliance fields marked as incomplete or not up to date | Verify each obligation field in the input JSON reflects current state; ensure `kept_up_to_date` and `lifecycle_coverage` flags are set; update technical documentation per Art. 11 before reassessment |
| System falls under multiple Annex III categories simultaneously | AI system serves multiple domains (e.g., employment + education) | Classify under the highest-risk applicable category; apply the most stringent obligations; document classification rationale for each category |
| GPAI model obligations unclear for downstream provider | Upstream GPAI provider has not supplied sufficient documentation per Art. 53 | Request technical documentation, training data summary, and copyright compliance information from the GPAI provider; if unavailable, document the gap and assess independent obligations |
| Conformity assessment route uncertain (internal vs. third-party) | Biometric identification system or insufficient harmonized standards | Biometric ID systems (Annex III point 1) require third-party assessment (Annex VII); all others may use internal control (Annex VI) unless harmonized standards are unavailable; consult notified body |
| Post-market monitoring shows model performance degradation | Data drift, concept drift, or deployment context changed since initial assessment | Trigger Art. 72 post-market monitoring procedures; report serious incidents within 15 days; update risk management system and technical documentation; consider re-running conformity assessment |

---

## Success Criteria

- **All AI systems inventoried and classified** -- every system assessed against the risk-based framework with documented classification rationale, including Art. 6(3) exception analysis where applicable
- **Prohibited practices identified and discontinued** -- all Art. 5 prohibited practices flagged by February 2, 2025, with documented evidence of discontinuation or lawful exception application
- **High-risk systems fully compliant by August 2, 2026** -- all 12 provider obligations verified, EU Declaration of Conformity signed, CE marking affixed, and EU database registration complete
- **Bias testing completed for all high-risk systems** -- demographic parity, equalized odds, and predictive parity metrics within four-fifths threshold for all protected attributes, or residual bias documented with justification
- **GPAI model obligations met by August 2, 2025** -- technical documentation maintained, downstream provider information supplied, copyright compliance verified, and training data summary published
- **Conformity assessment completed per correct route** -- internal control (Annex VI) or third-party assessment (Annex VII) selected based on system classification, with all certificates issued and filed

---

## Scope & Limitations

**In Scope:**
- AI system risk classification across all four tiers (Prohibited, High-Risk, Limited Risk, Minimal Risk)
- Annex III category analysis and Art. 6(3) exception evaluation
- Provider and deployer obligation mapping with compliance gap analysis
- GPAI model classification including systemic risk determination (10^25 FLOPs threshold)
- Bias detection and fairness testing mapped to Art. 10 data governance requirements
- Conformity assessment workflow guidance (Annex VI internal control and Annex VII third-party)
- Implementation timeline tracking with penalty exposure assessment

**Out of Scope:**
- Actual ML model training, retraining, or adversarial testing -- this skill provides compliance frameworks, not ML engineering tools
- Notified body selection, engagement, or audit execution
- National regulatory sandbox applications or experimental AI system exemptions
- Detailed GPAI Code of Practice implementation beyond obligation mapping
- CE marking physical affixation or EU database registration system interaction
- Legal advice on liability, insurance, or contractual allocation of AI Act obligations

**Important Notes:**
- The EU AI Act compliance deadline of August 2, 2026 for high-risk systems is firm -- organizations should begin classification and gap analysis immediately
- Penalties are severe: up to EUR 35 million or 7% of global turnover for prohibited practices, EUR 15 million or 3% for high-risk non-compliance
- SMEs and startups receive proportionate penalty treatment (lower of absolute or percentage)

---

## Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| `iso42001-ai-management` | ISO 42001 AIMS provides organizational framework for EU AI Act compliance; certification demonstrates Art. 17 QMS | When building AI governance program that satisfies both ISO 42001 and EU AI Act |
| `gdpr-dsgvo-expert` | Art. 10 data governance overlaps with GDPR; high-risk AI systems processing personal data require DPIA per GDPR Art. 35 | When AI system processes personal data and requires combined DPIA + conformity assessment |
| `mdr-745-specialist` | AI medical devices fall under both EU AI Act and MDR; MDR conformity assessment may satisfy AI Act per Art. 120 | When AI-enabled medical device requires dual MDR and AI Act compliance |
| `fda-consultant-specialist` | Cross-jurisdictional AI/ML SaMD compliance mapping between FDA PCCP and EU AI Act | When AI medical device is marketed in both US and EU |
| `infrastructure-compliance-auditor` | Technical security controls supporting Art. 15 accuracy, robustness, and cybersecurity requirements | When validating infrastructure security for deployed high-risk AI systems |

---

## Tool Reference

### ai_risk_classifier.py

Classifies AI systems into EU AI Act risk categories based on a JSON system description.

| Flag | Required | Description |
|------|----------|-------------|
| `--input <file>` | Yes (unless `--inline`) | Path to JSON file containing AI system description |
| `--inline '<json>'` | No | Inline JSON system description for quick classification |
| `--json` | No | Output results in JSON format for programmatic use |
| `--output <file>` | No | Export classification report to specified file path |

**Input Fields:** `name`, `description`, `domain`, `sub_domain`, `uses_biometrics`, `biometric_type`, `biometric_context`, `interacts_with_persons`, `generates_content`, `content_type`, `decision_type`, `affected_persons`, `is_safety_component`, `product_legislation`, `eu_deployment`, `social_scoring`, `manipulates_behavior`, `targets_vulnerable_groups`, `predictive_policing_individual`, `untargeted_scraping`, `is_gpai`, `training_compute_flops`, `critical_infrastructure`, `infrastructure_type`.

### ai_compliance_checker.py

Validates AI system compliance against all provider and deployer obligations with gap analysis.

| Flag | Required | Description |
|------|----------|-------------|
| `--input <file>` | Yes | Path to JSON compliance status file |
| `--role <role>` | No | Check obligations for specific role: `provider` (default) or `deployer` |
| `--json` | No | Output results in JSON format with remediation steps |
| `--output <file>` | No | Export compliance report to specified file path |

**Output:** Overall compliance score (0-100), per-obligation status, gap analysis with Art. references, and prioritized remediation recommendations.

### ai_bias_detector.py

Analyzes dataset statistics for bias indicators mapped to Art. 10 data governance requirements.

| Flag | Required | Description |
|------|----------|-------------|
| `--input <file>` | Yes | Path to JSON file with dataset statistics (demographics, outcomes, correlations) |
| `--protected-attributes <attrs>` | No | Comma-separated list of protected attributes to analyze (e.g., `gender,age_group,ethnicity`) |
| `--json` | No | Output results in JSON format |
| `--output <file>` | No | Export bias assessment report to specified file path |

**Thresholds:** Representation ratio 0.8-1.25 (within 20% of population), class imbalance >0.5, four-fifths rule (0.8) for disparate impact, proxy correlation >0.5 for proxy variable detection.

---

**Regulation Reference:** Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024
**Last Updated:** March 2026
**Version:** 1.0.0

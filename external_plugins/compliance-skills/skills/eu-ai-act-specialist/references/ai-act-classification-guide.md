# EU AI Act Classification Guide

Complete reference for classifying AI systems under Regulation (EU) 2024/1689. Covers Annex III high-risk categories, prohibited practices, GPAI model classification, and sector-specific guidance.

---

## Table of Contents

- [Classification Decision Tree](#classification-decision-tree)
- [Prohibited Practices — Complete Definitions](#prohibited-practices--complete-definitions)
- [Annex III High-Risk Categories — Detailed Reference](#annex-iii-high-risk-categories--detailed-reference)
- [Art. 6(3) Exception Analysis](#art-63-exception-analysis)
- [GPAI Model Classification](#gpai-model-classification)
- [Systemic Risk Assessment Methodology](#systemic-risk-assessment-methodology)
- [Software as Medical Device (SaMD) Classification](#software-as-medical-device-samd-classification)
- [AI in Regulated Sectors Mapping](#ai-in-regulated-sectors-mapping)
- [Classification Examples](#classification-examples)

---

## Classification Decision Tree

### Master Decision Flow

```
START: Does the system meet the Art. 3(1) definition of an AI system?
│
├── NO → OUT OF SCOPE
│   Document: Why the system does not meet the AI system definition
│   (e.g., simple rule-based logic, traditional software, basic automation)
│
└── YES → STEP 1: Check Prohibited Practices (Art. 5)
    │
    ├── System falls under Art. 5 prohibition
    │   → UNACCEPTABLE RISK
    │   Action: Discontinue immediately. Penalties up to EUR 35M / 7% turnover.
    │   Exception analysis: Check if narrow exceptions apply (Art. 5(2)-(4))
    │
    └── No prohibited practice
        │
        → STEP 2: Check Annex I (EU harmonisation legislation)
        │
        ├── System IS a safety component of a product covered by Annex I
        │   → HIGH-RISK (product legislation path)
        │   Assessment: Follow conformity assessment of the relevant product legislation
        │   Note: Annex I Section A → applies from Aug 2026
        │         Annex I Section B → applies from Aug 2027
        │
        └── System is NOT a safety component of Annex I product
            │
            → STEP 3: Check Annex III categories
            │
            ├── System falls under an Annex III category
            │   │
            │   → STEP 3a: Art. 6(3) exception analysis
            │   │
            │   ├── ALL four conditions met AND no significant risk
            │   │   → NOT HIGH-RISK
            │   │   Action: Document the exception determination and rationale
            │   │   Note: System may still have transparency obligations (Step 4)
            │   │
            │   └── Exception does NOT apply
            │       → HIGH-RISK
            │       Action: Full Chapter III Section 2 obligations apply
            │
            └── System does NOT fall under Annex III
                │
                → STEP 4: Check transparency obligations (Art. 50)
                │
                ├── System has transparency obligations
                │   → LIMITED RISK
                │   Action: Implement required disclosures
                │
                └── No transparency obligations
                    → MINIMAL RISK
                    Action: No mandatory requirements; voluntary codes encouraged
```

### Is It an AI System? (Art. 3(1) Analysis)

A system qualifies as an AI system if ALL of the following are true:

| Criterion | Question | Examples |
|-----------|----------|----------|
| **Machine-based** | Is it a machine-based system? | Software, hardware, hybrid systems |
| **Varying autonomy** | Does it operate with varying levels of autonomy? | From fully automated to human-supervised |
| **Adaptiveness** | May it exhibit adaptiveness after deployment? | Learning, updating, adjusting behaviour |
| **Inference** | Does it infer from input how to generate outputs? | Statistical inference, pattern recognition, optimization |
| **Output generation** | Does it generate predictions, content, recommendations, or decisions? | Classifications, text, images, scores, actions |
| **Environment influence** | Can outputs influence physical or virtual environments? | Decisions affecting people, controlling systems, generating content |

**Systems that are typically NOT AI systems:**
- Simple if/then rule engines with no learning component
- Traditional database queries
- Basic calculators or spreadsheet formulas
- Static template-based content generation
- Conventional cybersecurity tools (firewalls, antivirus signatures)

---

## Prohibited Practices — Complete Definitions

### 1. Subliminal Manipulation (Art. 5(1)(a))

**Prohibited:** AI systems that deploy subliminal techniques beyond a person's consciousness, or purposefully manipulative or deceptive techniques, with the objective or effect of materially distorting behaviour causing or likely to cause significant harm.

**Key elements:**
- Techniques operate below conscious awareness OR are purposefully manipulative/deceptive
- Objective or effect (not just intent) of materially distorting behaviour
- Causes or is likely to cause significant harm (physical, psychological, financial)

**Examples:**
- Subliminal visual/audio stimuli in AI-generated content designed to influence purchasing
- AI systems using dark patterns that exploit cognitive biases to manipulate decisions
- Personalized psychological manipulation at scale

**NOT prohibited:**
- Standard recommendation systems (unless they cross into manipulation)
- A/B testing with transparent variations
- AI-assisted marketing that does not use subliminal techniques

### 2. Exploitation of Vulnerabilities (Art. 5(1)(b))

**Prohibited:** AI systems exploiting vulnerabilities due to age, disability, or specific social or economic situation, with the objective or effect of materially distorting behaviour causing significant harm.

**Key elements:**
- Targets vulnerability related to age, disability, or socioeconomic situation
- Exploits (not merely affects) the vulnerability
- Materially distorts behaviour
- Causes significant harm

**Examples:**
- AI targeting elderly persons with deceptive financial products
- AI exploiting children's developmental vulnerabilities in gaming/social media
- AI targeting persons with cognitive disabilities with manipulative content
- Predatory lending AI targeting economically vulnerable communities

### 3. Social Scoring (Art. 5(1)(c))

**Prohibited:** AI systems used by public authorities (or on their behalf) evaluating or classifying natural persons over a period based on social behaviour or personal/personality characteristics, where the social score leads to detrimental or unfavourable treatment that is unjustified or disproportionate.

**Key elements:**
- Used by or on behalf of public authorities
- Evaluates/classifies persons based on social behaviour or personal traits
- Creates a social score
- Score leads to detrimental treatment in unrelated contexts, or treatment disproportionate to the behaviour

**Examples:**
- Government citizen scoring systems affecting access to services
- Public authority systems denying benefits based on social media behaviour
- Municipal systems scoring residents for civic compliance

### 4. Individual Predictive Policing (Art. 5(1)(d))

**Prohibited:** AI systems making risk assessments of natural persons to assess or predict the risk of committing a criminal offence, based solely on profiling or personality traits.

**Key elements:**
- Risk assessment for predicting criminal offending
- Based solely on profiling or personality traits
- Not based on objective, verifiable facts directly linked to criminal activity
- Individual-level prediction (not aggregate crime analytics)

**NOT prohibited:**
- AI supporting investigation of specific criminal activity
- Crime pattern analysis (geographic, temporal) not targeting individuals
- AI assessing evidence in active investigations

### 5. Untargeted Facial Image Scraping (Art. 5(1)(e))

**Prohibited:** AI systems creating or expanding facial recognition databases through untargeted scraping of facial images from the internet or CCTV footage.

**Key elements:**
- Creates or expands a facial recognition database
- Uses untargeted scraping (not specific, lawful collection)
- Sources: internet or CCTV footage

### 6. Emotion Recognition in Workplace/Education (Art. 5(1)(f))

**Prohibited:** AI systems inferring emotions in the workplace or educational institutions, except where for medical or safety reasons.

**Key elements:**
- Infers emotions of natural persons
- Context: workplace or educational institution
- Exception: medical reasons (e.g., detecting fatigue in safety-critical roles) or safety reasons

**Examples (prohibited):**
- Employee sentiment monitoring during meetings
- Student attention/engagement detection during lectures
- Job interview emotion analysis

**Examples (permitted exceptions):**
- Fatigue detection for commercial vehicle drivers (safety)
- Medical monitoring of patient emotional state during therapy

### 7. Biometric Categorization by Sensitive Attributes (Art. 5(1)(g))

**Prohibited:** AI systems categorizing natural persons based on biometric data to deduce race, political opinions, trade union membership, religious or philosophical beliefs, sex life, or sexual orientation.

**Exception:** Labelling or filtering of lawfully acquired biometric data in the area of law enforcement.

### 8. Real-Time Remote Biometric Identification in Public Spaces (Art. 5(1)(h))

**Prohibited:** Use of real-time remote biometric identification systems in publicly accessible spaces for law enforcement purposes.

**Narrow exceptions (Art. 5(2))** — only if strictly necessary for one of:
- Targeted search for specific victims (abduction, trafficking, sexual exploitation)
- Prevention of specific, substantial, imminent threat to life or physical safety, or genuine and present/foreseeable threat of a terrorist attack
- Identification of suspects for specific serious criminal offences (Art. 5(3) list)

**Safeguards for exceptions:**
- Prior judicial or independent administrative authorisation required
- Limited in time, geographic scope, and number of persons
- Cannot be used for other purposes once identified

---

## Annex III High-Risk Categories — Detailed Reference

### Category 1: Biometric Identification and Categorisation

**Scope:** AI systems intended for:

| Sub-category | Description | High-Risk? |
|-------------|-------------|------------|
| Remote biometric identification | Identifying natural persons at a distance by comparing biometric data to reference database | YES (except real-time public law enforcement, which is prohibited) |
| Biometric categorisation | Assigning persons to specific categories based on biometric data | YES (except by sensitive attributes, which is prohibited) |
| Emotion recognition | Inferring emotional state from biometric data | YES (except workplace/education, which is prohibited; except medical/safety, which is permitted) |

**Examples:**
- Airport facial recognition for boarding verification
- Access control using fingerprint/iris recognition
- Customer emotion analysis in retail settings
- Age verification using facial analysis

### Category 2: Critical Infrastructure

**Scope:** AI systems intended as safety components in the management and operation of:

| Infrastructure Type | Examples |
|--------------------|----------|
| Road traffic | Autonomous vehicle systems, traffic management AI, smart traffic signals |
| Water supply | Water treatment optimization, distribution network management, contamination detection |
| Gas supply | Pipeline monitoring, leak detection, distribution optimization |
| Heating supply | District heating optimization, demand prediction |
| Electricity supply | Grid management, load balancing, fault prediction, smart meter analytics |
| Digital infrastructure | Network management AI, cybersecurity AI for critical systems |

**Key qualifier:** The AI must be a SAFETY COMPONENT — meaning its failure or malfunction would endanger safety.

### Category 3: Education and Vocational Training

**Scope:** AI systems intended to be used for:

| Use Case | Description |
|----------|-------------|
| Admission decisions | AI determining or significantly influencing access to educational institutions |
| Learning outcome evaluation | AI assessing student performance, grading exams, evaluating competencies |
| Education level assessment | AI determining the appropriate level of education for a person |
| Proctoring | AI monitoring and detecting prohibited behaviour during tests and exams |

**Examples:**
- University admission scoring algorithms
- Automated essay grading systems
- AI-powered exam proctoring with behaviour analysis
- Adaptive learning systems that determine student placement levels
- AI recommending educational pathways based on student data

### Category 4: Employment and Worker Management

**Scope:** AI systems intended to be used for:

| Use Case | Description |
|----------|-------------|
| Recruitment and selection | Screening, filtering, evaluating candidates in recruitment, placing targeted job advertisements |
| Promotion and termination | Making decisions affecting terms of work-related relationships, promotion, or termination |
| Task allocation | Allocating tasks based on individual behaviour, personal traits, or characteristics |
| Performance monitoring | Monitoring and evaluating performance and behaviour of workers |

**Examples:**
- CV/resume screening algorithms
- Video interview analysis AI
- Employee performance prediction systems
- Workforce scheduling AI based on behavioural patterns
- Productivity monitoring with AI-driven analysis
- AI-assisted hiring/firing decision support

### Category 5: Essential Services

**Scope:** AI systems intended to be used for:

| Use Case | Description |
|----------|-------------|
| Creditworthiness assessment | Evaluating creditworthiness or establishing credit scores (except fraud detection) |
| Insurance risk assessment | Risk assessment and pricing for life and health insurance |
| Public benefits eligibility | Evaluating eligibility for public assistance benefits and services, or granting/reducing/revoking such benefits |
| Emergency dispatch | Evaluating and classifying emergency calls, or dispatching/prioritizing emergency first response services (police, fire, medical) |

**Examples:**
- AI credit scoring models
- Insurance underwriting AI for life/health policies
- Social welfare eligibility determination systems
- Emergency 911/112 call prioritization AI
- AI fraud detection in financial services (NOT high-risk — explicit exception)

### Category 6: Law Enforcement

**Scope:** AI systems intended to be used by law enforcement authorities for:

| Use Case | Description |
|----------|-------------|
| Polygraph/emotion detection | Detecting emotional state, assessing truthfulness (not real-time biometric ID) |
| Deepfake detection | Detecting AI-generated or manipulated content in criminal investigations |
| Risk assessment | Assessing risk of criminal offending or reoffending |
| Profiling | Profiling persons during detection, investigation, or prosecution of criminal offences |
| Crime analytics | Analysing patterns, trends, and relationships in data for criminal investigation |

### Category 7: Migration, Asylum, and Border Control

**Scope:** AI systems intended to be used by public authorities or on their behalf for:

| Use Case | Description |
|----------|-------------|
| Asylum risk assessment | Assessing risk related to irregular migration or health risk |
| Application examination | Examining applications for visas, residence permits, asylum |
| Identification | Identifying persons during border checks (not document verification) |
| Polygraph in asylum | Assessing truthfulness of asylum seekers |

### Category 8: Administration of Justice and Democratic Processes

**Scope:**

| Use Case | Description |
|----------|-------------|
| Judicial assistance | AI assisting judicial authorities in researching and interpreting facts and the law, and in applying the law to concrete facts |
| Democratic processes | AI intended to influence the outcome of an election or referendum (not including AI-generated content that does not directly interact with voters) |

---

## Art. 6(3) Exception Analysis

An AI system that falls under Annex III may still be classified as NOT high-risk if the provider determines it does not pose a significant risk to health, safety, or fundamental rights, AND the system performs **one of the following**:

### Exception Conditions (must meet at least one)

| Condition | Description |
|-----------|-------------|
| **Narrow procedural task** | Performs a narrow procedural task — a single, well-defined step in a broader process |
| **Improves prior human activity** | Improves the result of a previously completed human activity |
| **Detects decision patterns** | Detects decision-making patterns or deviations without replacing or influencing human assessment |
| **Preparatory task** | Performs a preparatory task to an assessment relevant to an Annex III use case |

### Additional Requirement

The AI system must NOT pose a significant risk of harm to health, safety, or fundamental rights of natural persons, including by not materially influencing the outcome of decision-making.

### Documentation Requirement

If a provider determines an Annex III system is not high-risk under Art. 6(3):
1. **Document the determination** and the rationale before placing on market
2. **Notify** the relevant market surveillance authority with the documentation
3. **Register** in the EU database with the determination

### Examples

| System | Annex III Category | Exception? | Rationale |
|--------|-------------------|------------|-----------|
| AI spell-checker for employee emails | Employment (4) | YES — narrow procedural task | Corrects spelling, does not influence employment decisions |
| AI that organizes CVs alphabetically | Employment (4) | YES — preparatory task | Organizes but does not screen, rank, or filter candidates |
| AI scoring candidates by skills match | Employment (4) | NO | Directly influences recruitment decision |
| AI formatting legal case documents | Justice (8) | YES — narrow procedural task | Formats documents, does not interpret law |
| AI predicting case outcomes for judges | Justice (8) | NO | Directly influences judicial decision-making |

---

## GPAI Model Classification

### What Is a GPAI Model? (Art. 3(63))

An AI model (including trained with large amounts of data using self-supervision at scale) that displays significant generality, is capable of competently performing a wide range of distinct tasks regardless of the way it is placed on the market, and can be integrated into a variety of downstream systems or applications.

### GPAI vs AI System

| Attribute | GPAI Model | AI System |
|-----------|-----------|-----------|
| What it is | A model/foundation model | A complete system using a model |
| Obligations | Chapter V (Art. 51-56) | Chapter III (if high-risk) + Art. 50 |
| Who is regulated | GPAI model provider | AI system provider and deployer |
| Integration | Integrated into downstream AI systems | End-use system |

### GPAI Classification Criteria

```
Is the model a GPAI model?
├── NO → Standard AI system rules apply
└── YES
    ├── Standard GPAI → Art. 53 obligations
    │   - Technical documentation
    │   - Information for downstream providers
    │   - Copyright compliance
    │   - Training data summary
    │
    └── Systemic Risk GPAI?
        │
        ├── Training compute >= 10^25 FLOPs? → PRESUMED systemic risk
        │   (provider can rebut presumption)
        │
        ├── AI Office designation based on high impact capabilities?
        │   → DESIGNATED systemic risk
        │
        └── Neither → Standard GPAI (Art. 53 only)
```

### Open-Source GPAI Exception (Art. 53(2))

GPAI models released under a free and open-source licence (allowing access, usage, modification, and distribution with attribution) benefit from **reduced obligations**:
- Must still comply with copyright policy and training data summary
- Exempt from technical documentation and downstream provider information requirements
- Exception does NOT apply to systemic risk models — they must meet ALL obligations regardless of licensing

---

## Systemic Risk Assessment Methodology

### Quantitative Indicators

| Indicator | Threshold | Source |
|-----------|-----------|--------|
| Training compute (FLOPs) | >= 10^25 FLOPs | Art. 51(2) — creates rebuttable presumption |
| Number of registered end users | High (no fixed threshold) | AI Office assessment |
| Number of downstream integrations | High (no fixed threshold) | AI Office assessment |

### Qualitative Indicators

| Indicator | Assessment Criteria |
|-----------|-------------------|
| High impact capabilities | Model benchmarks, evaluations, and testing demonstrate exceptional performance across multiple domains |
| Reach and scale | Number of persons potentially affected by model outputs |
| Reversibility | Whether harms from model outputs can be reversed |
| Autonomy of downstream systems | Degree of autonomy in AI systems built on the model |
| Potential for misuse | Risk of the model being used for harmful purposes at scale |
| Dual-use potential | Applicability to both beneficial and harmful use cases |

### AI Office Designation Process

1. AI Office may initiate designation based on available evidence
2. Provider is notified and can submit views
3. AI Office issues reasoned decision
4. Provider can challenge designation
5. Commission may update the compute threshold by delegated act

---

## Software as Medical Device (SaMD) Classification

AI systems that qualify as medical devices are subject to **both** the AI Act and EU MDR 2017/745.

### Dual Classification

| Regulation | Classification Path |
|-----------|-------------------|
| **AI Act** | High-risk if AI system is a safety component of a medical device (Annex I references MDR) |
| **MDR 2017/745** | Classified per Annex VIII rules, particularly Rule 11 for software |

### SaMD Classification Under MDR (Rule 11 + MDCG 2019-11)

| AI Function | Clinical Impact | MDR Class |
|-------------|----------------|-----------|
| Provides information for decision | Non-serious condition | IIa |
| Provides information for decision | Serious condition | IIb |
| Drives or informs critical decisions | Life-threatening or irreversible | III |
| Monitors physiological parameters | Vital parameters, risk of immediate danger | IIb |

### AI Act Implications for SaMD

- Must comply with BOTH MDR conformity assessment AND AI Act requirements
- Conformity assessment follows the MDR route (not AI Act Annex VI/VII)
- AI Act high-risk obligations (Art. 9-15, 17) still apply in full
- Technical documentation must address both MDR Annex II/III and AI Act Annex IV requirements

---

## AI in Regulated Sectors Mapping

### Cross-Regulation Mapping

| Sector | AI Act Classification | Other Applicable Regulation | Special Considerations |
|--------|----------------------|----------------------------|----------------------|
| **Healthcare / Medical Devices** | High-risk (Annex I — MDR) | MDR 2017/745, IVDR 2017/746 | Dual conformity assessment; MDCG guidance on AI/ML |
| **Automotive** | High-risk (Annex I — vehicle safety) | UNECE regulations, Type Approval | ADAS and autonomous driving systems |
| **Aviation** | High-risk (Annex I — civil aviation) | Regulation (EU) 2018/1139 | AI in air traffic management, aircraft systems |
| **Machinery** | High-risk (Annex I, Section B) | Machinery Regulation (EU) 2023/1230 | Extended deadline to Aug 2027 |
| **Financial Services** | High-risk (Annex III, point 5) | CRD, MiFID II, DORA | Credit scoring, insurance pricing |
| **Employment** | High-risk (Annex III, point 4) | Employment law, GDPR | Recruitment AI, performance monitoring |
| **Education** | High-risk (Annex III, point 3) | National education law | Admission, grading, proctoring |
| **Law Enforcement** | High-risk / Prohibited | LED (Law Enforcement Directive) | Biometric restrictions, exceptions for serious crime |
| **Telecommunications** | Potentially high-risk (critical infrastructure) | European Electronic Communications Code | Network management AI |
| **Energy** | High-risk (Annex III, point 2) | NIS2 Directive, Electricity Directive | Grid management, supply optimization |

### GDPR Interaction

| AI Act Requirement | GDPR Requirement | Alignment |
|-------------------|------------------|-----------|
| Art. 10 (Data governance) | Art. 5 (Data quality principles) | Complementary — AI Act adds AI-specific bias requirements |
| Art. 14 (Human oversight) | Art. 22 (Automated decision-making) | AI Act provides detailed oversight specifications |
| Art. 13 (Transparency) | Art. 13-14 (Right to information) | AI Act adds system-level transparency |
| Art. 9 (Risk management) | Art. 35 (DPIA) | AI Act risk management is broader; DPIA still required for personal data |
| Art. 10(5) (Special categories) | Art. 9 (Special category data) | AI Act permits processing for bias correction with safeguards |

---

## Classification Examples

### Example 1: CV Screening Tool

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Yes — uses NLP to parse and score CVs |
| **Prohibited?** | No |
| **Annex I product?** | No |
| **Annex III?** | Yes — Category 4 (Employment: recruitment screening) |
| **Art. 6(3) exception?** | No — directly influences candidate selection |
| **Classification** | **HIGH-RISK** |
| **Key obligations** | Full provider obligations including bias testing on demographic groups |

### Example 2: Customer Service Chatbot

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Yes — generates responses using NLP |
| **Prohibited?** | No |
| **Annex I product?** | No |
| **Annex III?** | No |
| **Art. 50?** | Yes — AI interacting with persons |
| **Classification** | **LIMITED RISK** |
| **Key obligations** | Disclose to users they are interacting with AI |

### Example 3: AI Credit Scoring Model

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Yes — uses ML to predict creditworthiness |
| **Prohibited?** | No |
| **Annex I product?** | No |
| **Annex III?** | Yes — Category 5 (Essential services: creditworthiness) |
| **Art. 6(3) exception?** | No — directly determines credit decisions |
| **Classification** | **HIGH-RISK** |
| **Key obligations** | Full provider obligations; fairness across demographic groups critical |

### Example 4: Spam Filter

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Likely yes — uses ML classification |
| **Prohibited?** | No |
| **Annex I product?** | No |
| **Annex III?** | No |
| **Art. 50?** | No |
| **Classification** | **MINIMAL RISK** |
| **Key obligations** | None mandatory; voluntary codes of conduct |

### Example 5: AI Diagnostic Imaging (Medical)

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Yes — analyses medical images for diagnosis |
| **Prohibited?** | No |
| **Annex I product?** | Yes — medical device under MDR 2017/745 |
| **Classification** | **HIGH-RISK** (product legislation path) |
| **Key obligations** | MDR conformity assessment + AI Act high-risk obligations |

### Example 6: Large Language Model (Foundation Model)

| Factor | Assessment |
|--------|-----------|
| **AI System?** | It is a GPAI model |
| **GPAI?** | Yes — general-purpose, performs wide range of tasks |
| **Systemic risk?** | Depends on training compute and AI Office assessment |
| **Classification** | **GPAI** (Art. 53) or **GPAI with systemic risk** (Art. 55) |
| **Key obligations** | Technical docs, downstream info, copyright policy, training data summary; if systemic: red-teaming, risk assessment, incident reporting |

### Example 7: Social Media Content Moderation

| Factor | Assessment |
|--------|-----------|
| **AI System?** | Yes — uses ML to classify content |
| **Prohibited?** | No |
| **Annex I product?** | No |
| **Annex III?** | No (not in listed categories) |
| **Art. 50?** | Possibly — if it generates responses to users |
| **Classification** | **MINIMAL or LIMITED RISK** |
| **Key obligations** | Transparency if interacting with users; otherwise voluntary |

---

**Regulation Reference:** Regulation (EU) 2024/1689, Annexes I, III, and relevant recitals

**Last Updated:** March 2026

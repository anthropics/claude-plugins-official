# DORA Third-Party Management Guide

Comprehensive guidance for managing ICT third-party risk under DORA (EU 2022/2554), including the ICT third-party register, contractual requirements, exit strategies, concentration risk assessment, and critical provider oversight.

---

## Table of Contents

- [ICT Third-Party Register](#ict-third-party-register)
- [Contractual Requirements Checklist](#contractual-requirements-checklist)
- [Exit Strategy Framework](#exit-strategy-framework)
- [Concentration Risk Assessment](#concentration-risk-assessment)
- [Critical Provider Oversight](#critical-provider-oversight)

---

## ICT Third-Party Register

### Overview

Article 28(3) of DORA requires financial entities to maintain a **register of information** relating to all contractual arrangements on the use of ICT services provided by ICT third-party service providers. This register must be available to competent authorities upon request.

### Register Structure

The register must distinguish between arrangements that cover **critical or important functions** and those that do not.

### Register Template

#### Section A: Entity Information

| Field | Description | Example |
|-------|------------|---------|
| Entity legal name | Full legal name of the financial entity | ABC Bank AG |
| Entity LEI | Legal Entity Identifier | 529900ABCDEF123456XX |
| Entity type | Type per DORA Article 2(1) | Credit institution |
| Competent authority | Supervisory authority | BaFin / ECB |
| Group membership | Parent company and group structure | XYZ Financial Group |
| Register last updated | Date of last update | 2026-03-09 |

#### Section B: Arrangement Details (Per Third-Party Provider)

| Field | Description | Required |
|-------|------------|----------|
| **Provider identification** | | |
| Provider legal name | Full legal name | Yes |
| Provider LEI | LEI (if available) | Yes (if available) |
| Provider registration country | Country of incorporation | Yes |
| Provider headquarters | Country of headquarters | Yes |
| Provider parent company | Parent entity (if part of group) | Yes (if applicable) |
| **Service details** | | |
| Service description | Detailed description of ICT services | Yes |
| Service type | Category: cloud, managed service, SaaS, infrastructure, etc. | Yes |
| Supports critical/important function | Yes/No | Yes |
| Critical function description | Business function supported (if critical) | If critical |
| Contract reference | Internal contract reference number | Yes |
| Contract start date | Effective date | Yes |
| Contract end date | Expiry/renewal date | Yes |
| Contract governing law | Applicable jurisdiction | Yes |
| **Data processing** | | |
| Data processed | Types of data processed by provider | Yes |
| Data storage location(s) | Countries where data is stored | Yes |
| Data processing location(s) | Countries where data is processed | Yes |
| Data transfer outside EU/EEA | Yes/No, and legal basis | Yes |
| **Sub-contracting** | | |
| Sub-contractors used | Yes/No | Yes |
| Sub-contractor details | Names, locations, services of key sub-contractors | If applicable |
| Sub-contractor notification | Notification procedure for sub-contractor changes | Yes |
| **Risk assessment** | | |
| Last risk assessment date | Date of most recent risk assessment | Yes |
| Risk rating | Low/Medium/High/Critical | Yes |
| Substitutability assessment | Easy/Moderate/Difficult/Very Difficult | Yes |
| Concentration risk flag | Yes/No | Yes |
| **Exit strategy** | | |
| Exit strategy documented | Yes/No | Yes (if critical) |
| Exit strategy last tested | Date of last test | If critical |
| Transition period | Required transition period | If critical |
| Alternative providers identified | Yes/No | If critical |

### Register Maintenance

- **Update frequency:** Upon any change to arrangements, and at minimum quarterly
- **Review cycle:** Annual comprehensive review
- **Reporting:** Available to competent authority upon request
- **Format:** Structured data format as specified by ESA ITS

---

## Contractual Requirements Checklist

### All ICT Service Arrangements (Article 30(2))

| # | Requirement | Article | Status |
|---|------------|---------|--------|
| 1 | Clear and complete description of all functions and ICT services to be provided | 30(2)(a) | [ ] |
| 2 | Locations where contracted/sub-contracted functions will be provided, and where data will be processed (including storage) | 30(2)(a) | [ ] |
| 3 | Provisions on availability, authenticity, integrity, and confidentiality of data (including personal data) | 30(2)(b) | [ ] |
| 4 | Provisions ensuring access, recovery, and return of data in case of insolvency, resolution, or discontinuation | 30(2)(c) | [ ] |
| 5 | Service level descriptions with quantitative and qualitative performance targets | 30(2)(d) | [ ] |
| 6 | Provisions on ICT third-party provider assistance in case of ICT incidents at no additional cost or at a cost determined ex ante | 30(2)(e) | [ ] |
| 7 | Obligation for ICT provider to cooperate with competent authorities and resolution authorities | 30(2)(f) | [ ] |
| 8 | Termination rights and related minimum notice periods | 30(2)(g) | [ ] |
| 9 | Conditions for participation in entity's ICT security awareness programs and digital operational resilience training | 30(2)(h) | [ ] |

### Critical or Important Function Arrangements (Article 30(3), Additional)

| # | Requirement | Article | Status |
|---|------------|---------|--------|
| 10 | Full service level descriptions with precise quantitative and qualitative targets | 30(3)(a) | [ ] |
| 11 | Notice periods and reporting obligations for developments with potential material impact | 30(3)(b) | [ ] |
| 12 | Obligation to implement and test business continuity plans and measures | 30(3)(c) | [ ] |
| 13 | Full access to performance and security data including independent audit reports | 30(3)(d) | [ ] |
| 14 | Participation in entity's TLPT (threat-led penetration testing) | 30(3)(e) | [ ] |
| 15 | Unrestricted right of the entity to monitor provider on an ongoing basis | 30(3)(f) | [ ] |
| 16 | Exit strategies including mandatory adequate transition period | 30(3)(g) | [ ] |

### Audit and Access Rights

| # | Requirement | Detail |
|---|------------|--------|
| 17 | Full access rights to provider premises | Including data centers and relevant facilities |
| 18 | Full and unrestricted access to information | Documents, data, systems as needed for audit |
| 19 | Right to conduct on-site inspections | Of the ICT third-party service provider |
| 20 | Right to conduct off-site audits | Remote audit capabilities |
| 21 | Freedom to determine audit scope and frequency | No provider restrictions on audit activities |
| 22 | Right to use third-party auditors | Including pooled audit arrangements |

### Sub-Contracting Requirements

| # | Requirement | Detail |
|---|------------|--------|
| 23 | Prior notification of sub-contracting | Provider must notify before engaging sub-contractors |
| 24 | Entity right to object | Right to object to sub-contracting that may impact services |
| 25 | Sub-contractor compliance | Sub-contractors must comply with same requirements |
| 26 | Chain supervision | Entity retains oversight throughout sub-contractor chain |

---

## Exit Strategy Framework

### When Exit Strategies Are Required

Exit strategies are **mandatory** for all arrangements covering critical or important functions (Article 28(8)).

### Exit Strategy Components

#### 1. Trigger Conditions

Define clear conditions that trigger exit strategy activation:

| Trigger | Description | Response Time |
|---------|------------|--------------|
| Material breach | Provider fails to meet SLAs or security requirements | Per contractual notice period |
| Insolvency | Provider enters insolvency or administration | Immediate activation |
| Regulatory action | Competent authority requires termination | Per regulatory timeline |
| Concentration risk | Concentration exceeds defined thresholds | Planned transition (6-18 months) |
| Security incident | Major security breach at provider | Assessed case-by-case |
| Strategic change | Entity strategy requires insourcing or provider change | Planned transition |
| CTPP designation | Provider designated as critical with restrictions | Per oversight framework |

#### 2. Transition Planning

| Phase | Duration | Activities |
|-------|----------|-----------|
| **Assessment** | 2-4 weeks | Evaluate trigger, assess impact, activate exit governance |
| **Planning** | 4-8 weeks | Identify alternative, define migration plan, resource allocation |
| **Preparation** | 4-12 weeks | Set up alternative environment, test migration procedures |
| **Migration** | 8-24 weeks | Data migration, system integration, parallel run |
| **Validation** | 2-4 weeks | Verify functionality, performance, security in new environment |
| **Cutover** | 1-2 weeks | Switch production to new environment, decommission old |
| **Post-transition** | 4-8 weeks | Monitor stability, resolve issues, complete data deletion at old provider |

#### 3. Data Management During Exit

- **Data extraction:** Define formats, methods, and timelines for data extraction from provider
- **Data migration:** Procedures for secure data transfer to alternative provider or in-house
- **Data validation:** Integrity verification of all migrated data
- **Data deletion:** Verifiable deletion of all entity data from outgoing provider
- **Continuity:** Ensure no data loss or service disruption during transition

#### 4. Service Continuity During Transition

- Define minimum service levels during transition period
- Establish parallel-run requirements before cutover
- Plan for fallback if migration encounters issues
- Maintain provider cooperation requirements during transition

#### 5. Testing Exit Strategies

Exit strategies must be **tested** to ensure they work:

| Test Type | Frequency | Scope |
|-----------|-----------|-------|
| Tabletop exercise | Annual | Walk through exit scenarios with key stakeholders |
| Data extraction test | Annual | Extract sample data from provider, validate completeness |
| Alternative provider readiness | Biannual | Verify alternative provider can onboard within defined timeline |
| Full migration drill | Every 2-3 years | End-to-end migration test for most critical arrangements |

---

## Concentration Risk Assessment

### Overview

Article 29 requires financial entities to assess and manage risks arising from concentrating ICT services with a limited number of providers.

### Assessment Methodology

#### Step 1: Map ICT Service Dependencies

For each ICT third-party provider, document:
- All services provided
- Business functions supported
- Data volumes and sensitivity
- Number of entity staff dependent on the service
- Availability requirements

#### Step 2: Identify Concentration Indicators

| Indicator | Assessment Questions |
|-----------|---------------------|
| **Provider concentration** | How many critical functions depend on a single provider? Is there a single provider supporting > 30% of critical functions? |
| **Technology concentration** | Are multiple services built on the same underlying technology platform? |
| **Geographic concentration** | Are multiple services hosted in the same geographic location or jurisdiction? |
| **Sub-contractor concentration** | Do multiple providers rely on the same underlying sub-contractors? |
| **Sector concentration** | Does the provider serve a large proportion of the financial sector (systemic provider)? |
| **Substitutability** | How easily can the provider be replaced? What is the switching timeline and cost? |
| **Vendor lock-in** | Are proprietary formats, APIs, or technologies creating lock-in? |
| **Single points of failure** | Would provider failure cause cascading failures across multiple functions? |

#### Step 3: Concentration Risk Scoring

| Risk Level | Score | Criteria |
|-----------|-------|---------|
| **Low** | 1 | Single non-critical function, easily substitutable, multiple alternatives |
| **Medium** | 2 | Multiple functions or one important function, moderate switching effort |
| **High** | 3 | Critical function, limited alternatives, significant switching effort (> 6 months) |
| **Critical** | 4 | Multiple critical functions, very few alternatives, provider potentially systemic, switching > 12 months |

#### Step 4: Mitigation Strategies

| Risk Level | Mitigation Actions |
|-----------|-------------------|
| **Low** | Monitor, review annually |
| **Medium** | Develop contingency plans, identify alternative providers |
| **High** | Implement multi-vendor strategy, test exit procedures, enhance contractual protections |
| **Critical** | Active multi-vendor diversification, regular exit testing, board-level reporting, competent authority engagement |

#### Step 5: Reporting

- Include concentration risk assessment in the ICT risk management framework
- Report concentration risk to management body at least annually
- Update assessment when entering new ICT arrangements or upon material changes
- Report to competent authority upon request

### Concentration Risk Register

| Provider | Services | Critical Functions | Substitutability | Concentration Score | Mitigation |
|----------|----------|--------------------|------------------|--------------------| -----------|
| Provider A | Cloud infrastructure | 3 of 5 | Difficult | Critical (4) | Multi-cloud strategy in progress |
| Provider B | Payment processing | 1 of 5 | Moderate | High (3) | Alternative provider identified |
| Provider C | Email/collaboration | 0 of 5 | Easy | Low (1) | Standard monitoring |

---

## Critical Provider Oversight

### Overview

Articles 31–44 establish an **Oversight Framework** for critical ICT third-party service providers (CTPPs). This framework is unique to DORA and has no equivalent in other cybersecurity regulations.

### Designation Process

The ESAs designate CTPPs based on:

| Criterion | Description |
|-----------|------------|
| Systemic impact | Impact that a failure or operational outage would have on financial entities |
| Systemic character | Systemic character or importance of financial entities relying on the provider |
| Dependency degree | Degree to which financial entities depend on the provider's services |
| Substitutability | Degree of substitutability of the ICT third-party service provider |
| Cross-border reach | Number of Member States in which the provider operates or provides services |

### Lead Overseer

One of the three ESAs (EBA, ESMA, EIOPA) is assigned as **Lead Overseer** for each designated CTPP based on the types of financial entities primarily using the provider.

### Oversight Powers

The Lead Overseer may:

| Power | Description |
|-------|------------|
| **Request information** | Any information and documentation necessary for oversight duties |
| **General investigations** | Examination of records, data, procedures, and any material |
| **On-site inspections** | Inspect the CTPP's premises, including data centers and sub-contractor facilities |
| **Issue recommendations** | Formal recommendations on ICT security, quality measures, resilience, and more |
| **Periodic penalty payments** | For non-compliance with recommendations: up to 1% of average daily worldwide turnover, for up to 6 months |

### Financial Entity Obligations Regarding CTPPs

If your ICT provider is designated as a CTPP:

1. **Verify compliance** — Confirm that your provider is cooperating with the Lead Overseer
2. **Review contracts** — Ensure contracts contain all DORA-mandated provisions, including cooperation with authorities
3. **Monitor oversight outcomes** — Track any recommendations issued to your CTPP by the Lead Overseer
4. **Assess impact** — Evaluate whether oversight actions affect the services you receive
5. **Exit readiness** — Maintain tested exit strategies in case oversight actions require transition
6. **Report** — Report material developments in the CTPP relationship to your competent authority

### Non-EU ICT Third-Party Providers

CTPPs established in third countries (non-EU) must:
- Establish a subsidiary within the Union within 12 months of designation
- The subsidiary is subject to the full oversight framework
- Failure to establish may result in the Lead Overseer recommending that financial entities suspend or terminate arrangements

---

*Last Updated: March 2026*
*Regulation Reference: EU 2022/2554, Articles 28-44*

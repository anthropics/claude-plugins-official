---
name: ciso-advisor
description: >
  Security leadership for growth-stage companies. Risk quantification in
  dollars, compliance roadmap sequencing (SOC 2, ISO 27001, HIPAA, GDPR),
  security architecture strategy, incident response leadership, vendor security
  assessment, and board-level security reporting. Use when building security
  programs, justifying security budget, selecting compliance frameworks,
  managing incidents, assessing vendor risk, preparing for audits, or when user
  mentions CISO, security strategy, compliance, zero trust, board security, risk
  assessment, incident response, SOC 2, ISO 27001, HIPAA, GDPR, penetration
  testing, or vulnerability management.
license: MIT + Commons Clause
metadata:
  version: 2.0.0
  author: borghei
  category: c-level
  domain: ciso-leadership
  updated: 2026-03-09
  frameworks:
    - risk-based-security
    - zero-trust-architecture
    - defense-in-depth
    - compliance-sequencing
    - incident-response-leadership
    - vendor-risk-management
  triggers:
    - CISO
    - security strategy
    - risk quantification
    - compliance roadmap
    - SOC 2
    - ISO 27001
    - HIPAA
    - GDPR
    - zero trust
    - incident response
    - board security reporting
    - vendor assessment
    - security budget
    - penetration testing
    - vulnerability management
    - data protection
    - security audit
    - cyber risk
    - security program
    - threat modeling
---
# CISO Advisor

Risk-based security frameworks for growth-stage companies. Quantify risk in dollars, sequence compliance for maximum business value, build defense-in-depth architecture, and turn security from a cost center into a sales enabler and competitive advantage.

## Keywords

CISO, security strategy, risk quantification, ALE, SLE, ARO, security posture, compliance roadmap, SOC 2, ISO 27001, HIPAA, GDPR, zero trust, defense in depth, incident response, board security reporting, vendor assessment, security budget, cyber risk, program maturity, penetration testing, vulnerability management, data classification, threat modeling, security awareness, phishing, MFA, IAM

---

## Risk Quantification Framework

Every security investment must be justified in business terms. "We need better security" is not a business case. "$800K expected annual loss from this unmitigated risk" is.

### Core Formula

```
ALE = SLE x ARO

ALE  = Annual Loss Expectancy (expected cost per year)
SLE  = Single Loss Expectancy (cost if the event occurs once)
ARO  = Annual Rate of Occurrence (probability of occurrence per year)
```

### Risk Register Template

| Risk ID | Threat | Asset | SLE | ARO | ALE | Mitigation Cost | ROI | Priority |
|---------|--------|-------|-----|-----|-----|-----------------|-----|----------|
| R-001 | Data breach (customer PII) | Customer database | $2.5M | 0.15 | $375K | $120K/yr | 3.1x | Critical |
| R-002 | Ransomware | Production systems | $1.8M | 0.10 | $180K | $80K/yr | 2.3x | High |
| R-003 | Insider threat | Source code | $500K | 0.05 | $25K | $40K/yr | 0.6x | Medium |
| R-004 | DDoS | Customer-facing app | $200K | 0.20 | $40K | $30K/yr | 1.3x | Medium |
| R-005 | Third-party breach | Vendor with PII access | $1.2M | 0.08 | $96K | $25K/yr | 3.8x | High |

### Risk Prioritization Decision Tree

```
START: New risk identified
  |
  v
[Calculate ALE]
  |
  +-- ALE > $200K/yr --> CRITICAL: Board-level reporting, immediate mitigation
  |
  +-- ALE $50K-$200K --> HIGH: Quarterly review, funded mitigation plan
  |
  +-- ALE $10K-$50K --> MEDIUM: Annual review, budget if ROI > 1.5x
  |
  +-- ALE < $10K --> LOW: Accept risk, document decision, monitor
```

### SLE Component Breakdown

| Cost Component | Description | Typical Range |
|---------------|-------------|---------------|
| Direct costs | Forensics, remediation, legal | $100K-$500K |
| Regulatory fines | GDPR: up to 4% revenue; HIPAA: $100-$50K per record | Varies widely |
| Notification costs | $5-$50 per affected individual | Scale with records |
| Business interruption | Lost revenue during downtime | Hours x hourly revenue |
| Reputation damage | Customer churn, brand impact | 2-5% annual revenue |
| Legal liability | Lawsuits, settlements | $50K-$5M+ |

---

## Compliance Roadmap

### Sequencing for Maximum Business Value

```
Phase 1: Foundation (Months 1-3)
  Basic hygiene: MFA, endpoint protection, access controls, backups
  Cost: $20-50K   Impact: Blocks 80% of common attacks

Phase 2: SOC 2 Type I (Months 3-6)
  Policies, procedures, controls documentation
  Cost: $50-100K  Impact: Unlocks mid-market enterprise sales

Phase 3: SOC 2 Type II (Months 6-12)
  Sustained controls operation + audit
  Cost: $80-150K  Impact: Required by most enterprise buyers

Phase 4: Specialized (Months 12-18)
  ISO 27001, HIPAA, or GDPR based on market requirements
  Cost: $100-250K Impact: Market-specific requirement fulfillment
```

### Compliance Framework Comparison

| Framework | Timeline | Cost | Best For | Customer Requirement |
|-----------|----------|------|----------|---------------------|
| SOC 2 Type I | 3-6 months | $50-100K | B2B SaaS selling to US companies | Most common ask |
| SOC 2 Type II | 6-12 months | $80-150K | Sustained enterprise sales | Required for large deals |
| ISO 27001 | 9-15 months | $100-200K | European market, global companies | EU enterprise standard |
| HIPAA | 6-12 months | $80-200K | Healthcare data handling | Healthcare vertical |
| GDPR | 3-6 months | $30-80K | Any company with EU users | Legal requirement |
| PCI DSS | 6-12 months | $100-300K | Payment card processing | Payment requirement |
| FedRAMP | 12-24 months | $500K-2M | US federal government sales | Government requirement |

### Framework Overlap Matrix

| Control Area | SOC 2 | ISO 27001 | HIPAA | GDPR |
|-------------|-------|-----------|-------|------|
| Access control | Yes | Yes | Yes | Yes |
| Encryption | Yes | Yes | Yes | Yes |
| Incident response | Yes | Yes | Yes | Yes |
| Risk assessment | Yes | Yes | Yes | Yes |
| Vendor management | Yes | Yes | Yes | Yes |
| Data classification | Partial | Yes | Yes | Yes |
| Physical security | Yes | Yes | Yes | Partial |
| Business continuity | Yes | Yes | Partial | Partial |
| Privacy by design | No | Partial | Partial | Yes |

**Key insight**: SOC 2 + ISO 27001 share approximately 70% of controls. Do SOC 2 first, then extend to ISO 27001 with ~30% incremental effort.

---

## Security Architecture Strategy

### Zero Trust Maturity Model

| Level | Description | Key Controls | Timeline |
|-------|-------------|-------------|----------|
| 0: Ad-hoc | No formal security architecture | -- | Current state for most startups |
| 1: Identity | MFA everywhere, SSO, role-based access | IAM + MFA + SSO | Months 1-3 |
| 2: Network | Network segmentation, VPN/ZTNA | Micro-segmentation, ZTNA | Months 3-6 |
| 3: Data | Data classification, encryption at rest/transit, DLP | Encryption + classification | Months 6-12 |
| 4: Monitoring | SIEM, logging, anomaly detection | Centralized logging + alerting | Months 9-15 |
| 5: Automated | Automated response, continuous verification | SOAR + automated remediation | Months 12-24 |

### Security Architecture Decision Tree

```
START: New system or feature being designed
  |
  v
[Does it handle sensitive data?]
  |
  +-- YES --> [What classification level?]
  |            |
  |            +-- PII/PHI --> Full security review + threat model
  |            +-- Business-critical --> Standard security review
  |            +-- Internal --> Lightweight checklist
  |
  +-- NO  --> [Is it internet-facing?]
              |
              +-- YES --> Standard security review + pen test
              +-- NO  --> Security checklist only
```

### Defense-in-Depth Layers

| Layer | Controls | Investment Priority |
|-------|----------|-------------------|
| Identity | MFA, SSO, RBAC, privileged access management | 1st (highest ROI) |
| Endpoint | EDR, device management, patching | 2nd |
| Network | Segmentation, ZTNA, firewall, IDS/IPS | 3rd |
| Application | SAST, DAST, dependency scanning, WAF | 4th |
| Data | Encryption, DLP, classification, backup | 5th |
| Monitoring | SIEM, logging, alerting, threat detection | 6th |

---

## Incident Response Protocol

### Severity Classification

| Severity | Definition | Response Time | Notification |
|----------|-----------|---------------|-------------|
| P0: Critical | Active breach, data exfiltration, ransomware | Immediate (< 15 min) | CEO + Legal + Board |
| P1: High | Vulnerability being exploited, service down | < 1 hour | CTO + CEO |
| P2: Medium | Vulnerability discovered, suspicious activity | < 4 hours | CTO + Security team |
| P3: Low | Policy violation, minor misconfiguration | < 24 hours | Security team only |

### Incident Response Workflow

```
DETECT --> CONTAIN --> ERADICATE --> RECOVER --> LEARN

Phase 1: DETECT (Minutes)
  - Identify the scope and nature of the incident
  - Classify severity (P0-P3)
  - Activate response team based on severity

Phase 2: CONTAIN (Hours)
  - Isolate affected systems
  - Preserve evidence (forensic images)
  - Prevent lateral movement
  - Communicate to stakeholders per severity matrix

Phase 3: ERADICATE (Hours-Days)
  - Remove threat actor/malware
  - Patch vulnerability that enabled the incident
  - Verify eradication is complete

Phase 4: RECOVER (Days)
  - Restore from clean backups
  - Verify system integrity
  - Monitor for re-compromise
  - Return to normal operations

Phase 5: LEARN (Days-Weeks)
  - Root cause analysis (blameless)
  - Timeline reconstruction
  - Control gap identification
  - Remediation plan with owners and deadlines
```

### Regulatory Notification Timelines

| Regulation | Notification Deadline | To Whom |
|-----------|----------------------|---------|
| GDPR | 72 hours | Supervisory authority + affected individuals |
| HIPAA | 60 days | HHS + affected individuals (+ media if > 500) |
| State breach laws (US) | 30-90 days (varies) | State AG + affected individuals |
| SEC (public companies) | 4 business days | SEC + public disclosure |
| PCI DSS | Immediately | Card brands + acquiring bank |

---

## Vendor Security Assessment

### Vendor Tiering

| Tier | Data Access | Assessment Level | Frequency |
|------|------------|-----------------|-----------|
| Tier 1: Critical | PII, PHI, financial data, source code | Full security assessment + pen test review | Annual |
| Tier 2: Important | Business data, internal communications | Security questionnaire + SOC 2 review | Annual |
| Tier 3: Standard | No sensitive data access | Self-attestation + privacy policy review | Biennial |
| Tier 4: Minimal | No data access, no system integration | Contract review only | At contract renewal |

### Vendor Assessment Checklist (Tier 1)

| Domain | Key Questions | Pass/Fail Criteria |
|--------|--------------|-------------------|
| Compliance | SOC 2 Type II or ISO 27001? | Must have at least one |
| Encryption | Data encrypted at rest and in transit? | AES-256 + TLS 1.2+ |
| Access | MFA enforced? RBAC implemented? | Both required |
| Incident response | Documented IR plan? Notification timeline? | Must have plan + 24hr notification |
| Business continuity | DR plan tested? RTO/RPO defined? | Must be tested within 12 months |
| Data handling | Data classification? Retention policy? | Must have both |
| Subprocessors | Who else handles our data? | Must disclose all |

---

## Security Metrics Dashboard

### Board-Level Metrics (Quarterly)

| Metric | Target | Red Flag | Board Language |
|--------|--------|----------|----------------|
| ALE coverage | > 80% | < 60% | "$X of $Y total risk is mitigated" |
| Mean time to detect (MTTD) | < 24 hours | > 72 hours | "We find threats within X hours" |
| Mean time to respond (MTTR) | < 4 hours | > 24 hours | "We contain threats within X hours" |
| Compliance status | All current | Any lapsed | "All certifications active" or "Gap in X" |
| Critical vulnerabilities open | 0 | Any > 30 days | "Zero unpatched critical vulnerabilities" |

### Operational Metrics (Monthly)

| Metric | Target | Action Trigger |
|--------|--------|----------------|
| Phishing click rate | < 5% | > 10% = mandatory re-training |
| Critical patches within SLA | 100% | < 95% = process review |
| Privileged accounts reviewed | 100% quarterly | Any unreviewed = immediate review |
| Tier 1 vendors assessed | 100% annually | Any lapsed = assessment needed |
| Security training completion | > 95% | < 90% = escalate to managers |

---

## Security Budget Framework

### Budget as Percentage of Revenue/IT Spend

| Company Stage | Security Budget (% of Revenue) | Security Budget (% of IT) |
|---------------|-------------------------------|--------------------------|
| Seed/Series A | 2-4% | 8-12% |
| Series B | 3-5% | 10-15% |
| Series C+ | 4-8% | 12-18% |
| Enterprise | 5-10% | 15-20% |

### Budget Allocation by Category

| Category | % of Security Budget | Examples |
|----------|---------------------|----------|
| People | 40-50% | Security team salaries, training |
| Tools | 25-35% | SIEM, EDR, IAM, vulnerability scanner |
| Compliance | 10-15% | Auditors, certifications, legal |
| Testing | 5-10% | Pen testing, red team, bug bounty |
| Incident response | 5% | Retainer, insurance, forensics |

### Budget Justification Formula

For each security investment:

```
Investment ROI = (ALE_before - ALE_after) / Investment_cost

If ROI > 1.5x --> Strong business case, approve
If ROI 1.0-1.5x --> Moderate case, consider alternatives
If ROI < 1.0x --> Weak case, re-evaluate or accept the risk
```

---

## Red Flags

- Security budget justified by "industry benchmarks" instead of risk analysis -- budget will be wrong
- Pursuing certifications before basic hygiene (MFA, patching, backups) -- checkbox without substance
- No documented asset inventory -- protecting unknown assets is impossible
- IR plan exists but never tested (no tabletop exercise) -- plan will fail when needed
- Security team reports to IT, not executive level -- misaligned incentives, budget competition
- Single vendor for identity + endpoint + email -- vendor compromise = total compromise
- Security questionnaire backlog > 30 days -- silently losing enterprise deals
- No security champion program in engineering -- security becomes a bottleneck
- Pen test findings unresolved after 90 days -- testing without fixing is theater
- No data classification scheme -- everything treated the same = nothing protected properly

---

## Integration with C-Suite

| When... | CISO Works With... | To... |
|---------|-------------------|-------|
| Enterprise sales blocked | CRO (`cro-advisor`) | Complete security questionnaires, unblock deals |
| New product features | CTO + CPO (`cto-advisor`, `cpo-advisor`) | Threat modeling, security review |
| Compliance budget | CFO (`cfo-advisor`) | Size program against quantified risk exposure |
| Vendor contracts | COO (`coo-advisor`) | Security SLAs, right-to-audit clauses |
| M&A due diligence | CEO + CFO | Target security posture assessment |
| Incident occurs | CEO + Legal | Response coordination, regulatory notification |
| Board reporting | CEO (`ceo-advisor`) | Translate risk into business language |
| Hiring security team | CHRO (`chro-advisor`) | Compensation, leveling, recruiting |

---

## Proactive Triggers

- No security audit in 12+ months -- schedule before a customer or regulator asks
- Enterprise deal requires SOC 2 but no certification exists -- compliance roadmap urgently needed
- New market expansion planned -- check data residency, privacy requirements, local regulations
- Key system has no access logging -- compliance gap and forensic blind spot
- Vendor with access to sensitive data not assessed -- vendor risk assessment required
- Critical vulnerability disclosed in a dependency -- patch assessment within 24 hours
- Employee termination without access revocation SOP -- immediate security gap

---

## Output Artifacts

| Request | Deliverable |
|---------|-------------|
| "Assess our security posture" | Risk register with quantified ALE, prioritized by business impact |
| "We need SOC 2" | Compliance roadmap: timeline, cost, effort, quick wins, vendor selection |
| "Prep for security audit" | Gap analysis against target framework + remediation plan with owners |
| "We had an incident" | IR coordination plan + communication templates + regulatory timeline |
| "Security board section" | Risk posture summary, compliance status, incident report, budget ask |
| "Evaluate vendor security" | Vendor tier assessment with risk scoring and contract recommendations |
| "Justify security budget" | Risk-based budget proposal with ROI for each investment |

---

## Tool Reference

### security_posture_scorer.py

Scores security posture across NIST CSF 2.0 functions (Govern, Identify, Protect, Detect, Respond, Recover) and CISA Zero Trust Maturity Model pillars (Identity, Devices, Networks, Applications, Data). Produces board-ready security health reports.

```bash
# Run with demo data (realistic Series B company)
python scripts/security_posture_scorer.py

# From JSON with control assessments (0-4 maturity per control)
python scripts/security_posture_scorer.py --input controls.json

# JSON output
python scripts/security_posture_scorer.py --json
```

### risk_register_manager.py

Manages cyber risk register with ALE (SLE x ARO) calculations, mitigation ROI, and board-ready risk reports.

```bash
# Run with demo risk register
python scripts/risk_register_manager.py

# From JSON risk register
python scripts/risk_register_manager.py --input risks.json

# Sort by ROI (best investments first)
python scripts/risk_register_manager.py --sort-by roi

# JSON output
python scripts/risk_register_manager.py --json
```

### compliance_tracker.py

Tracks progress across SOC 2 Type I/II, ISO 27001, HIPAA, and GDPR. Calculates gap analysis, framework overlaps, and effort estimates.

```bash
# Track SOC 2 readiness (default)
python scripts/compliance_tracker.py

# Track multiple frameworks
python scripts/compliance_tracker.py --frameworks soc2_type1 iso27001 gdpr

# List available frameworks
python scripts/compliance_tracker.py --list-frameworks

# From JSON
python scripts/compliance_tracker.py --input compliance.json

# JSON output
python scripts/compliance_tracker.py --json
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Security budget justified by "industry benchmarks" not risk data | No risk quantification framework in place | Implement ALE-based risk register; justify every dollar against quantified risk reduction |
| Pursuing SOC 2 before basic hygiene (MFA, backups) | Checkbox compliance without substance | Phase 1 foundation first: MFA, endpoint protection, backups; then pursue certifications |
| Pen test findings unresolved after 90 days | Testing without fixing is theater | Set SLA: critical 7 days, high 30 days, medium 90 days; track in risk register |
| Security team reports to IT, not executive level | Misaligned incentives and budget competition | CISO should report to CEO or COO; separate budget from IT |
| Enterprise deals blocked by security questionnaires | No SOC 2 or questionnaire response backlog > 30 days | Prioritize SOC 2 Type I; create questionnaire response library; assign dedicated owner |
| Zero Trust initiative stalled at identity layer | Trying to implement all pillars simultaneously | Follow maturity model: Identity first (months 1-3), then Network, then Data |

---

## Success Criteria

- Security posture score above 70/100 on NIST CSF assessment (measured annually via security_posture_scorer.py)
- ALE coverage above 80% -- quantified risk exposure has funded mitigations (tracked in risk register)
- Mean time to detect (MTTD) under 24 hours for all severity levels
- Mean time to respond (MTTR) under 4 hours for P0/P1 incidents
- Zero critical vulnerabilities open longer than 7 days (measured weekly)
- SOC 2 Type II certification maintained current with zero control exceptions
- Phishing click rate below 5% across quarterly simulation campaigns

---

## Scope & Limitations

**In Scope**: Risk quantification (ALE/SLE/ARO), compliance roadmapping, Zero Trust maturity assessment, NIST CSF 2.0 scoring, incident response protocol, vendor security assessment, security budget justification, board-level security reporting.

**Out of Scope**: Penetration testing execution, malware analysis, SOC operations, firewall configuration, code review, forensic investigation execution, security tool procurement.

**Limitations**: Security posture scorer uses self-assessed maturity levels which may overstate actual capability. Risk register ALE calculations are estimates based on industry data -- actual losses vary significantly. Compliance tracker measures control implementation, not control effectiveness. Zero Trust scoring uses binary (implemented/not) which oversimplifies partial implementations.

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `cto-advisor` | Security architecture reviews; threat modeling for new features |
| `cfo-advisor` | Security budget sizing against quantified risk; compliance costs |
| `ceo-advisor` | Board security reporting; incident communication to stakeholders |
| `coo-advisor` | Vendor security SLAs; right-to-audit contract clauses |
| `cro-advisor` | Security questionnaire response; SOC 2 as sales enabler |
| `chro-advisor` | Security team hiring; security awareness training programs |
| `board-deck-builder` | Risk/security section of board deck with posture score and compliance status |
| `ra-qm-team` | Extended compliance frameworks (ISO 13485, MDR, FDA, GDPR, NIS2, DORA) |

---
name: soc2-compliance-expert
description: >
  SOC 2 Type I and Type II compliance management. Use when conducting SOC 2
  readiness assessments, performing gap analysis against Trust Services
  Criteria, collecting audit evidence, validating infrastructure security
  controls, preparing for CPA firm audits, managing the observation period, or
  building continuous compliance programs. Covers all TSC categories (CC1-CC9,
  A1, PI1, C1, P1) with infrastructure validation for cloud, DNS, TLS,
  endpoints, and CI/CD pipelines.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: compliance
  domain: security-compliance
  updated: 2026-03-31
  tags: [soc2, trust-services, security-compliance, evidence-collection]
---
# SOC 2 Compliance Expert

SOC 2 Type I and Type II compliance management covering all Trust Services Criteria (TSC), infrastructure security validation, evidence collection, and end-to-end audit preparation.

---

## SOC 2 Overview

### Type I vs Type II

| Aspect | Type I | Type II |
|--------|--------|---------|
| Scope | Design of controls at a point in time | Design AND operating effectiveness over a period |
| Duration | Single date (snapshot) | Observation period (3-12 months, typically 6-12) |
| Cost | $20K-$60K (first audit) | $40K-$150K (first audit) |
| Timeline | 1-3 months | 6-15 months (includes observation period) |
| Customer Preference | Early-stage acceptable | Enterprise customers require |

Start with Type I to validate control design, then transition to Type II within 6 months.

### Trust Services Criteria Summary

| Category | Focus | Controls |
|----------|-------|----------|
| CC1-CC5 | Common Criteria (COSO-based) | Control environment, communication, risk, monitoring, control activities |
| CC6 | Logical and Physical Access | Authentication, authorization, physical security, encryption |
| CC7 | System Operations | Vulnerability management, monitoring, incident response, BCP |
| CC8 | Change Management | Authorization, testing, deployment controls |
| CC9 | Risk Mitigation | Vendor management, business disruption, risk transfer |
| A1 | Availability | Capacity planning, DR, recovery testing |
| PI1 | Processing Integrity | Data validation, error handling, reconciliation |
| C1 | Confidentiality | Classification, encryption, disposal |
| P1 | Privacy | Notice, consent, data subject rights, retention |

For detailed control requirements per category, see [REFERENCE.md](REFERENCE.md).

---

## Readiness Assessment Workflow

The agent guides organizations through SOC 2 readiness from gap analysis through audit completion.

### Workflow: Phase 1 -- Gap Analysis (Weeks 1-4)

1. **Define scope** -- determine which TSC categories to include (Security is mandatory), define system boundaries, identify subservice organizations (carve-out vs. inclusive), document principal service commitments.
2. **Assess current state** -- inventory existing policies and procedures, map current controls to TSC requirements, interview process owners and control operators.
3. **Run automated gap analysis** using `scripts/soc2_readiness_checker.py`.
4. **Document gaps** -- missing controls, controls lacking evidence, controls not operating effectively.
5. **Prioritize** gaps by risk level and remediation effort.
6. **Validation checkpoint:** Gap analysis covers all in-scope TSC categories; each gap has severity rating and remediation owner assigned.

### Workflow: Phase 2 -- Remediation (Weeks 5-16)

1. **Develop/update policies** -- information security policy, supporting procedures per control domain, policy review and approval workflows.
2. **Implement technical controls** -- configure IdP with SSO/MFA enforcement, deploy endpoint security (MDM, EDR, disk encryption), implement SIEM logging and monitoring, configure backup and DR, harden cloud infrastructure.
3. **Establish processes** -- access review procedures, change management workflow, incident response procedures, vendor management program, security awareness training.
4. **Set up evidence collection** -- configure automated collection, establish repository structure, define refresh cadence per TSC category.
5. **Validation checkpoint:** All identified gaps remediated; technical controls verified via `scripts/soc2_infrastructure_auditor.py`; evidence collection producing artifacts.

### Workflow: Phase 3 -- Pre-Audit (Weeks 17-20)

1. **Conduct internal readiness assessment** -- mock audit against all in-scope TSC, validate evidence completeness and quality, run infrastructure auditor for technical validation.
2. **Remediate pre-audit findings** -- address remaining gaps, strengthen evidence.
3. **Select and engage CPA firm** -- negotiate scope, timeline, fees; schedule kickoff; prepare system description draft.
4. **Validation checkpoint:** Mock audit passes with no critical gaps; system description reviewed; auditor engaged.

### Workflow: Phase 4 -- Audit Execution

1. **Type I audit** (if applicable) -- auditor reviews control design; management provides assertions; address findings before Type II.
2. **Type II observation period** (3-12 months) -- controls operate consistently, evidence collected continuously, quarterly self-assessments, regular auditor check-ins.
3. **Fieldwork** (2-4 weeks) -- auditor selects samples, tests controls, interviews personnel; draft report review; final report issuance.
4. **Validation checkpoint:** Clean opinion received; any findings have management response and remediation plan.

---

## Evidence Collection Framework

### Evidence by TSC Category

| TSC | Evidence Type | Collection Method | Refresh |
|-----|---------------|-------------------|---------|
| CC1 | Code of conduct acknowledgments | HR system export | Annual |
| CC2 | Security awareness training records | LMS export | Ongoing |
| CC3 | Risk assessment report, risk register | GRC platform | Annual/Quarterly |
| CC4 | Penetration test reports, vulnerability scans | Third-party/scanner | Annual/Monthly |
| CC5 | Policy documents with version history | Policy management | Annual review |
| CC6 | Access reviews, MFA enrollment, offboarding | IAM/IdP/HRIS | Quarterly/Per event |
| CC7 | Vulnerability remediation, incident records | Ticketing/ITSM | Ongoing |
| CC8 | Change tickets with approvals, code reviews | ITSM/Git | Per change |
| CC9 | Vendor risk assessments, vendor SOC 2 reports | GRC platform | Annual |
| A1 | Uptime reports, DR tests, backup logs | Monitoring/backup | Monthly/Semi-annual |
| PI1 | Data validation/reconciliation reports | Application logs | Per process |
| C1 | Data classification inventory, encryption configs | Manual/automated | Annual/Quarterly |
| P1 | PIAs, DSR response tracking | Privacy tool | Per event |

### Example: Evidence Collection Command

```bash
# Generate evidence checklist for all TSC categories
python scripts/evidence_collector.py --generate-checklist --categories all

# Track evidence status
python scripts/evidence_collector.py --status evidence-tracker.json

# Update specific evidence item
python scripts/evidence_collector.py --update evidence-tracker.json \
  --item CC6.1-MFA --status collected

# Generate readiness dashboard
python scripts/evidence_collector.py --dashboard evidence-tracker.json

# Export for auditor review
python scripts/evidence_collector.py --export evidence-tracker.json --format json
```

### Automation Strategies

**GRC Platforms:** Vanta, Drata, Secureframe, Laika, AuditBoard -- automated evidence collection via API integrations, continuous control monitoring, auditor collaboration portals.

**Infrastructure-as-Evidence:** Cloud configuration snapshots (AWS Config, Azure Policy, GCP Org Policies), Terraform state as configuration evidence, Git history as change management evidence, CI/CD pipeline logs as deployment control evidence.

---

## Infrastructure Security Validation

The agent validates infrastructure configurations against SOC 2 requirements.

### Quick Reference: Infrastructure Checks

| Domain | Key Checks | SOC 2 Mapping |
|--------|-----------|---------------|
| Cloud (AWS/Azure/GCP) | Encryption, IAM, logging, network, backup, secrets | CC6, CC7, A1, C1 |
| DNS | SPF, DKIM, DMARC, DNSSEC, CAA | CC6.6, CC2.2 |
| TLS/SSL | TLS 1.2+, AEAD ciphers, HSTS, auto-renewal | CC6.7 |
| Endpoint | MDM, disk encryption, EDR, patching, screen lock | CC6.1, CC6.8, CC7.1 |
| Network | Segmentation, WAF, DDoS, VPN/ZTNA, egress filtering | CC6.6, A1.1 |
| Container | Image scanning, minimal base, no privileged, RBAC | CC6.1, CC7.1 |
| CI/CD | Signed commits, branch protection, SAST/DAST, SBOM | CC7.1, CC8.1 |
| Secrets | Vault storage, rotation policies, git scanning | CC6.1 |

For detailed per-provider control mappings, see [REFERENCE.md](REFERENCE.md#infrastructure-security-checks).

### Example: Infrastructure Audit Command

```bash
# Full infrastructure audit
python scripts/soc2_infrastructure_auditor.py --config infra-config.json

# Audit specific domains only
python scripts/soc2_infrastructure_auditor.py --config infra-config.json \
  --domains dns tls cloud

# JSON output with severity ratings
python scripts/soc2_infrastructure_auditor.py --config infra-config.json --format json

# Generate sample configuration template
python scripts/soc2_infrastructure_auditor.py --generate-template
```

---

## Audit Timeline

### Typical Timeline (First SOC 2)

| Phase | Duration | Activities |
|-------|----------|------------|
| Scoping | 2-4 weeks | Define TSC, system boundaries, auditor selection |
| Gap Analysis | 2-4 weeks | Assess current controls, identify gaps |
| Remediation | 8-16 weeks | Implement missing controls, policies, procedures |
| Type I Audit | 2-4 weeks | Point-in-time control design assessment |
| Type II Observation | 3-12 months | Controls operate, evidence collected continuously |
| Type II Fieldwork | 2-4 weeks | Auditor testing, evidence review, interviews |
| Report Issuance | 2-4 weeks | Draft review, management response, final report |

### Annual Renewal

- Begin renewal planning 3 months before observation period ends
- Maintain continuous compliance between audit periods
- Address prior-year findings before new observation period
- Bridge letters available for gaps between reports

---

## Incident Response Requirements

### IRP Structure

1. **Preparation** -- IR team defined, communication channels established, runbooks for common incidents, legal/PR contacts on retainer.
2. **Detection and Analysis** -- monitoring/alerting coverage, severity classification (SEV1-SEV4), triage procedures, escalation matrix.
3. **Containment, Eradication, Recovery** -- isolate affected systems, preserve evidence, identify root cause, restore and validate.
4. **Post-Incident** -- blameless post-mortem within 5 business days, lessons learned, control improvements, notification assessment (MTTD, MTTR, MTTC tracking).

For severity level definitions and breach notification timelines, see [REFERENCE.md](REFERENCE.md#incident-response-plan).

---

## Tools

### SOC 2 Readiness Checker

```bash
# Full readiness assessment
python scripts/soc2_readiness_checker.py --config org-controls.json

# JSON output for programmatic use
python scripts/soc2_readiness_checker.py --config org-controls.json --format json

# Check specific TSC categories
python scripts/soc2_readiness_checker.py --config org-controls.json \
  --categories security availability

# Include cloud provider control mapping
python scripts/soc2_readiness_checker.py --config org-controls.json --cloud-mapping
```

### Evidence Collector

```bash
# Generate checklist and track status
python scripts/evidence_collector.py --generate-checklist --categories all
python scripts/evidence_collector.py --status evidence-tracker.json
python scripts/evidence_collector.py --dashboard evidence-tracker.json
```

### Infrastructure Auditor

```bash
# Validate infrastructure against SOC 2 requirements
python scripts/soc2_infrastructure_auditor.py --config infra-config.json
python scripts/soc2_infrastructure_auditor.py --config infra-config.json --format json
```

---

## References

| Document | Description |
|----------|-------------|
| [REFERENCE.md](REFERENCE.md) | Detailed TSC controls, infrastructure checks, access control specs, vendor management, training, IRP, BC/DR |
| [Trust Services Criteria Guide](references/trust-services-criteria-guide.md) | Complete TSC reference with control objectives and audit questions |
| [Infrastructure Security Controls](references/infrastructure-security-controls.md) | Cloud, DNS, TLS, endpoint, container, CI/CD security configurations |
| [Audit Preparation Playbook](references/audit-preparation-playbook.md) | End-to-end audit prep guide with timelines, checklists, cost estimation |

---

## Troubleshooting

| Problem | Likely Cause | Resolution |
|---------|-------------|------------|
| Readiness checker scores are 0% across all categories | Controls JSON missing `config_key` values or all set to false | Verify the input JSON maps each TSC control to a boolean value under the correct `config_key`. Run `--generate-sample > sample-config.json` to see the expected structure. |
| Infrastructure auditor reports all checks as "fail" | Infrastructure config JSON is empty or uses wrong key names | Run `--generate-template` to produce a valid template. Populate DNS, TLS, cloud, endpoint, and other sections with actual infrastructure state. |
| Evidence collector checklist missing categories | `--categories` flag filtering output | Use `--categories all` to generate the complete checklist. Available categories: `security`, `availability`, `processing_integrity`, `confidentiality`, `privacy`. |
| Evidence tracker status not updating | Tracker file path incorrect or file not writable | Verify the path passed to `--status` or `--update` points to an existing tracker JSON file. Check file permissions. |
| Cloud mapping not appearing in readiness report | `--cloud-mapping` flag not included | Add `--cloud-mapping` to the readiness checker command to include AWS/Azure/GCP control mappings in the output. |
| Type II observation period too short for auditor | Observation period is less than 3 months | Most CPA firms require a minimum 3-month observation period for Type II. A 6-12 month period carries more weight. Plan the observation window during the scoping phase. |
| Auditor requests evidence not in the tracker | Evidence catalog does not cover all TSC subcriteria for the selected scope | Supplement the auto-generated checklist with auditor-specific evidence requests. Each CPA firm may have additional requirements beyond the standard TSC evidence items. |

---

## Success Criteria

- SOC 2 scope defined with all applicable TSC categories selected, system boundaries documented, and subservice organizations identified (carve-out vs inclusive)
- Gap analysis completed with every identified gap assigned a severity rating, remediation owner, and target completion date
- Readiness score of 80%+ across all in-scope TSC categories before engaging the CPA firm, trending to 95%+ before Type II fieldwork
- Evidence collection framework operational with centralized repository, defined refresh cadence per TSC category, and automated collection where possible
- Infrastructure audit passes with no critical or high-severity findings in DNS, TLS, cloud, endpoint, or access control domains
- Type II observation period of at least 6 months with continuous control operation, quarterly self-assessments, and no significant control failures
- Clean SOC 2 Type II opinion received with any findings addressed by management response and documented remediation plans

---

## Scope & Limitations

**In Scope:**
- SOC 2 Type I and Type II readiness assessment against all TSC categories (CC1-CC9, A1, PI1, C1, P1)
- Infrastructure security validation (DNS, TLS, cloud, endpoint, network, container, CI/CD, secrets)
- Evidence collection framework generation and tracking
- Gap analysis with severity-rated findings and remediation guidance
- Audit timeline planning and CPA firm engagement preparation
- Incident response plan structure and requirements
- Continuous compliance program design

**Out of Scope:**
- CPA firm audit execution (the tools prepare for audit; the actual Type I/II report requires an independent CPA firm)
- SOC 1 (ICFR) assessment (SOC 1 covers financial reporting controls, not security/availability/privacy)
- SOC 3 report generation (SOC 3 is a public-facing summary derived from SOC 2; it requires a completed SOC 2 audit)
- Penetration testing execution (use infrastructure-compliance-auditor or engage a third-party pentest firm)
- GRC platform selection or implementation (the skill is compatible with Vanta, Drata, Secureframe, etc., but does not implement them)
- Legal advice on customer contractual requirements for SOC 2 reports
- Physical security assessments (the infrastructure auditor covers logical controls; physical data center audits require on-site assessment)

---

## Integration Points

| Skill | Integration |
|-------|------------|
| [infrastructure-compliance-auditor](../infrastructure-compliance-auditor/) | Provides Vanta-level infrastructure checks across cloud, DNS, TLS, endpoints, access controls, and CI/CD that map directly to SOC 2 TSC requirements |
| [nist-csf-specialist](../nist-csf-specialist/) | NIST CSF functions map to SOC 2 TSC categories; use the control mapper to build unified control matrices for organizations pursuing both |
| [information-security-manager-iso27001](../information-security-manager-iso27001/) | ISO 27001 Annex A controls provide a management system backbone that satisfies many SOC 2 requirements; shared evidence reduces audit burden |
| [pci-dss-specialist](../pci-dss-specialist/) | PCI DSS requirements overlap with SOC 2 CC6 (access), CC7 (operations), CC8 (change management); shared controls for payment-processing organizations |
| [gdpr-dsgvo-expert](../gdpr-dsgvo-expert/) | GDPR requirements align with SOC 2 Privacy (P1) criteria; organizations processing EU personal data can leverage shared privacy controls |
| [nis2-directive-specialist](../nis2-directive-specialist/) | NIS2 minimum security measures overlap with SOC 2 security criteria; EU entities can map shared incident response, access control, and encryption controls |

---

## Tool Reference

### soc2_readiness_checker.py

Evaluates organizational controls against SOC 2 Trust Services Criteria with per-category scoring.

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | Yes (or `--generate-sample`) | Path to organization controls JSON file with boolean values for each TSC control |
| `--format` | No | Output format: `json` for structured output, omit for human-readable text |
| `--categories` | No | Space-separated TSC categories to assess (e.g., `security availability`). Omit for all. |
| `--cloud-mapping` | No | Include cloud provider (AWS/Azure/GCP) control mappings in the output |
| `--generate-sample` | No | Generate a sample controls JSON template (pipe to file with `> sample-config.json`) |

### evidence_collector.py

Generates evidence collection checklists and tracks evidence gathering status.

| Flag | Required | Description |
|------|----------|-------------|
| `--generate-checklist` | No | Generate an evidence collection checklist for the specified categories |
| `--categories` | No | Space-separated TSC categories: `security`, `availability`, `processing_integrity`, `confidentiality`, `privacy`, or `all` |
| `--status` | No | Path to evidence tracker JSON file to display collection status |
| `--update` | No | Path to evidence tracker JSON file to update (use with `--item` and `--status`) |
| `--item` | No | Evidence item identifier to update (e.g., `CC6.1-MFA`) |
| `--dashboard` | No | Path to evidence tracker JSON file to generate a readiness dashboard |
| `--export` | No | Path to evidence tracker JSON file to export |
| `--format` | No | Export format: `json` for structured output |

### soc2_infrastructure_auditor.py

Audits infrastructure configurations against SOC 2 requirements with severity-rated findings.

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | Yes (or `--generate-template`) | Path to infrastructure configuration JSON file with DNS, TLS, cloud, endpoint, and other domain settings |
| `--format` | No | Output format: `json` for structured findings with severity ratings, omit for human-readable text |
| `--domains` | No | Space-separated infrastructure domains to audit (e.g., `dns tls cloud`). Omit for all domains. |
| `--generate-template` | No | Generate a sample infrastructure configuration template (pipe to file with `> infra-config.json`) |

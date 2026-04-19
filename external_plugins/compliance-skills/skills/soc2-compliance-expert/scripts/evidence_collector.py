#!/usr/bin/env python3
"""
SOC 2 Evidence Collector

Generates evidence collection checklists per TSC category, tracks evidence status,
calculates audit readiness percentage, and manages evidence collection workflows.

Usage:
    python evidence_collector.py --generate-checklist --categories all
    python evidence_collector.py --generate-checklist --categories security availability --format json
    python evidence_collector.py --status evidence-tracker.json
    python evidence_collector.py --update evidence-tracker.json --item CC6.1-MFA --status collected
    python evidence_collector.py --dashboard evidence-tracker.json
    python evidence_collector.py --export evidence-tracker.json --format json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Evidence Definitions by TSC Category
# ---------------------------------------------------------------------------

EVIDENCE_CATALOG: dict[str, dict[str, Any]] = {
    "security": {
        "name": "Security (Common Criteria)",
        "evidence_items": {
            # CC1 - Control Environment
            "CC1.1-CODE_OF_CONDUCT": {
                "name": "Code of Conduct Policy",
                "tsc_criteria": "CC1.1",
                "description": "Signed code of conduct/ethics policy document",
                "evidence_type": "document",
                "collection_method": "HR system export",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Code of conduct policy document (current version)",
                    "Employee acknowledgment records (signed within last 12 months)",
                    "New hire acknowledgment evidence from onboarding",
                ],
            },
            "CC1.2-ORG_STRUCTURE": {
                "name": "Organizational Structure and Oversight",
                "tsc_criteria": "CC1.2",
                "description": "Board/management oversight documentation",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Current organizational chart",
                    "Board/committee meeting minutes (security discussions)",
                    "Security governance committee charter",
                    "CISO/security lead job description and appointment",
                ],
            },
            "CC1.3-ROLES": {
                "name": "Roles and Responsibilities",
                "tsc_criteria": "CC1.3",
                "description": "Defined security roles and RACI matrix",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Security RACI matrix",
                    "Job descriptions with security responsibilities",
                    "Team structure documentation",
                ],
            },
            "CC1.4-BACKGROUND_CHECKS": {
                "name": "Background Check Records",
                "tsc_criteria": "CC1.4",
                "description": "Background check policy and completion evidence",
                "evidence_type": "record",
                "collection_method": "HR system export",
                "refresh_frequency": "per_hire",
                "artifacts": [
                    "Background check policy document",
                    "Background check completion log (sample of hires in period)",
                    "Screening vendor contract",
                ],
            },
            # CC2 - Communication
            "CC2.1-SECURITY_AWARENESS": {
                "name": "Security Awareness Training Records",
                "tsc_criteria": "CC2.1",
                "description": "Training completion records for all employees",
                "evidence_type": "record",
                "collection_method": "LMS export",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Security awareness training curriculum/content",
                    "Training completion report (all employees)",
                    "New hire training completion evidence",
                    "Phishing simulation results (monthly campaigns)",
                ],
            },
            "CC2.2-EXTERNAL_COMMS": {
                "name": "External Security Communication",
                "tsc_criteria": "CC2.2",
                "description": "Public-facing security commitments and notices",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Privacy policy (current published version)",
                    "Security page or trust center URL",
                    "Customer notification procedures for incidents",
                    "Status page configuration",
                ],
            },
            "CC2.3-SYSTEM_DESC": {
                "name": "System Description",
                "tsc_criteria": "CC2.3",
                "description": "SOC 2 system description (Section III)",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "System description document",
                    "Data flow diagrams",
                    "Network architecture diagrams",
                    "System boundary definition",
                    "Subservice organization list",
                ],
            },
            # CC3 - Risk Assessment
            "CC3.1-RISK_ASSESSMENT": {
                "name": "Annual Risk Assessment",
                "tsc_criteria": "CC3.1",
                "description": "Formal risk assessment with risk register",
                "evidence_type": "document",
                "collection_method": "GRC platform or manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Risk assessment report (current year)",
                    "Risk register with scoring and treatment decisions",
                    "Risk acceptance sign-offs for accepted risks",
                ],
            },
            "CC3.2-FRAUD_RISK": {
                "name": "Fraud Risk Assessment",
                "tsc_criteria": "CC3.2",
                "description": "Fraud risk identification and anti-fraud controls",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Fraud risk assessment document",
                    "Segregation of duties matrix",
                    "Anti-fraud control documentation",
                ],
            },
            # CC4 - Monitoring
            "CC4.1-MONITORING": {
                "name": "Continuous Monitoring Evidence",
                "tsc_criteria": "CC4.1",
                "description": "Ongoing security monitoring and evaluations",
                "evidence_type": "system_output",
                "collection_method": "automated",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "SIEM dashboard screenshots or reports",
                    "Vulnerability scan results (internal and external)",
                    "Penetration test report (annual)",
                    "Cloud security posture management report",
                    "Control self-assessment results",
                ],
            },
            "CC4.2-DEFICIENCY_MGMT": {
                "name": "Deficiency Management Records",
                "tsc_criteria": "CC4.2",
                "description": "Finding tracking, remediation, and management reporting",
                "evidence_type": "record",
                "collection_method": "ticketing system",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "Finding/deficiency tracker with status and owners",
                    "Remediation evidence for closed findings",
                    "Management reporting on security metrics",
                ],
            },
            # CC5 - Control Activities
            "CC5.3-POLICIES": {
                "name": "Policy Management Evidence",
                "tsc_criteria": "CC5.3",
                "description": "Policy documents with version control and acknowledgments",
                "evidence_type": "document",
                "collection_method": "policy management system",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Information security policy (current version, approved)",
                    "Acceptable use policy",
                    "Data classification policy",
                    "Incident response policy",
                    "Change management policy",
                    "Access control policy",
                    "Policy review and approval records",
                    "Employee policy acknowledgment records",
                ],
            },
            # CC6 - Access Controls
            "CC6.1-MFA": {
                "name": "MFA Enforcement Evidence",
                "tsc_criteria": "CC6.1",
                "description": "Multi-factor authentication configuration and enrollment",
                "evidence_type": "system_config",
                "collection_method": "IdP dashboard export",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "IdP MFA policy configuration screenshot",
                    "MFA enrollment report (100% coverage)",
                    "MFA method distribution (TOTP, FIDO2, hardware key)",
                    "Conditional access policies",
                ],
            },
            "CC6.1-SSO": {
                "name": "SSO Configuration Evidence",
                "tsc_criteria": "CC6.1",
                "description": "Single Sign-On configuration for SaaS applications",
                "evidence_type": "system_config",
                "collection_method": "IdP dashboard",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "SSO-enabled application inventory",
                    "SAML/OIDC configuration for each application",
                    "Password policy configuration",
                    "Session timeout configuration",
                ],
            },
            "CC6.2-PROVISIONING": {
                "name": "Access Provisioning Records",
                "tsc_criteria": "CC6.2",
                "description": "Access request and approval workflows",
                "evidence_type": "record",
                "collection_method": "ITSM/ticketing system",
                "refresh_frequency": "per_event",
                "artifacts": [
                    "Access request tickets (sample with approvals)",
                    "Role definitions and access matrices",
                    "SCIM provisioning configuration",
                    "New hire access provisioning checklist",
                ],
            },
            "CC6.3-ACCESS_REVIEWS": {
                "name": "Access Review Completion Records",
                "tsc_criteria": "CC6.3",
                "description": "Periodic access reviews with remediation",
                "evidence_type": "record",
                "collection_method": "IAM/IGA platform",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Quarterly privileged access review records",
                    "Semi-annual standard access review records",
                    "Access revocation evidence from reviews",
                    "Service account access review records",
                ],
            },
            "CC6.5-OFFBOARDING": {
                "name": "Terminated User Access Removal",
                "tsc_criteria": "CC6.5",
                "description": "Evidence of access removal upon employee termination",
                "evidence_type": "record",
                "collection_method": "HRIS + IdP correlation",
                "refresh_frequency": "per_event",
                "artifacts": [
                    "Offboarding checklist (completed samples)",
                    "Terminated user access removal evidence (same-day)",
                    "HRIS termination to IdP deactivation correlation",
                    "Equipment return records",
                ],
            },
            "CC6.6-NETWORK": {
                "name": "Network Security Configuration",
                "tsc_criteria": "CC6.6",
                "description": "Firewall rules, WAF, and network segmentation",
                "evidence_type": "system_config",
                "collection_method": "infrastructure export",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Firewall rule sets (deny-by-default demonstrated)",
                    "WAF configuration and rules",
                    "Network segmentation diagram",
                    "VPN/ZTNA configuration",
                ],
            },
            "CC6.7-ENCRYPTION_TRANSIT": {
                "name": "Encryption in Transit Configuration",
                "tsc_criteria": "CC6.7",
                "description": "TLS configuration, HSTS, and certificate management",
                "evidence_type": "system_config",
                "collection_method": "automated scan",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "TLS configuration (minimum TLS 1.2)",
                    "SSL Labs or equivalent scan results (A+ rating)",
                    "HSTS configuration evidence",
                    "Certificate management process (automated renewal)",
                ],
            },
            "CC6.8-ENDPOINT": {
                "name": "Endpoint Security Configuration",
                "tsc_criteria": "CC6.8",
                "description": "EDR, MDM, and disk encryption evidence",
                "evidence_type": "system_config",
                "collection_method": "MDM/EDR dashboard",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "EDR deployment report (coverage percentage)",
                    "MDM enrollment report",
                    "Disk encryption status report (FileVault/BitLocker)",
                    "OS patch compliance report",
                ],
            },
            # CC7 - System Operations
            "CC7.1-VULN_MGMT": {
                "name": "Vulnerability Management Records",
                "tsc_criteria": "CC7.1",
                "description": "Vulnerability scanning results and remediation tracking",
                "evidence_type": "system_output",
                "collection_method": "scanner export",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "Monthly vulnerability scan results (internal)",
                    "Monthly vulnerability scan results (external)",
                    "Vulnerability remediation tracking (SLA compliance)",
                    "Container image scan results",
                    "Dependency scanning results",
                ],
            },
            "CC7.2-LOGGING": {
                "name": "Security Monitoring and Logging",
                "tsc_criteria": "CC7.2",
                "description": "SIEM configuration, log sources, and alert rules",
                "evidence_type": "system_config",
                "collection_method": "SIEM dashboard",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "SIEM log source inventory",
                    "Alert rules and escalation procedures",
                    "Sample security alerts and response evidence",
                    "Log retention configuration (minimum 90 days)",
                ],
            },
            "CC7.3-INCIDENT_RESPONSE": {
                "name": "Incident Response Evidence",
                "tsc_criteria": "CC7.3",
                "description": "IRP documentation, testing, and incident records",
                "evidence_type": "document",
                "collection_method": "manual + ticketing",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Incident response plan (current version)",
                    "Severity level definitions and escalation matrix",
                    "Tabletop exercise records (quarterly)",
                    "Incident tickets and post-mortem reports (if any)",
                    "MTTD/MTTR metrics tracking",
                ],
            },
            # CC8 - Change Management
            "CC8.1-CHANGE_MGMT": {
                "name": "Change Management Records",
                "tsc_criteria": "CC8.1",
                "description": "Change tickets, code reviews, and deployment evidence",
                "evidence_type": "record",
                "collection_method": "ITSM + Git platform",
                "refresh_frequency": "per_change",
                "artifacts": [
                    "Change management policy/procedure",
                    "Sample change tickets with approvals (10-15 samples)",
                    "Code review evidence (PR approvals)",
                    "Branch protection rule configuration",
                    "CI/CD pipeline configuration",
                    "Emergency change records (if any)",
                ],
            },
            # CC9 - Risk Mitigation
            "CC9.1-VENDOR_MGMT": {
                "name": "Vendor Management Records",
                "tsc_criteria": "CC9.1",
                "description": "Vendor risk assessments and SOC 2 report reviews",
                "evidence_type": "document",
                "collection_method": "GRC platform or manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Vendor inventory with risk tiering",
                    "Vendor risk assessment questionnaires (critical vendors)",
                    "Vendor SOC 2 reports reviewed (critical vendors)",
                    "Vendor contractual security requirements (DPA samples)",
                    "Subprocessor list (current)",
                ],
            },
            "CC9.2-INSURANCE": {
                "name": "Risk Transfer and Insurance",
                "tsc_criteria": "CC9.2",
                "description": "Cyber insurance and business continuity coverage",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Cyber liability insurance certificate",
                    "Coverage summary (limits and exclusions)",
                    "Annual coverage review documentation",
                ],
            },
        },
    },
    "availability": {
        "name": "Availability",
        "evidence_items": {
            "A1.1-CAPACITY": {
                "name": "Capacity Planning Evidence",
                "tsc_criteria": "A1.1",
                "description": "Capacity monitoring, auto-scaling, and forecasting",
                "evidence_type": "system_output",
                "collection_method": "monitoring dashboard",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "Capacity monitoring dashboard (utilization metrics)",
                    "Auto-scaling configuration",
                    "Capacity alerting thresholds",
                    "Annual capacity planning review",
                ],
            },
            "A1.2-DR": {
                "name": "Disaster Recovery Plan and Testing",
                "tsc_criteria": "A1.2",
                "description": "DR plan, RTO/RPO definitions, and failover testing",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "semi-annual",
                "artifacts": [
                    "Disaster recovery plan (current version)",
                    "RTO/RPO definitions by system tier",
                    "DR failover test results (annual minimum)",
                    "Multi-region/multi-AZ architecture evidence",
                    "Business impact analysis (BIA)",
                ],
            },
            "A1.3-BACKUP": {
                "name": "Backup Management Evidence",
                "tsc_criteria": "A1.3",
                "description": "Backup configuration, encryption, and restoration testing",
                "evidence_type": "system_config",
                "collection_method": "backup system export",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "Backup configuration (schedule, retention, encryption)",
                    "Monthly backup restoration test results",
                    "Backup monitoring alerts",
                    "Immutable/air-gapped backup configuration",
                ],
            },
            "A1.5-SLA": {
                "name": "SLA Monitoring and Reporting",
                "tsc_criteria": "A1.1",
                "description": "Uptime monitoring, SLA achievement, and status page",
                "evidence_type": "system_output",
                "collection_method": "monitoring platform",
                "refresh_frequency": "monthly",
                "artifacts": [
                    "Monthly uptime reports",
                    "SLA definitions and commitments",
                    "Status page configuration",
                    "Scheduled maintenance notifications",
                ],
            },
        },
    },
    "processing_integrity": {
        "name": "Processing Integrity",
        "evidence_items": {
            "PI1.1-VALIDATION": {
                "name": "Data Validation and Reconciliation",
                "tsc_criteria": "PI1.1",
                "description": "Input validation, processing checks, and reconciliation",
                "evidence_type": "system_config",
                "collection_method": "application documentation",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Input validation rules documentation",
                    "Data reconciliation procedures and results",
                    "Error handling configuration",
                    "Processing integrity monitoring",
                ],
            },
            "PI1.2-ERROR_HANDLING": {
                "name": "Error Detection and Correction Records",
                "tsc_criteria": "PI1.2",
                "description": "Error handling, dead letter queues, and correction procedures",
                "evidence_type": "record",
                "collection_method": "application logs",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Error handling procedures",
                    "Dead letter queue configuration",
                    "Error notification and escalation procedures",
                    "Error trend analysis reports",
                ],
            },
        },
    },
    "confidentiality": {
        "name": "Confidentiality",
        "evidence_items": {
            "C1.1-CLASSIFICATION": {
                "name": "Data Classification Evidence",
                "tsc_criteria": "C1.1",
                "description": "Data classification policy and asset inventory",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Data classification policy",
                    "Data asset inventory with classification labels",
                    "Handling procedures per classification level",
                    "Employee training on classification",
                ],
            },
            "C1.1-ENCRYPTION_REST": {
                "name": "Encryption at Rest Configuration",
                "tsc_criteria": "C1.1",
                "description": "Data at rest encryption with key management",
                "evidence_type": "system_config",
                "collection_method": "cloud provider dashboard",
                "refresh_frequency": "quarterly",
                "artifacts": [
                    "Encryption at rest configuration (all data stores)",
                    "Key management service configuration",
                    "Key rotation policy and evidence",
                    "HSM usage for production keys (if applicable)",
                ],
            },
            "C1.2-DISPOSAL": {
                "name": "Data Disposal Evidence",
                "tsc_criteria": "C1.2",
                "description": "Data retention schedule and disposal records",
                "evidence_type": "record",
                "collection_method": "manual + automated",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Data retention schedule by category",
                    "Automated retention enforcement configuration",
                    "Disposal/destruction records",
                    "Certificates of destruction (physical media)",
                ],
            },
        },
    },
    "privacy": {
        "name": "Privacy",
        "evidence_items": {
            "P1.1-PRIVACY_NOTICE": {
                "name": "Privacy Notice and Consent",
                "tsc_criteria": "P1.1",
                "description": "Published privacy notice with consent management",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Privacy policy (current published version with URL)",
                    "Cookie consent configuration",
                    "Consent management platform configuration",
                    "Terms of service (current version)",
                ],
            },
            "P1.4-RETENTION": {
                "name": "Retention and Disposal Schedule",
                "tsc_criteria": "P1.4",
                "description": "Personal data retention periods and disposal procedures",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "Personal data retention schedule",
                    "Automated retention enforcement evidence",
                    "Legal hold procedures",
                    "Backup data retention scope",
                ],
            },
            "P1.5-DSR": {
                "name": "Data Subject Request Records",
                "tsc_criteria": "P1.5",
                "description": "DSR intake, processing, and response tracking",
                "evidence_type": "record",
                "collection_method": "privacy management tool",
                "refresh_frequency": "per_request",
                "artifacts": [
                    "DSR intake and tracking procedures",
                    "DSR response log (with response times)",
                    "Identity verification procedures for DSRs",
                    "Sample completed DSR records",
                ],
            },
            "P1.6-DPA": {
                "name": "Data Processing Agreements",
                "tsc_criteria": "P1.6",
                "description": "DPAs with all data processors and subprocessors",
                "evidence_type": "document",
                "collection_method": "legal/manual",
                "refresh_frequency": "annual",
                "artifacts": [
                    "DPA template (current version)",
                    "Executed DPAs with critical processors",
                    "Subprocessor list with DPA status",
                    "Subprocessor change notification procedures",
                ],
            },
            "P1.8-PIA": {
                "name": "Privacy Impact Assessments",
                "tsc_criteria": "P1.8",
                "description": "PIAs for new or changed data processing activities",
                "evidence_type": "document",
                "collection_method": "manual",
                "refresh_frequency": "per_change",
                "artifacts": [
                    "PIA template and procedure",
                    "Completed PIAs (sample)",
                    "Privacy compliance monitoring metrics",
                    "Annual privacy program review",
                ],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Evidence Tracking
# ---------------------------------------------------------------------------

def generate_checklist(categories: list[str] | None = None) -> dict:
    """Generate evidence collection checklist for specified categories."""
    if categories is None or "all" in categories:
        active = EVIDENCE_CATALOG
    else:
        active = {k: v for k, v in EVIDENCE_CATALOG.items() if k in categories}

    checklist = {
        "generated_date": datetime.now().isoformat(),
        "categories": [],
        "total_items": 0,
        "total_artifacts": 0,
    }

    for cat_id, cat_def in active.items():
        cat_items = []
        for item_id, item_def in cat_def["evidence_items"].items():
            cat_items.append({
                "item_id": item_id,
                "name": item_def["name"],
                "tsc_criteria": item_def["tsc_criteria"],
                "description": item_def["description"],
                "evidence_type": item_def["evidence_type"],
                "collection_method": item_def["collection_method"],
                "refresh_frequency": item_def["refresh_frequency"],
                "artifacts": item_def["artifacts"],
                "status": "pending",
                "collected_date": None,
                "collector": None,
                "notes": "",
                "artifact_statuses": {a: "pending" for a in item_def["artifacts"]},
            })
            checklist["total_artifacts"] += len(item_def["artifacts"])

        checklist["categories"].append({
            "category_id": cat_id,
            "category_name": cat_def["name"],
            "items": cat_items,
        })
        checklist["total_items"] += len(cat_items)

    return checklist


def load_tracker(path: str) -> dict:
    """Load evidence tracker from JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Tracker file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in tracker file: {e}", file=sys.stderr)
        sys.exit(1)


def save_tracker(tracker: dict, path: str) -> None:
    """Save evidence tracker to JSON file."""
    with open(path, "w") as f:
        json.dump(tracker, f, indent=2)
    print(f"Tracker saved to: {path}")


def update_item_status(tracker: dict, item_id: str, new_status: str, collector: str | None = None, notes: str | None = None) -> bool:
    """Update the status of an evidence item in the tracker."""
    valid_statuses = {"pending", "in_progress", "collected", "missing", "not_applicable"}
    if new_status not in valid_statuses:
        print(f"Error: Invalid status '{new_status}'. Must be one of: {', '.join(sorted(valid_statuses))}", file=sys.stderr)
        return False

    for category in tracker.get("categories", []):
        for item in category.get("items", []):
            if item["item_id"] == item_id:
                item["status"] = new_status
                if new_status == "collected":
                    item["collected_date"] = datetime.now().isoformat()
                if collector:
                    item["collector"] = collector
                if notes:
                    item["notes"] = notes
                return True

    print(f"Error: Item '{item_id}' not found in tracker", file=sys.stderr)
    return False


def calculate_readiness(tracker: dict) -> dict:
    """Calculate overall and per-category readiness percentages."""
    results = {
        "assessment_date": datetime.now().isoformat(),
        "overall": {},
        "categories": [],
    }

    total_items = 0
    total_collected = 0
    total_pending = 0
    total_missing = 0
    total_in_progress = 0
    total_na = 0

    for category in tracker.get("categories", []):
        cat_total = 0
        cat_collected = 0
        cat_pending = 0
        cat_missing = 0
        cat_in_progress = 0
        cat_na = 0

        for item in category.get("items", []):
            status = item.get("status", "pending")
            cat_total += 1

            if status == "collected":
                cat_collected += 1
            elif status == "pending":
                cat_pending += 1
            elif status == "missing":
                cat_missing += 1
            elif status == "in_progress":
                cat_in_progress += 1
            elif status == "not_applicable":
                cat_na += 1

        applicable = cat_total - cat_na
        readiness_pct = round((cat_collected / applicable) * 100, 1) if applicable > 0 else 100.0

        results["categories"].append({
            "category_id": category["category_id"],
            "category_name": category["category_name"],
            "total": cat_total,
            "collected": cat_collected,
            "in_progress": cat_in_progress,
            "pending": cat_pending,
            "missing": cat_missing,
            "not_applicable": cat_na,
            "readiness_pct": readiness_pct,
        })

        total_items += cat_total
        total_collected += cat_collected
        total_pending += cat_pending
        total_missing += cat_missing
        total_in_progress += cat_in_progress
        total_na += cat_na

    total_applicable = total_items - total_na
    overall_pct = round((total_collected / total_applicable) * 100, 1) if total_applicable > 0 else 100.0

    results["overall"] = {
        "total_items": total_items,
        "collected": total_collected,
        "in_progress": total_in_progress,
        "pending": total_pending,
        "missing": total_missing,
        "not_applicable": total_na,
        "readiness_pct": overall_pct,
    }

    return results


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_checklist_human(checklist: dict) -> str:
    """Format checklist as human-readable output."""
    lines = []
    lines.append("=" * 78)
    lines.append("SOC 2 EVIDENCE COLLECTION CHECKLIST")
    lines.append("=" * 78)
    lines.append(f"Generated: {checklist['generated_date'][:10]}")
    lines.append(f"Total Evidence Items: {checklist['total_items']}")
    lines.append(f"Total Artifacts: {checklist['total_artifacts']}")
    lines.append("")

    for cat in checklist["categories"]:
        lines.append("-" * 78)
        lines.append(f"  {cat['category_name'].upper()} ({len(cat['items'])} items)")
        lines.append("-" * 78)

        for item in cat["items"]:
            lines.append(f"\n  [ ] {item['item_id']}: {item['name']}")
            lines.append(f"      TSC: {item['tsc_criteria']} | Type: {item['evidence_type']} | Refresh: {item['refresh_frequency']}")
            lines.append(f"      Collection: {item['collection_method']}")
            lines.append(f"      Artifacts required:")
            for artifact in item["artifacts"]:
                lines.append(f"        [ ] {artifact}")

    lines.append("")
    lines.append("=" * 78)
    lines.append("Status Legend: [ ] Pending  [~] In Progress  [x] Collected  [!] Missing  [-] N/A")
    lines.append("=" * 78)

    return "\n".join(lines)


def format_dashboard(readiness: dict) -> str:
    """Format readiness dashboard as human-readable output."""
    lines = []
    lines.append("=" * 78)
    lines.append("SOC 2 EVIDENCE READINESS DASHBOARD")
    lines.append("=" * 78)
    lines.append(f"Assessment Date: {readiness['assessment_date'][:10]}")
    lines.append("")

    overall = readiness["overall"]
    bar_filled = int(overall["readiness_pct"] / 5)
    bar_empty = 20 - bar_filled
    bar = "#" * bar_filled + "." * bar_empty

    lines.append(f"OVERALL READINESS: [{bar}] {overall['readiness_pct']}%")
    lines.append(f"  Collected: {overall['collected']} | In Progress: {overall['in_progress']} | Pending: {overall['pending']} | Missing: {overall['missing']} | N/A: {overall['not_applicable']}")
    lines.append("")

    lines.append("-" * 78)
    lines.append(f"  {'Category':<35} {'Readiness':>10}   {'Collected':>9} {'Progress':>9} {'Pending':>8} {'Missing':>8}")
    lines.append("-" * 78)

    for cat in readiness["categories"]:
        cat_bar_filled = int(cat["readiness_pct"] / 10)
        cat_bar_empty = 10 - cat_bar_filled
        cat_bar = "#" * cat_bar_filled + "." * cat_bar_empty

        status_icon = "PASS" if cat["readiness_pct"] >= 80 else "WARN" if cat["readiness_pct"] >= 50 else "FAIL"

        lines.append(
            f"  [{status_icon}] {cat['category_name']:<30} [{cat_bar}] {cat['readiness_pct']:>5.1f}%"
            f"   {cat['collected']:>5}/{cat['total']:<3}"
            f" {cat['in_progress']:>6}"
            f" {cat['pending']:>8}"
            f" {cat['missing']:>8}"
        )

    lines.append("")

    # Recommendations
    if overall["readiness_pct"] >= 90:
        lines.append("STATUS: Ready for audit. Final review of collected evidence recommended.")
    elif overall["readiness_pct"] >= 70:
        lines.append("STATUS: Nearly ready. Focus on collecting remaining evidence items.")
    elif overall["readiness_pct"] >= 50:
        lines.append("STATUS: Moderate readiness. Significant evidence gaps remain.")
    else:
        lines.append("STATUS: Not ready. Major evidence collection effort required.")

    if overall["missing"] > 0:
        lines.append(f"WARNING: {overall['missing']} evidence items marked as MISSING. These require immediate attention.")

    lines.append("")
    lines.append("=" * 78)

    return "\n".join(lines)


def format_status_report(tracker: dict) -> str:
    """Format detailed status report from tracker."""
    readiness = calculate_readiness(tracker)
    lines = [format_dashboard(readiness)]

    lines.append("")
    lines.append("-" * 78)
    lines.append("DETAILED ITEM STATUS")
    lines.append("-" * 78)

    status_icons = {
        "collected": "[x]",
        "in_progress": "[~]",
        "pending": "[ ]",
        "missing": "[!]",
        "not_applicable": "[-]",
    }

    for category in tracker.get("categories", []):
        lines.append(f"\n  {category['category_name']}")
        lines.append(f"  {'~' * 60}")

        for item in category.get("items", []):
            icon = status_icons.get(item.get("status", "pending"), "[ ]")
            lines.append(f"    {icon} {item['item_id']}: {item['name']}")
            if item.get("collected_date"):
                lines.append(f"        Collected: {item['collected_date'][:10]}")
            if item.get("collector"):
                lines.append(f"        Collector: {item['collector']}")
            if item.get("notes"):
                lines.append(f"        Notes: {item['notes']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SOC 2 Evidence Collector - Generate checklists, track evidence, and measure audit readiness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --generate-checklist --categories all
  %(prog)s --generate-checklist --categories security availability --format json > tracker.json
  %(prog)s --status tracker.json
  %(prog)s --update tracker.json --item CC6.1-MFA --status collected --collector "Jane Doe"
  %(prog)s --dashboard tracker.json
  %(prog)s --export tracker.json --format json

Evidence Status Values:
  pending           Not yet started
  in_progress       Collection underway
  collected         Evidence gathered and verified
  missing           Evidence not available (requires attention)
  not_applicable    Not relevant to organization
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generate-checklist",
        action="store_true",
        help="Generate evidence collection checklist",
    )
    group.add_argument(
        "--status",
        metavar="TRACKER_FILE",
        help="Display status report from tracker file",
    )
    group.add_argument(
        "--update",
        metavar="TRACKER_FILE",
        help="Update evidence item status in tracker file",
    )
    group.add_argument(
        "--dashboard",
        metavar="TRACKER_FILE",
        help="Display readiness dashboard from tracker file",
    )
    group.add_argument(
        "--export",
        metavar="TRACKER_FILE",
        help="Export tracker data",
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        default=["all"],
        help="TSC categories: all, security, availability, processing_integrity, confidentiality, privacy",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--item",
        help="Evidence item ID (for --update)",
    )
    parser.add_argument(
        "--new-status",
        dest="new_status",
        choices=["pending", "in_progress", "collected", "missing", "not_applicable"],
        help="New status value (for --update). Use this or positional --status-value.",
    )
    parser.add_argument(
        "--collector",
        help="Name of person who collected the evidence (for --update)",
    )
    parser.add_argument(
        "--notes",
        help="Additional notes (for --update)",
    )

    args = parser.parse_args()

    if args.generate_checklist:
        checklist = generate_checklist(args.categories)
        if args.format == "json":
            print(json.dumps(checklist, indent=2))
        else:
            print(format_checklist_human(checklist))

    elif args.status:
        tracker = load_tracker(args.status)
        print(format_status_report(tracker))

    elif args.update:
        if not args.item:
            parser.error("--item is required with --update")
        status_val = args.new_status
        if not status_val:
            parser.error("--new-status is required with --update")
        tracker = load_tracker(args.update)
        if update_item_status(tracker, args.item, status_val, args.collector, args.notes):
            save_tracker(tracker, args.update)
            print(f"Updated {args.item} to status: {status_val}")
        else:
            sys.exit(1)

    elif args.dashboard:
        tracker = load_tracker(args.dashboard)
        readiness = calculate_readiness(tracker)
        if args.format == "json":
            print(json.dumps(readiness, indent=2))
        else:
            print(format_dashboard(readiness))

    elif args.export:
        tracker = load_tracker(args.export)
        if args.format == "json":
            readiness = calculate_readiness(tracker)
            export = {
                "readiness": readiness,
                "tracker": tracker,
            }
            print(json.dumps(export, indent=2))
        else:
            print(format_status_report(tracker))


if __name__ == "__main__":
    main()

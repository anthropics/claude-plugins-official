#!/usr/bin/env python3
"""
SOC 2 Readiness Checker

Evaluates an organization's controls against SOC 2 Trust Services Criteria (TSC).
Scores readiness (0-100) per category, identifies gaps, and provides remediation steps.
Includes control mapping to common cloud services (AWS, GCP, Azure).

Usage:
    python soc2_readiness_checker.py --config org-controls.json
    python soc2_readiness_checker.py --config org-controls.json --format json
    python soc2_readiness_checker.py --config org-controls.json --categories security availability
    python soc2_readiness_checker.py --config org-controls.json --cloud-mapping
    python soc2_readiness_checker.py --generate-sample > sample-config.json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# TSC Control Definitions
# ---------------------------------------------------------------------------

TSC_CONTROLS: dict[str, dict[str, Any]] = {
    "security": {
        "name": "Security (Common Criteria)",
        "description": "Protection against unauthorized access, both logical and physical",
        "controls": {
            "CC1.1": {
                "name": "Code of Conduct / Ethics Policy",
                "description": "Organization has documented code of conduct signed by all employees",
                "config_key": "code_of_conduct",
                "remediation": "Draft and publish a code of conduct policy. Require all employees to acknowledge annually via HR system or policy management platform.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC1.2": {
                "name": "Board / Management Oversight",
                "description": "Board or management committee provides oversight of security program",
                "config_key": "board_oversight",
                "remediation": "Establish a security governance committee with documented charter. Schedule quarterly security briefings to board or executive team.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC1.3": {
                "name": "Roles and Responsibilities",
                "description": "Security roles, responsibilities, and organizational structure are defined",
                "config_key": "roles_defined",
                "remediation": "Create RACI matrix for security functions. Document job descriptions with security responsibilities. Designate CISO or security lead.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC1.4": {
                "name": "Hiring and Background Checks",
                "description": "Background checks performed for employees with access to sensitive data",
                "config_key": "background_checks",
                "remediation": "Implement background check policy for all employees. Use a screening vendor for criminal, education, and employment verification.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC2.1": {
                "name": "Internal Security Communication",
                "description": "Security policies and objectives communicated internally",
                "config_key": "internal_communication",
                "remediation": "Deploy centralized policy portal. Send quarterly security newsletters. Include security in onboarding materials.",
                "weight": 1,
                "cloud_mapping": {},
            },
            "CC2.2": {
                "name": "External Communication",
                "description": "Security commitments communicated externally (privacy policy, trust center)",
                "config_key": "external_communication",
                "remediation": "Publish privacy policy and security page. Create trust center with compliance documentation. Document customer notification procedures.",
                "weight": 1,
                "cloud_mapping": {},
            },
            "CC2.3": {
                "name": "System Description",
                "description": "Accurate system description documenting boundaries and components",
                "config_key": "system_description",
                "remediation": "Author system description covering infrastructure, software, people, procedures, and data. Include data flow diagrams and system boundaries.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "CC3.1": {
                "name": "Risk Assessment",
                "description": "Annual risk assessment identifying threats, vulnerabilities, and risk treatments",
                "config_key": "risk_assessment",
                "remediation": "Conduct formal annual risk assessment. Maintain risk register with likelihood/impact scoring. Document risk treatment decisions.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "CC3.2": {
                "name": "Fraud Risk Assessment",
                "description": "Fraud risks identified and assessed with anti-fraud controls",
                "config_key": "fraud_risk_assessment",
                "remediation": "Perform fraud risk assessment covering financial, data manipulation, and insider threat risks. Implement segregation of duties.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC4.1": {
                "name": "Continuous Monitoring",
                "description": "Ongoing monitoring of controls through automated and manual processes",
                "config_key": "continuous_monitoring",
                "remediation": "Deploy SIEM for security event monitoring. Implement cloud security posture management (CSPM). Establish KPI dashboard for security metrics.",
                "weight": 3,
                "cloud_mapping": {
                    "aws": ["AWS Security Hub", "Amazon GuardDuty", "AWS Config"],
                    "azure": ["Microsoft Defender for Cloud", "Azure Monitor", "Azure Policy"],
                    "gcp": ["Security Command Center", "Cloud Monitoring", "Policy Intelligence"],
                },
            },
            "CC4.2": {
                "name": "Deficiency Reporting",
                "description": "Control deficiencies identified, reported, and remediated",
                "config_key": "deficiency_reporting",
                "remediation": "Establish finding management process with severity classification. Assign remediation owners and deadlines. Report to management monthly.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC5.1": {
                "name": "Control Activities Design",
                "description": "Control activities selected and developed to mitigate risks",
                "config_key": "control_activities",
                "remediation": "Map controls to identified risks. Document control design rationale. Classify controls as preventive, detective, or corrective.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC5.3": {
                "name": "Policy Management",
                "description": "Policies documented, approved, distributed, and acknowledged",
                "config_key": "policy_management",
                "remediation": "Implement policy management system with version control. Establish annual review cycle. Track employee acknowledgments.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "CC6.1": {
                "name": "Logical Access Security",
                "description": "Authentication and authorization controls implemented (SSO, MFA)",
                "config_key": "logical_access",
                "remediation": "Deploy centralized identity provider with SSO. Enforce MFA for all users. Implement role-based access control (RBAC).",
                "weight": 5,
                "cloud_mapping": {
                    "aws": ["AWS IAM", "AWS SSO (Identity Center)", "AWS Organizations"],
                    "azure": ["Azure Active Directory", "Conditional Access", "PIM"],
                    "gcp": ["Cloud IAM", "Identity Platform", "BeyondCorp Enterprise"],
                },
            },
            "CC6.2": {
                "name": "Access Provisioning",
                "description": "Access provisioned based on role with documented approval",
                "config_key": "access_provisioning",
                "remediation": "Implement access request workflow with manager approval. Use SCIM for automated provisioning. Maintain role definitions.",
                "weight": 4,
                "cloud_mapping": {},
            },
            "CC6.3": {
                "name": "Access Reviews and Removal",
                "description": "Periodic access reviews performed, access removed on termination",
                "config_key": "access_reviews",
                "remediation": "Schedule quarterly access reviews for privileged accounts, semi-annual for standard. Automate deprovisioning on termination via HRIS integration.",
                "weight": 5,
                "cloud_mapping": {},
            },
            "CC6.4": {
                "name": "Physical Access Controls",
                "description": "Physical access to facilities and data centers restricted and monitored",
                "config_key": "physical_access",
                "remediation": "Implement badge access system. Maintain visitor logs. Ensure data center has biometric access, CCTV, and environmental controls.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "CC6.6": {
                "name": "Network Security",
                "description": "Network boundaries protected (firewalls, WAF, segmentation)",
                "config_key": "network_security",
                "remediation": "Configure firewalls with deny-by-default rules. Deploy WAF on public endpoints. Implement network segmentation between environments.",
                "weight": 4,
                "cloud_mapping": {
                    "aws": ["Security Groups", "NACLs", "AWS WAF", "AWS Shield"],
                    "azure": ["NSGs", "Azure Firewall", "Azure WAF", "DDoS Protection"],
                    "gcp": ["VPC Firewall Rules", "Cloud Armor", "Cloud NAT"],
                },
            },
            "CC6.7": {
                "name": "Encryption in Transit",
                "description": "Data encrypted in transit using TLS 1.2+",
                "config_key": "encryption_transit",
                "remediation": "Enforce TLS 1.2 minimum (TLS 1.3 preferred). Configure HSTS headers. Use AEAD cipher suites only. Automate certificate management.",
                "weight": 4,
                "cloud_mapping": {
                    "aws": ["ACM", "ALB/NLB TLS termination", "CloudFront"],
                    "azure": ["Application Gateway", "Azure Front Door", "Azure CDN"],
                    "gcp": ["Cloud Load Balancing", "Certificate Manager", "Cloud CDN"],
                },
            },
            "CC6.8": {
                "name": "Endpoint Protection",
                "description": "Malware prevention and endpoint security deployed",
                "config_key": "endpoint_protection",
                "remediation": "Deploy EDR solution (CrowdStrike, SentinelOne). Enable disk encryption on all devices. Implement MDM for device management.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "CC7.1": {
                "name": "Vulnerability Management",
                "description": "Regular vulnerability scanning with defined remediation SLAs",
                "config_key": "vulnerability_management",
                "remediation": "Implement monthly vulnerability scanning (internal and external). Define remediation SLAs by severity. Track remediation completion.",
                "weight": 4,
                "cloud_mapping": {
                    "aws": ["Amazon Inspector", "ECR image scanning"],
                    "azure": ["Defender for Cloud", "Defender for Containers"],
                    "gcp": ["Security Command Center", "Artifact Analysis"],
                },
            },
            "CC7.2": {
                "name": "Security Monitoring and Alerting",
                "description": "Security events monitored with alerting for anomalies",
                "config_key": "security_monitoring",
                "remediation": "Deploy SIEM with log aggregation from all critical systems. Define alert rules for security events. Establish 24/7 monitoring capability.",
                "weight": 4,
                "cloud_mapping": {
                    "aws": ["CloudTrail", "CloudWatch", "VPC Flow Logs", "GuardDuty"],
                    "azure": ["Azure Monitor", "Log Analytics", "Microsoft Sentinel"],
                    "gcp": ["Cloud Audit Logs", "Cloud Logging", "Chronicle SIEM"],
                },
            },
            "CC7.3": {
                "name": "Incident Response",
                "description": "Incident response plan documented, tested, and maintained",
                "config_key": "incident_response",
                "remediation": "Document incident response plan with severity levels and escalation paths. Conduct quarterly tabletop exercises. Track MTTD and MTTR metrics.",
                "weight": 5,
                "cloud_mapping": {},
            },
            "CC8.1": {
                "name": "Change Management",
                "description": "Changes authorized, tested, and approved before deployment",
                "config_key": "change_management",
                "remediation": "Implement change management workflow with approval gates. Require code reviews for all changes. Enforce branch protection rules.",
                "weight": 4,
                "cloud_mapping": {},
            },
            "CC9.1": {
                "name": "Vendor Risk Management",
                "description": "Third-party vendors assessed for security risk",
                "config_key": "vendor_management",
                "remediation": "Establish vendor risk assessment program. Tier vendors by data access and criticality. Collect SOC 2 reports from critical vendors annually.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "CC9.2": {
                "name": "Risk Transfer",
                "description": "Cyber insurance and risk transfer mechanisms in place",
                "config_key": "risk_transfer",
                "remediation": "Obtain cyber liability insurance. Review coverage annually against risk profile. Ensure coverage includes breach response costs.",
                "weight": 1,
                "cloud_mapping": {},
            },
        },
    },
    "availability": {
        "name": "Availability",
        "description": "System availability for operation and use as committed",
        "controls": {
            "A1.1": {
                "name": "Capacity Planning",
                "description": "System capacity monitored and managed to meet availability commitments",
                "config_key": "capacity_planning",
                "remediation": "Implement capacity monitoring dashboards. Configure auto-scaling with defined limits. Set alerting thresholds at 70%, 85%, 95% utilization.",
                "weight": 3,
                "cloud_mapping": {
                    "aws": ["Auto Scaling", "CloudWatch Metrics", "Compute Optimizer"],
                    "azure": ["Azure Autoscale", "Azure Monitor Metrics", "Advisor"],
                    "gcp": ["Autoscaler", "Cloud Monitoring", "Recommender"],
                },
            },
            "A1.2": {
                "name": "Disaster Recovery",
                "description": "DR plan documented with defined RTO/RPO and tested regularly",
                "config_key": "disaster_recovery",
                "remediation": "Document DR plan with RTO/RPO per system tier. Deploy multi-region/multi-AZ architecture for Tier 1 systems. Conduct annual DR failover tests.",
                "weight": 5,
                "cloud_mapping": {
                    "aws": ["AWS Backup", "S3 Cross-Region Replication", "Route 53 failover"],
                    "azure": ["Azure Site Recovery", "Geo-redundant Storage", "Traffic Manager"],
                    "gcp": ["Cloud Storage dual-region", "Regional persistent disks", "Cloud DNS"],
                },
            },
            "A1.3": {
                "name": "Recovery Testing",
                "description": "Backup restoration and DR recovery tested with documented results",
                "config_key": "recovery_testing",
                "remediation": "Schedule monthly backup restoration tests. Conduct semi-annual DR failover tests. Document results including RTO/RPO achievement.",
                "weight": 4,
                "cloud_mapping": {},
            },
            "A1.4": {
                "name": "Backup Management",
                "description": "Backups performed regularly with encryption and retention policies",
                "config_key": "backup_management",
                "remediation": "Configure daily backups for production data. Enable backup encryption. Set 30-day minimum retention. Implement immutable backups for ransomware protection.",
                "weight": 4,
                "cloud_mapping": {
                    "aws": ["AWS Backup", "S3 Versioning", "RDS automated backups"],
                    "azure": ["Azure Backup", "Blob versioning", "SQL automated backups"],
                    "gcp": ["Cloud Storage versioning", "Cloud SQL automated backups", "Persistent disk snapshots"],
                },
            },
            "A1.5": {
                "name": "SLA Management",
                "description": "Uptime SLAs defined, monitored, and reported",
                "config_key": "sla_management",
                "remediation": "Define uptime SLAs (99.9% minimum). Deploy status page for external visibility. Monitor SLA achievement monthly. Document credit/penalty structure.",
                "weight": 2,
                "cloud_mapping": {},
            },
        },
    },
    "processing_integrity": {
        "name": "Processing Integrity",
        "description": "System processing is complete, valid, accurate, timely, and authorized",
        "controls": {
            "PI1.1": {
                "name": "Data Completeness and Accuracy",
                "description": "Processing controls ensure completeness and accuracy of data",
                "config_key": "data_completeness",
                "remediation": "Implement input validation rules. Deploy data reconciliation procedures. Use checksums for data integrity verification.",
                "weight": 4,
                "cloud_mapping": {},
            },
            "PI1.2": {
                "name": "Error Handling",
                "description": "Errors detected, reported, and corrected in a timely manner",
                "config_key": "error_handling",
                "remediation": "Implement comprehensive error handling with classification. Configure dead letter queues for failed messages. Establish error notification and escalation procedures.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "PI1.3": {
                "name": "Input/Output Validation",
                "description": "Input and output data validated for completeness and accuracy",
                "config_key": "io_validation",
                "remediation": "Implement input validation at all API endpoints. Deploy output reconciliation procedures. Use schema validation for data exchanges.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "PI1.4": {
                "name": "Processing Authorization",
                "description": "Data processing authorized and scheduled appropriately",
                "config_key": "processing_authorization",
                "remediation": "Document authorized processing activities. Implement job scheduling with audit trails. Require approval for ad-hoc data processing.",
                "weight": 2,
                "cloud_mapping": {},
            },
        },
    },
    "confidentiality": {
        "name": "Confidentiality",
        "description": "Information designated as confidential is protected as committed",
        "controls": {
            "C1.1": {
                "name": "Data Classification",
                "description": "Data classified by sensitivity with handling procedures per level",
                "config_key": "data_classification",
                "remediation": "Define data classification levels (Public, Internal, Confidential, Restricted). Create handling procedures per level. Train employees on classification.",
                "weight": 4,
                "cloud_mapping": {},
            },
            "C1.2": {
                "name": "Encryption at Rest",
                "description": "Confidential data encrypted at rest using AES-256",
                "config_key": "encryption_rest",
                "remediation": "Enable encryption at rest for all data stores. Use AES-256 encryption with managed keys. Implement key rotation policy (annual minimum).",
                "weight": 5,
                "cloud_mapping": {
                    "aws": ["AWS KMS", "S3 default encryption", "RDS encryption", "EBS encryption"],
                    "azure": ["Azure Key Vault", "Storage Service Encryption", "TDE for SQL"],
                    "gcp": ["Cloud KMS", "Default encryption", "CMEK", "Cloud HSM"],
                },
            },
            "C1.3": {
                "name": "Data Disposal",
                "description": "Confidential data disposed of securely per retention schedule",
                "config_key": "data_disposal",
                "remediation": "Define data retention schedule. Implement automated deletion per schedule. Use cryptographic erasure for cloud data. Obtain certificates of destruction for physical media.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "C1.4": {
                "name": "NDA Management",
                "description": "NDAs in place before sharing confidential information",
                "config_key": "nda_management",
                "remediation": "Require NDA before sharing confidential information with third parties. Maintain NDA register with expiration tracking. Conduct annual review.",
                "weight": 2,
                "cloud_mapping": {},
            },
        },
    },
    "privacy": {
        "name": "Privacy",
        "description": "Personal information collected, used, retained, disclosed, and disposed per commitments",
        "controls": {
            "P1.1": {
                "name": "Privacy Notice",
                "description": "Privacy notice published covering data collection and use practices",
                "config_key": "privacy_notice",
                "remediation": "Publish comprehensive privacy notice. Cover categories of data collected, purposes, third-party sharing, and data subject rights. Update annually.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "P1.2": {
                "name": "Consent Management",
                "description": "Consent obtained and managed for personal data processing",
                "config_key": "consent_management",
                "remediation": "Implement granular consent management (not all-or-nothing). Record consent with timestamp and version. Provide easy withdrawal mechanism.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "P1.3": {
                "name": "Data Minimization",
                "description": "Personal data collection limited to what is necessary",
                "config_key": "data_minimization",
                "remediation": "Conduct data minimization review. Document justification for each data element collected. Eliminate unnecessary data collection.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "P1.4": {
                "name": "Retention and Disposal",
                "description": "Personal data retained per schedule and disposed of securely",
                "config_key": "retention_disposal",
                "remediation": "Define retention periods by data category. Implement automated retention enforcement. Include backup data in scope.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "P1.5": {
                "name": "Data Subject Rights",
                "description": "Procedures for handling data subject access, correction, and deletion requests",
                "config_key": "data_subject_rights",
                "remediation": "Implement DSR intake and tracking system. Define 30-day response SLA. Train support team on DSR handling procedures.",
                "weight": 3,
                "cloud_mapping": {},
            },
            "P1.6": {
                "name": "Third-Party Disclosure",
                "description": "Data sharing with third parties governed by agreements",
                "config_key": "third_party_disclosure",
                "remediation": "Execute DPAs with all data processors. Maintain subprocessor list. Notify customers of subprocessor changes.",
                "weight": 2,
                "cloud_mapping": {},
            },
            "P1.7": {
                "name": "Data Quality",
                "description": "Procedures to maintain accuracy and completeness of personal data",
                "config_key": "data_quality",
                "remediation": "Implement data accuracy verification procedures. Provide self-service correction for data subjects. Conduct periodic data quality audits.",
                "weight": 1,
                "cloud_mapping": {},
            },
            "P1.8": {
                "name": "Privacy Monitoring",
                "description": "Privacy compliance monitored and enforced with PIAs for new processing",
                "config_key": "privacy_monitoring",
                "remediation": "Conduct Privacy Impact Assessments (PIAs) for new processing activities. Monitor privacy compliance metrics. Perform annual privacy program review.",
                "weight": 2,
                "cloud_mapping": {},
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Assessment Logic
# ---------------------------------------------------------------------------

CONTROL_STATUS_SCORES = {
    "implemented": 100,
    "partially_implemented": 50,
    "planned": 20,
    "not_implemented": 0,
    "not_applicable": None,
}


def load_config(path: str) -> dict:
    """Load organization controls configuration from JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        sys.exit(1)


def assess_category(category_id: str, category_def: dict, org_controls: dict) -> dict:
    """Assess a single TSC category against organization controls."""
    controls = category_def["controls"]
    results = []
    total_weighted_score = 0
    total_weight = 0
    gaps = []
    implemented_count = 0
    total_applicable = 0

    for control_id, control_def in controls.items():
        config_key = control_def["config_key"]
        status = org_controls.get(config_key, "not_implemented")
        weight = control_def["weight"]

        if isinstance(status, dict):
            status_value = status.get("status", "not_implemented")
            notes = status.get("notes", "")
        else:
            status_value = status
            notes = ""

        score = CONTROL_STATUS_SCORES.get(status_value)

        if score is None:
            # not_applicable
            result = {
                "control_id": control_id,
                "name": control_def["name"],
                "status": "not_applicable",
                "score": "N/A",
                "notes": notes,
            }
            results.append(result)
            continue

        total_applicable += 1
        total_weighted_score += score * weight
        total_weight += weight

        if score == 100:
            implemented_count += 1

        if score < 100:
            gaps.append({
                "control_id": control_id,
                "name": control_def["name"],
                "status": status_value,
                "current_score": score,
                "weight": weight,
                "remediation": control_def["remediation"],
                "priority": "critical" if weight >= 4 else "high" if weight >= 3 else "medium" if weight >= 2 else "low",
            })

        result = {
            "control_id": control_id,
            "name": control_def["name"],
            "status": status_value,
            "score": score,
            "weight": weight,
            "notes": notes,
        }
        results.append(result)

    category_score = round(total_weighted_score / total_weight, 1) if total_weight > 0 else 0

    # Sort gaps by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda g: priority_order.get(g["priority"], 99))

    return {
        "category_id": category_id,
        "category_name": category_def["name"],
        "description": category_def["description"],
        "score": category_score,
        "implemented": implemented_count,
        "total_applicable": total_applicable,
        "controls": results,
        "gaps": gaps,
        "readiness": "ready" if category_score >= 80 else "needs_work" if category_score >= 50 else "not_ready",
    }


def get_cloud_mapping(category_id: str, category_def: dict) -> list:
    """Extract cloud service mappings for a category."""
    mappings = []
    for control_id, control_def in category_def["controls"].items():
        if control_def.get("cloud_mapping"):
            mappings.append({
                "control_id": control_id,
                "name": control_def["name"],
                "cloud_services": control_def["cloud_mapping"],
            })
    return mappings


def run_assessment(config: dict, categories: list[str] | None = None, include_cloud: bool = False) -> dict:
    """Run full SOC 2 readiness assessment."""
    org_controls = config.get("controls", {})
    org_info = config.get("organization", {})

    if categories:
        active_categories = {k: v for k, v in TSC_CONTROLS.items() if k in categories}
    else:
        active_categories = TSC_CONTROLS

    category_results = []
    all_gaps = []
    total_score = 0
    category_count = 0

    for cat_id, cat_def in active_categories.items():
        result = assess_category(cat_id, cat_def, org_controls)
        category_results.append(result)
        total_score += result["score"]
        category_count += 1
        all_gaps.extend(result["gaps"])

    overall_score = round(total_score / category_count, 1) if category_count > 0 else 0

    # Determine overall readiness
    if overall_score >= 80:
        overall_readiness = "ready"
        readiness_message = "Organization is ready to engage an auditor for SOC 2 examination."
    elif overall_score >= 60:
        overall_readiness = "nearly_ready"
        readiness_message = "Organization needs targeted remediation before engaging an auditor. Focus on critical and high-priority gaps."
    elif overall_score >= 40:
        overall_readiness = "needs_work"
        readiness_message = "Significant control gaps exist. Recommend 8-16 weeks of remediation before audit engagement."
    else:
        overall_readiness = "not_ready"
        readiness_message = "Organization is not ready for SOC 2 audit. Recommend comprehensive compliance program implementation (16-24 weeks minimum)."

    # Count gaps by priority
    gap_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for gap in all_gaps:
        gap_summary[gap["priority"]] += 1

    assessment = {
        "assessment_date": datetime.now().isoformat(),
        "organization": org_info,
        "overall_score": overall_score,
        "overall_readiness": overall_readiness,
        "readiness_message": readiness_message,
        "gap_summary": gap_summary,
        "total_gaps": len(all_gaps),
        "categories": category_results,
    }

    if include_cloud:
        cloud_mappings = []
        for cat_id, cat_def in active_categories.items():
            mappings = get_cloud_mapping(cat_id, cat_def)
            if mappings:
                cloud_mappings.append({
                    "category": cat_def["name"],
                    "mappings": mappings,
                })
        assessment["cloud_mappings"] = cloud_mappings

    return assessment


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_human_readable(assessment: dict) -> str:
    """Format assessment results as human-readable report."""
    lines = []
    lines.append("=" * 78)
    lines.append("SOC 2 READINESS ASSESSMENT REPORT")
    lines.append("=" * 78)
    lines.append("")

    org = assessment.get("organization", {})
    if org:
        lines.append(f"Organization: {org.get('name', 'N/A')}")
        lines.append(f"Assessment Date: {assessment['assessment_date'][:10]}")
        lines.append(f"Scope: {', '.join(org.get('tsc_scope', ['Security']))}")
        lines.append("")

    lines.append(f"OVERALL READINESS SCORE: {assessment['overall_score']}/100")
    lines.append(f"Status: {assessment['overall_readiness'].upper().replace('_', ' ')}")
    lines.append(f"Assessment: {assessment['readiness_message']}")
    lines.append("")

    # Gap summary
    gs = assessment["gap_summary"]
    lines.append(f"Gap Summary: {gs['critical']} Critical | {gs['high']} High | {gs['medium']} Medium | {gs['low']} Low")
    lines.append(f"Total Gaps: {assessment['total_gaps']}")
    lines.append("")

    # Category scores
    lines.append("-" * 78)
    lines.append("CATEGORY SCORES")
    lines.append("-" * 78)
    for cat in assessment["categories"]:
        bar_filled = int(cat["score"] / 5)
        bar_empty = 20 - bar_filled
        bar = "#" * bar_filled + "." * bar_empty
        status_icon = "PASS" if cat["readiness"] == "ready" else "WARN" if cat["readiness"] == "needs_work" else "FAIL"
        lines.append(f"  [{status_icon}] {cat['category_name']:<35} [{bar}] {cat['score']:>5.1f}/100  ({cat['implemented']}/{cat['total_applicable']} controls)")
    lines.append("")

    # Detailed gaps by category
    lines.append("-" * 78)
    lines.append("GAPS AND REMEDIATION")
    lines.append("-" * 78)

    for cat in assessment["categories"]:
        if not cat["gaps"]:
            continue
        lines.append("")
        lines.append(f"  {cat['category_name']} ({len(cat['gaps'])} gaps)")
        lines.append(f"  {'~' * 60}")

        for gap in cat["gaps"]:
            priority_tag = f"[{gap['priority'].upper()}]"
            lines.append(f"    {priority_tag:<12} {gap['control_id']}: {gap['name']}")
            lines.append(f"                 Status: {gap['status'].replace('_', ' ')}")
            lines.append(f"                 Action: {gap['remediation']}")
            lines.append("")

    # Cloud mappings
    if "cloud_mappings" in assessment and assessment["cloud_mappings"]:
        lines.append("-" * 78)
        lines.append("CLOUD SERVICE MAPPINGS")
        lines.append("-" * 78)
        for cm in assessment["cloud_mappings"]:
            lines.append(f"\n  {cm['category']}")
            for mapping in cm["mappings"]:
                lines.append(f"    {mapping['control_id']}: {mapping['name']}")
                for provider, services in mapping["cloud_services"].items():
                    lines.append(f"      {provider.upper()}: {', '.join(services)}")
        lines.append("")

    lines.append("=" * 78)
    lines.append("END OF REPORT")
    lines.append("=" * 78)

    return "\n".join(lines)


def generate_sample_config() -> dict:
    """Generate a sample organization configuration file."""
    sample = {
        "organization": {
            "name": "Acme Corp",
            "industry": "SaaS",
            "employees": 150,
            "tsc_scope": ["security", "availability", "confidentiality"],
            "cloud_providers": ["aws"],
            "target_audit_date": "2026-09-01",
            "audit_type": "type_ii",
        },
        "controls": {
            # CC1 - Control Environment
            "code_of_conduct": "implemented",
            "board_oversight": "partially_implemented",
            "roles_defined": "implemented",
            "background_checks": "implemented",
            # CC2 - Communication
            "internal_communication": "implemented",
            "external_communication": "partially_implemented",
            "system_description": "not_implemented",
            # CC3 - Risk Assessment
            "risk_assessment": "partially_implemented",
            "fraud_risk_assessment": "not_implemented",
            # CC4 - Monitoring
            "continuous_monitoring": "partially_implemented",
            "deficiency_reporting": "planned",
            # CC5 - Control Activities
            "control_activities": "partially_implemented",
            "policy_management": "partially_implemented",
            # CC6 - Access Controls
            "logical_access": {"status": "partially_implemented", "notes": "SSO deployed, MFA not enforced for all users"},
            "access_provisioning": "partially_implemented",
            "access_reviews": "not_implemented",
            "physical_access": "implemented",
            "network_security": "implemented",
            "encryption_transit": "implemented",
            "endpoint_protection": "partially_implemented",
            # CC7 - System Operations
            "vulnerability_management": "partially_implemented",
            "security_monitoring": "partially_implemented",
            "incident_response": "planned",
            # CC8 - Change Management
            "change_management": "partially_implemented",
            # CC9 - Risk Mitigation
            "vendor_management": "not_implemented",
            "risk_transfer": "implemented",
            # A1 - Availability
            "capacity_planning": "implemented",
            "disaster_recovery": "partially_implemented",
            "recovery_testing": "not_implemented",
            "backup_management": "implemented",
            "sla_management": "partially_implemented",
            # PI1 - Processing Integrity
            "data_completeness": "partially_implemented",
            "error_handling": "implemented",
            "io_validation": "partially_implemented",
            "processing_authorization": "not_implemented",
            # C1 - Confidentiality
            "data_classification": "not_implemented",
            "encryption_rest": "implemented",
            "data_disposal": "not_implemented",
            "nda_management": "partially_implemented",
            # P1 - Privacy
            "privacy_notice": "implemented",
            "consent_management": "partially_implemented",
            "data_minimization": "not_implemented",
            "retention_disposal": "not_implemented",
            "data_subject_rights": "planned",
            "third_party_disclosure": "partially_implemented",
            "data_quality": "not_implemented",
            "privacy_monitoring": "not_implemented",
        },
    }
    return sample


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SOC 2 Readiness Checker - Assess organizational controls against Trust Services Criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config org-controls.json
  %(prog)s --config org-controls.json --format json
  %(prog)s --config org-controls.json --categories security availability
  %(prog)s --config org-controls.json --cloud-mapping
  %(prog)s --generate-sample > sample-config.json

Control Status Values (in config JSON):
  implemented            Control fully operational with evidence
  partially_implemented  Control exists but has gaps
  planned                Control planned but not yet implemented
  not_implemented        Control does not exist
  not_applicable         Control not relevant to organization
        """,
    )

    parser.add_argument(
        "--config",
        help="Path to JSON configuration file describing organization controls",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["security", "availability", "processing_integrity", "confidentiality", "privacy"],
        help="Specific TSC categories to assess (default: all)",
    )
    parser.add_argument(
        "--cloud-mapping",
        action="store_true",
        help="Include cloud service control mappings in output",
    )
    parser.add_argument(
        "--generate-sample",
        action="store_true",
        help="Generate a sample configuration file and exit",
    )

    args = parser.parse_args()

    if args.generate_sample:
        print(json.dumps(generate_sample_config(), indent=2))
        return

    if not args.config:
        parser.error("--config is required unless using --generate-sample")

    config = load_config(args.config)
    assessment = run_assessment(config, args.categories, args.cloud_mapping)

    if args.format == "json":
        print(json.dumps(assessment, indent=2))
    else:
        print(format_human_readable(assessment))


if __name__ == "__main__":
    main()

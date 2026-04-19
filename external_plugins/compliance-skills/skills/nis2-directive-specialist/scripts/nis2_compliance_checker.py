#!/usr/bin/env python3
"""
NIS2 Compliance Checker

Assesses organizational compliance against all 10 minimum security measures
defined in Article 21 of the NIS2 Directive (EU 2022/2555). Validates incident
reporting readiness, supply chain security, and management accountability.
Generates per-measure scoring and gap analysis reports.

Usage:
    python nis2_compliance_checker.py --template > assessment.json
    python nis2_compliance_checker.py --config assessment.json
    python nis2_compliance_checker.py --config assessment.json --measures 1 2 4 --json
    python nis2_compliance_checker.py --config assessment.json --output gap_report.json --json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# --- Assessment Structure ---

MEASURES = {
    1: {
        "title": "Risk analysis and information system security policies",
        "article": "Article 21(2)(a)",
        "controls": [
            {
                "id": "M1.1",
                "question": "Is there a formal risk assessment methodology documented and approved?",
                "weight": 20,
                "iso27001_map": "A.5.1, 6.1.2",
                "guidance": "Establish a documented risk assessment methodology covering identification, analysis, evaluation, and treatment of cybersecurity risks.",
            },
            {
                "id": "M1.2",
                "question": "Is a comprehensive asset inventory maintained covering all information systems?",
                "weight": 15,
                "iso27001_map": "A.5.9, A.5.10",
                "guidance": "Maintain an up-to-date inventory of all hardware, software, data, and network assets with ownership assignments.",
            },
            {
                "id": "M1.3",
                "question": "Are information security policies documented and approved by management?",
                "weight": 20,
                "iso27001_map": "A.5.1, A.5.2",
                "guidance": "Develop a policy framework including an overarching information security policy and supporting topic-specific policies.",
            },
            {
                "id": "M1.4",
                "question": "Are risk assessments performed at least annually or upon significant changes?",
                "weight": 15,
                "iso27001_map": "8.2",
                "guidance": "Conduct risk assessments at planned intervals and when significant changes occur to systems, services, or threat landscape.",
            },
            {
                "id": "M1.5",
                "question": "Are risk treatment plans documented with clear ownership and timelines?",
                "weight": 15,
                "iso27001_map": "6.1.3, 8.3",
                "guidance": "For each identified risk above tolerance, document a treatment plan specifying controls, responsible owner, and implementation deadline.",
            },
            {
                "id": "M1.6",
                "question": "Are policies reviewed and updated at least annually?",
                "weight": 15,
                "iso27001_map": "A.5.1",
                "guidance": "Implement a policy review cycle to ensure policies remain current with evolving threats and business changes.",
            },
        ],
    },
    2: {
        "title": "Incident handling",
        "article": "Article 21(2)(b)",
        "controls": [
            {
                "id": "M2.1",
                "question": "Are incident detection capabilities deployed (SIEM, IDS/IPS, EDR)?",
                "weight": 20,
                "iso27001_map": "A.8.16",
                "guidance": "Deploy monitoring tools capable of detecting security events across network, endpoint, and application layers.",
            },
            {
                "id": "M2.2",
                "question": "Is there a documented incident classification and triage procedure?",
                "weight": 15,
                "iso27001_map": "A.5.25",
                "guidance": "Define incident severity levels, classification criteria, and triage procedures to prioritize response.",
            },
            {
                "id": "M2.3",
                "question": "Are incident response plans and playbooks documented for key scenarios?",
                "weight": 20,
                "iso27001_map": "A.5.26",
                "guidance": "Develop response playbooks for common incident types (ransomware, data breach, DDoS, insider threat, supply chain compromise).",
            },
            {
                "id": "M2.4",
                "question": "Is there a 24/7 incident response capability or on-call rotation?",
                "weight": 15,
                "iso27001_map": "A.5.24",
                "guidance": "Ensure incidents can be detected and responded to at any time, including weekends and holidays.",
            },
            {
                "id": "M2.5",
                "question": "Are post-incident reviews conducted and lessons learned documented?",
                "weight": 15,
                "iso27001_map": "A.5.27",
                "guidance": "Conduct structured post-incident reviews to identify root causes and improve security measures.",
            },
            {
                "id": "M2.6",
                "question": "Are incident response exercises conducted at least annually?",
                "weight": 15,
                "iso27001_map": "A.5.24",
                "guidance": "Run tabletop exercises or simulated incident drills to validate response plans and team readiness.",
            },
        ],
    },
    3: {
        "title": "Business continuity and crisis management",
        "article": "Article 21(2)(c)",
        "controls": [
            {
                "id": "M3.1",
                "question": "Has a business impact analysis (BIA) been conducted?",
                "weight": 20,
                "iso27001_map": "A.5.30",
                "guidance": "Conduct BIA to identify critical business functions, acceptable downtimes (RTO), and data loss tolerances (RPO).",
            },
            {
                "id": "M3.2",
                "question": "Are business continuity plans (BCP) documented and approved?",
                "weight": 20,
                "iso27001_map": "A.5.30",
                "guidance": "Develop BCPs for all critical functions identified in the BIA with clear roles, procedures, and contact information.",
            },
            {
                "id": "M3.3",
                "question": "Are disaster recovery plans (DRP) in place for critical systems?",
                "weight": 20,
                "iso27001_map": "A.5.30",
                "guidance": "Create technical recovery procedures for each critical system including failover, restoration, and validation steps.",
            },
            {
                "id": "M3.4",
                "question": "Are backups performed regularly with tested restoration procedures?",
                "weight": 20,
                "iso27001_map": "A.8.13",
                "guidance": "Implement automated backups aligned with RPO requirements. Test restoration procedures at least quarterly.",
            },
            {
                "id": "M3.5",
                "question": "Are BCP/DRP plans tested at least annually?",
                "weight": 20,
                "iso27001_map": "A.5.30",
                "guidance": "Conduct annual BCP/DRP tests ranging from tabletop exercises to full failover tests for critical systems.",
            },
        ],
    },
    4: {
        "title": "Supply chain security",
        "article": "Article 21(2)(d)",
        "controls": [
            {
                "id": "M4.1",
                "question": "Is there a documented supplier risk assessment process?",
                "weight": 20,
                "iso27001_map": "A.5.19, A.5.21",
                "guidance": "Establish a process to assess cybersecurity risks of suppliers before onboarding and periodically thereafter.",
            },
            {
                "id": "M4.2",
                "question": "Do contracts with suppliers include cybersecurity requirements?",
                "weight": 20,
                "iso27001_map": "A.5.20",
                "guidance": "Include security clauses covering data protection, incident notification, right to audit, and sub-contractor requirements.",
            },
            {
                "id": "M4.3",
                "question": "Is supplier security posture monitored on an ongoing basis?",
                "weight": 15,
                "iso27001_map": "A.5.22",
                "guidance": "Monitor suppliers through periodic assessments, certification verification, and security rating services.",
            },
            {
                "id": "M4.4",
                "question": "Are suppliers required to notify of security incidents?",
                "weight": 15,
                "iso27001_map": "A.5.20",
                "guidance": "Require suppliers to report security incidents that could affect your organization within defined timelines.",
            },
            {
                "id": "M4.5",
                "question": "Are aggregate supply chain risks assessed (concentration, geographic, geopolitical)?",
                "weight": 15,
                "iso27001_map": "A.5.21",
                "guidance": "Assess risks from supply chain concentration, single points of failure, and geopolitical factors.",
            },
            {
                "id": "M4.6",
                "question": "Are supplier tiers defined with proportionate security requirements?",
                "weight": 15,
                "iso27001_map": "A.5.19",
                "guidance": "Categorize suppliers by criticality (Tier 1/2/3) with proportionate security assessment and monitoring requirements.",
            },
        ],
    },
    5: {
        "title": "Security in network and information systems acquisition, development, and maintenance",
        "article": "Article 21(2)(e)",
        "controls": [
            {
                "id": "M5.1",
                "question": "Is a secure development lifecycle (SDLC) implemented?",
                "weight": 20,
                "iso27001_map": "A.8.25, A.8.26",
                "guidance": "Integrate security requirements, threat modeling, secure coding, and security testing into the development lifecycle.",
            },
            {
                "id": "M5.2",
                "question": "Is there a vulnerability management program with defined SLAs?",
                "weight": 20,
                "iso27001_map": "A.8.8",
                "guidance": "Implement vulnerability scanning, prioritization, and remediation with defined timelines based on severity.",
            },
            {
                "id": "M5.3",
                "question": "Is patch management performed with defined timelines?",
                "weight": 20,
                "iso27001_map": "A.8.8",
                "guidance": "Establish patch management procedures with timelines: critical patches within 24-72 hours, high within 1-2 weeks.",
            },
            {
                "id": "M5.4",
                "question": "Are security reviews conducted for system changes?",
                "weight": 20,
                "iso27001_map": "A.8.32",
                "guidance": "Require security review and approval for all changes to production systems, including infrastructure and application changes.",
            },
            {
                "id": "M5.5",
                "question": "Is secure configuration management applied to all systems?",
                "weight": 20,
                "iso27001_map": "A.8.9",
                "guidance": "Define and enforce security baselines for operating systems, applications, network devices, and cloud services.",
            },
        ],
    },
    6: {
        "title": "Policies and procedures for assessing effectiveness of cybersecurity risk management",
        "article": "Article 21(2)(f)",
        "controls": [
            {
                "id": "M6.1",
                "question": "Are cybersecurity metrics and KPIs defined and tracked?",
                "weight": 20,
                "iso27001_map": "9.1",
                "guidance": "Define measurable KPIs (mean time to detect, mean time to respond, patch compliance, vulnerability counts, etc.).",
            },
            {
                "id": "M6.2",
                "question": "Are regular internal security assessments or audits conducted?",
                "weight": 20,
                "iso27001_map": "9.2",
                "guidance": "Conduct internal security audits at least annually covering all 10 NIS2 minimum measures.",
            },
            {
                "id": "M6.3",
                "question": "Is penetration testing performed at least annually?",
                "weight": 20,
                "iso27001_map": "A.8.8",
                "guidance": "Commission external penetration testing annually covering network, web application, and social engineering vectors.",
            },
            {
                "id": "M6.4",
                "question": "Is continuous vulnerability scanning operational?",
                "weight": 20,
                "iso27001_map": "A.8.8",
                "guidance": "Run automated vulnerability scans at least weekly for external assets and monthly for internal infrastructure.",
            },
            {
                "id": "M6.5",
                "question": "Is there a documented continuous improvement process?",
                "weight": 20,
                "iso27001_map": "10.1, 10.2",
                "guidance": "Implement a process to identify improvement opportunities from audits, incidents, metrics, and external threat intelligence.",
            },
        ],
    },
    7: {
        "title": "Basic cyber hygiene practices and cybersecurity training",
        "article": "Article 21(2)(g)",
        "controls": [
            {
                "id": "M7.1",
                "question": "Do all employees receive cybersecurity awareness training at onboarding and annually?",
                "weight": 25,
                "iso27001_map": "A.6.3",
                "guidance": "Implement mandatory cybersecurity awareness training for all staff upon hiring and at least annually thereafter.",
            },
            {
                "id": "M7.2",
                "question": "Do management body members receive dedicated cybersecurity training?",
                "weight": 25,
                "iso27001_map": "A.6.3, Article 20(2)",
                "guidance": "Mandatory under NIS2 Article 20(2). Management body members must have sufficient knowledge to assess cybersecurity risks.",
            },
            {
                "id": "M7.3",
                "question": "Are phishing simulation exercises conducted regularly?",
                "weight": 15,
                "iso27001_map": "A.6.3",
                "guidance": "Run phishing simulations at least quarterly to measure and improve employee resistance to social engineering.",
            },
            {
                "id": "M7.4",
                "question": "Is role-based security training provided for technical staff?",
                "weight": 20,
                "iso27001_map": "A.6.3",
                "guidance": "Provide specialized training for IT, security, and development staff on secure coding, incident response, and tool usage.",
            },
            {
                "id": "M7.5",
                "question": "Are training records maintained and effectiveness measured?",
                "weight": 15,
                "iso27001_map": "A.6.3",
                "guidance": "Track completion rates, quiz scores, phishing simulation results, and link to security incident trends.",
            },
        ],
    },
    8: {
        "title": "Policies and procedures regarding use of cryptography and encryption",
        "article": "Article 21(2)(h)",
        "controls": [
            {
                "id": "M8.1",
                "question": "Is there a documented cryptography and encryption policy?",
                "weight": 20,
                "iso27001_map": "A.8.24",
                "guidance": "Define approved cryptographic algorithms, key lengths, and use cases for data at rest, in transit, and in use.",
            },
            {
                "id": "M8.2",
                "question": "Is data encrypted at rest using strong algorithms (AES-256 or equivalent)?",
                "weight": 20,
                "iso27001_map": "A.8.24",
                "guidance": "Encrypt sensitive data at rest in databases, file systems, and backups using AES-256 or equivalent.",
            },
            {
                "id": "M8.3",
                "question": "Is data encrypted in transit using TLS 1.2+ for all communications?",
                "weight": 20,
                "iso27001_map": "A.8.24",
                "guidance": "Enforce TLS 1.2 minimum (TLS 1.3 preferred) for all external and internal network communications.",
            },
            {
                "id": "M8.4",
                "question": "Are key management procedures documented and followed?",
                "weight": 20,
                "iso27001_map": "A.8.24",
                "guidance": "Implement key lifecycle management covering generation, distribution, storage, rotation, and destruction.",
            },
            {
                "id": "M8.5",
                "question": "Are cryptographic implementations reviewed for weaknesses periodically?",
                "weight": 20,
                "iso27001_map": "A.8.24",
                "guidance": "Review cryptographic algorithms and implementations against current best practices and deprecation schedules.",
            },
        ],
    },
    9: {
        "title": "Human resources security, access control policies, and asset management",
        "article": "Article 21(2)(i)",
        "controls": [
            {
                "id": "M9.1",
                "question": "Are pre-employment background checks conducted for sensitive roles?",
                "weight": 15,
                "iso27001_map": "A.6.1",
                "guidance": "Conduct background verification proportionate to role sensitivity, classification of information accessed, and perceived risks.",
            },
            {
                "id": "M9.2",
                "question": "Is role-based access control (RBAC) implemented?",
                "weight": 20,
                "iso27001_map": "A.5.15, A.8.2",
                "guidance": "Implement RBAC with least privilege principle. Define roles, map to access permissions, and enforce consistently.",
            },
            {
                "id": "M9.3",
                "question": "Is privileged access management (PAM) deployed for administrative accounts?",
                "weight": 20,
                "iso27001_map": "A.8.2, A.8.18",
                "guidance": "Implement PAM solutions for just-in-time access, session recording, and credential vaulting for privileged accounts.",
            },
            {
                "id": "M9.4",
                "question": "Are access rights reviewed at least quarterly for critical systems?",
                "weight": 15,
                "iso27001_map": "A.5.18",
                "guidance": "Conduct regular access reviews to verify that permissions remain appropriate and remove stale accounts.",
            },
            {
                "id": "M9.5",
                "question": "Are departure procedures ensuring timely access revocation in place?",
                "weight": 15,
                "iso27001_map": "A.6.5",
                "guidance": "Implement automated access revocation triggered by HR departure workflow, effective within 24 hours of termination.",
            },
            {
                "id": "M9.6",
                "question": "Is there a comprehensive asset inventory with ownership?",
                "weight": 15,
                "iso27001_map": "A.5.9, A.5.10, A.5.11",
                "guidance": "Maintain a complete inventory of information assets (hardware, software, data, services) with designated owners.",
            },
        ],
    },
    10: {
        "title": "Multi-factor authentication, secured communications, and secured emergency communications",
        "article": "Article 21(2)(j)",
        "controls": [
            {
                "id": "M10.1",
                "question": "Is MFA enforced for all remote access?",
                "weight": 20,
                "iso27001_map": "A.8.5",
                "guidance": "Require MFA for VPN, remote desktop, cloud services, and any external access to organizational resources.",
            },
            {
                "id": "M10.2",
                "question": "Is MFA enforced for all privileged and administrative accounts?",
                "weight": 20,
                "iso27001_map": "A.8.5",
                "guidance": "Require MFA for all accounts with elevated privileges, including system administrators and security personnel.",
            },
            {
                "id": "M10.3",
                "question": "Is MFA enforced for access to critical systems and sensitive data?",
                "weight": 15,
                "iso27001_map": "A.8.5",
                "guidance": "Require MFA for access to systems classified as critical or containing sensitive/personal data.",
            },
            {
                "id": "M10.4",
                "question": "Are communications encrypted end-to-end for sensitive exchanges?",
                "weight": 15,
                "iso27001_map": "A.8.24, A.5.14",
                "guidance": "Deploy end-to-end encrypted communication tools for confidential business communications.",
            },
            {
                "id": "M10.5",
                "question": "Are out-of-band emergency communication channels established and tested?",
                "weight": 15,
                "iso27001_map": "A.5.24, A.5.30",
                "guidance": "Establish alternative communication channels (satellite phones, out-of-band messaging) for crisis situations.",
            },
            {
                "id": "M10.6",
                "question": "Are hardware security keys (FIDO2/WebAuthn) supported for high-risk accounts?",
                "weight": 15,
                "iso27001_map": "A.8.5",
                "guidance": "Support phishing-resistant authentication methods such as FIDO2 hardware keys for high-value targets.",
            },
        ],
    },
}

INCIDENT_REPORTING_CHECKS = [
    {
        "id": "IR.1",
        "question": "Can the organization issue an early warning within 24 hours of detecting a significant incident?",
        "weight": 25,
        "reference": "Article 23(4)(a)",
    },
    {
        "id": "IR.2",
        "question": "Can the organization submit an incident notification within 72 hours?",
        "weight": 25,
        "reference": "Article 23(4)(b)",
    },
    {
        "id": "IR.3",
        "question": "Can the organization produce a final report within 1 month of incident notification?",
        "weight": 20,
        "reference": "Article 23(4)(d)",
    },
    {
        "id": "IR.4",
        "question": "Is the national CSIRT contact information documented and accessible to incident responders?",
        "weight": 15,
        "reference": "Article 23",
    },
    {
        "id": "IR.5",
        "question": "Are templates prepared for early warning, notification, and final report submissions?",
        "weight": 15,
        "reference": "Article 23",
    },
]

MANAGEMENT_ACCOUNTABILITY_CHECKS = [
    {
        "id": "MA.1",
        "question": "Has the management body formally approved the cybersecurity risk management measures?",
        "weight": 30,
        "reference": "Article 20(1)",
    },
    {
        "id": "MA.2",
        "question": "Does the management body oversee implementation of cybersecurity measures?",
        "weight": 25,
        "reference": "Article 20(1)",
    },
    {
        "id": "MA.3",
        "question": "Have management body members completed cybersecurity training?",
        "weight": 25,
        "reference": "Article 20(2)",
    },
    {
        "id": "MA.4",
        "question": "Is cybersecurity a regular agenda item in management body meetings?",
        "weight": 20,
        "reference": "Article 20",
    },
]


def generate_template() -> Dict[str, Any]:
    """Generate an assessment input template."""
    template = {
        "_instructions": "Fill in each response with: 'yes', 'partial', 'no', or 'not_applicable'. "
                         "Add optional 'notes' field for context.",
        "organization": {
            "name": "Your Organization Name",
            "entity_type": "essential or important",
            "sector": "e.g., energy",
            "assessment_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "measures": {},
        "incident_reporting": {},
        "management_accountability": {},
    }

    for measure_num, measure_data in MEASURES.items():
        template["measures"][f"measure_{measure_num}"] = {
            "title": measure_data["title"],
            "controls": {},
        }
        for control in measure_data["controls"]:
            template["measures"][f"measure_{measure_num}"]["controls"][control["id"]] = {
                "question": control["question"],
                "response": "yes | partial | no | not_applicable",
                "notes": "",
            }

    for check in INCIDENT_REPORTING_CHECKS:
        template["incident_reporting"][check["id"]] = {
            "question": check["question"],
            "response": "yes | partial | no",
            "notes": "",
        }

    for check in MANAGEMENT_ACCOUNTABILITY_CHECKS:
        template["management_accountability"][check["id"]] = {
            "question": check["question"],
            "response": "yes | partial | no",
            "notes": "",
        }

    return template


def score_response(response: str) -> float:
    """Convert a response to a numeric score."""
    mapping = {
        "yes": 1.0,
        "partial": 0.5,
        "no": 0.0,
        "not_applicable": None,
    }
    return mapping.get(response.lower().strip(), 0.0)


def assess_measure(measure_num: int, responses: Dict[str, Any]) -> Dict[str, Any]:
    """Assess a single measure based on responses."""
    measure_data = MEASURES[measure_num]
    controls_key = f"measure_{measure_num}"

    result = {
        "measure": measure_num,
        "title": measure_data["title"],
        "article": measure_data["article"],
        "controls": [],
        "score": 0,
        "max_score": 0,
        "gaps": [],
        "recommendations": [],
    }

    measure_responses = responses.get("measures", {}).get(controls_key, {}).get("controls", {})

    total_weighted_score = 0.0
    total_weight = 0

    for control in measure_data["controls"]:
        control_response = measure_responses.get(control["id"], {})
        response_value = control_response.get("response", "no") if isinstance(control_response, dict) else "no"
        notes = control_response.get("notes", "") if isinstance(control_response, dict) else ""

        score = score_response(response_value)

        control_result = {
            "id": control["id"],
            "question": control["question"],
            "response": response_value,
            "notes": notes,
            "weight": control["weight"],
            "iso27001_map": control["iso27001_map"],
        }

        if score is None:
            control_result["status"] = "not_applicable"
            control_result["score_contribution"] = "N/A"
        else:
            weighted = score * control["weight"]
            total_weighted_score += weighted
            total_weight += control["weight"]
            control_result["status"] = "compliant" if score == 1.0 else ("partial" if score == 0.5 else "non_compliant")
            control_result["score_contribution"] = round(weighted, 1)

            if score < 1.0:
                gap = {
                    "control_id": control["id"],
                    "question": control["question"],
                    "current_status": control_result["status"],
                    "guidance": control["guidance"],
                    "iso27001_map": control["iso27001_map"],
                    "priority": "high" if score == 0.0 else "medium",
                }
                result["gaps"].append(gap)
                result["recommendations"].append({
                    "control_id": control["id"],
                    "action": control["guidance"],
                    "priority": gap["priority"],
                })

        result["controls"].append(control_result)

    if total_weight > 0:
        result["score"] = round((total_weighted_score / total_weight) * 100, 1)
    else:
        result["score"] = 0

    result["max_score"] = 100
    result["compliance_level"] = _compliance_level(result["score"])

    return result


def assess_incident_reporting(responses: Dict[str, Any]) -> Dict[str, Any]:
    """Assess incident reporting readiness."""
    ir_responses = responses.get("incident_reporting", {})

    result = {
        "category": "Incident Reporting Readiness",
        "checks": [],
        "score": 0,
        "gaps": [],
    }

    total_weighted_score = 0.0
    total_weight = 0

    for check in INCIDENT_REPORTING_CHECKS:
        check_response = ir_responses.get(check["id"], {})
        response_value = check_response.get("response", "no") if isinstance(check_response, dict) else "no"
        notes = check_response.get("notes", "") if isinstance(check_response, dict) else ""

        score = score_response(response_value)
        if score is None:
            score = 0.0

        weighted = score * check["weight"]
        total_weighted_score += weighted
        total_weight += check["weight"]

        check_result = {
            "id": check["id"],
            "question": check["question"],
            "response": response_value,
            "notes": notes,
            "status": "compliant" if score == 1.0 else ("partial" if score == 0.5 else "non_compliant"),
            "reference": check["reference"],
        }
        result["checks"].append(check_result)

        if score < 1.0:
            result["gaps"].append({
                "check_id": check["id"],
                "question": check["question"],
                "current_status": check_result["status"],
                "reference": check["reference"],
                "priority": "critical" if score == 0.0 else "high",
            })

    if total_weight > 0:
        result["score"] = round((total_weighted_score / total_weight) * 100, 1)

    result["compliance_level"] = _compliance_level(result["score"])
    return result


def assess_management_accountability(responses: Dict[str, Any]) -> Dict[str, Any]:
    """Assess management accountability compliance."""
    ma_responses = responses.get("management_accountability", {})

    result = {
        "category": "Management Accountability",
        "checks": [],
        "score": 0,
        "gaps": [],
    }

    total_weighted_score = 0.0
    total_weight = 0

    for check in MANAGEMENT_ACCOUNTABILITY_CHECKS:
        check_response = ma_responses.get(check["id"], {})
        response_value = check_response.get("response", "no") if isinstance(check_response, dict) else "no"
        notes = check_response.get("notes", "") if isinstance(check_response, dict) else ""

        score = score_response(response_value)
        if score is None:
            score = 0.0

        weighted = score * check["weight"]
        total_weighted_score += weighted
        total_weight += check["weight"]

        check_result = {
            "id": check["id"],
            "question": check["question"],
            "response": response_value,
            "notes": notes,
            "status": "compliant" if score == 1.0 else ("partial" if score == 0.5 else "non_compliant"),
            "reference": check["reference"],
        }
        result["checks"].append(check_result)

        if score < 1.0:
            result["gaps"].append({
                "check_id": check["id"],
                "question": check["question"],
                "current_status": check_result["status"],
                "reference": check["reference"],
                "priority": "critical" if score == 0.0 else "high",
            })

    if total_weight > 0:
        result["score"] = round((total_weighted_score / total_weight) * 100, 1)

    result["compliance_level"] = _compliance_level(result["score"])
    return result


def _compliance_level(score: float) -> str:
    """Determine compliance level from score."""
    if score >= 90:
        return "strong"
    elif score >= 70:
        return "adequate"
    elif score >= 50:
        return "partial"
    elif score >= 25:
        return "weak"
    else:
        return "non_compliant"


def run_full_assessment(
    responses: Dict[str, Any], measure_filter: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Run a complete NIS2 compliance assessment."""
    result = {
        "timestamp": datetime.now().isoformat(),
        "organization": responses.get("organization", {}),
        "summary": {},
        "measures": [],
        "incident_reporting": {},
        "management_accountability": {},
        "overall_score": 0,
        "overall_compliance_level": "",
        "critical_gaps": [],
        "remediation_priorities": [],
    }

    # Assess measures
    measures_to_check = measure_filter if measure_filter else list(MEASURES.keys())
    measure_scores = []

    for m_num in measures_to_check:
        if m_num in MEASURES:
            measure_result = assess_measure(m_num, responses)
            result["measures"].append(measure_result)
            measure_scores.append(measure_result["score"])

    # Assess incident reporting
    ir_result = assess_incident_reporting(responses)
    result["incident_reporting"] = ir_result

    # Assess management accountability
    ma_result = assess_management_accountability(responses)
    result["management_accountability"] = ma_result

    # Calculate overall score
    all_scores = measure_scores + [ir_result["score"], ma_result["score"]]
    if all_scores:
        result["overall_score"] = round(sum(all_scores) / len(all_scores), 1)

    result["overall_compliance_level"] = _compliance_level(result["overall_score"])

    # Summary
    result["summary"] = {
        "total_measures_assessed": len(measures_to_check),
        "measures_compliant": sum(1 for s in measure_scores if s >= 90),
        "measures_partial": sum(1 for s in measure_scores if 50 <= s < 90),
        "measures_non_compliant": sum(1 for s in measure_scores if s < 50),
        "overall_score": result["overall_score"],
        "compliance_level": result["overall_compliance_level"],
        "incident_reporting_score": ir_result["score"],
        "management_accountability_score": ma_result["score"],
    }

    # Collect critical gaps
    for measure_result in result["measures"]:
        for gap in measure_result.get("gaps", []):
            if gap["priority"] == "high":
                result["critical_gaps"].append({
                    "measure": measure_result["measure"],
                    "measure_title": measure_result["title"],
                    **gap,
                })

    for gap in ir_result.get("gaps", []):
        if gap["priority"] == "critical":
            result["critical_gaps"].append({"area": "Incident Reporting", **gap})

    for gap in ma_result.get("gaps", []):
        if gap["priority"] == "critical":
            result["critical_gaps"].append({"area": "Management Accountability", **gap})

    # Prioritized remediation
    all_gaps = []
    for measure_result in result["measures"]:
        for rec in measure_result.get("recommendations", []):
            all_gaps.append({
                "measure": measure_result["measure"],
                "measure_title": measure_result["title"],
                **rec,
            })

    # Sort: high priority first, then by measure number
    all_gaps.sort(key=lambda x: (0 if x["priority"] == "high" else 1, x.get("measure", 0)))
    result["remediation_priorities"] = all_gaps

    return result


def format_text_report(result: Dict[str, Any]) -> str:
    """Format assessment result as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("NIS2 COMPLIANCE ASSESSMENT REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {result['timestamp']}")

    org = result.get("organization", {})
    if org:
        lines.append(f"Organization: {org.get('name', 'N/A')}")
        lines.append(f"Entity type:  {org.get('entity_type', 'N/A')}")
        lines.append(f"Sector:       {org.get('sector', 'N/A')}")
    lines.append("")

    # Summary
    summary = result.get("summary", {})
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Overall Score:          {summary.get('overall_score', 0)}/100")
    lines.append(f"  Compliance Level:       {summary.get('compliance_level', 'N/A').upper()}")
    lines.append(f"  Measures Assessed:      {summary.get('total_measures_assessed', 0)}")
    lines.append(f"  Compliant (>=90):       {summary.get('measures_compliant', 0)}")
    lines.append(f"  Partial (50-89):        {summary.get('measures_partial', 0)}")
    lines.append(f"  Non-compliant (<50):    {summary.get('measures_non_compliant', 0)}")
    lines.append(f"  Incident Reporting:     {summary.get('incident_reporting_score', 0)}/100")
    lines.append(f"  Management Accountability: {summary.get('management_accountability_score', 0)}/100")
    lines.append("")

    # Measure scores
    lines.append("MEASURE SCORES")
    lines.append("-" * 40)
    for measure_result in result.get("measures", []):
        score = measure_result["score"]
        level = measure_result["compliance_level"]
        bar = "#" * int(score / 5) + "." * (20 - int(score / 5))
        lines.append(f"  M{measure_result['measure']:2d}. {measure_result['title'][:45]:<45s}")
        lines.append(f"       [{bar}] {score:5.1f}/100 ({level})")
    lines.append("")

    # Critical gaps
    critical_gaps = result.get("critical_gaps", [])
    if critical_gaps:
        lines.append("CRITICAL GAPS")
        lines.append("-" * 40)
        for gap in critical_gaps:
            area = gap.get("measure_title", gap.get("area", ""))
            lines.append(f"  [!!!] {gap.get('control_id', gap.get('check_id', ''))}: {gap.get('question', '')}")
            lines.append(f"        Area: {area}")
            if gap.get("guidance"):
                lines.append(f"        Action: {gap['guidance']}")
            lines.append("")

    # Remediation priorities
    priorities = result.get("remediation_priorities", [])
    if priorities:
        lines.append("REMEDIATION PRIORITIES (Top 10)")
        lines.append("-" * 40)
        for i, rec in enumerate(priorities[:10], 1):
            lines.append(f"  {i}. [{rec['priority'].upper()}] {rec['control_id']} (Measure {rec['measure']})")
            lines.append(f"     {rec['action']}")
            lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="NIS2 Compliance Checker — Assess compliance against Article 21 minimum measures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --template > assessment.json
  %(prog)s --config assessment.json
  %(prog)s --config assessment.json --measures 1 2 4 --json
  %(prog)s --config assessment.json --output gap_report.json --json
        """,
    )

    parser.add_argument("--config", help="Path to JSON assessment file (use --template to generate)")
    parser.add_argument("--template", action="store_true", help="Generate assessment input template")
    parser.add_argument("--measures", nargs="+", type=int, help="Assess specific measures only (e.g., 1 2 4)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", help="Write output to file")

    args = parser.parse_args()

    # Template mode
    if args.template:
        template = generate_template()
        print(json.dumps(template, indent=2))
        return

    # Assessment mode
    if not args.config:
        parser.error("--config is required for assessment (use --template to generate input file)")

    try:
        with open(args.config) as f:
            responses = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate measure filter
    if args.measures:
        invalid = [m for m in args.measures if m not in MEASURES]
        if invalid:
            parser.error(f"Invalid measure numbers: {invalid}. Valid: 1-10")

    # Run assessment
    result = run_full_assessment(responses, measure_filter=args.measures)

    # Format output
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_text_report(result)

    # Write or print
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()

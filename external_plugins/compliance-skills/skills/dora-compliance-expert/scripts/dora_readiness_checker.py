#!/usr/bin/env python3
"""
DORA Readiness Checker

Assesses organizational readiness against all 5 pillars of the Digital
Operational Resilience Act (EU 2022/2554). Validates ICT risk management,
incident management, resilience testing, third-party risk management, and
information sharing arrangements. Generates per-pillar scoring and gap analysis.

Usage:
    python dora_readiness_checker.py --template > assessment.json
    python dora_readiness_checker.py --config assessment.json
    python dora_readiness_checker.py --config assessment.json --pillars 1 3 4 --json
    python dora_readiness_checker.py --config assessment.json --output readiness_report.json --json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# --- DORA Pillar Definitions ---

PILLARS = {
    1: {
        "title": "ICT Risk Management",
        "chapter": "Chapter II (Articles 5-16)",
        "controls": [
            {
                "id": "P1.1",
                "question": "Has the management body formally approved the ICT risk management framework?",
                "weight": 15,
                "article": "Article 5",
                "iso27001_map": "Cl.5.1, Cl.5.2",
                "guidance": "The management body must define, approve, oversee, and be responsible for implementing the ICT risk management framework.",
            },
            {
                "id": "P1.2",
                "question": "Is there a documented digital operational resilience strategy approved by the management body?",
                "weight": 12,
                "article": "Article 6(8)",
                "iso27001_map": "Cl.5.2, A.5.1",
                "guidance": "Define a strategy covering ICT risk tolerance, key information security objectives, and ICT reference architecture.",
            },
            {
                "id": "P1.3",
                "question": "Is a comprehensive ICT asset inventory maintained with classification and dependency mapping?",
                "weight": 10,
                "article": "Article 8",
                "iso27001_map": "A.5.9, A.5.10",
                "guidance": "Identify and document all ICT-supported business functions, information assets, ICT assets, and interconnections with third-party providers.",
            },
            {
                "id": "P1.4",
                "question": "Are ICT risk assessments conducted at least annually?",
                "weight": 10,
                "article": "Article 8(6)",
                "iso27001_map": "Cl.6.1, Cl.8.2",
                "guidance": "Perform risk assessments at least annually and upon significant changes to network and information system infrastructure.",
            },
            {
                "id": "P1.5",
                "question": "Are ICT security policies, protocols, and tools implemented for protection and prevention?",
                "weight": 10,
                "article": "Article 9",
                "iso27001_map": "A.8.9, A.8.20, A.8.5",
                "guidance": "Implement security policies covering network security, change management, patching, authentication (MFA), and access control (least privilege).",
            },
            {
                "id": "P1.6",
                "question": "Are mechanisms in place to detect anomalous activities on networks and systems?",
                "weight": 10,
                "article": "Article 10",
                "iso27001_map": "A.8.16",
                "guidance": "Deploy multiple layers of detection controls including automated alerting and monitoring mechanisms.",
            },
            {
                "id": "P1.7",
                "question": "Are ICT response and recovery plans documented and tested?",
                "weight": 10,
                "article": "Article 11",
                "iso27001_map": "A.5.24, A.5.26, A.5.30",
                "guidance": "Implement ICT business continuity policy with response and recovery plans activated upon ICT incident identification.",
            },
            {
                "id": "P1.8",
                "question": "Are backup policies defined with regular restoration testing?",
                "weight": 8,
                "article": "Article 12",
                "iso27001_map": "A.8.13",
                "guidance": "Establish backup policies specifying scope, frequency, and retention. Restore on separate systems and perform integrity checks.",
            },
            {
                "id": "P1.9",
                "question": "Are post-incident reviews conducted and findings implemented?",
                "weight": 8,
                "article": "Article 13",
                "iso27001_map": "A.5.27, Cl.10.1",
                "guidance": "Gather information on vulnerabilities and threats, review incidents after recovery, and implement improvement findings.",
            },
            {
                "id": "P1.10",
                "question": "Are crisis communication plans established for internal and external stakeholders?",
                "weight": 7,
                "article": "Article 14",
                "iso27001_map": "A.5.24, A.5.30",
                "guidance": "Develop communication plans and designate at least one spokesperson for external crisis communication.",
            },
        ],
    },
    2: {
        "title": "ICT-Related Incident Management",
        "chapter": "Chapter III (Articles 17-23)",
        "controls": [
            {
                "id": "P2.1",
                "question": "Is there a documented ICT incident management process with early warning indicators?",
                "weight": 18,
                "article": "Article 17",
                "iso27001_map": "A.5.24, A.5.25",
                "guidance": "Define procedures to identify, track, log, categorize, and classify all ICT-related incidents. Assign roles for different incident types.",
            },
            {
                "id": "P2.2",
                "question": "Is there a formal incident classification methodology using all DORA criteria?",
                "weight": 18,
                "article": "Article 18",
                "iso27001_map": "A.5.25",
                "guidance": "Classify incidents using: clients affected, duration, geographic spread, data losses, criticality of services, and economic impact.",
            },
            {
                "id": "P2.3",
                "question": "Can the organization submit an initial incident report within 4 hours of classifying an incident as major?",
                "weight": 20,
                "article": "Article 19(4)(a)",
                "iso27001_map": "A.5.26",
                "guidance": "Establish processes to classify and report major incidents to the competent authority within 4 hours (or 24 hours from detection at latest).",
            },
            {
                "id": "P2.4",
                "question": "Can the organization produce an intermediate report within 72 hours?",
                "weight": 15,
                "article": "Article 19(4)(b)",
                "iso27001_map": "A.5.26",
                "guidance": "Prepare processes and templates for intermediate reports covering severity, root cause assessment, and recovery status.",
            },
            {
                "id": "P2.5",
                "question": "Can the organization produce a final report within 1 month of the intermediate report?",
                "weight": 12,
                "article": "Article 19(4)(c)",
                "iso27001_map": "A.5.27",
                "guidance": "Ensure root cause analysis, impact assessment, and lessons learned are documented within the required timeline.",
            },
            {
                "id": "P2.6",
                "question": "Are templates prepared for all reporting stages (initial, intermediate, final)?",
                "weight": 10,
                "article": "Article 20",
                "iso27001_map": "A.5.24",
                "guidance": "Pre-populate templates aligned with ESA reporting formats for rapid submission during incidents.",
            },
            {
                "id": "P2.7",
                "question": "Are procedures in place to inform clients of major incidents affecting their financial interests?",
                "weight": 7,
                "article": "Article 19(1)",
                "iso27001_map": "A.5.24",
                "guidance": "Establish client notification procedures including content, channels, and timelines for incident communication.",
            },
        ],
    },
    3: {
        "title": "Digital Operational Resilience Testing",
        "chapter": "Chapter IV (Articles 24-27)",
        "controls": [
            {
                "id": "P3.1",
                "question": "Is there a documented digital operational resilience testing program?",
                "weight": 15,
                "article": "Article 24",
                "iso27001_map": "Cl.9.1",
                "guidance": "Establish a testing program as an integral part of the ICT risk management framework, proportionate to entity size and risk profile.",
            },
            {
                "id": "P3.2",
                "question": "Are vulnerability assessments and scans performed at least annually?",
                "weight": 15,
                "article": "Article 25",
                "iso27001_map": "A.8.8",
                "guidance": "Conduct automated and manual vulnerability scanning for all critical systems on at least an annual basis.",
            },
            {
                "id": "P3.3",
                "question": "Are network security assessments performed annually?",
                "weight": 12,
                "article": "Article 25",
                "iso27001_map": "A.8.20",
                "guidance": "Assess network architecture, segmentation, configuration, and traffic patterns for security weaknesses.",
            },
            {
                "id": "P3.4",
                "question": "Are scenario-based tests (tabletop exercises) conducted at least annually?",
                "weight": 12,
                "article": "Article 25",
                "iso27001_map": "A.5.24",
                "guidance": "Design and execute scenario-based tests covering cyber attacks, system failures, and third-party provider disruption.",
            },
            {
                "id": "P3.5",
                "question": "Is penetration testing performed at least annually for critical systems?",
                "weight": 15,
                "article": "Article 25",
                "iso27001_map": "A.8.8",
                "guidance": "Commission penetration tests covering network, application, and social engineering vectors for critical systems.",
            },
            {
                "id": "P3.6",
                "question": "Is source code review conducted for in-house developed critical applications?",
                "weight": 8,
                "article": "Article 25",
                "iso27001_map": "A.8.28, A.8.29",
                "guidance": "Perform security-focused source code reviews for applications supporting critical business functions.",
            },
            {
                "id": "P3.7",
                "question": "Has the entity assessed whether TLPT (threat-led penetration testing) is required?",
                "weight": 10,
                "article": "Article 26",
                "iso27001_map": "N/A (DORA-specific)",
                "guidance": "Competent authorities identify entities that must carry out TLPT. Assess applicability and begin preparations if required.",
            },
            {
                "id": "P3.8",
                "question": "Are test results documented and used to drive remediation?",
                "weight": 13,
                "article": "Article 24(6)",
                "iso27001_map": "Cl.10.1, Cl.10.2",
                "guidance": "Document all test findings, track remediation actions, verify fixes, and incorporate lessons into the ICT risk management framework.",
            },
        ],
    },
    4: {
        "title": "ICT Third-Party Risk Management",
        "chapter": "Chapter V (Articles 28-44)",
        "controls": [
            {
                "id": "P4.1",
                "question": "Is a complete register of all ICT third-party arrangements maintained?",
                "weight": 15,
                "article": "Article 28(3)",
                "iso27001_map": "A.5.19",
                "guidance": "Maintain a register distinguishing critical/important from non-critical function arrangements, including entity details, service scope, and data locations.",
            },
            {
                "id": "P4.2",
                "question": "Is due diligence conducted before entering ICT third-party arrangements?",
                "weight": 12,
                "article": "Article 28(4)",
                "iso27001_map": "A.5.19, A.5.21",
                "guidance": "Conduct pre-engagement risk assessment, due diligence on provider capabilities, and conflict of interest evaluation.",
            },
            {
                "id": "P4.3",
                "question": "Do contracts include all DORA-mandated provisions (SLAs, audit rights, termination, TLPT participation)?",
                "weight": 15,
                "article": "Article 30",
                "iso27001_map": "A.5.20",
                "guidance": "Ensure contracts cover service descriptions, SLAs, data location, incident assistance, audit rights, termination, and TLPT participation.",
            },
            {
                "id": "P4.4",
                "question": "Are ICT third-party providers supporting critical functions subject to enhanced contractual requirements?",
                "weight": 12,
                "article": "Article 30(3)",
                "iso27001_map": "A.5.20, A.5.22",
                "guidance": "Apply additional provisions for critical function providers: detailed SLAs, BCP testing, security awareness, notice periods for material changes.",
            },
            {
                "id": "P4.5",
                "question": "Are exit strategies documented and tested for critical function outsourcing?",
                "weight": 12,
                "article": "Article 28(8)",
                "iso27001_map": "A.5.20",
                "guidance": "Develop comprehensive exit strategies ensuring orderly transition without disruption. Include data migration and alternative provider plans.",
            },
            {
                "id": "P4.6",
                "question": "Is concentration risk assessed across ICT third-party providers?",
                "weight": 12,
                "article": "Article 29",
                "iso27001_map": "A.5.21",
                "guidance": "Identify concentration on single providers, assess substitutability, and develop multi-vendor strategies where appropriate.",
            },
            {
                "id": "P4.7",
                "question": "Is there ongoing monitoring of ICT third-party provider performance and security?",
                "weight": 10,
                "article": "Article 28(5)",
                "iso27001_map": "A.5.22",
                "guidance": "Continuously monitor provider SLA performance, security posture, and compliance with contractual obligations.",
            },
            {
                "id": "P4.8",
                "question": "Are sub-contractor chains for critical services documented and risk-assessed?",
                "weight": 12,
                "article": "Article 29(2)",
                "iso27001_map": "A.5.21",
                "guidance": "Document the sub-contracting chain for all critical ICT services and assess risks from sub-processor dependencies.",
            },
        ],
    },
    5: {
        "title": "Information Sharing",
        "chapter": "Chapter VI (Article 45)",
        "controls": [
            {
                "id": "P5.1",
                "question": "Does the entity participate in cyber threat intelligence sharing arrangements?",
                "weight": 30,
                "article": "Article 45(1)",
                "iso27001_map": "A.5.7",
                "guidance": "Consider joining information-sharing communities (ISACs, CERT groups) for exchanging IoCs, TTPs, and threat intelligence.",
            },
            {
                "id": "P5.2",
                "question": "Are information-sharing arrangements compliant with data protection and confidentiality requirements?",
                "weight": 25,
                "article": "Article 45(2)",
                "iso27001_map": "A.5.7, A.5.14",
                "guidance": "Ensure sharing arrangements respect business confidentiality, personal data protection (GDPR), and competition law.",
            },
            {
                "id": "P5.3",
                "question": "Has the entity notified its competent authority of participation in information-sharing arrangements?",
                "weight": 20,
                "article": "Article 45(3)",
                "iso27001_map": "N/A (DORA-specific)",
                "guidance": "Notify the competent authority when joining or establishing information-sharing arrangements.",
            },
            {
                "id": "P5.4",
                "question": "Are procedures in place to assess and act on shared threat intelligence?",
                "weight": 25,
                "article": "Article 45(1)",
                "iso27001_map": "A.5.7",
                "guidance": "Establish processes to receive, analyze, and operationalize cyber threat intelligence from sharing arrangements.",
            },
        ],
    },
}


def generate_template() -> Dict[str, Any]:
    """Generate an assessment input template."""
    template = {
        "_instructions": "Fill in each response with: 'yes', 'partial', 'no', or 'not_applicable'. "
                         "Add optional 'notes' field for context.",
        "organization": {
            "name": "Your Organization Name",
            "entity_type": "e.g., credit_institution, investment_firm, insurance_undertaking",
            "simplified_framework": False,
            "assessment_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "pillars": {},
    }

    for pillar_num, pillar_data in PILLARS.items():
        template["pillars"][f"pillar_{pillar_num}"] = {
            "title": pillar_data["title"],
            "controls": {},
        }
        for control in pillar_data["controls"]:
            template["pillars"][f"pillar_{pillar_num}"]["controls"][control["id"]] = {
                "question": control["question"],
                "response": "yes | partial | no | not_applicable",
                "notes": "",
            }

    return template


def score_response(response: str) -> Optional[float]:
    """Convert response to numeric score."""
    mapping = {
        "yes": 1.0,
        "partial": 0.5,
        "no": 0.0,
        "not_applicable": None,
    }
    return mapping.get(response.lower().strip(), 0.0)


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


def assess_pillar(pillar_num: int, responses: Dict[str, Any]) -> Dict[str, Any]:
    """Assess a single DORA pillar."""
    pillar_data = PILLARS[pillar_num]
    pillar_key = f"pillar_{pillar_num}"

    result = {
        "pillar": pillar_num,
        "title": pillar_data["title"],
        "chapter": pillar_data["chapter"],
        "controls": [],
        "score": 0,
        "gaps": [],
        "recommendations": [],
    }

    pillar_responses = responses.get("pillars", {}).get(pillar_key, {}).get("controls", {})

    total_weighted = 0.0
    total_weight = 0

    for control in pillar_data["controls"]:
        control_resp = pillar_responses.get(control["id"], {})
        response_value = control_resp.get("response", "no") if isinstance(control_resp, dict) else "no"
        notes = control_resp.get("notes", "") if isinstance(control_resp, dict) else ""

        score = score_response(response_value)

        control_result = {
            "id": control["id"],
            "question": control["question"],
            "response": response_value,
            "notes": notes,
            "weight": control["weight"],
            "article": control["article"],
            "iso27001_map": control["iso27001_map"],
        }

        if score is None:
            control_result["status"] = "not_applicable"
        else:
            weighted = score * control["weight"]
            total_weighted += weighted
            total_weight += control["weight"]

            if score == 1.0:
                control_result["status"] = "compliant"
            elif score == 0.5:
                control_result["status"] = "partial"
            else:
                control_result["status"] = "non_compliant"

            if score < 1.0:
                priority = "critical" if score == 0.0 and control["weight"] >= 15 else (
                    "high" if score == 0.0 else "medium"
                )
                gap = {
                    "control_id": control["id"],
                    "question": control["question"],
                    "current_status": control_result["status"],
                    "guidance": control["guidance"],
                    "article": control["article"],
                    "iso27001_map": control["iso27001_map"],
                    "priority": priority,
                }
                result["gaps"].append(gap)
                result["recommendations"].append({
                    "control_id": control["id"],
                    "action": control["guidance"],
                    "priority": priority,
                    "article": control["article"],
                })

        result["controls"].append(control_result)

    if total_weight > 0:
        result["score"] = round((total_weighted / total_weight) * 100, 1)

    result["compliance_level"] = _compliance_level(result["score"])
    return result


def run_full_assessment(
    responses: Dict[str, Any], pillar_filter: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Run a complete DORA readiness assessment."""
    result = {
        "timestamp": datetime.now().isoformat(),
        "organization": responses.get("organization", {}),
        "summary": {},
        "pillars": [],
        "overall_score": 0,
        "overall_readiness_level": "",
        "critical_gaps": [],
        "remediation_priorities": [],
    }

    pillars_to_check = pillar_filter if pillar_filter else list(PILLARS.keys())
    pillar_scores = []

    for p_num in pillars_to_check:
        if p_num in PILLARS:
            pillar_result = assess_pillar(p_num, responses)
            result["pillars"].append(pillar_result)
            pillar_scores.append(pillar_result["score"])

    # Overall score
    if pillar_scores:
        # Weight pillars differently: Pillar 1 and 4 are most impactful
        weights = {1: 30, 2: 20, 3: 15, 4: 25, 5: 10}
        weighted_sum = 0.0
        weight_total = 0
        for pillar_result in result["pillars"]:
            w = weights.get(pillar_result["pillar"], 20)
            weighted_sum += pillar_result["score"] * w
            weight_total += w
        if weight_total > 0:
            result["overall_score"] = round(weighted_sum / weight_total, 1)

    result["overall_readiness_level"] = _compliance_level(result["overall_score"])

    # Summary
    result["summary"] = {
        "total_pillars_assessed": len(pillars_to_check),
        "pillars_compliant": sum(1 for s in pillar_scores if s >= 90),
        "pillars_partial": sum(1 for s in pillar_scores if 50 <= s < 90),
        "pillars_non_compliant": sum(1 for s in pillar_scores if s < 50),
        "overall_score": result["overall_score"],
        "readiness_level": result["overall_readiness_level"],
        "pillar_scores": {
            p["title"]: p["score"] for p in result["pillars"]
        },
    }

    # Critical gaps
    for pillar_result in result["pillars"]:
        for gap in pillar_result.get("gaps", []):
            if gap["priority"] in ("critical", "high"):
                result["critical_gaps"].append({
                    "pillar": pillar_result["pillar"],
                    "pillar_title": pillar_result["title"],
                    **gap,
                })

    # Remediation priorities
    all_recs = []
    for pillar_result in result["pillars"]:
        for rec in pillar_result.get("recommendations", []):
            all_recs.append({
                "pillar": pillar_result["pillar"],
                "pillar_title": pillar_result["title"],
                **rec,
            })

    priority_order = {"critical": 0, "high": 1, "medium": 2}
    all_recs.sort(key=lambda x: (priority_order.get(x["priority"], 3), x.get("pillar", 0)))
    result["remediation_priorities"] = all_recs

    return result


def format_text_report(result: Dict[str, Any]) -> str:
    """Format assessment as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("DORA READINESS ASSESSMENT REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {result['timestamp']}")

    org = result.get("organization", {})
    if org:
        lines.append(f"Organization: {org.get('name', 'N/A')}")
        lines.append(f"Entity type:  {org.get('entity_type', 'N/A')}")
        lines.append(f"Simplified framework: {'Yes' if org.get('simplified_framework') else 'No'}")
    lines.append("")

    # Summary
    summary = result.get("summary", {})
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Overall Score:        {summary.get('overall_score', 0)}/100")
    lines.append(f"  Readiness Level:      {summary.get('readiness_level', 'N/A').upper()}")
    lines.append(f"  Pillars Assessed:     {summary.get('total_pillars_assessed', 0)}")
    lines.append(f"  Compliant (>=90):     {summary.get('pillars_compliant', 0)}")
    lines.append(f"  Partial (50-89):      {summary.get('pillars_partial', 0)}")
    lines.append(f"  Non-compliant (<50):  {summary.get('pillars_non_compliant', 0)}")
    lines.append("")

    # Pillar scores
    lines.append("PILLAR SCORES")
    lines.append("-" * 40)
    for pillar_result in result.get("pillars", []):
        score = pillar_result["score"]
        level = pillar_result["compliance_level"]
        bar = "#" * int(score / 5) + "." * (20 - int(score / 5))
        lines.append(f"  P{pillar_result['pillar']}. {pillar_result['title']:<45s}")
        lines.append(f"      [{bar}] {score:5.1f}/100 ({level})")
    lines.append("")

    # Critical gaps
    critical_gaps = result.get("critical_gaps", [])
    if critical_gaps:
        lines.append("CRITICAL GAPS")
        lines.append("-" * 40)
        for gap in critical_gaps:
            marker = "[!!!]" if gap["priority"] == "critical" else "[!!]"
            lines.append(f"  {marker} {gap['control_id']}: {gap['question']}")
            lines.append(f"        Pillar: {gap.get('pillar_title', '')}")
            lines.append(f"        Article: {gap.get('article', '')}")
            lines.append(f"        Action: {gap['guidance']}")
            lines.append("")

    # Top remediation priorities
    priorities = result.get("remediation_priorities", [])
    if priorities:
        lines.append("REMEDIATION PRIORITIES (Top 10)")
        lines.append("-" * 40)
        for i, rec in enumerate(priorities[:10], 1):
            lines.append(f"  {i}. [{rec['priority'].upper()}] {rec['control_id']} (Pillar {rec['pillar']})")
            lines.append(f"     {rec['action']}")
            lines.append(f"     Ref: {rec['article']}")
            lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="DORA Readiness Checker — Assess compliance against all 5 DORA pillars",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --template > assessment.json
  %(prog)s --config assessment.json
  %(prog)s --config assessment.json --pillars 1 3 4 --json
  %(prog)s --config assessment.json --output readiness_report.json --json
        """,
    )

    parser.add_argument("--config", help="Path to JSON assessment file (use --template to generate)")
    parser.add_argument("--template", action="store_true", help="Generate assessment input template")
    parser.add_argument("--pillars", nargs="+", type=int, help="Assess specific pillars only (e.g., 1 3 4)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", help="Write output to file")

    args = parser.parse_args()

    if args.template:
        template = generate_template()
        print(json.dumps(template, indent=2))
        return

    if not args.config:
        parser.error("--config is required for assessment (use --template to generate input file)")

    try:
        with open(args.config) as f:
            responses = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)

    if args.pillars:
        invalid = [p for p in args.pillars if p not in PILLARS]
        if invalid:
            parser.error(f"Invalid pillar numbers: {invalid}. Valid: 1-5")

    result = run_full_assessment(responses, pillar_filter=args.pillars)

    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_text_report(result)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Board Meeting Simulator - Simulate and validate meeting protocol execution.

Validates role activation, contribution completeness, phase sequencing,
and generates meeting readiness assessments. Helps prep for structured
multi-agent board deliberations.
"""

import argparse
import json
import sys
from datetime import datetime


ROLES = ["CEO", "CFO", "CMO", "CPO", "CRO", "COO", "CHRO", "CTO", "CISO"]

TOPIC_ROUTING = {
    "market_expansion": {"required": ["CEO", "CMO", "CFO", "CRO", "COO"], "optional": ["CTO"]},
    "product_direction": {"required": ["CEO", "CPO", "CTO", "CMO"], "optional": ["CFO"]},
    "hiring_org": {"required": ["CEO", "CHRO", "CFO", "COO"], "optional": ["CTO", "CMO"]},
    "pricing": {"required": ["CMO", "CFO", "CRO", "CPO"], "optional": []},
    "technology": {"required": ["CTO", "CPO", "CFO", "CISO"], "optional": []},
    "fundraising": {"required": ["CEO", "CFO", "CRO"], "optional": []},
    "security_incident": {"required": ["CEO", "CTO", "CISO", "COO"], "optional": []},
    "m_and_a": {"required": ["CEO", "CFO", "CTO", "CHRO", "COO"], "optional": []},
    "strategy": {"required": ["CEO", "CFO", "CMO", "CPO", "CRO"], "optional": ["COO"]},
    "cost_reduction": {"required": ["CEO", "CFO", "COO", "CHRO"], "optional": []},
}

PHASES = [
    {"phase": 1, "name": "Context Gathering", "required_outputs": ["agenda", "activated_roles", "context_loaded"]},
    {"phase": 2, "name": "Independent Contributions", "required_outputs": ["isolated_contributions"]},
    {"phase": 3, "name": "Critic Analysis", "required_outputs": ["consensus_assessment", "unvalidated_assumptions", "missing_perspectives", "uncomfortable_truth"]},
    {"phase": 4, "name": "Synthesis", "required_outputs": ["decision_required", "perspectives_summary", "agreements", "disagreements", "recommended_decision", "action_items"]},
    {"phase": 5, "name": "Founder Review", "required_outputs": ["founder_decision"]},
    {"phase": 6, "name": "Decision Extraction", "required_outputs": ["decisions_logged", "action_items_assigned"]},
]


def simulate_meeting(data: dict) -> dict:
    """Simulate and validate meeting protocol."""
    topic = data.get("topic", "strategy")
    topic_type = data.get("topic_type", "strategy")
    activated_roles = data.get("activated_roles", [])
    contributions = data.get("contributions", {})
    phase_status = data.get("phase_status", {})
    complexity_score = data.get("complexity_score", 7)

    routing = TOPIC_ROUTING.get(topic_type, TOPIC_ROUTING["strategy"])

    results = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "topic_type": topic_type,
        "complexity_score": complexity_score,
        "meeting_type": "Full Board" if complexity_score >= 8 else "Multi-Advisor" if complexity_score >= 5 else "Dual Advisor",
        "role_assessment": {},
        "phase_assessment": [],
        "contribution_quality": {},
        "readiness_score": 0,
        "warnings": [],
        "protocol_violations": [],
        "recommendations": [],
    }

    # Role assessment
    if not activated_roles:
        activated_roles = routing["required"]

    missing_required = [r for r in routing["required"] if r not in activated_roles]
    extra_roles = [r for r in activated_roles if r not in routing["required"] and r not in routing.get("optional", [])]
    recommended_additions = [r for r in routing.get("optional", []) if r not in activated_roles]

    results["role_assessment"] = {
        "activated": activated_roles,
        "required": routing["required"],
        "missing_required": missing_required,
        "extra_roles": extra_roles,
        "recommended_additions": recommended_additions,
        "attendee_count": len(activated_roles),
        "max_recommended": 6,
        "role_count_ok": len(activated_roles) <= 6,
    }

    if missing_required:
        results["warnings"].append(f"Missing required roles: {', '.join(missing_required)}")
    if len(activated_roles) > 6:
        results["warnings"].append(f"Too many attendees ({len(activated_roles)} > 6 max). Reduce to prevent noise.")

    # Phase assessment
    readiness_total = 0
    readiness_count = 0
    for phase_config in PHASES:
        phase_num = phase_config["phase"]
        phase_data = phase_status.get(str(phase_num), {})
        status = phase_data.get("status", "not_started")

        outputs_present = []
        outputs_missing = []
        for output in phase_config["required_outputs"]:
            if phase_data.get(output, False):
                outputs_present.append(output)
            else:
                outputs_missing.append(output)

        completeness = len(outputs_present) / len(phase_config["required_outputs"]) * 100 if phase_config["required_outputs"] else 0

        phase_result = {
            "phase": phase_num,
            "name": phase_config["name"],
            "status": status,
            "completeness_pct": round(completeness),
            "outputs_present": outputs_present,
            "outputs_missing": outputs_missing,
        }
        results["phase_assessment"].append(phase_result)

        if status == "complete":
            readiness_total += 100
        elif status == "in_progress":
            readiness_total += completeness
        readiness_count += 1

    # Contribution quality checks
    for role in activated_roles:
        contrib = contributions.get(role, {})
        quality = {
            "role": role,
            "has_key_points": bool(contrib.get("key_points")),
            "has_recommendation": bool(contrib.get("recommendation")),
            "has_confidence": bool(contrib.get("confidence")),
            "has_key_assumption": bool(contrib.get("key_assumption")),
            "has_change_condition": bool(contrib.get("what_would_change_mind")),
            "points_count": len(contrib.get("key_points", [])),
            "format_compliant": True,
        }

        # Validate format
        violations = []
        if quality["points_count"] > 5:
            violations.append(f"{role}: More than 5 key points ({quality['points_count']})")
            quality["format_compliant"] = False
        if not quality["has_recommendation"]:
            violations.append(f"{role}: Missing recommendation")
            quality["format_compliant"] = False
        if not quality["has_confidence"]:
            violations.append(f"{role}: Missing confidence level")
            quality["format_compliant"] = False

        results["contribution_quality"][role] = quality
        results["protocol_violations"].extend(violations)

    # Cross-pollination check
    if data.get("cross_pollination_detected", False):
        results["protocol_violations"].append("CRITICAL: Cross-pollination detected in Phase 2. Contributions must be isolated.")

    # Overall readiness
    results["readiness_score"] = round(readiness_total / readiness_count) if readiness_count > 0 else 0

    # Recommendations
    if results["readiness_score"] < 50:
        results["recommendations"].append("Meeting not ready. Complete earlier phases before proceeding.")
    if missing_required:
        results["recommendations"].append(f"Activate missing roles before starting: {', '.join(missing_required)}")
    if results["protocol_violations"]:
        results["recommendations"].append(f"Fix {len(results['protocol_violations'])} protocol violations before synthesis.")

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 60,
        "BOARD MEETING PROTOCOL ASSESSMENT",
        "=" * 60,
        f"Topic: {results['topic']}",
        f"Type: {results['topic_type']}  |  Complexity: {results['complexity_score']}/10",
        f"Meeting Type: {results['meeting_type']}",
        f"Readiness: {results['readiness_score']}%",
        "",
        "ROLE ACTIVATION:",
        f"  Activated: {', '.join(results['role_assessment']['activated'])} ({results['role_assessment']['attendee_count']})",
        f"  Required:  {', '.join(results['role_assessment']['required'])}",
    ]

    ra = results["role_assessment"]
    if ra["missing_required"]:
        lines.append(f"  MISSING:   {', '.join(ra['missing_required'])}")
    if ra["recommended_additions"]:
        lines.append(f"  Optional:  {', '.join(ra['recommended_additions'])}")

    lines.extend(["", "PHASE STATUS:"])
    for p in results["phase_assessment"]:
        icon = "[x]" if p["status"] == "complete" else "[~]" if p["status"] == "in_progress" else "[ ]"
        lines.append(f"  {icon} Phase {p['phase']}: {p['name']} ({p['completeness_pct']}%)")
        if p["outputs_missing"]:
            lines.append(f"      Missing: {', '.join(p['outputs_missing'])}")

    if results["protocol_violations"]:
        lines.extend(["", "PROTOCOL VIOLATIONS:"])
        for v in results["protocol_violations"]:
            lines.append(f"  [!] {v}")

    if results["warnings"]:
        lines.extend(["", "WARNINGS:"])
        for w in results["warnings"]:
            lines.append(f"  [W] {w}")

    if results["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Simulate and validate board meeting protocol")
    parser.add_argument("--input", "-i", help="JSON file with meeting data")
    parser.add_argument("--topic", help="Meeting topic")
    parser.add_argument("--type", choices=list(TOPIC_ROUTING.keys()), default="strategy", help="Topic type")
    parser.add_argument("--complexity", type=int, default=7, help="Complexity score (1-10)")
    parser.add_argument("--roles", nargs="*", help="Activated roles")
    parser.add_argument("--list-topics", action="store_true", help="List topic types and required roles")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list_topics:
        print("Topic Types and Required Roles:")
        for topic, routing in TOPIC_ROUTING.items():
            print(f"  {topic}: {', '.join(routing['required'])} (optional: {', '.join(routing.get('optional', []))})")
        return

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "topic": args.topic or "Q2 Strategy Review",
            "topic_type": args.type,
            "complexity_score": args.complexity,
            "activated_roles": args.roles or TOPIC_ROUTING.get(args.type, {}).get("required", ["CEO", "CFO"]),
            "contributions": {},
            "phase_status": {
                "1": {"status": "complete", "agenda": True, "activated_roles": True, "context_loaded": True},
                "2": {"status": "in_progress", "isolated_contributions": False},
            },
        }

    results = simulate_meeting(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Board Deck Structure Validator - Validates board deck completeness and quality.

Checks a board deck outline against best-practice section requirements,
identifies missing sections, flags quality issues, and scores overall readiness.
"""

import argparse
import json
import sys
from datetime import datetime

REQUIRED_SECTIONS = {
    "executive_summary": {
        "owner": "CEO",
        "weight": 15,
        "checks": ["three_sentence_rule", "forward_looking", "no_vague_language"],
        "description": "3-sentence executive summary with state, development, priority"
    },
    "metrics_dashboard": {
        "owner": "COO",
        "weight": 15,
        "checks": ["has_targets", "has_status_indicators", "max_8_metrics"],
        "description": "6-8 key metrics with targets and RAG status"
    },
    "financial_update": {
        "owner": "CFO",
        "weight": 15,
        "checks": ["pnl_summary", "cash_position", "variance_explanations", "forecast"],
        "description": "P&L, cash position, burn multiple, variance to plan, forecast"
    },
    "revenue_pipeline": {
        "owner": "CRO",
        "weight": 10,
        "checks": ["arr_waterfall", "nrr_trend", "pipeline_by_stage", "forecast_confidence"],
        "description": "ARR waterfall, NRR, pipeline, forecast with confidence"
    },
    "product_update": {
        "owner": "CPO",
        "weight": 8,
        "checks": ["shipped_items", "upcoming_items", "pmf_signals"],
        "description": "Shipped, shipping next, PMF signals, key learning"
    },
    "growth_marketing": {
        "owner": "CMO",
        "weight": 7,
        "checks": ["cac_by_channel", "pipeline_contribution", "experiments"],
        "description": "CAC by channel, pipeline contribution, what works/cut/testing"
    },
    "engineering_technical": {
        "owner": "CTO",
        "weight": 5,
        "checks": ["delivery_velocity", "tech_debt", "infrastructure"],
        "description": "Delivery velocity, tech debt, infrastructure, security posture"
    },
    "team_people": {
        "owner": "CHRO",
        "weight": 8,
        "checks": ["headcount_vs_plan", "hiring_pipeline", "attrition", "engagement"],
        "description": "Headcount, hiring, attrition, engagement, notable changes"
    },
    "risk_security": {
        "owner": "CISO",
        "weight": 5,
        "checks": ["security_posture", "compliance_status", "incidents", "top_risks"],
        "description": "Security posture, compliance, incidents, top 3 risks"
    },
    "strategic_outlook": {
        "owner": "CEO",
        "weight": 10,
        "checks": ["next_quarter_priorities", "board_decisions_needed", "specific_asks"],
        "description": "Next quarter priorities, decisions needed, specific asks"
    },
    "appendix": {
        "owner": "Multiple",
        "weight": 2,
        "checks": ["financial_model", "pipeline_data", "cohort_charts"],
        "description": "Detailed data (not presented unless asked)"
    }
}

DECK_TYPES = {
    "quarterly": {"max_slides": 30, "min_slides": 20, "advance_send_hours": 48},
    "monthly": {"max_slides": 12, "min_slides": 8, "advance_send_hours": 24},
    "fundraising": {"max_slides": 15, "min_slides": 12, "advance_send_hours": 0},
    "emergency": {"max_slides": 8, "min_slides": 5, "advance_send_hours": 0},
}

QUALITY_CHECKS = [
    {"id": "narrative_throughline", "description": "Deck follows 4-act structure (where we said, where we are, why gap, what we do)", "severity": "high"},
    {"id": "opening_by_slide_3", "description": "Key message clear by slide 3", "severity": "high"},
    {"id": "no_vague_asks", "description": "Asks section has specific, actionable requests", "severity": "high"},
    {"id": "numbers_consistent", "description": "Financial numbers consistent across sections", "severity": "critical"},
    {"id": "bad_news_souf", "description": "Bad news uses SOUF framework (State, Own, Understand, Fix)", "severity": "medium"},
    {"id": "max_6_lines_per_slide", "description": "No slide exceeds 6 lines of text", "severity": "medium"},
    {"id": "variance_explained", "description": "Every variance from target has a one-sentence cause", "severity": "high"},
    {"id": "action_items_from_last", "description": "Follow-up on previous meeting action items included", "severity": "medium"},
    {"id": "consistent_formatting", "description": "One template, one color scheme, one font throughout", "severity": "low"},
    {"id": "pre_read_ready", "description": "Deck works as a standalone document for pre-reading", "severity": "medium"},
]


def validate_deck(deck_data: dict) -> dict:
    """Validate a board deck against best practices."""
    deck_type = deck_data.get("type", "quarterly")
    sections = deck_data.get("sections", {})
    slide_count = deck_data.get("slide_count", 0)
    quality_flags = deck_data.get("quality_flags", {})

    type_config = DECK_TYPES.get(deck_type, DECK_TYPES["quarterly"])
    results = {
        "timestamp": datetime.now().isoformat(),
        "deck_type": deck_type,
        "overall_score": 0,
        "max_score": 100,
        "grade": "",
        "section_results": [],
        "missing_sections": [],
        "quality_issues": [],
        "slide_count_assessment": {},
        "recommendations": [],
    }

    # Section completeness
    total_weight = 0
    earned_weight = 0
    for section_id, config in REQUIRED_SECTIONS.items():
        section_present = section_id in sections
        section_data = sections.get(section_id, {})
        checks_passed = 0
        checks_total = len(config["checks"])
        failed_checks = []

        if section_present:
            for check in config["checks"]:
                if section_data.get(check, False):
                    checks_passed += 1
                else:
                    failed_checks.append(check)

            completeness = (checks_passed / checks_total) if checks_total > 0 else 0
            section_score = config["weight"] * completeness
            earned_weight += section_score
            results["section_results"].append({
                "section": section_id,
                "owner": config["owner"],
                "present": True,
                "checks_passed": checks_passed,
                "checks_total": checks_total,
                "completeness_pct": round(completeness * 100),
                "score": round(section_score, 1),
                "max_score": config["weight"],
                "failed_checks": failed_checks,
            })
        else:
            results["missing_sections"].append({
                "section": section_id,
                "owner": config["owner"],
                "weight": config["weight"],
                "description": config["description"],
            })
            results["section_results"].append({
                "section": section_id,
                "owner": config["owner"],
                "present": False,
                "checks_passed": 0,
                "checks_total": checks_total,
                "completeness_pct": 0,
                "score": 0,
                "max_score": config["weight"],
                "failed_checks": config["checks"],
            })

        total_weight += config["weight"]

    # Slide count assessment
    if slide_count > 0:
        if slide_count > type_config["max_slides"]:
            results["slide_count_assessment"] = {
                "status": "over",
                "count": slide_count,
                "max": type_config["max_slides"],
                "message": f"Too many slides ({slide_count} vs max {type_config['max_slides']}). Cut ruthlessly.",
            }
        elif slide_count < type_config["min_slides"]:
            results["slide_count_assessment"] = {
                "status": "under",
                "count": slide_count,
                "min": type_config["min_slides"],
                "message": f"Too few slides ({slide_count} vs min {type_config['min_slides']}). May lack depth.",
            }
        else:
            results["slide_count_assessment"] = {
                "status": "ok",
                "count": slide_count,
                "range": f"{type_config['min_slides']}-{type_config['max_slides']}",
                "message": "Slide count within recommended range.",
            }

    # Quality checks
    for check in QUALITY_CHECKS:
        passed = quality_flags.get(check["id"], False)
        if not passed:
            results["quality_issues"].append({
                "check": check["id"],
                "description": check["description"],
                "severity": check["severity"],
            })

    # Calculate overall score
    quality_penalty = sum(
        3 if issue["severity"] == "critical"
        else 2 if issue["severity"] == "high"
        else 1
        for issue in results["quality_issues"]
    )
    raw_score = (earned_weight / total_weight * 100) if total_weight > 0 else 0
    results["overall_score"] = max(0, round(raw_score - quality_penalty))

    # Grade
    score = results["overall_score"]
    if score >= 90:
        results["grade"] = "A"
    elif score >= 80:
        results["grade"] = "B"
    elif score >= 70:
        results["grade"] = "C"
    elif score >= 60:
        results["grade"] = "D"
    else:
        results["grade"] = "F"

    # Recommendations
    if results["missing_sections"]:
        owners = set(s["owner"] for s in results["missing_sections"])
        results["recommendations"].append(
            f"Missing {len(results['missing_sections'])} sections. Contact: {', '.join(sorted(owners))}"
        )
    critical_quality = [i for i in results["quality_issues"] if i["severity"] == "critical"]
    if critical_quality:
        results["recommendations"].append(
            f"CRITICAL: {len(critical_quality)} critical quality issue(s) must be fixed before board send."
        )
    high_quality = [i for i in results["quality_issues"] if i["severity"] == "high"]
    if high_quality:
        results["recommendations"].append(
            f"HIGH: {len(high_quality)} high-severity quality issue(s) should be addressed."
        )
    incomplete = [s for s in results["section_results"] if s["present"] and s["completeness_pct"] < 80]
    if incomplete:
        results["recommendations"].append(
            f"{len(incomplete)} section(s) below 80% completeness: {', '.join(s['section'] for s in incomplete)}"
        )

    return results


def format_text(results: dict) -> str:
    """Format results as human-readable text."""
    lines = [
        "=" * 60,
        "BOARD DECK STRUCTURE VALIDATION REPORT",
        "=" * 60,
        f"Deck Type: {results['deck_type'].upper()}",
        f"Date: {results['timestamp'][:10]}",
        f"Overall Score: {results['overall_score']}/100 (Grade: {results['grade']})",
        "",
    ]

    # Slide count
    sca = results.get("slide_count_assessment", {})
    if sca:
        status_icon = {"ok": "[OK]", "over": "[!]", "under": "[?]"}.get(sca.get("status", ""), "")
        lines.append(f"Slide Count: {status_icon} {sca.get('message', '')}")
        lines.append("")

    # Section results
    lines.append("SECTION COMPLETENESS:")
    lines.append("-" * 60)
    lines.append(f"{'Section':<25} {'Owner':<8} {'Score':>6} {'Complete':>9} {'Status'}")
    lines.append("-" * 60)
    for s in results["section_results"]:
        status = "PRESENT" if s["present"] else "MISSING"
        icon = "[G]" if s["completeness_pct"] >= 80 else "[Y]" if s["completeness_pct"] >= 50 else "[R]"
        if not s["present"]:
            icon = "[R]"
        lines.append(
            f"{s['section']:<25} {s['owner']:<8} {s['score']:>5.1f}/{s['max_score']:<2} "
            f"{s['completeness_pct']:>7}%  {icon} {status}"
        )
    lines.append("")

    # Missing sections
    if results["missing_sections"]:
        lines.append("MISSING SECTIONS:")
        for ms in results["missing_sections"]:
            lines.append(f"  - {ms['section']} ({ms['owner']}): {ms['description']}")
        lines.append("")

    # Quality issues
    if results["quality_issues"]:
        lines.append("QUALITY ISSUES:")
        for qi in results["quality_issues"]:
            sev = qi["severity"].upper()
            lines.append(f"  [{sev}] {qi['description']}")
        lines.append("")

    # Recommendations
    if results["recommendations"]:
        lines.append("RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            lines.append(f"  -> {rec}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate board deck structure against best practices"
    )
    parser.add_argument(
        "--input", "-i",
        help="JSON file with deck structure data (stdin if omitted)"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["quarterly", "monthly", "fundraising", "emergency"],
        default="quarterly",
        help="Deck type (default: quarterly)"
    )
    parser.add_argument(
        "--slides", "-s",
        type=int, default=0,
        help="Number of slides in the deck"
    )
    parser.add_argument(
        "--sections",
        nargs="*",
        help="List of section IDs present in the deck"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    args = parser.parse_args()

    # Build deck data
    if args.input:
        with open(args.input) as f:
            deck_data = json.load(f)
    elif args.sections:
        deck_data = {
            "type": args.type,
            "slide_count": args.slides,
            "sections": {s: {} for s in args.sections},
        }
    else:
        # Demo mode
        deck_data = {
            "type": args.type,
            "slide_count": args.slides if args.slides else 24,
            "sections": {
                "executive_summary": {"three_sentence_rule": True, "forward_looking": True, "no_vague_language": False},
                "metrics_dashboard": {"has_targets": True, "has_status_indicators": True, "max_8_metrics": True},
                "financial_update": {"pnl_summary": True, "cash_position": True, "variance_explanations": False, "forecast": True},
                "revenue_pipeline": {"arr_waterfall": True, "nrr_trend": True, "pipeline_by_stage": True, "forecast_confidence": False},
                "product_update": {"shipped_items": True, "upcoming_items": True, "pmf_signals": False},
                "strategic_outlook": {"next_quarter_priorities": True, "board_decisions_needed": True, "specific_asks": False},
            },
            "quality_flags": {
                "narrative_throughline": True,
                "opening_by_slide_3": True,
                "numbers_consistent": True,
                "action_items_from_last": False,
            },
        }

    deck_data["type"] = deck_data.get("type", args.type)
    if args.slides:
        deck_data["slide_count"] = args.slides

    results = validate_deck(deck_data)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()

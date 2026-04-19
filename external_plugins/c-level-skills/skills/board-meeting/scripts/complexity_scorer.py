#!/usr/bin/env python3
"""
Decision Complexity Scorer - Score decision complexity to determine routing.

Evaluates decisions against domain count, reversibility, financial impact,
team impact, and time pressure. Outputs routing recommendation.
"""

import argparse
import json
import sys
from datetime import datetime


FACTORS = {
    "domain_count": {"weight": 0.25, "scores": {0: "Single domain", 1: "2 domains", 2: "3+ domains"}},
    "reversibility": {"weight": 0.25, "scores": {0: "Easily reversed", 1: "Partially reversible", 2: "Irreversible"}},
    "financial_impact": {"weight": 0.20, "scores": {0: "< 5% of budget", 1: "5-20% of budget", 2: "> 20% of budget"}},
    "team_impact": {"weight": 0.15, "scores": {0: "Single team", 1: "Multiple teams", 2: "Org-wide"}},
    "time_pressure": {"weight": 0.15, "scores": {0: "No urgency", 1: "Days to decide", 2: "Hours to decide"}},
}

MODIFIERS = [
    {"id": "cross_functional", "label": "Affects 2+ functional areas", "add": 1},
    {"id": "irreversible_costly", "label": "Decision is irreversible or very costly to reverse", "add": 1},
    {"id": "disagreement", "label": "Expected disagreement between advisors", "add": 1},
    {"id": "team_10_plus", "label": "Direct impact on 10+ team members", "add": 1},
    {"id": "compliance", "label": "Compliance or regulatory dimension", "add": 1},
    {"id": "external_stakeholders", "label": "Involves external stakeholders (board, investors, partners)", "add": 1},
    {"id": "sets_precedent", "label": "Sets precedent for future decisions", "add": 1},
    {"id": "contradicts_previous", "label": "Contradicts a previous logged decision", "add": 1},
]

ROUTING = [
    {"min": 1, "max": 3, "type": "SINGLE ADVISOR", "description": "Route to primary domain expert. Return answer directly."},
    {"min": 4, "max": 6, "type": "DUAL ADVISOR", "description": "Route to primary + secondary. Synthesize before returning."},
    {"min": 7, "max": 8, "type": "MULTI-ADVISOR", "description": "Route to 3-4 relevant roles. Full synthesis with conflict mapping."},
    {"min": 9, "max": 10, "type": "FULL BOARD MEETING", "description": "Invoke board-meeting protocol. All relevant roles contribute independently."},
]


def score_complexity(data: dict) -> dict:
    """Score decision complexity and determine routing."""
    factor_scores = data.get("factors", {})
    active_modifiers = data.get("modifiers", [])
    topic = data.get("topic", "Unspecified")

    results = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "factor_scores": {},
        "base_score": 0,
        "modifier_score": 0,
        "total_score": 0,
        "active_modifiers": [],
        "routing": {},
        "recommended_roles": [],
        "rationale": [],
    }

    # Score factors
    base_total = 0
    for factor_name, config in FACTORS.items():
        score = factor_scores.get(factor_name, 1)
        score = min(2, max(0, score))
        weighted = score * config["weight"] * 5  # Scale to contribute to 0-10
        base_total += weighted
        results["factor_scores"][factor_name] = {
            "score": score,
            "label": config["scores"].get(score, "Unknown"),
            "weight": config["weight"],
            "weighted": round(weighted, 2),
        }

    results["base_score"] = round(base_total, 1)

    # Apply modifiers
    modifier_total = 0
    for mod in MODIFIERS:
        if mod["id"] in active_modifiers:
            modifier_total += mod["add"]
            results["active_modifiers"].append(mod["label"])

    results["modifier_score"] = modifier_total
    results["total_score"] = min(10, round(results["base_score"] + modifier_total))

    # Determine routing
    total = results["total_score"]
    for route in ROUTING:
        if route["min"] <= total <= route["max"]:
            results["routing"] = {
                "type": route["type"],
                "description": route["description"],
                "score_range": f"{route['min']}-{route['max']}",
            }
            break

    # Build rationale
    high_factors = [(n, d) for n, d in results["factor_scores"].items() if d["score"] == 2]
    if high_factors:
        results["rationale"].append(
            f"High complexity factors: {', '.join(d['label'] for _, d in high_factors)}"
        )
    if results["active_modifiers"]:
        results["rationale"].append(
            f"Active modifiers (+{modifier_total}): {', '.join(results['active_modifiers'][:3])}"
        )
    results["rationale"].append(
        f"Total score {total}/10 -> {results['routing'].get('type', 'Unknown')}"
    )

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 60,
        "DECISION COMPLEXITY ASSESSMENT",
        "=" * 60,
        f"Topic: {results['topic']}",
        f"Complexity Score: {results['total_score']}/10 (base: {results['base_score']:.1f}, modifiers: +{results['modifier_score']})",
        f"Routing: {results['routing'].get('type', 'N/A')}",
        "",
        "FACTOR BREAKDOWN:",
        f"{'Factor':<20} {'Score':>6} {'Description':<30} {'Weighted':>8}",
        "-" * 60,
    ]

    for name, data in results["factor_scores"].items():
        lines.append(f"{name:<20} {data['score']:>5}/2 {data['label']:<30} {data['weighted']:>7.2f}")

    if results["active_modifiers"]:
        lines.extend(["", f"MODIFIERS (+{results['modifier_score']}):"])
        for mod in results["active_modifiers"]:
            lines.append(f"  [+1] {mod}")

    lines.extend(["", "ROUTING DECISION:"])
    r = results["routing"]
    lines.append(f"  {r.get('type', 'N/A')}: {r.get('description', '')}")

    if results["rationale"]:
        lines.extend(["", "RATIONALE:"])
        for rat in results["rationale"]:
            lines.append(f"  {rat}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Score decision complexity for routing")
    parser.add_argument("--input", "-i", help="JSON file with decision data")
    parser.add_argument("--topic", help="Decision topic")
    parser.add_argument("--domains", type=int, choices=[0, 1, 2], help="Domain count (0=single, 1=two, 2=three+)")
    parser.add_argument("--reversibility", type=int, choices=[0, 1, 2], help="Reversibility (0=easy, 1=partial, 2=irreversible)")
    parser.add_argument("--financial", type=int, choices=[0, 1, 2], help="Financial impact (0=<5%%, 1=5-20%%, 2=>20%%)")
    parser.add_argument("--team", type=int, choices=[0, 1, 2], help="Team impact (0=single, 1=multi, 2=org-wide)")
    parser.add_argument("--urgency", type=int, choices=[0, 1, 2], help="Time pressure (0=none, 1=days, 2=hours)")
    parser.add_argument("--modifiers", nargs="*", choices=[m["id"] for m in MODIFIERS], default=[], help="Active modifiers")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "topic": args.topic or "Strategic decision",
            "factors": {
                "domain_count": args.domains if args.domains is not None else 1,
                "reversibility": args.reversibility if args.reversibility is not None else 1,
                "financial_impact": args.financial if args.financial is not None else 1,
                "team_impact": args.team if args.team is not None else 1,
                "time_pressure": args.urgency if args.urgency is not None else 0,
            },
            "modifiers": args.modifiers,
        }

    results = score_complexity(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()

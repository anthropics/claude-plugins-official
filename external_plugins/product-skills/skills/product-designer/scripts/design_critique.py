#!/usr/bin/env python3
"""
Design Critique Generator

Evaluates a UI design against established heuristics (Nielsen's 10,
Gestalt principles, accessibility standards) and generates a structured
critique report with severity ratings and improvement suggestions.

Uses ONLY Python standard library.

Usage:
    python design_critique.py --checklist
    python design_critique.py --answers answers.json
    python design_critique.py --answers answers.json --json
"""

import argparse
import json
import sys
from typing import Dict, List


# Nielsen's 10 Usability Heuristics
NIELSEN_HEURISTICS = [
    {
        "id": "N1",
        "name": "Visibility of system status",
        "description": "The design keeps users informed about what is happening through appropriate feedback within reasonable time.",
        "checkpoints": [
            "Loading states are visible for operations >1 second",
            "Progress indicators shown for multi-step processes",
            "Success/error feedback appears after user actions",
            "Current location is clear in navigation",
        ],
    },
    {
        "id": "N2",
        "name": "Match between system and real world",
        "description": "The design uses language, concepts, and conventions familiar to the user.",
        "checkpoints": [
            "Labels use user language, not internal jargon",
            "Icons follow established conventions",
            "Information appears in natural and logical order",
            "Metaphors match real-world expectations",
        ],
    },
    {
        "id": "N3",
        "name": "User control and freedom",
        "description": "Users can easily undo, redo, or exit unwanted states.",
        "checkpoints": [
            "Undo is available for destructive actions",
            "Cancel/back options are clearly visible",
            "Users can exit flows without losing progress",
            "Confirmation dialogs for irreversible actions",
        ],
    },
    {
        "id": "N4",
        "name": "Consistency and standards",
        "description": "Users don't have to wonder whether different words, situations, or actions mean the same thing.",
        "checkpoints": [
            "UI elements behave the same way throughout",
            "Terminology is consistent across all pages",
            "Visual patterns (spacing, colors) are consistent",
            "Platform conventions are followed",
        ],
    },
    {
        "id": "N5",
        "name": "Error prevention",
        "description": "Good design prevents problems from occurring in the first place.",
        "checkpoints": [
            "Form validation occurs before submission",
            "Constraints prevent invalid inputs",
            "Destructive actions require confirmation",
            "Default values reduce user effort and errors",
        ],
    },
    {
        "id": "N6",
        "name": "Recognition rather than recall",
        "description": "Minimize the user's memory load by making elements, actions, and options visible.",
        "checkpoints": [
            "Options are visible rather than requiring memorization",
            "Help and instructions are easily accessible",
            "Recently used items are easily accessible",
            "Search and filter options are visible",
        ],
    },
    {
        "id": "N7",
        "name": "Flexibility and efficiency of use",
        "description": "Accelerators allow experienced users to speed up interaction.",
        "checkpoints": [
            "Keyboard shortcuts available for frequent actions",
            "Customizable interface elements",
            "Shortcuts or recent items for repeat tasks",
            "Batch operations for power users",
        ],
    },
    {
        "id": "N8",
        "name": "Aesthetic and minimalist design",
        "description": "Interfaces should not contain irrelevant or rarely needed information.",
        "checkpoints": [
            "Each screen focuses on one primary action",
            "Visual hierarchy guides attention to important elements",
            "Whitespace used effectively",
            "No unnecessary decorative elements that distract",
        ],
    },
    {
        "id": "N9",
        "name": "Help users recognize, diagnose, and recover from errors",
        "description": "Error messages should be expressed in plain language and suggest a solution.",
        "checkpoints": [
            "Error messages are in plain language (no codes)",
            "Error messages indicate what went wrong specifically",
            "Error messages suggest how to fix the issue",
            "Errors are visually prominent and close to the source",
        ],
    },
    {
        "id": "N10",
        "name": "Help and documentation",
        "description": "Help information should be easy to search, focused on the task, and not too large.",
        "checkpoints": [
            "Help is easily accessible from any screen",
            "Contextual help is provided where needed",
            "Onboarding guides new users through key features",
            "Documentation is searchable and task-focused",
        ],
    },
]

# Accessibility heuristics
A11Y_HEURISTICS = [
    {
        "id": "A1",
        "name": "Color contrast",
        "checkpoints": [
            "Text meets 4.5:1 contrast ratio (WCAG AA)",
            "Large text meets 3:1 contrast ratio",
            "Color is not the only way to convey information",
            "Focus indicators have sufficient contrast",
        ],
    },
    {
        "id": "A2",
        "name": "Keyboard navigation",
        "checkpoints": [
            "All interactive elements reachable via Tab key",
            "Focus order follows logical reading order",
            "Focus ring is visible on all interactive elements",
            "No keyboard traps (user can always navigate away)",
        ],
    },
    {
        "id": "A3",
        "name": "Screen reader support",
        "checkpoints": [
            "All images have meaningful alt text",
            "Form inputs have associated labels",
            "ARIA attributes used correctly for dynamic content",
            "Headings follow logical hierarchy (h1 > h2 > h3)",
        ],
    },
]

SEVERITY_LEVELS = {
    0: {"label": "Cosmetic", "action": "Fix when possible", "color": "gray"},
    1: {"label": "Minor", "action": "Low priority fix", "color": "yellow"},
    2: {"label": "Major", "action": "Fix before next release", "color": "orange"},
    3: {"label": "Critical", "action": "Fix immediately", "color": "red"},
}


def generate_checklist() -> Dict:
    """Generate empty checklist for evaluation."""
    checklist = {"heuristics": [], "accessibility": []}

    for h in NIELSEN_HEURISTICS:
        entry = {
            "id": h["id"],
            "name": h["name"],
            "checkpoints": [
                {"check": cp, "pass": None, "severity": None, "notes": ""}
                for cp in h["checkpoints"]
            ],
        }
        checklist["heuristics"].append(entry)

    for a in A11Y_HEURISTICS:
        entry = {
            "id": a["id"],
            "name": a["name"],
            "checkpoints": [
                {"check": cp, "pass": None, "severity": None, "notes": ""}
                for cp in a["checkpoints"]
            ],
        }
        checklist["accessibility"].append(entry)

    return checklist


def analyze_answers(answers: Dict) -> Dict:
    """Analyze completed checklist and generate critique report."""
    issues = []
    passes = []
    total_checks = 0
    passed_checks = 0

    for section_key in ["heuristics", "accessibility"]:
        for heuristic in answers.get(section_key, []):
            for cp in heuristic.get("checkpoints", []):
                total_checks += 1
                if cp.get("pass") is True:
                    passed_checks += 1
                    passes.append({
                        "heuristic_id": heuristic["id"],
                        "heuristic_name": heuristic["name"],
                        "checkpoint": cp["check"],
                    })
                elif cp.get("pass") is False:
                    severity = cp.get("severity", 1)
                    issues.append({
                        "heuristic_id": heuristic["id"],
                        "heuristic_name": heuristic["name"],
                        "checkpoint": cp["check"],
                        "severity": severity,
                        "severity_label": SEVERITY_LEVELS.get(severity, SEVERITY_LEVELS[1])["label"],
                        "action": SEVERITY_LEVELS.get(severity, SEVERITY_LEVELS[1])["action"],
                        "notes": cp.get("notes", ""),
                    })

    # Sort issues by severity (highest first)
    issues.sort(key=lambda x: -x["severity"])

    # Calculate scores
    compliance_score = round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0

    severity_counts = {v["label"]: 0 for v in SEVERITY_LEVELS.values()}
    for issue in issues:
        severity_counts[issue["severity_label"]] = severity_counts.get(issue["severity_label"], 0) + 1

    # Overall grade
    if compliance_score >= 90 and severity_counts.get("Critical", 0) == 0:
        grade = "A"
    elif compliance_score >= 80 and severity_counts.get("Critical", 0) == 0:
        grade = "B"
    elif compliance_score >= 65:
        grade = "C"
    elif compliance_score >= 50:
        grade = "D"
    else:
        grade = "F"

    return {
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "compliance_score": compliance_score,
            "grade": grade,
            "severity_distribution": severity_counts,
        },
        "issues": issues,
        "strengths": passes[:5],
        "top_priorities": issues[:5],
    }


def format_checklist_output(checklist: Dict) -> str:
    """Format checklist as human-readable text for manual evaluation."""
    lines = []
    lines.append("=" * 60)
    lines.append("DESIGN CRITIQUE CHECKLIST")
    lines.append("=" * 60)
    lines.append("\nFill in pass (true/false), severity (0-3), and notes for each checkpoint.")
    lines.append("Save as JSON and run: python design_critique.py --answers answers.json\n")

    for section in ["heuristics", "accessibility"]:
        section_label = "NIELSEN'S 10 HEURISTICS" if section == "heuristics" else "ACCESSIBILITY"
        lines.append(f"\n  {section_label}")
        lines.append("  " + "-" * 50)

        for h in checklist[section]:
            lines.append(f"\n  [{h['id']}] {h['name']}")
            for cp in h["checkpoints"]:
                lines.append(f"    [ ] {cp['check']}")

    lines.append("\n\nSeverity scale: 0=Cosmetic, 1=Minor, 2=Major, 3=Critical")
    return "\n".join(lines)


def format_report_output(report: Dict) -> str:
    """Format critique report as human-readable text."""
    s = report["summary"]
    lines = []
    lines.append("=" * 60)
    lines.append("DESIGN CRITIQUE REPORT")
    lines.append("=" * 60)

    lines.append(f"\n  COMPLIANCE SCORE: {s['compliance_score']}%  (Grade: {s['grade']})")
    lines.append(f"  Checks: {s['passed']} passed / {s['failed']} failed / {s['total_checks']} total")

    lines.append(f"\n  SEVERITY DISTRIBUTION")
    for label, count in s["severity_distribution"].items():
        bar = "#" * (count * 3)
        lines.append(f"    {label:<12} {count:>3} {bar}")

    if report["top_priorities"]:
        lines.append(f"\n  TOP PRIORITIES (fix first)")
        lines.append("  " + "-" * 50)
        for i, issue in enumerate(report["top_priorities"], 1):
            lines.append(f"  {i}. [{issue['severity_label'].upper()}] {issue['checkpoint']}")
            lines.append(f"     Heuristic: {issue['heuristic_id']} - {issue['heuristic_name']}")
            lines.append(f"     Action: {issue['action']}")
            if issue["notes"]:
                lines.append(f"     Notes: {issue['notes']}")

    if report["strengths"]:
        lines.append(f"\n  STRENGTHS")
        lines.append("  " + "-" * 50)
        for strength in report["strengths"]:
            lines.append(f"    + {strength['checkpoint']}")

    if report["issues"]:
        lines.append(f"\n  ALL ISSUES ({len(report['issues'])} total)")
        lines.append("  " + "-" * 50)
        for issue in report["issues"]:
            lines.append(f"    [{issue['severity_label']:<9}] {issue['checkpoint']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate design critique based on usability heuristics and accessibility standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate empty checklist
  python design_critique.py --checklist

  # Export checklist as JSON to fill in
  python design_critique.py --checklist --json > checklist.json

  # Analyze completed checklist
  python design_critique.py --answers completed_checklist.json

  # JSON report
  python design_critique.py --answers completed_checklist.json --json
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--checklist", action="store_true", help="Generate empty checklist for evaluation")
    group.add_argument("--answers", help="Path to completed checklist JSON file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.checklist:
        checklist = generate_checklist()
        if args.json:
            print(json.dumps(checklist, indent=2))
        else:
            print(format_checklist_output(checklist))
    else:
        with open(args.answers, "r") as f:
            answers = json.load(f)

        report = analyze_answers(answers)

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(format_report_output(report))


if __name__ == "__main__":
    main()

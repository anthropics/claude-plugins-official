#!/usr/bin/env python3
"""
Landing Page CTA Analyzer

Analyzes CTA placement, copy strength, friction level,
and conversion optimization on landing pages.

Usage:
    python cta_analyzer.py page.html
    python cta_analyzer.py page.html --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

BUTTON_PATTERN = re.compile(r'<(button|a)[^>]*(?:class\s*=\s*"[^"]*(?:btn|button|cta)[^"]*"|role\s*=\s*"button")[^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
LINK_CTA_PATTERN = re.compile(r'<a[^>]+href[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
HTML_TAG = re.compile(r"<[^>]+>")

STRONG_VERBS = {"start", "get", "create", "build", "try", "claim", "unlock", "discover", "join", "book", "download", "access"}
WEAK_VERBS = {"submit", "click", "send", "go", "enter", "continue"}
FRICTION_REDUCERS = ["no credit card", "free", "cancel anytime", "no commitment", "money-back", "risk-free", "2 minutes", "instant"]


def extract_ctas(html: str) -> list:
    ctas = []

    # Find buttons
    for match in BUTTON_PATTERN.finditer(html):
        text = HTML_TAG.sub("", match.group(2)).strip()
        if text and len(text) < 60:
            pos = match.start()
            ctas.append({"text": text, "position_char": pos, "type": "button"})

    # Find links that look like CTAs
    for match in LINK_CTA_PATTERN.finditer(html):
        text = HTML_TAG.sub("", match.group(1)).strip()
        tag = match.group(0).lower()
        if text and len(text) < 60 and any(kw in tag for kw in ["btn", "button", "cta", "trial", "demo", "signup", "start"]):
            pos = match.start()
            ctas.append({"text": text, "position_char": pos, "type": "link"})

    return ctas


def analyze_cta(cta_text: str) -> dict:
    lower = cta_text.lower()
    words = lower.split()
    first_word = words[0] if words else ""

    strength = "moderate"
    if first_word in STRONG_VERBS:
        strength = "strong"
    elif first_word in WEAK_VERBS:
        strength = "weak"

    has_ownership = any(w in words for w in ["my", "your"])
    has_benefit = len(words) > 2

    score = 50
    if strength == "strong":
        score += 25
    elif strength == "weak":
        score -= 15
    if has_ownership:
        score += 10
    if has_benefit:
        score += 15

    return {
        "text": cta_text,
        "strength": strength,
        "has_ownership_language": has_ownership,
        "describes_what_you_get": has_benefit,
        "word_count": len(words),
        "score": min(100, max(0, score)),
    }


def analyze_page(html: str) -> dict:
    html_length = len(html)
    ctas = extract_ctas(html)

    # Check for friction reducers near CTAs
    lower_html = html.lower()
    friction_found = [f for f in FRICTION_REDUCERS if f in lower_html]

    # Estimate CTA positions (early = above fold, middle, late)
    cta_analyses = []
    for cta in ctas:
        position_pct = (cta["position_char"] / html_length * 100) if html_length > 0 else 0
        zone = "above_fold" if position_pct < 20 else "mid_page" if position_pct < 60 else "bottom"
        analysis = analyze_cta(cta["text"])
        analysis["zone"] = zone
        analysis["position_pct"] = round(position_pct, 1)
        cta_analyses.append(analysis)

    # Scoring
    issues = []
    recommendations = []
    score = 50

    # CTA count
    if len(ctas) == 0:
        issues.append("No CTAs found on the page.")
        score -= 30
    elif len(ctas) == 1:
        issues.append("Only 1 CTA. Best practice: 2-3 CTAs throughout the page.")
        score -= 10
    elif 2 <= len(ctas) <= 4:
        score += 15
    else:
        recommendations.append(f"{len(ctas)} CTAs found -- ensure they don't compete. All should drive the same action.")

    # Above fold CTA
    above_fold = [c for c in cta_analyses if c["zone"] == "above_fold"]
    if above_fold:
        score += 15
    else:
        issues.append("No CTA above the fold. Primary CTA must be visible without scrolling.")
        score -= 15

    # CTA consistency
    cta_texts = [c["text"].lower() for c in cta_analyses]
    unique_texts = set(cta_texts)
    if len(unique_texts) > 2 and len(ctas) > 1:
        issues.append(f"{len(unique_texts)} different CTA texts. Use consistent CTAs driving one action.")
        score -= 10

    # Friction reducers
    if friction_found:
        score += 10
        recommendations.append(f"Good: Friction reducers detected: {', '.join(friction_found)}")
    else:
        recommendations.append("Add friction reducers near CTAs: 'No credit card required', 'Free for 14 days', etc.")
        score -= 5

    # CTA strength
    strong_ctas = [c for c in cta_analyses if c["strength"] == "strong"]
    weak_ctas = [c for c in cta_analyses if c["strength"] == "weak"]
    if weak_ctas:
        recommendations.append(f"Strengthen weak CTAs: {', '.join([c['text'] for c in weak_ctas][:3])}")

    score = max(0, min(100, score))

    return {
        "total_ctas": len(ctas),
        "score": score,
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F",
        "ctas": cta_analyses,
        "friction_reducers_found": friction_found,
        "placement": {
            "above_fold": len(above_fold),
            "mid_page": len([c for c in cta_analyses if c["zone"] == "mid_page"]),
            "bottom": len([c for c in cta_analyses if c["zone"] == "bottom"]),
        },
        "issues": issues,
        "recommendations": recommendations,
    }


def format_human(result: dict) -> str:
    lines = ["\n" + "=" * 55, "  LANDING PAGE CTA ANALYZER", "=" * 55]
    lines.append(f"\n  Score: {result['score']}/100 ({result['grade']}) | CTAs Found: {result['total_ctas']}")
    p = result["placement"]
    lines.append(f"  Placement: Above-fold: {p['above_fold']} | Mid-page: {p['mid_page']} | Bottom: {p['bottom']}")

    if result["ctas"]:
        lines.append(f"\n  CTA Analysis:")
        for c in result["ctas"]:
            lines.append(f"    \"{c['text']}\" | {c['strength']} | {c['zone']} ({c['position_pct']}%) | Score: {c['score']}")

    if result["issues"]:
        lines.append(f"\n  Issues:")
        for i in result["issues"]:
            lines.append(f"    ! {i}")

    lines.append(f"\n  Recommendations:")
    for r in result["recommendations"]:
        lines.append(f"    > {r}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze CTA placement and quality on landing pages.")
    parser.add_argument("file", help="HTML file")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        html = Path(args.file).read_text()
    except FileNotFoundError:
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    result = analyze_page(html)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))


if __name__ == "__main__":
    main()

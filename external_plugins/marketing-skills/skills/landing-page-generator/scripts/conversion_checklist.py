#!/usr/bin/env python3
"""
Landing Page Conversion Checklist

Runs a comprehensive conversion optimization audit on
landing page HTML against 2025-2026 best practices.

Usage:
    python conversion_checklist.py page.html
    python conversion_checklist.py page.html --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

HTML_TAG = re.compile(r"<[^>]+>")


def audit_page(html: str) -> dict:
    lower = html.lower()
    plain = HTML_TAG.sub(" ", html)
    plain = re.sub(r"\s+", " ", plain).strip()

    checks = []
    score = 0
    max_score = 0

    def check(name, condition, points, fail_msg):
        nonlocal score, max_score
        max_score += points
        if condition:
            score += points
            checks.append({"name": name, "status": "PASS", "points": points})
        else:
            checks.append({"name": name, "status": "FAIL", "points": 0, "max_points": points, "fix": fail_msg})

    # Above the Fold
    check("H1 Tag Present", bool(re.search(r"<h1", lower)), 10, "Add a clear H1 headline")
    check("Single H1", len(re.findall(r"<h1", lower)) <= 1, 5, "Use only one H1 per page")
    check("CTA Button Present", bool(re.search(r"(btn|button|cta)", lower)), 10, "Add a prominent CTA button")
    check("Subheadline Present", bool(re.search(r"<(h2|p class[^>]*sub)", lower)), 5, "Add a subheadline under H1")

    # Navigation
    has_nav = bool(re.search(r"<nav|<header[^>]*>.*<a", lower, re.DOTALL))
    nav_link_count = len(re.findall(r"<nav.*?</nav>", lower, re.DOTALL))
    check("Minimal Navigation", not has_nav or nav_link_count <= 1, 8, "Remove navigation -- landing pages should have no exit paths")

    # Social Proof
    check("Customer Logos", bool(re.search(r"(logo|customer|trusted.by|used.by|brand)", lower)), 8, "Add customer logos or 'Trusted by' section")
    check("Testimonials", bool(re.search(r'(testimonial|review|".*".*[-—])', lower)), 8, "Add named testimonials with specific outcomes")
    check("Numbers/Metrics", bool(re.search(r"\d+\s*(team|compan|customer|user|client)", plain, re.IGNORECASE)), 5, "Add specific customer counts or metrics")

    # Trust & Credibility
    check("Security Badges", bool(re.search(r"(soc.2|gdpr|iso|secure|encrypted|ssl|badge)", lower)), 5, "Add security badges if relevant")
    check("Privacy Policy Link", bool(re.search(r"privacy", lower)), 3, "Link to privacy policy near forms")

    # CTA Optimization
    cta_count = len(re.findall(r"(btn|button|cta)", lower))
    check("Multiple CTAs", cta_count >= 2, 8, "Place CTAs at hero, mid-page, and bottom")
    check("Risk Reversal Near CTA", bool(re.search(r"(no credit card|cancel anytime|free trial|money.back|risk.free|guarantee)", lower)), 8, "Add risk reversal text near CTAs")

    # Objection Handling
    check("FAQ Section", bool(re.search(r"(faq|frequently|common question)", lower)), 5, "Add FAQ section to handle buying objections")
    check("How It Works", bool(re.search(r"(how it works|step \d|3 steps|getting started)", lower)), 5, "Add 'How It Works' section (3-4 steps)")

    # Mobile & Performance
    check("Viewport Meta", bool(re.search(r'name\s*=\s*"viewport"', lower)), 5, "Add viewport meta tag for mobile")
    check("Mobile-Friendly", bool(re.search(r"(responsive|mobile|@media)", lower)), 3, "Add responsive CSS/media queries")

    images = re.findall(r"<img[^>]*>", html, re.IGNORECASE)
    images_with_alt = len(re.findall(r'<img[^>]+alt\s*=\s*"[^"]+', html, re.IGNORECASE))
    check("Image Alt Text", not images or images_with_alt >= len(images) * 0.8, 3, "Add alt text to all images")

    # SEO
    check("Title Tag", bool(re.search(r"<title[^>]*>.+</title>", lower)), 3, "Add a title tag with primary keyword")
    check("Meta Description", bool(re.search(r'name\s*=\s*"description"', lower)), 3, "Add meta description with benefit + CTA")
    check("OG Image", bool(re.search(r'property\s*=\s*"og:image"', lower)), 2, "Add Open Graph image for social sharing")

    # Content Quality
    word_count = len(plain.split())
    check("Adequate Content", word_count >= 200, 3, "Page has very little content. Add more copy.")
    check("Not Too Long", word_count <= 3000, 2, "Page is extremely long. Consider trimming.")

    # Form optimization (if form exists)
    has_form = bool(re.search(r"<form", lower))
    if has_form:
        inputs = re.findall(r"<input[^>]+type\s*=\s*\"(?!hidden|submit|button)", lower)
        check("Form Fields < 5", len(inputs) <= 5, 5, f"Form has {len(inputs)} fields. Reduce to minimum required.")

    pct = round(score / max(max_score, 1) * 100)

    return {
        "score": pct,
        "points": f"{score}/{max_score}",
        "grade": "A" if pct >= 85 else "B" if pct >= 70 else "C" if pct >= 55 else "D" if pct >= 40 else "F",
        "checks": checks,
        "passed": sum(1 for c in checks if c["status"] == "PASS"),
        "failed": sum(1 for c in checks if c["status"] == "FAIL"),
        "total_checks": len(checks),
        "quick_wins": [c["fix"] for c in checks if c["status"] == "FAIL" and c.get("max_points", 0) >= 5][:5],
        "benchmarks": {
            "median_conversion_rate": "6.6% (all industries, 2025 data)",
            "top_10_pct": ">10% conversion rate",
            "page_load_target": "<3 seconds on mobile",
            "note": "Every second of load time reduces conversion by ~7%",
        },
    }


def format_human(result: dict) -> str:
    lines = ["\n" + "=" * 60, "  LANDING PAGE CONVERSION CHECKLIST", "=" * 60]
    lines.append(f"\n  Score: {result['score']}% ({result['grade']}) | {result['passed']}/{result['total_checks']} checks passed")

    lines.append(f"\n  Checklist:")
    for c in result["checks"]:
        icon = "+" if c["status"] == "PASS" else "X"
        fix = f" -- {c.get('fix', '')}" if c["status"] == "FAIL" else ""
        lines.append(f"    [{icon}] {c['name']}{fix}")

    if result["quick_wins"]:
        lines.append(f"\n  Top Quick Wins:")
        for i, qw in enumerate(result["quick_wins"], 1):
            lines.append(f"    {i}. {qw}")

    b = result["benchmarks"]
    lines.append(f"\n  Benchmarks (2025-2026):")
    lines.append(f"    Median conversion: {b['median_conversion_rate']}")
    lines.append(f"    Top performers: {b['top_10_pct']}")
    lines.append(f"    Load target: {b['page_load_target']}")
    lines.append(f"    Note: {b['note']}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run conversion optimization checklist on landing page.")
    parser.add_argument("file", help="HTML file to audit")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        html = Path(args.file).read_text()
    except FileNotFoundError:
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    result = audit_page(html)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Landing Page Speed Estimator

Estimates page load performance from HTML source, checking
against Core Web Vitals targets and conversion benchmarks.

Usage:
    python page_speed_estimator.py page.html
    python page_speed_estimator.py page.html --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

CWV_TARGETS = {
    "lcp": {"good": 2.5, "needs_improvement": 4.0, "unit": "seconds"},
    "cls": {"good": 0.1, "needs_improvement": 0.25, "unit": "score"},
    "fid": {"good": 100, "needs_improvement": 300, "unit": "ms"},
    "ttfb": {"good": 600, "needs_improvement": 1200, "unit": "ms"},
}


def estimate_speed(html: str) -> dict:
    size_bytes = len(html.encode("utf-8"))
    size_kb = size_bytes / 1024

    # Count resources
    scripts = re.findall(r"<script[^>]*(?:src|>)", html, re.IGNORECASE)
    external_scripts = [s for s in scripts if 'src=' in s.lower()]
    inline_scripts = [s for s in scripts if 'src=' not in s.lower()]
    stylesheets = re.findall(r'<link[^>]+rel\s*=\s*"stylesheet"', html, re.IGNORECASE)
    images = re.findall(r"<img[^>]+>", html, re.IGNORECASE)
    videos = re.findall(r"<video[^>]+>", html, re.IGNORECASE)
    iframes = re.findall(r"<iframe[^>]+>", html, re.IGNORECASE)
    fonts = re.findall(r"font-family|@font-face|fonts\.googleapis", html, re.IGNORECASE)

    # Check for optimization patterns
    has_lazy_loading = bool(re.search(r'loading\s*=\s*"lazy"', html, re.IGNORECASE))
    has_async_scripts = bool(re.search(r'<script[^>]+async', html, re.IGNORECASE))
    has_defer_scripts = bool(re.search(r'<script[^>]+defer', html, re.IGNORECASE))
    has_preload = bool(re.search(r'rel\s*=\s*"preload"', html, re.IGNORECASE))
    has_webp_avif = bool(re.search(r'\.(webp|avif)', html, re.IGNORECASE))
    has_srcset = bool(re.search(r'srcset\s*=', html, re.IGNORECASE))
    has_viewport = bool(re.search(r'name\s*=\s*"viewport"', html, re.IGNORECASE))
    images_with_dims = len(re.findall(r'<img[^>]+width[^>]+height', html, re.IGNORECASE))

    # Estimate LCP (rough)
    lcp_estimate = 1.0  # base
    lcp_estimate += size_kb / 200  # page size impact
    lcp_estimate += len(external_scripts) * 0.15  # render blocking
    lcp_estimate += len(stylesheets) * 0.1
    lcp_estimate += len(images) * 0.08
    if not has_async_scripts and not has_defer_scripts and external_scripts:
        lcp_estimate += 0.5
    if not has_webp_avif and images:
        lcp_estimate += 0.3
    if has_preload:
        lcp_estimate -= 0.2

    # CLS risk
    cls_risk = 0.0
    images_without_dims = len(images) - images_with_dims
    cls_risk += images_without_dims * 0.03
    if iframes:
        cls_risk += len(iframes) * 0.05
    if not has_viewport:
        cls_risk += 0.1

    # Build report
    checks = []

    # Page weight
    if size_kb < 500:
        checks.append({"name": "Page Weight", "status": "PASS", "detail": f"{size_kb:.0f}KB (target: <1MB)"})
    elif size_kb < 1024:
        checks.append({"name": "Page Weight", "status": "WARN", "detail": f"{size_kb:.0f}KB"})
    else:
        checks.append({"name": "Page Weight", "status": "FAIL", "detail": f"{size_kb:.0f}KB (>1MB)"})

    # Scripts
    if len(external_scripts) <= 3:
        checks.append({"name": "External Scripts", "status": "PASS", "detail": f"{len(external_scripts)} scripts"})
    else:
        checks.append({"name": "External Scripts", "status": "WARN", "detail": f"{len(external_scripts)} scripts -- reduce render-blocking JS"})

    if external_scripts and (has_async_scripts or has_defer_scripts):
        checks.append({"name": "Script Loading", "status": "PASS", "detail": "async/defer detected"})
    elif external_scripts:
        checks.append({"name": "Script Loading", "status": "WARN", "detail": "No async/defer on scripts"})

    # Images
    if images and has_lazy_loading:
        checks.append({"name": "Lazy Loading", "status": "PASS", "detail": "Lazy loading detected"})
    elif images:
        checks.append({"name": "Lazy Loading", "status": "WARN", "detail": "No lazy loading on images"})

    if images and has_webp_avif:
        checks.append({"name": "Modern Image Formats", "status": "PASS", "detail": "WebP/AVIF detected"})
    elif images:
        checks.append({"name": "Modern Image Formats", "status": "WARN", "detail": "Use WebP/AVIF for 25-50% size reduction"})

    if images_without_dims > 0:
        checks.append({"name": "Image Dimensions", "status": "WARN", "detail": f"{images_without_dims} images missing width/height (causes CLS)"})

    # CWV estimates
    lcp_status = "PASS" if lcp_estimate <= CWV_TARGETS["lcp"]["good"] else "WARN" if lcp_estimate <= CWV_TARGETS["lcp"]["needs_improvement"] else "FAIL"
    cls_status = "PASS" if cls_risk <= CWV_TARGETS["cls"]["good"] else "WARN" if cls_risk <= CWV_TARGETS["cls"]["needs_improvement"] else "FAIL"

    checks.append({"name": "Est. LCP", "status": lcp_status, "detail": f"~{lcp_estimate:.1f}s (target: <2.5s)"})
    checks.append({"name": "Est. CLS Risk", "status": cls_status, "detail": f"~{cls_risk:.2f} (target: <0.1)"})

    # Conversion impact
    conversion_impact = []
    if lcp_estimate > 3:
        lost_pct = round((lcp_estimate - 1) * 7)
        conversion_impact.append(f"~{lost_pct}% potential conversion loss from slow load time")
    if not has_viewport:
        conversion_impact.append("Missing viewport meta -- mobile users will have poor experience")

    recs = []
    if not has_async_scripts and external_scripts:
        recs.append("Add async or defer to non-critical scripts.")
    if not has_lazy_loading and images:
        recs.append("Add loading='lazy' to below-fold images.")
    if not has_webp_avif and images:
        recs.append("Convert images to WebP/AVIF format (25-50% smaller).")
    if images_without_dims > 0:
        recs.append("Add explicit width and height to all images to prevent CLS.")
    if not has_preload:
        recs.append("Add rel='preload' for critical resources (hero image, main font).")
    if size_kb > 1024:
        recs.append("Reduce page weight below 1MB. Compress images and minify CSS/JS.")

    if not recs:
        recs.append("Page looks well-optimized. Monitor CWV in Google Search Console for real-user data.")

    # Score
    score = 100
    for c in checks:
        if c["status"] == "WARN":
            score -= 8
        elif c["status"] == "FAIL":
            score -= 15
    score = max(0, min(100, score))

    return {
        "page_size_kb": round(size_kb, 1),
        "score": score,
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F",
        "resource_counts": {
            "external_scripts": len(external_scripts),
            "inline_scripts": len(inline_scripts),
            "stylesheets": len(stylesheets),
            "images": len(images),
            "videos": len(videos),
            "iframes": len(iframes),
            "fonts": len(fonts),
        },
        "cwv_estimates": {
            "lcp_seconds": round(lcp_estimate, 1),
            "cls_risk": round(cls_risk, 2),
        },
        "checks": checks,
        "conversion_impact": conversion_impact,
        "recommendations": recs,
    }


def format_human(result: dict) -> str:
    lines = ["\n" + "=" * 55, "  LANDING PAGE SPEED ESTIMATOR", "=" * 55]
    lines.append(f"\n  Score: {result['score']}/100 ({result['grade']}) | Size: {result['page_size_kb']}KB")
    r = result["resource_counts"]
    lines.append(f"  Scripts: {r['external_scripts']}ext/{r['inline_scripts']}inline | CSS: {r['stylesheets']} | Images: {r['images']}")

    cwv = result["cwv_estimates"]
    lines.append(f"\n  Core Web Vitals Estimates:")
    lines.append(f"    LCP: ~{cwv['lcp_seconds']}s (target: <2.5s)")
    lines.append(f"    CLS Risk: ~{cwv['cls_risk']} (target: <0.1)")

    lines.append(f"\n  Checks:")
    for c in result["checks"]:
        icon = {"PASS": "+", "WARN": "!", "FAIL": "X"}
        lines.append(f"    [{icon.get(c['status'], '?')}] {c['name']}: {c['detail']}")

    if result["conversion_impact"]:
        lines.append(f"\n  Conversion Impact:")
        for ci in result["conversion_impact"]:
            lines.append(f"    !! {ci}")

    lines.append(f"\n  Recommendations:")
    for rec in result["recommendations"]:
        lines.append(f"    > {rec}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Estimate landing page speed and Core Web Vitals.")
    parser.add_argument("file", help="HTML file to analyze")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        html = Path(args.file).read_text()
    except FileNotFoundError:
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    result = estimate_speed(html)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))


if __name__ == "__main__":
    main()

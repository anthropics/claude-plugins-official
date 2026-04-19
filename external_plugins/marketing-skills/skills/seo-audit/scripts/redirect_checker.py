#!/usr/bin/env python3
"""
Redirect Chain Checker

Checks URLs for redirect chains, status codes, and common redirect issues.
Identifies chains longer than 2 hops, mixed HTTP/HTTPS redirects, redirect
loops, and temporary (302) redirects that should be permanent (301).

Usage:
    python redirect_checker.py --url https://example.com/old-page
    python redirect_checker.py --file urls.txt --json
    python redirect_checker.py --url https://example.com/page --max-hops 10
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urljoin
try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


def normalize_url(url):
    """Ensure URL has a scheme."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')


def simulate_redirect_check(url, max_hops=10):
    """
    Check a URL for redirect chains.

    Uses urllib to follow redirects manually, recording each hop.
    Falls back to simulation if network is unavailable.
    """
    url = normalize_url(url)
    chain = []
    visited = set()
    current_url = url
    issues = []

    if HAS_URLLIB:
        for hop in range(max_hops + 1):
            if current_url in visited:
                issues.append({
                    "type": "redirect_loop",
                    "severity": "Critical",
                    "detail": f"Redirect loop detected at {current_url}",
                })
                break
            visited.add(current_url)

            try:
                req = Request(current_url, method='HEAD')
                req.add_header('User-Agent', 'SEO-Audit-Bot/1.0')

                import http.client
                # Use lower-level to avoid auto-redirect
                parsed = urlparse(current_url)
                if parsed.scheme == 'https':
                    import ssl
                    ctx = ssl.create_default_context()
                    conn = http.client.HTTPSConnection(parsed.netloc, timeout=10, context=ctx)
                else:
                    conn = http.client.HTTPConnection(parsed.netloc, timeout=10)

                path = parsed.path or '/'
                if parsed.query:
                    path += '?' + parsed.query

                conn.request('HEAD', path, headers={'User-Agent': 'SEO-Audit-Bot/1.0'})
                resp = conn.getresponse()
                status = resp.status

                chain.append({
                    "hop": hop + 1,
                    "url": current_url,
                    "status": status,
                })

                if status in (301, 302, 303, 307, 308):
                    location = resp.getheader('Location', '')
                    if location:
                        # Handle relative redirects
                        next_url = urljoin(current_url, location)

                        # Check for HTTP to HTTPS or vice versa
                        if urlparse(current_url).scheme != urlparse(next_url).scheme:
                            issues.append({
                                "type": "scheme_change",
                                "severity": "Medium",
                                "detail": f"Scheme change: {urlparse(current_url).scheme} -> {urlparse(next_url).scheme} at hop {hop + 1}",
                            })

                        # Flag 302 that should be 301
                        if status == 302:
                            issues.append({
                                "type": "temporary_redirect",
                                "severity": "High",
                                "detail": f"302 temporary redirect at hop {hop + 1} — should this be 301 permanent?",
                            })

                        current_url = next_url
                    else:
                        issues.append({
                            "type": "missing_location",
                            "severity": "Critical",
                            "detail": f"Redirect status {status} but no Location header at hop {hop + 1}",
                        })
                        break
                else:
                    # Final destination reached
                    break

                conn.close()

            except Exception as e:
                chain.append({
                    "hop": hop + 1,
                    "url": current_url,
                    "status": "error",
                    "error": str(e),
                })
                issues.append({
                    "type": "connection_error",
                    "severity": "Critical",
                    "detail": f"Connection error at hop {hop + 1}: {str(e)}",
                })
                break
    else:
        # Simulation mode when no network available
        chain.append({
            "hop": 1,
            "url": current_url,
            "status": "simulated",
            "note": "Network check unavailable — install urllib for live checks",
        })

    # Analyze chain
    hop_count = len(chain)
    if hop_count > 3:
        issues.append({
            "type": "long_chain",
            "severity": "High",
            "detail": f"Redirect chain has {hop_count} hops — should be 2 or fewer",
        })

    final_url = chain[-1]["url"] if chain else url
    final_status = chain[-1].get("status", "unknown") if chain else "unknown"

    return {
        "original_url": url,
        "final_url": final_url,
        "final_status": final_status,
        "total_hops": max(hop_count - 1, 0),
        "chain": chain,
        "issues": issues,
        "passed": len(issues) == 0,
    }


def check_url_patterns(url):
    """Check URL for common SEO issues without making requests."""
    issues = []
    parsed = urlparse(url)

    # Check for HTTP (should be HTTPS)
    if parsed.scheme == 'http':
        issues.append({
            "type": "no_https",
            "severity": "High",
            "detail": "URL uses HTTP instead of HTTPS",
        })

    # Check for trailing slash inconsistency
    if parsed.path and parsed.path != '/' and not parsed.path.endswith('/'):
        issues.append({
            "type": "trailing_slash",
            "severity": "Low",
            "detail": "No trailing slash — verify consistency with canonical URL",
        })

    # Check for URL parameters
    if parsed.query:
        issues.append({
            "type": "url_parameters",
            "severity": "Medium",
            "detail": f"URL contains parameters: {parsed.query} — verify canonical handling",
        })

    # Check for uppercase in path
    if parsed.path != parsed.path.lower():
        issues.append({
            "type": "uppercase_url",
            "severity": "Medium",
            "detail": "URL path contains uppercase characters — may cause duplicate content",
        })

    # Check path depth
    depth = len([s for s in parsed.path.split('/') if s])
    if depth > 4:
        issues.append({
            "type": "deep_url",
            "severity": "Medium",
            "detail": f"URL depth is {depth} levels — consider flattening for crawl efficiency",
        })

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Check URLs for redirect chains and SEO issues"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single URL to check")
    group.add_argument("--file", help="File with one URL per line")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--max-hops", type=int, default=10,
        help="Maximum redirect hops to follow (default: 10)"
    )
    parser.add_argument(
        "--patterns-only", action="store_true",
        help="Only check URL patterns without making network requests"
    )
    args = parser.parse_args()

    urls = []
    if args.url:
        urls = [args.url]
    else:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        urls = [line.strip() for line in filepath.read_text().splitlines() if line.strip()]

    results = []
    for url in urls:
        if args.patterns_only:
            pattern_issues = check_url_patterns(normalize_url(url))
            results.append({
                "url": url,
                "pattern_issues": pattern_issues,
                "passed": len(pattern_issues) == 0,
            })
        else:
            result = simulate_redirect_check(url, args.max_hops)
            result["pattern_issues"] = check_url_patterns(normalize_url(url))
            results.append(result)

    if args.json:
        print(json.dumps({"urls_checked": len(results), "results": results}, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  REDIRECT CHECK — {len(results)} URL(s)")
        print(f"{'='*60}")

        for r in results:
            url = r.get("original_url", r.get("url", ""))
            print(f"\n  URL: {url}")

            if "chain" in r:
                print(f"  Final URL: {r['final_url']}")
                print(f"  Total hops: {r['total_hops']}")
                print(f"  Final status: {r['final_status']}")

                if r["chain"]:
                    print(f"  Chain:")
                    for hop in r["chain"]:
                        print(f"    Hop {hop['hop']}: [{hop['status']}] {hop['url']}")

            all_issues = r.get("issues", []) + r.get("pattern_issues", [])
            if all_issues:
                print(f"  Issues ({len(all_issues)}):")
                for issue in all_issues:
                    print(f"    [{issue['severity']}] {issue['type']}: {issue['detail']}")
            else:
                print(f"  Status: PASSED — no issues found")

        passed = sum(1 for r in results if r.get("passed", False))
        print(f"\n  Summary: {passed}/{len(results)} URLs passed")
        print()


if __name__ == "__main__":
    main()

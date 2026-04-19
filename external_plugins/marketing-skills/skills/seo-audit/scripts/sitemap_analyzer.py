#!/usr/bin/env python3
"""
XML Sitemap Analyzer

Analyzes XML sitemaps for SEO issues including missing URLs, invalid entries,
stale lastmod dates, priority misconfigurations, and size violations.
Supports both sitemap index files and individual sitemaps.

Usage:
    python sitemap_analyzer.py --sitemap https://example.com/sitemap.xml
    python sitemap_analyzer.py --file sitemap.xml --json
    python sitemap_analyzer.py --file sitemap.xml --check-urls
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False


SITEMAP_NS = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1',
}

MAX_URLS_PER_SITEMAP = 50000
MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB uncompressed


def parse_sitemap_xml(content):
    """Parse sitemap XML content and extract URLs."""
    if not HAS_XML:
        return [], [], "XML parser not available"

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return [], [], f"XML parse error: {str(e)}"

    tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag

    urls = []
    sub_sitemaps = []

    if tag == 'sitemapindex':
        # Sitemap index file
        for sitemap in root.findall('.//sm:sitemap', SITEMAP_NS):
            loc = sitemap.find('sm:loc', SITEMAP_NS)
            lastmod = sitemap.find('sm:lastmod', SITEMAP_NS)
            if loc is not None and loc.text:
                sub_sitemaps.append({
                    "url": loc.text.strip(),
                    "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else None,
                })
        # Also try without namespace
        if not sub_sitemaps:
            for sitemap in root.findall('.//sitemap'):
                loc = sitemap.find('loc')
                lastmod = sitemap.find('lastmod')
                if loc is not None and loc.text:
                    sub_sitemaps.append({
                        "url": loc.text.strip(),
                        "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else None,
                    })

    elif tag == 'urlset':
        # Regular sitemap
        for url_elem in root.findall('.//sm:url', SITEMAP_NS):
            entry = {}
            loc = url_elem.find('sm:loc', SITEMAP_NS)
            lastmod = url_elem.find('sm:lastmod', SITEMAP_NS)
            changefreq = url_elem.find('sm:changefreq', SITEMAP_NS)
            priority = url_elem.find('sm:priority', SITEMAP_NS)

            if loc is not None and loc.text:
                entry["url"] = loc.text.strip()
                entry["lastmod"] = lastmod.text.strip() if lastmod is not None and lastmod.text else None
                entry["changefreq"] = changefreq.text.strip() if changefreq is not None and changefreq.text else None
                entry["priority"] = priority.text.strip() if priority is not None and priority.text else None
                urls.append(entry)

        # Also try without namespace
        if not urls:
            for url_elem in root.findall('.//url'):
                entry = {}
                loc = url_elem.find('loc')
                lastmod = url_elem.find('lastmod')
                changefreq = url_elem.find('changefreq')
                priority = url_elem.find('priority')

                if loc is not None and loc.text:
                    entry["url"] = loc.text.strip()
                    entry["lastmod"] = lastmod.text.strip() if lastmod is not None and lastmod.text else None
                    entry["changefreq"] = changefreq.text.strip() if changefreq is not None and changefreq.text else None
                    entry["priority"] = priority.text.strip() if priority is not None and priority.text else None
                    urls.append(entry)

    return urls, sub_sitemaps, None


def parse_date(date_str):
    """Parse various date formats."""
    if not date_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    # Handle timezone offset without colon
    date_str = re.sub(r'(\+\d{2}):(\d{2})$', r'\1\2', date_str)
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def analyze_urls(urls, content_size=None):
    """Analyze sitemap URLs for issues."""
    issues = []
    stats = {
        "total_urls": len(urls),
        "with_lastmod": 0,
        "with_changefreq": 0,
        "with_priority": 0,
        "stale_urls": 0,
        "duplicate_urls": 0,
        "domains": set(),
    }

    seen_urls = set()
    now = datetime.now()
    stale_threshold = now - timedelta(days=365)

    valid_changefreqs = {'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'}
    stale_urls = []

    for entry in urls:
        url = entry.get("url", "")
        parsed = urlparse(url)
        stats["domains"].add(parsed.netloc)

        # Check for duplicates
        normalized = url.rstrip('/')
        if normalized in seen_urls:
            stats["duplicate_urls"] += 1
            issues.append({
                "type": "duplicate_url",
                "severity": "Medium",
                "url": url,
                "detail": "Duplicate URL in sitemap",
            })
        seen_urls.add(normalized)

        # Check lastmod
        if entry.get("lastmod"):
            stats["with_lastmod"] += 1
            parsed_date = parse_date(entry["lastmod"])
            if parsed_date:
                if parsed_date.replace(tzinfo=None) < stale_threshold:
                    stats["stale_urls"] += 1
                    stale_urls.append(url)
            else:
                issues.append({
                    "type": "invalid_lastmod",
                    "severity": "Low",
                    "url": url,
                    "detail": f"Invalid date format: {entry['lastmod']}",
                })

        # Check changefreq
        if entry.get("changefreq"):
            stats["with_changefreq"] += 1
            if entry["changefreq"].lower() not in valid_changefreqs:
                issues.append({
                    "type": "invalid_changefreq",
                    "severity": "Low",
                    "url": url,
                    "detail": f"Invalid changefreq: {entry['changefreq']}",
                })

        # Check priority
        if entry.get("priority"):
            stats["with_priority"] += 1
            try:
                pval = float(entry["priority"])
                if pval < 0 or pval > 1:
                    issues.append({
                        "type": "invalid_priority",
                        "severity": "Low",
                        "url": url,
                        "detail": f"Priority out of range: {entry['priority']}",
                    })
            except ValueError:
                issues.append({
                    "type": "invalid_priority",
                    "severity": "Low",
                    "url": url,
                    "detail": f"Non-numeric priority: {entry['priority']}",
                })

        # Check URL format
        if not url.startswith(('http://', 'https://')):
            issues.append({
                "type": "invalid_url",
                "severity": "High",
                "url": url,
                "detail": "URL missing scheme (http/https)",
            })

        # Check for URL parameters (potential duplicates)
        if parsed.query:
            issues.append({
                "type": "parameterized_url",
                "severity": "Medium",
                "url": url,
                "detail": "URL contains query parameters — verify canonical handling",
            })

    # Size checks
    if len(urls) > MAX_URLS_PER_SITEMAP:
        issues.append({
            "type": "too_many_urls",
            "severity": "Critical",
            "detail": f"Sitemap contains {len(urls)} URLs — max is {MAX_URLS_PER_SITEMAP}",
        })

    if content_size and content_size > MAX_SIZE_BYTES:
        issues.append({
            "type": "file_too_large",
            "severity": "Critical",
            "detail": f"Sitemap is {content_size / 1024 / 1024:.1f}MB — max is 50MB",
        })

    # Coverage checks
    if stats["with_lastmod"] == 0 and len(urls) > 0:
        issues.append({
            "type": "no_lastmod",
            "severity": "Medium",
            "detail": "No URLs have lastmod dates — Google uses this for crawl prioritization",
        })
    elif stats["with_lastmod"] < len(urls):
        issues.append({
            "type": "partial_lastmod",
            "severity": "Low",
            "detail": f"Only {stats['with_lastmod']}/{len(urls)} URLs have lastmod dates",
        })

    if stats["stale_urls"] > 0:
        issues.append({
            "type": "stale_content",
            "severity": "Medium",
            "detail": f"{stats['stale_urls']} URLs have lastmod dates older than 1 year",
        })

    # Multiple domains check
    if len(stats["domains"]) > 1:
        issues.append({
            "type": "multiple_domains",
            "severity": "High",
            "detail": f"Sitemap contains URLs from {len(stats['domains'])} different domains",
        })

    stats["domains"] = list(stats["domains"])
    return stats, issues, stale_urls


def main():
    parser = argparse.ArgumentParser(
        description="Analyze XML sitemap for SEO issues"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sitemap", help="URL of sitemap to fetch and analyze")
    group.add_argument("--file", help="Local XML sitemap file to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--check-urls", action="store_true",
        help="List all URLs found in the sitemap"
    )
    args = parser.parse_args()

    content = None
    content_size = None

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        content = filepath.read_text(encoding="utf-8", errors="replace")
        content_size = filepath.stat().st_size
    elif args.sitemap:
        try:
            from urllib.request import urlopen, Request
            req = Request(args.sitemap, headers={'User-Agent': 'SEO-Audit-Bot/1.0'})
            resp = urlopen(req, timeout=30)
            content = resp.read().decode("utf-8", errors="replace")
            content_size = len(content.encode("utf-8"))
        except Exception as e:
            print(f"Error fetching sitemap: {e}", file=sys.stderr)
            sys.exit(1)

    urls, sub_sitemaps, parse_error = parse_sitemap_xml(content)

    if parse_error:
        print(f"Error: {parse_error}", file=sys.stderr)
        sys.exit(1)

    stats, issues, stale_urls = analyze_urls(urls, content_size)

    # Determine sitemap type
    sitemap_type = "sitemap_index" if sub_sitemaps else "urlset"

    result = {
        "source": args.file or args.sitemap,
        "type": sitemap_type,
        "file_size_bytes": content_size,
        "stats": stats,
        "sub_sitemaps": sub_sitemaps if sub_sitemaps else None,
        "issues": issues,
        "issue_count": len(issues),
        "passed": all(i["severity"] not in ("Critical", "High") for i in issues),
    }

    if args.check_urls:
        result["all_urls"] = [u["url"] for u in urls]

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  SITEMAP ANALYSIS")
        print(f"{'='*60}")
        print(f"  Source: {args.file or args.sitemap}")
        print(f"  Type: {sitemap_type}")
        if content_size:
            print(f"  File size: {content_size / 1024:.1f} KB")

        if sub_sitemaps:
            print(f"\n  Sitemap Index: {len(sub_sitemaps)} sub-sitemaps")
            for sm in sub_sitemaps[:10]:
                mod = f" (lastmod: {sm['lastmod']})" if sm['lastmod'] else ""
                print(f"    - {sm['url']}{mod}")
            if len(sub_sitemaps) > 10:
                print(f"    ... and {len(sub_sitemaps) - 10} more")

        if urls:
            print(f"\n  URL Statistics:")
            print(f"    Total URLs: {stats['total_urls']}")
            print(f"    With lastmod: {stats['with_lastmod']}")
            print(f"    With changefreq: {stats['with_changefreq']}")
            print(f"    With priority: {stats['with_priority']}")
            print(f"    Duplicates: {stats['duplicate_urls']}")
            print(f"    Stale (>1 year): {stats['stale_urls']}")
            print(f"    Domains: {', '.join(stats['domains'])}")

        if issues:
            print(f"\n  Issues ({len(issues)}):")
            for issue in issues:
                url_info = f" — {issue['url']}" if 'url' in issue else ""
                print(f"    [{issue['severity']}] {issue['type']}: {issue['detail']}{url_info}")
        else:
            print(f"\n  No issues found.")

        status = "PASSED" if result["passed"] else "NEEDS ATTENTION"
        print(f"\n  Overall: {status}")

        if args.check_urls and urls:
            print(f"\n  All URLs:")
            for u in urls:
                mod = f" [{u['lastmod']}]" if u.get('lastmod') else ""
                print(f"    {u['url']}{mod}")

        print()


if __name__ == "__main__":
    main()

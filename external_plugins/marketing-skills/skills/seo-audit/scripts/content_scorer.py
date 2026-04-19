#!/usr/bin/env python3
"""
SEO Content Quality Scorer

Scores content across SEO dimensions including keyword usage, readability,
structure, E-E-A-T signals, AI content detection markers, and on-page
optimization. Produces a weighted score 0-100 with actionable recommendations.

Usage:
    python content_scorer.py article.md
    python content_scorer.py article.md --keyword "cloud cost optimization" --json
    python content_scorer.py article.md --keyword "SEO audit" --verbose
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path


def count_words(text):
    """Count words in text."""
    return len(text.split())


def count_sentences(text):
    """Count sentences in text."""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def count_syllables(word):
    """Estimate syllable count for a word."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    count = 0
    vowels = 'aeiouy'
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith('e'):
        count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1
    return max(count, 1)


def flesch_reading_ease(text):
    """Calculate Flesch Reading Ease score."""
    words = text.split()
    word_count = len(words)
    sentence_count = count_sentences(text)
    if word_count == 0 or sentence_count == 0:
        return 0

    syllable_count = sum(count_syllables(w) for w in words)
    score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    return round(max(0, min(100, score)), 1)


def analyze_keyword_usage(text, keyword):
    """Analyze keyword placement and density."""
    if not keyword:
        return {"score": 0, "checks": {}, "detail": "No keyword provided"}

    text_lower = text.lower()
    keyword_lower = keyword.lower()
    words = text_lower.split()
    word_count = len(words)

    checks = {}

    # Keyword density
    keyword_count = text_lower.count(keyword_lower)
    density = (keyword_count * len(keyword_lower.split()) / max(word_count, 1)) * 100
    checks["density"] = {
        "value": round(density, 2),
        "pass": 0.5 <= density <= 2.5,
        "detail": f"Keyword density: {round(density, 2)}% (target: 0.5-2.5%)",
    }

    # Keyword in first 100 words
    first_100 = " ".join(words[:100])
    in_first_100 = keyword_lower in first_100
    checks["in_first_100_words"] = {
        "pass": in_first_100,
        "detail": "Keyword found in first 100 words" if in_first_100
        else "Keyword NOT in first 100 words",
    }

    # Keyword in headings
    headings = re.findall(r'^#{1,3}\s+(.+)', text, re.MULTILINE)
    headings_with_kw = sum(1 for h in headings if keyword_lower in h.lower())
    checks["in_headings"] = {
        "count": headings_with_kw,
        "total_headings": len(headings),
        "pass": headings_with_kw >= 1,
        "detail": f"Keyword in {headings_with_kw}/{len(headings)} headings",
    }

    # Keyword in H1
    h1s = re.findall(r'^#\s+(.+)', text, re.MULTILINE)
    in_h1 = any(keyword_lower in h.lower() for h in h1s)
    checks["in_h1"] = {
        "pass": in_h1,
        "detail": "Keyword found in H1" if in_h1 else "Keyword NOT in H1",
    }

    passed = sum(1 for c in checks.values() if c["pass"])
    score = (passed / len(checks)) * 100
    return {"score": round(score, 1), "checks": checks}


def analyze_structure(text):
    """Analyze content structure for SEO."""
    checks = {}

    lines = text.splitlines()
    word_count = count_words(text)

    # H1 presence
    h1s = re.findall(r'^#\s+', text, re.MULTILINE)
    checks["h1_present"] = {
        "pass": len(h1s) == 1,
        "count": len(h1s),
        "detail": f"{len(h1s)} H1 tag(s) — should be exactly 1",
    }

    # H2 sections
    h2s = re.findall(r'^##\s+', text, re.MULTILINE)
    checks["h2_sections"] = {
        "pass": len(h2s) >= 3,
        "count": len(h2s),
        "detail": f"{len(h2s)} H2 sections found",
    }

    # Heading hierarchy (no skipped levels)
    heading_levels = [len(m.group(1)) for m in re.finditer(r'^(#{1,6})\s+', text, re.MULTILINE)]
    skipped = False
    for i in range(1, len(heading_levels)):
        if heading_levels[i] > heading_levels[i-1] + 1:
            skipped = True
            break
    checks["heading_hierarchy"] = {
        "pass": not skipped,
        "detail": "Heading hierarchy is clean" if not skipped
        else "Heading levels are skipped (e.g., H2 to H4)",
    }

    # Word count
    checks["word_count"] = {
        "value": word_count,
        "pass": word_count >= 800,
        "detail": f"{word_count} words (minimum 800 for comprehensive content)",
    }

    # Paragraph length
    paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip() and not p.strip().startswith('#')]
    long_paragraphs = sum(1 for p in paragraphs if count_words(p) > 150)
    checks["paragraph_length"] = {
        "pass": long_paragraphs == 0,
        "long_count": long_paragraphs,
        "detail": f"{long_paragraphs} paragraphs exceed 150 words",
    }

    # Lists present
    list_items = len(re.findall(r'^\s*[\-\*\d+\.]\s+', text, re.MULTILINE))
    checks["lists_present"] = {
        "pass": list_items >= 3,
        "count": list_items,
        "detail": f"{list_items} list items found",
    }

    # Tables present
    table_rows = len(re.findall(r'^\s*\|.*\|', text, re.MULTILINE))
    checks["tables_present"] = {
        "pass": table_rows >= 3,
        "count": table_rows,
        "detail": f"{table_rows} table rows found",
    }

    passed = sum(1 for c in checks.values() if c["pass"])
    score = (passed / len(checks)) * 100
    return {"score": round(score, 1), "checks": checks}


def analyze_eeat(text):
    """Analyze E-E-A-T signals in content."""
    checks = {}

    # Author attribution
    has_author = bool(re.search(
        r'(author|written by|by\s+[A-Z][a-z]+\s+[A-Z])',
        text, re.IGNORECASE
    ))
    checks["author_attribution"] = {
        "pass": has_author,
        "detail": "Author attribution found" if has_author else "No author attribution",
    }

    # Date signals
    has_dates = bool(re.search(r'(published|updated|modified|date).*\d{4}', text, re.IGNORECASE))
    checks["date_signals"] = {
        "pass": has_dates,
        "detail": "Publication date signals found" if has_dates else "No date signals",
    }

    # Source citations
    citations = len(re.findall(
        r'(according to|source:|cited from|published in|\(\d{4}\)|reported by)',
        text, re.IGNORECASE
    ))
    checks["source_citations"] = {
        "pass": citations >= 2,
        "count": citations,
        "detail": f"{citations} source citations found",
    }

    # External links
    ext_links = len(re.findall(r'\[.*?\]\(https?://[^)]+\)', text))
    checks["external_references"] = {
        "pass": ext_links >= 1,
        "count": ext_links,
        "detail": f"{ext_links} external links found",
    }

    # Experience markers
    experience_markers = len(re.findall(
        r'\b(we found|we tested|we noticed|in our experience|I\'ve seen|'
        r'we observed|our data shows|in practice|real-world)\b',
        text, re.IGNORECASE
    ))
    checks["experience_signals"] = {
        "pass": experience_markers >= 1,
        "count": experience_markers,
        "detail": f"{experience_markers} first-hand experience markers found",
    }

    passed = sum(1 for c in checks.values() if c["pass"])
    score = (passed / len(checks)) * 100
    return {"score": round(score, 1), "checks": checks}


def analyze_ai_patterns(text):
    """Detect AI content patterns that may reduce SEO performance."""
    checks = {}
    word_count = count_words(text)

    # AI filler words
    filler_words = [
        'delve', 'landscape', 'crucial', 'vital', 'pivotal', 'leverage',
        'robust', 'comprehensive', 'holistic', 'foster', 'facilitate',
        'utilize', 'furthermore', 'moreover', 'streamline', 'cutting-edge',
        'game-changer', 'paradigm', 'synergy', 'ecosystem', 'transformative',
        'seamless', 'navigate', 'embark',
    ]
    filler_count = sum(
        len(re.findall(r'\b' + w + r'\b', text, re.IGNORECASE))
        for w in filler_words
    )
    per_1000 = (filler_count / max(word_count, 1)) * 1000
    checks["ai_filler_density"] = {
        "pass": per_1000 < 3,
        "count": filler_count,
        "per_1000": round(per_1000, 1),
        "detail": f"{filler_count} AI filler words ({round(per_1000, 1)} per 1000 words)",
    }

    # Hedging phrases
    hedging = len(re.findall(
        r"(it'?s important to note|it'?s worth mentioning|one might argue|"
        r"it goes without saying|needless to say)",
        text, re.IGNORECASE
    ))
    checks["hedging_phrases"] = {
        "pass": hedging == 0,
        "count": hedging,
        "detail": f"{hedging} hedging phrases found",
    }

    # Sentence length uniformity
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) >= 5:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        checks["sentence_variety"] = {
            "pass": std_dev > 4,
            "std_dev": round(std_dev, 1),
            "detail": f"Sentence length std dev: {round(std_dev, 1)} (>4 is natural variety)",
        }
    else:
        checks["sentence_variety"] = {
            "pass": True,
            "detail": "Not enough sentences to analyze variety",
        }

    passed = sum(1 for c in checks.values() if c["pass"])
    score = (passed / len(checks)) * 100
    return {"score": round(score, 1), "checks": checks}


def calculate_overall(keyword_score, structure_score, eeat_score, ai_score, readability):
    """Calculate weighted overall SEO content score."""
    # Readability factor (target 60-70)
    readability_score = 100 if 50 <= readability <= 80 else max(0, 100 - abs(readability - 65) * 2)

    weighted = (
        keyword_score * 0.25 +
        structure_score * 0.25 +
        eeat_score * 0.20 +
        ai_score * 0.15 +
        readability_score * 0.15
    )
    return round(weighted, 1)


def main():
    parser = argparse.ArgumentParser(
        description="Score content quality for SEO"
    )
    parser.add_argument("file", help="Path to content file (Markdown or HTML)")
    parser.add_argument("--keyword", help="Target keyword to analyze placement")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", action="store_true", help="Show all check details")
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    text = filepath.read_text(encoding="utf-8", errors="replace")
    word_count = count_words(text)
    readability = flesch_reading_ease(text)

    keyword_analysis = analyze_keyword_usage(text, args.keyword)
    structure_analysis = analyze_structure(text)
    eeat_analysis = analyze_eeat(text)
    ai_analysis = analyze_ai_patterns(text)

    overall = calculate_overall(
        keyword_analysis["score"],
        structure_analysis["score"],
        eeat_analysis["score"],
        ai_analysis["score"],
        readability,
    )

    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D" if overall >= 40 else "F"

    result = {
        "file": str(filepath),
        "word_count": word_count,
        "readability_score": readability,
        "overall_score": overall,
        "grade": grade,
        "keyword_analysis": keyword_analysis,
        "structure_analysis": structure_analysis,
        "eeat_analysis": eeat_analysis,
        "ai_pattern_analysis": ai_analysis,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  SEO CONTENT SCORE: {overall}/100 (Grade: {grade})")
        print(f"{'='*60}")
        print(f"  File: {filepath}")
        print(f"  Words: {word_count}")
        print(f"  Readability: {readability} (Flesch Reading Ease)")
        if args.keyword:
            print(f"  Keyword: {args.keyword}")
        print()
        print(f"  Keyword Usage:  {keyword_analysis['score']}/100")
        print(f"  Structure:      {structure_analysis['score']}/100")
        print(f"  E-E-A-T:        {eeat_analysis['score']}/100")
        print(f"  AI Patterns:    {ai_analysis['score']}/100")

        if args.verbose:
            for label, analysis in [
                ("Keyword", keyword_analysis),
                ("Structure", structure_analysis),
                ("E-E-A-T", eeat_analysis),
                ("AI Patterns", ai_analysis),
            ]:
                print(f"\n  --- {label} Details ---")
                for key, check in analysis.get("checks", {}).items():
                    status = "PASS" if check.get("pass") else "FAIL"
                    print(f"  [{status}] {key}: {check['detail']}")

        print()


if __name__ == "__main__":
    main()

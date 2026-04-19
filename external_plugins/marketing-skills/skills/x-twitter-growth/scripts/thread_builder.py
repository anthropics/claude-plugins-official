#!/usr/bin/env python3
"""
Twitter Thread Builder

Structures long-form content into optimal Twitter threads with hooks,
transitions, and engagement triggers. Supports text and JSON input.

Input: Text file with sections (use # headers or [Section] markers) or JSON.

Usage:
    python thread_builder.py content.txt
    python thread_builder.py content.txt --target-tweets 8
    python thread_builder.py content.json --format json
    python thread_builder.py content.txt --style numbered
"""

import argparse
import json
import re
import sys
import textwrap
from typing import Any, Dict, List, Optional, Tuple


MAX_TWEET_LENGTH = 280
THREAD_CONNECTOR_WORDS = ["Here's the thing:", "But here's what happened:", "And that's where it gets interesting:",
                          "The key insight:", "What most people miss:", "Here's why this matters:"]


def load_content(filepath: str) -> Dict[str, Any]:
    """Load content from text or JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Try JSON first
    try:
        data = json.loads(content)
        return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Parse as text with sections
    return parse_text_content(content)


def parse_text_content(text: str) -> Dict[str, Any]:
    """Parse text content into structured sections."""
    lines = text.split("\n")
    title = ""
    sections = []
    current_section = {"title": "", "content": ""}

    for line in lines:
        stripped = line.strip()

        # Detect title (first # heading)
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            continue

        # Detect section headers
        if stripped.startswith("## ") or re.match(r"^\[.+\]$", stripped):
            if current_section["content"].strip():
                sections.append(current_section)
            section_title = stripped.lstrip("#").strip().strip("[]")
            current_section = {"title": section_title, "content": ""}
            continue

        current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    # If no sections found, split by paragraphs
    if not sections:
        paragraphs = re.split(r"\n\s*\n", text)
        if paragraphs and not title:
            title = paragraphs[0].strip()[:100]
            paragraphs = paragraphs[1:]
        for i, para in enumerate(paragraphs):
            if para.strip():
                sections.append({"title": f"Point {i+1}", "content": para.strip()})

    return {"title": title, "sections": sections}


def split_text_to_tweets(text: str, max_length: int = MAX_TWEET_LENGTH) -> List[str]:
    """Split text into tweet-sized chunks, breaking at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    tweets = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If single sentence exceeds limit, wrap it
        if len(sentence) > max_length:
            if current:
                tweets.append(current.strip())
                current = ""
            # Hard wrap long sentences
            wrapped = textwrap.wrap(sentence, width=max_length - 5)
            for chunk in wrapped:
                tweets.append(chunk.strip())
            continue

        test = f"{current} {sentence}".strip() if current else sentence
        if len(test) <= max_length:
            current = test
        else:
            if current:
                tweets.append(current.strip())
            current = sentence

    if current.strip():
        tweets.append(current.strip())

    return tweets


def build_thread(data: Dict[str, Any], target_tweets: int, style: str,
                 add_numbering: bool) -> List[Dict[str, str]]:
    """Build optimized thread from structured content."""
    title = data.get("title", "")
    sections = data.get("sections", [])

    thread = []

    # Tweet 1: Hook
    hook = data.get("hook", "")
    if not hook:
        if title:
            hook = title
            # Add engagement hook if title is short
            if len(hook) < 200:
                hook += "\n\nA thread:"
        elif sections:
            hook = sections[0]["content"].split(".")[0] + "."

    thread.append({"role": "hook", "text": hook[:MAX_TWEET_LENGTH]})

    # Build body tweets from sections
    body_tweets = []
    for section in sections:
        content = section["content"].strip()
        if not content:
            continue

        # Add section transition if titled
        if section.get("title") and section["title"] != content[:50]:
            content = f"{section['title']}:\n\n{content}"

        chunks = split_text_to_tweets(content, MAX_TWEET_LENGTH - 10)  # Leave room for numbering
        for chunk in chunks:
            body_tweets.append({"role": "body", "text": chunk})

    # If we have more tweets than target, consolidate
    if len(body_tweets) > target_tweets - 2:  # -2 for hook and closer
        consolidated = []
        i = 0
        while i < len(body_tweets):
            current = body_tweets[i]["text"]
            while i + 1 < len(body_tweets):
                combined = current + " " + body_tweets[i + 1]["text"]
                if len(combined) <= MAX_TWEET_LENGTH - 10:
                    current = combined
                    i += 1
                else:
                    break
            consolidated.append({"role": "body", "text": current})
            i += 1
        body_tweets = consolidated[:target_tweets - 2]

    thread.extend(body_tweets)

    # Final tweet: CTA / closer
    closer = data.get("cta", "")
    if not closer:
        closer = "If you found this valuable:\n\n"
        closer += "1. Follow me for more insights\n"
        closer += "2. Repost the first tweet to share\n"
        closer += "3. Drop a reply with your thoughts"

    thread.append({"role": "closer", "text": closer[:MAX_TWEET_LENGTH]})

    # Apply numbering
    if add_numbering or style == "numbered":
        total = len(thread)
        for i, tweet in enumerate(thread):
            prefix = f"{i+1}/{total} "
            if len(prefix + tweet["text"]) <= MAX_TWEET_LENGTH:
                tweet["text"] = prefix + tweet["text"]

    return thread


def analyze_thread(thread: List[Dict]) -> Dict[str, Any]:
    """Analyze thread quality metrics."""
    texts = [t["text"] for t in thread]
    lengths = [len(t) for t in texts]

    # Check for engagement triggers
    has_question = any("?" in t for t in texts[1:-1])  # Questions in body
    has_data = any(re.search(r'\d+%|\$\d+|\d+x', t) for t in texts)
    hook_length = lengths[0] if lengths else 0

    issues = []
    if hook_length < 80:
        issues.append("Hook tweet is short - consider making it more compelling")
    if hook_length > 250:
        issues.append("Hook tweet is very long - shorter hooks often perform better")
    if not has_question:
        issues.append("No questions in thread body - add one to drive replies")
    if not has_data:
        issues.append("No data points or statistics - consider adding one for credibility")

    avg_length = sum(lengths) / len(lengths) if lengths else 0
    fill_rate = avg_length / MAX_TWEET_LENGTH * 100

    return {
        "total_tweets": len(thread),
        "total_characters": sum(lengths),
        "avg_tweet_length": round(avg_length, 0),
        "character_fill_rate": round(fill_rate, 1),
        "shortest_tweet": min(lengths) if lengths else 0,
        "longest_tweet": max(lengths) if lengths else 0,
        "has_question_in_body": has_question,
        "has_data_point": has_data,
        "issues": issues,
    }


def print_human(thread: List[Dict], analysis: Dict) -> None:
    """Print thread in human-readable format."""
    print("=" * 60)
    print("  Twitter Thread Builder")
    print("=" * 60)

    for i, tweet in enumerate(thread):
        role_label = {"hook": "HOOK", "body": "BODY", "closer": "CTA"}.get(tweet["role"], "")
        chars = len(tweet["text"])
        bar = "#" * int(chars / MAX_TWEET_LENGTH * 20)
        print(f"\n  --- Tweet {i+1} [{role_label}] ({chars}/{MAX_TWEET_LENGTH} chars) {bar} ---")
        # Indent tweet text
        for line in tweet["text"].split("\n"):
            print(f"  {line}")

    # Analysis
    a = analysis
    print(f"\n  {'=' * 56}")
    print(f"  THREAD ANALYSIS")
    print(f"  {'=' * 56}")
    print(f"  Total Tweets:      {a['total_tweets']}")
    print(f"  Total Characters:  {a['total_characters']}")
    print(f"  Avg Tweet Length:  {a['avg_tweet_length']:.0f} chars ({a['character_fill_rate']:.0f}% fill)")
    print(f"  Has Questions:     {'Yes' if a['has_question_in_body'] else 'No'}")
    print(f"  Has Data Points:   {'Yes' if a['has_data_point'] else 'No'}")

    if a["issues"]:
        print(f"\n  Suggestions:")
        for issue in a["issues"]:
            print(f"  [!] {issue}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Structure long-form content into optimal Twitter threads"
    )
    parser.add_argument("file", help="Text or JSON file with content")
    parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")
    parser.add_argument("--target-tweets", type=int, default=8,
                        help="Target number of tweets in thread (default: 8)")
    parser.add_argument("--style", choices=["numbered", "clean"], default="clean",
                        help="Thread style (default: clean)")
    parser.add_argument("--numbered", action="store_true", help="Add tweet numbering (1/N format)")
    args = parser.parse_args()

    data = load_content(args.file)
    thread = build_thread(data, args.target_tweets, args.style, args.numbered)
    analysis = analyze_thread(thread)

    if args.format == "json":
        output = {"thread": thread, "analysis": analysis}
        print(json.dumps(output, indent=2))
    else:
        print_human(thread, analysis)


if __name__ == "__main__":
    main()

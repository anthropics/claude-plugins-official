#!/usr/bin/env python3
"""
Tweet Performance Analyzer

Analyzes tweet performance patterns from exported X/Twitter analytics data.
Identifies top-performing content types, optimal posting times, engagement
patterns, and actionable content insights.

Expected CSV columns: tweet_id, text, created_at, impressions, engagements,
  likes, retweets, replies, type, has_media

Usage:
    python tweet_analyzer.py tweets.csv
    python tweet_analyzer.py tweets.csv --format json
    python tweet_analyzer.py tweets.csv --min-impressions 500
    python tweet_analyzer.py tweets.csv --top 20
"""

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime from common formats."""
    if not dt_str or dt_str.strip() == "":
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M", "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return None


def safe_int(val: str, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def load_tweets(filepath: str) -> List[Dict[str, Any]]:
    """Load tweet data from CSV."""
    tweets = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_datetime(row.get("created_at", ""))
            impressions = safe_int(row.get("impressions", "0"))
            engagements = safe_int(row.get("engagements", "0"))
            likes = safe_int(row.get("likes", "0"))
            retweets = safe_int(row.get("retweets", "0"))
            replies = safe_int(row.get("replies", "0"))

            eng_rate = (engagements / impressions * 100) if impressions > 0 else 0

            tweet = {
                "tweet_id": row.get("tweet_id", "").strip(),
                "text": row.get("text", "").strip(),
                "created_at": dt,
                "impressions": impressions,
                "engagements": engagements,
                "likes": likes,
                "retweets": retweets,
                "replies": replies,
                "engagement_rate": round(eng_rate, 2),
                "type": row.get("type", "single").strip().lower(),
                "has_media": row.get("has_media", "").strip().lower() in ("yes", "true", "1"),
                "hour": dt.hour if dt else None,
                "day_of_week": dt.strftime("%A") if dt else None,
            }
            tweets.append(tweet)
    return tweets


def analyze_overall(tweets: List[Dict]) -> Dict[str, Any]:
    """Calculate overall performance metrics."""
    impressions = [t["impressions"] for t in tweets]
    eng_rates = [t["engagement_rate"] for t in tweets]
    likes = [t["likes"] for t in tweets]
    retweets = [t["retweets"] for t in tweets]
    replies = [t["replies"] for t in tweets]

    return {
        "total_tweets": len(tweets),
        "total_impressions": sum(impressions),
        "avg_impressions": round(statistics.mean(impressions), 0) if impressions else 0,
        "median_impressions": round(statistics.median(impressions), 0) if impressions else 0,
        "avg_engagement_rate": round(statistics.mean(eng_rates), 2) if eng_rates else 0,
        "median_engagement_rate": round(statistics.median(eng_rates), 2) if eng_rates else 0,
        "avg_likes": round(statistics.mean(likes), 1) if likes else 0,
        "avg_retweets": round(statistics.mean(retweets), 1) if retweets else 0,
        "avg_replies": round(statistics.mean(replies), 1) if replies else 0,
        "total_likes": sum(likes),
        "total_retweets": sum(retweets),
        "total_replies": sum(replies),
    }


def analyze_by_type(tweets: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by tweet type."""
    type_groups = defaultdict(list)
    for t in tweets:
        type_groups[t["type"]].append(t)

    result = {}
    for tweet_type, group in sorted(type_groups.items()):
        eng_rates = [t["engagement_rate"] for t in group]
        impressions = [t["impressions"] for t in group]
        result[tweet_type] = {
            "count": len(group),
            "avg_engagement_rate": round(statistics.mean(eng_rates), 2),
            "avg_impressions": round(statistics.mean(impressions), 0),
            "total_impressions": sum(impressions),
        }
    return result


def analyze_by_media(tweets: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by media presence."""
    with_media = [t for t in tweets if t["has_media"]]
    without_media = [t for t in tweets if not t["has_media"]]

    def stats(group):
        if not group:
            return {"count": 0, "avg_engagement_rate": 0, "avg_impressions": 0}
        eng = [t["engagement_rate"] for t in group]
        imp = [t["impressions"] for t in group]
        return {
            "count": len(group),
            "avg_engagement_rate": round(statistics.mean(eng), 2),
            "avg_impressions": round(statistics.mean(imp), 0),
        }

    return {"with_media": stats(with_media), "without_media": stats(without_media)}


def analyze_posting_times(tweets: List[Dict]) -> Dict[str, Any]:
    """Analyze performance by posting time."""
    hour_groups = defaultdict(list)
    day_groups = defaultdict(list)

    for t in tweets:
        if t["hour"] is not None:
            hour_groups[t["hour"]].append(t["engagement_rate"])
        if t["day_of_week"]:
            day_groups[t["day_of_week"]].append(t["engagement_rate"])

    # Best hours
    hour_stats = {}
    for hour, rates in sorted(hour_groups.items()):
        hour_stats[f"{hour:02d}:00"] = {
            "count": len(rates),
            "avg_engagement_rate": round(statistics.mean(rates), 2),
        }

    # Best days
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_stats = {}
    for day in day_order:
        if day in day_groups:
            rates = day_groups[day]
            day_stats[day] = {
                "count": len(rates),
                "avg_engagement_rate": round(statistics.mean(rates), 2),
            }

    # Find best posting windows
    best_hours = sorted(hour_stats.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True)[:5]
    best_days = sorted(day_stats.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True)[:3]

    return {
        "by_hour": hour_stats,
        "by_day": day_stats,
        "best_hours": [{"hour": h, "avg_eng_rate": s["avg_engagement_rate"], "tweets": s["count"]}
                       for h, s in best_hours],
        "best_days": [{"day": d, "avg_eng_rate": s["avg_engagement_rate"], "tweets": s["count"]}
                      for d, s in best_days],
    }


def analyze_text_patterns(tweets: List[Dict]) -> Dict[str, Any]:
    """Analyze text content patterns correlated with performance."""
    patterns = {
        "has_question": {"pattern": r"\?", "with": [], "without": []},
        "has_number": {"pattern": r"\d+", "with": [], "without": []},
        "has_emoji": {"pattern": r"[\U0001F600-\U0001F9FF]", "with": [], "without": []},
        "starts_with_hook": {"pattern": r"^(Here's|I just|Most people|The secret|Why do|How to|What if)",
                             "with": [], "without": []},
        "has_thread_marker": {"pattern": r"(thread|🧵|\d+/)", "with": [], "without": []},
    }

    for t in tweets:
        text = t["text"]
        eng = t["engagement_rate"]
        for key, p in patterns.items():
            if re.search(p["pattern"], text, re.IGNORECASE):
                p["with"].append(eng)
            else:
                p["without"].append(eng)

    results = {}
    for key, p in patterns.items():
        with_avg = round(statistics.mean(p["with"]), 2) if p["with"] else 0
        without_avg = round(statistics.mean(p["without"]), 2) if p["without"] else 0
        lift = ((with_avg - without_avg) / without_avg * 100) if without_avg > 0 else 0
        results[key] = {
            "with_count": len(p["with"]),
            "without_count": len(p["without"]),
            "with_avg_engagement": with_avg,
            "without_avg_engagement": without_avg,
            "lift_pct": round(lift, 1),
        }

    # Tweet length analysis
    length_buckets = {"short (<100)": [], "medium (100-200)": [], "long (200-280)": []}
    for t in tweets:
        text_len = len(t["text"])
        eng = t["engagement_rate"]
        if text_len < 100:
            length_buckets["short (<100)"].append(eng)
        elif text_len < 200:
            length_buckets["medium (100-200)"].append(eng)
        else:
            length_buckets["long (200-280)"].append(eng)

    length_stats = {}
    for bucket, rates in length_buckets.items():
        length_stats[bucket] = {
            "count": len(rates),
            "avg_engagement_rate": round(statistics.mean(rates), 2) if rates else 0,
        }

    results["length_analysis"] = length_stats
    return results


def get_top_tweets(tweets: List[Dict], n: int = 10) -> List[Dict]:
    """Get top performing tweets by engagement rate."""
    return sorted(tweets, key=lambda t: t["engagement_rate"], reverse=True)[:n]


def print_human(overall: Dict, type_analysis: Dict, media_analysis: Dict,
                time_analysis: Dict, text_analysis: Dict, top_tweets: List[Dict]) -> None:
    """Print analysis in human-readable format."""
    print("=" * 70)
    print("  X/Twitter Performance Analysis")
    print("=" * 70)

    o = overall
    print(f"\n  --- Overall Metrics ---")
    print(f"  Total Tweets:        {o['total_tweets']}")
    print(f"  Total Impressions:   {o['total_impressions']:,}")
    print(f"  Avg Impressions:     {o['avg_impressions']:,.0f}")
    print(f"  Avg Engagement Rate: {o['avg_engagement_rate']:.2f}%")
    print(f"  Avg Likes:           {o['avg_likes']:.1f}")
    print(f"  Avg Retweets:        {o['avg_retweets']:.1f}")
    print(f"  Avg Replies:         {o['avg_replies']:.1f}")

    # By type
    print(f"\n  --- By Content Type ---")
    print(f"  {'Type':<20} {'Count':>6} {'Avg Eng%':>9} {'Avg Impressions':>16}")
    for t_type, stats in sorted(type_analysis.items(), key=lambda x: x[1]["avg_engagement_rate"], reverse=True):
        print(f"  {t_type:<20} {stats['count']:>6} {stats['avg_engagement_rate']:>8.2f}% {stats['avg_impressions']:>15,.0f}")

    # Media
    print(f"\n  --- Media Impact ---")
    wm = media_analysis["with_media"]
    wom = media_analysis["without_media"]
    print(f"  With media:    {wm['avg_engagement_rate']:.2f}% eng rate (n={wm['count']})")
    print(f"  Without media: {wom['avg_engagement_rate']:.2f}% eng rate (n={wom['count']})")
    if wom["avg_engagement_rate"] > 0:
        lift = (wm["avg_engagement_rate"] - wom["avg_engagement_rate"]) / wom["avg_engagement_rate"] * 100
        direction = "+" if lift > 0 else ""
        print(f"  Media lift:    {direction}{lift:.1f}%")

    # Best times
    print(f"\n  --- Best Posting Times ---")
    for h in time_analysis["best_hours"][:3]:
        print(f"  {h['hour']}: {h['avg_eng_rate']:.2f}% avg engagement (n={h['tweets']})")
    print()
    for d in time_analysis["best_days"][:3]:
        print(f"  {d['day']}: {d['avg_eng_rate']:.2f}% avg engagement (n={d['tweets']})")

    # Text patterns
    print(f"\n  --- Content Patterns ---")
    for key, stats in text_analysis.items():
        if key == "length_analysis":
            continue
        if stats["with_count"] >= 3:
            label = key.replace("_", " ").title()
            direction = "+" if stats["lift_pct"] > 0 else ""
            print(f"  {label:<25} {direction}{stats['lift_pct']:.1f}% lift "
                  f"({stats['with_avg_engagement']:.2f}% vs {stats['without_avg_engagement']:.2f}%)")

    length = text_analysis.get("length_analysis", {})
    if length:
        print(f"\n  --- Tweet Length ---")
        for bucket, stats in length.items():
            if stats["count"] > 0:
                bar = "#" * max(1, int(stats["avg_engagement_rate"] * 3))
                print(f"  {bucket:<20} {stats['avg_engagement_rate']:.2f}% (n={stats['count']})  {bar}")

    # Top tweets
    print(f"\n  --- Top Performing Tweets ---")
    for i, t in enumerate(top_tweets[:5], 1):
        text_preview = t["text"][:60] + "..." if len(t["text"]) > 60 else t["text"]
        print(f"  {i}. [{t['engagement_rate']:.2f}%] {text_preview}")
        print(f"     Impressions: {t['impressions']:,} | Likes: {t['likes']} | "
              f"RT: {t['retweets']} | Replies: {t['replies']}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze tweet performance patterns from exported X/Twitter data"
    )
    parser.add_argument("file", help="CSV file with tweet data")
    parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")
    parser.add_argument("--min-impressions", type=int, default=0,
                        help="Minimum impressions filter")
    parser.add_argument("--top", type=int, default=10, help="Number of top tweets to show")
    args = parser.parse_args()

    tweets = load_tweets(args.file)
    if not tweets:
        print("Error: No valid tweet data found", file=sys.stderr)
        sys.exit(1)

    if args.min_impressions > 0:
        tweets = [t for t in tweets if t["impressions"] >= args.min_impressions]

    overall = analyze_overall(tweets)
    type_analysis = analyze_by_type(tweets)
    media_analysis = analyze_by_media(tweets)
    time_analysis = analyze_posting_times(tweets)
    text_analysis = analyze_text_patterns(tweets)
    top_tweets = get_top_tweets(tweets, args.top)

    if args.format == "json":
        # Serialize datetimes
        for t in top_tweets:
            t["created_at"] = t["created_at"].isoformat() if t["created_at"] else None
        output = {
            "overall": overall,
            "by_type": type_analysis,
            "media_impact": media_analysis,
            "posting_times": time_analysis,
            "content_patterns": text_analysis,
            "top_tweets": top_tweets,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print_human(overall, type_analysis, media_analysis, time_analysis, text_analysis, top_tweets)


if __name__ == "__main__":
    main()

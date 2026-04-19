#!/usr/bin/env python3
"""
Twitter/X Growth Tracker

Tracks follower growth, engagement rates, and identifies best posting times
from analytics data. Supports daily, weekly, and monthly period analysis.

Expected CSV columns: date, followers, impressions, engagements, likes,
  retweets, replies, tweets_posted, profile_visits

Usage:
    python growth_tracker.py analytics.csv
    python growth_tracker.py analytics.csv --period monthly
    python growth_tracker.py analytics.csv --format json
    python growth_tracker.py analytics.csv --compare-periods
"""

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from common formats."""
    if not date_str or date_str.strip() == "":
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def safe_int(val: str, default: int = 0) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def load_analytics(filepath: str) -> List[Dict[str, Any]]:
    """Load analytics data from CSV."""
    data = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("date", ""))
            if not dt:
                continue
            entry = {
                "date": dt,
                "followers": safe_int(row.get("followers", "0")),
                "impressions": safe_int(row.get("impressions", "0")),
                "engagements": safe_int(row.get("engagements", "0")),
                "likes": safe_int(row.get("likes", "0")),
                "retweets": safe_int(row.get("retweets", "0")),
                "replies": safe_int(row.get("replies", "0")),
                "tweets_posted": safe_int(row.get("tweets_posted", "0")),
                "profile_visits": safe_int(row.get("profile_visits", "0")),
            }
            data.append(entry)
    return sorted(data, key=lambda x: x["date"])


def group_by_period(data: List[Dict], period: str) -> Dict[str, List[Dict]]:
    """Group data entries by period."""
    groups = defaultdict(list)
    for entry in data:
        dt = entry["date"]
        if period == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Start of week (Monday)
            start = dt - timedelta(days=dt.weekday())
            key = f"{start.strftime('%Y-%m-%d')} to {(start + timedelta(days=6)).strftime('%Y-%m-%d')}"
        elif period == "monthly":
            key = dt.strftime("%Y-%m")
        else:
            key = dt.strftime("%Y-%m-%d")
        groups[key].append(entry)
    return dict(sorted(groups.items()))


def calculate_period_metrics(entries: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate metrics for a period."""
    if not entries:
        return {}

    followers_start = entries[0]["followers"]
    followers_end = entries[-1]["followers"]
    follower_growth = followers_end - followers_start

    total_impressions = sum(e["impressions"] for e in entries)
    total_engagements = sum(e["engagements"] for e in entries)
    total_likes = sum(e["likes"] for e in entries)
    total_retweets = sum(e["retweets"] for e in entries)
    total_replies = sum(e["replies"] for e in entries)
    total_tweets = sum(e["tweets_posted"] for e in entries)
    total_profile_visits = sum(e["profile_visits"] for e in entries)

    eng_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0

    # Per-tweet metrics
    per_tweet_impressions = total_impressions / total_tweets if total_tweets > 0 else 0
    per_tweet_engagements = total_engagements / total_tweets if total_tweets > 0 else 0

    # Follower conversion rate (profile visits to followers)
    conversion_rate = (follower_growth / total_profile_visits * 100) if total_profile_visits > 0 and follower_growth > 0 else 0

    return {
        "days": len(entries),
        "followers_start": followers_start,
        "followers_end": followers_end,
        "follower_growth": follower_growth,
        "follower_growth_pct": round(follower_growth / followers_start * 100, 2) if followers_start > 0 else 0,
        "total_impressions": total_impressions,
        "total_engagements": total_engagements,
        "engagement_rate": round(eng_rate, 2),
        "total_likes": total_likes,
        "total_retweets": total_retweets,
        "total_replies": total_replies,
        "total_tweets_posted": total_tweets,
        "total_profile_visits": total_profile_visits,
        "per_tweet_impressions": round(per_tweet_impressions, 0),
        "per_tweet_engagements": round(per_tweet_engagements, 1),
        "profile_conversion_rate": round(conversion_rate, 2),
    }


def calculate_growth_trajectory(data: List[Dict]) -> Dict[str, Any]:
    """Calculate growth trends and projections."""
    if len(data) < 2:
        return {"trend": "insufficient_data"}

    followers = [(e["date"], e["followers"]) for e in data if e["followers"] > 0]
    if len(followers) < 2:
        return {"trend": "insufficient_data"}

    # Daily growth rates
    daily_growth = []
    for i in range(1, len(followers)):
        days_diff = (followers[i][0] - followers[i-1][0]).days
        if days_diff > 0 and followers[i-1][1] > 0:
            growth = (followers[i][1] - followers[i-1][1]) / days_diff
            daily_growth.append(growth)

    if not daily_growth:
        return {"trend": "flat"}

    avg_daily = statistics.mean(daily_growth)
    recent_daily = statistics.mean(daily_growth[-7:]) if len(daily_growth) >= 7 else avg_daily

    current = followers[-1][1]
    # Projections
    days_to_next_milestone = None
    milestones = [100, 500, 1000, 5000, 10000, 25000, 50000, 100000]
    next_milestone = None
    for m in milestones:
        if current < m:
            next_milestone = m
            if recent_daily > 0:
                days_to_next_milestone = int((m - current) / recent_daily)
            break

    # Trend direction
    if len(daily_growth) >= 14:
        first_half = statistics.mean(daily_growth[:len(daily_growth)//2])
        second_half = statistics.mean(daily_growth[len(daily_growth)//2:])
        if second_half > first_half * 1.1:
            trend = "accelerating"
        elif second_half < first_half * 0.9:
            trend = "decelerating"
        else:
            trend = "steady"
    else:
        trend = "steady"

    return {
        "trend": trend,
        "avg_daily_growth": round(avg_daily, 1),
        "recent_daily_growth": round(recent_daily, 1),
        "current_followers": current,
        "next_milestone": next_milestone,
        "days_to_milestone": days_to_next_milestone,
        "projected_30d": int(current + recent_daily * 30),
        "projected_90d": int(current + recent_daily * 90),
    }


def find_best_posting_patterns(data: List[Dict]) -> Dict[str, Any]:
    """Identify best posting frequency and patterns."""
    if not data:
        return {}

    # Correlation between tweets posted and engagement
    daily_data = [(e["tweets_posted"], e["engagements"], e["impressions"]) for e in data if e["tweets_posted"] > 0]

    frequency_buckets = defaultdict(list)
    for tweets, eng, imp in daily_data:
        eng_rate = (eng / imp * 100) if imp > 0 else 0
        if tweets <= 1:
            frequency_buckets["1 tweet/day"].append(eng_rate)
        elif tweets <= 3:
            frequency_buckets["2-3 tweets/day"].append(eng_rate)
        elif tweets <= 5:
            frequency_buckets["4-5 tweets/day"].append(eng_rate)
        else:
            frequency_buckets["6+ tweets/day"].append(eng_rate)

    freq_analysis = {}
    for bucket, rates in frequency_buckets.items():
        if rates:
            freq_analysis[bucket] = {
                "days": len(rates),
                "avg_engagement_rate": round(statistics.mean(rates), 2),
            }

    # Best day of week
    dow_data = defaultdict(list)
    for e in data:
        day = e["date"].strftime("%A")
        if e["impressions"] > 0:
            eng_rate = e["engagements"] / e["impressions"] * 100
            dow_data[day].append(eng_rate)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_analysis = {}
    for day in day_order:
        if day in dow_data:
            dow_analysis[day] = {
                "avg_engagement_rate": round(statistics.mean(dow_data[day]), 2),
                "days_sampled": len(dow_data[day]),
            }

    return {
        "posting_frequency": freq_analysis,
        "day_of_week": dow_analysis,
    }


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def print_human(period_data: Dict[str, Dict], trajectory: Dict,
                patterns: Dict, period_type: str) -> None:
    """Print growth report in human-readable format."""
    print("=" * 65)
    print(f"  X/Twitter Growth Report ({period_type})")
    print("=" * 65)

    # Trajectory
    t = trajectory
    if t.get("trend") != "insufficient_data":
        print(f"\n  --- Growth Trajectory ---")
        print(f"  Current Followers:   {format_number(t['current_followers'])}")
        print(f"  Trend:               {t['trend']}")
        print(f"  Avg Daily Growth:    {t['avg_daily_growth']:+.1f} followers/day")
        print(f"  Recent Daily Growth: {t['recent_daily_growth']:+.1f} followers/day")
        print(f"  30-Day Projection:   {format_number(t['projected_30d'])}")
        print(f"  90-Day Projection:   {format_number(t['projected_90d'])}")
        if t.get("next_milestone"):
            days = t["days_to_milestone"]
            if days and days > 0:
                print(f"  Next Milestone:      {format_number(t['next_milestone'])} (est. {days} days)")

    # Period breakdown
    print(f"\n  --- Period Breakdown ---")
    print(f"  {'Period':<22} {'Followers':>10} {'Growth':>8} {'Eng Rate':>9} {'Tweets':>7} {'Impressions':>12}")
    print(f"  {'-'*22} {'-'*10} {'-'*8} {'-'*9} {'-'*7} {'-'*12}")

    for period_key, metrics in period_data.items():
        growth_str = f"{metrics['follower_growth']:+,}"
        print(f"  {period_key:<22} {metrics['followers_end']:>10,} {growth_str:>8} "
              f"{metrics['engagement_rate']:>8.2f}% {metrics['total_tweets_posted']:>7} "
              f"{format_number(metrics['total_impressions']):>12}")

    # Posting patterns
    freq = patterns.get("posting_frequency", {})
    if freq:
        print(f"\n  --- Posting Frequency Impact ---")
        for bucket, stats in sorted(freq.items()):
            bar = "#" * max(1, int(stats["avg_engagement_rate"] * 3))
            print(f"  {bucket:<20} {stats['avg_engagement_rate']:.2f}% eng (n={stats['days']})  {bar}")

    dow = patterns.get("day_of_week", {})
    if dow:
        print(f"\n  --- Day of Week Performance ---")
        for day, stats in dow.items():
            bar = "#" * max(1, int(stats["avg_engagement_rate"] * 3))
            print(f"  {day:<12} {stats['avg_engagement_rate']:.2f}% eng  {bar}")

    # Health assessment
    print(f"\n  --- Assessment ---")
    last_period = list(period_data.values())[-1] if period_data else {}
    if last_period:
        eng = last_period.get("engagement_rate", 0)
        if eng >= 6:
            print(f"  Engagement rate is excellent ({eng:.2f}%)")
        elif eng >= 3:
            print(f"  Engagement rate is good ({eng:.2f}%)")
        elif eng >= 1:
            print(f"  Engagement rate is average ({eng:.2f}%) - focus on content quality")
        else:
            print(f"  Engagement rate is low ({eng:.2f}%) - review content strategy")

        growth_pct = last_period.get("follower_growth_pct", 0)
        if growth_pct > 10:
            print(f"  Strong follower growth ({growth_pct:.1f}%)")
        elif growth_pct > 0:
            print(f"  Positive follower growth ({growth_pct:.1f}%)")
        elif growth_pct == 0:
            print(f"  Flat follower growth - increase content volume or try new formats")
        else:
            print(f"  Follower decline ({growth_pct:.1f}%) - investigate content and engagement strategy")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Track follower growth, engagement rates, and best posting times"
    )
    parser.add_argument("file", help="CSV file with analytics data")
    parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly",
                        help="Aggregation period (default: weekly)")
    args = parser.parse_args()

    data = load_analytics(args.file)
    if not data:
        print("Error: No valid analytics data found", file=sys.stderr)
        sys.exit(1)

    grouped = group_by_period(data, args.period)
    period_metrics = {k: calculate_period_metrics(v) for k, v in grouped.items()}
    trajectory = calculate_growth_trajectory(data)
    patterns = find_best_posting_patterns(data)

    if args.format == "json":
        output = {
            "period_type": args.period,
            "periods": period_metrics,
            "trajectory": trajectory,
            "posting_patterns": patterns,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print_human(period_metrics, trajectory, patterns, args.period)


if __name__ == "__main__":
    main()

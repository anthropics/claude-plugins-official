---
name: x-twitter-growth
description: >
  This skill should be used when the user asks to "analyze tweets", "grow on Twitter",
  "build Twitter threads", "optimize X posting schedule", "track follower growth",
  "improve tweet engagement", or "create a Twitter content strategy".
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: marketing
  domain: social-media
  updated: 2026-04-02
  tags: [twitter, x, social-media, engagement, threads, growth-hacking]
---
# X/Twitter Growth Skill

## Overview

Production-ready X/Twitter growth toolkit for analyzing tweet performance patterns, structuring optimal threads, and tracking engagement metrics. Designed for creators, marketers, and brand accounts looking to grow audience and engagement systematically through data-driven content decisions.

## Quick Start

```bash
# Analyze tweet performance patterns from exported data
python scripts/tweet_analyzer.py tweets.csv

# Structure long-form content into optimal Twitter threads
python scripts/thread_builder.py content.txt --target-tweets 8

# Track follower growth, engagement rates, and best posting times
python scripts/growth_tracker.py analytics.csv --period monthly
```

## Tools Overview

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `tweet_analyzer.py` | Performance pattern analysis | CSV with tweet data | Engagement patterns + insights |
| `thread_builder.py` | Thread structuring | Text file or JSON | Formatted thread + hooks |
| `growth_tracker.py` | Growth & engagement tracking | CSV with analytics data | Growth report + best times |

## Workflows

### Workflow 1: Content Performance Audit

1. Export tweet data from X Analytics or third-party tool as CSV
2. Run `tweet_analyzer.py` to identify top-performing patterns
3. Identify which content types, formats, and topics drive engagement
4. Use insights to refine content strategy and posting schedule
5. Re-audit monthly to track improvement

### Workflow 2: Thread Creation Pipeline

1. Draft long-form content in text or markdown format
2. Run `thread_builder.py` to split into optimal thread structure
3. Review hook tweet (tweet 1) for maximum engagement potential
4. Add call-to-action and engagement hooks per recommendations
5. Schedule using identified best posting times from `growth_tracker.py`

### Workflow 3: Monthly Growth Review

1. Export analytics data for the period
2. Run `growth_tracker.py --period monthly` for growth metrics
3. Run `tweet_analyzer.py` on the same period for content insights
4. Compare engagement rates to prior period
5. Identify top 5 tweets and extract replicable patterns

## Reference Documentation

See `references/x-growth-playbook.md` for comprehensive strategies covering:
- Content format frameworks
- Engagement optimization tactics
- Thread writing best practices
- Algorithm understanding
- Growth compounding strategies

## Common Patterns

### Pattern: Tweet Data CSV Format
```csv
tweet_id,text,created_at,impressions,engagements,likes,retweets,replies,type,has_media
T001,"Here's what I learned...",2025-06-15 09:30:00,15000,850,320,95,45,thread_start,no
T002,"Check out this chart",2025-06-14 14:00:00,8500,420,180,35,22,single,yes
```

### Pattern: Thread Content Input
```text
# How I Grew to 50K Followers in 6 Months

The biggest lesson was consistency over virality. Here's the complete breakdown...

[Section 1: Finding Your Niche]
Most creators make the mistake of being too broad. Pick one topic and go deep...

[Section 2: Content Pillars]
I built 3 content pillars that I rotate through each week...
```

### Engagement Rate Benchmarks

| Metric | Low | Average | Good | Excellent |
|--------|-----|---------|------|-----------|
| Engagement Rate | < 1% | 1-3% | 3-6% | > 6% |
| Reply Rate | < 0.1% | 0.1-0.5% | 0.5-1% | > 1% |
| Retweet Rate | < 0.2% | 0.2-1% | 1-3% | > 3% |
| Thread Completion | < 20% | 20-40% | 40-60% | > 60% |

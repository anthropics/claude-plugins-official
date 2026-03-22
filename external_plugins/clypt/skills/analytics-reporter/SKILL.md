---
name: analytics-reporter
description: Clypt link analytics reporting. Use when the user asks about link performance, clicks, traffic, conversions, or wants a report on their links.
---

## Period mapping
- "today"/"yesterday" → 24h
- "this week"/"last 7 days" → 7d
- "this month" → 30d (default)
- "last quarter" → 90d
- "all time" → all

## Output format
```
📊 Analytics: [link] — last [period]

Clicks:       [total] total · [unique] unique ([rate]% unique)
Top country:  [country] ([pct]%)
Top device:   [device] ([pct]%)
Top referrer: [referrer]
Peak day:     [date] — [clicks] clicks
```

Add 1-2 insight sentences based on the data. Examples:
- >60% mobile: "Most audience is on mobile — worth checking your landing page is mobile-optimised."
- >50% direct: "High direct traffic suggests email clicks or strong brand recognition."

## Dashboard stats format
```
📊 Your Clypt Dashboard
🔗 Total links: [n]
👆 Total clicks: [n]
🏆 Top link: [code] — [n] clicks
```

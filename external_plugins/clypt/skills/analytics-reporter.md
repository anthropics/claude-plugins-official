# Clypt Analytics Reporter

## When this skill activates
Activates when user asks about clicks, performance, traffic, conversions, or wants a report.

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

Add 1-2 insight sentences based on the data pattern.

## Dashboard stats format
```
📊 Your Clypt Dashboard
🔗 Total links: [n]
👆 Total clicks: [n]
🏆 Top link: [code] — [n] clicks
```

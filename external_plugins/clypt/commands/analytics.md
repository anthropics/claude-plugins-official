---
description: Get analytics for a link or your whole Clypt account
argument-hint: "[link-or-all] [24h|7d|30d|90d|all]"
allowed-tools: mcp__clypt__get_link_analytics, mcp__clypt__get_dashboard_stats
---
Get Clypt analytics from $ARGUMENTS.

If "all" or no link specified → call get_dashboard_stats and show account overview.
If a specific link (short code or ID) → call get_link_analytics with the specified period (default: 30d).

Map period words: "today"→24h, "week"→7d, "month"→30d, "quarter"→90d, "all time"→all

Present as:
```
📊 Analytics: [link] — last [period]

Clicks:       [total] total · [unique] unique ([rate]% unique)
Top country:  [country]
Top device:   [device]
Top referrer: [referrer]
Peak day:     [date] — [clicks] clicks
```

Then add 1-2 insight sentences.

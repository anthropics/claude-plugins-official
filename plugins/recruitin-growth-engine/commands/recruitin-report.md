---
description: Generate a weekly performance report for all active campaigns
argument-hint: [week-number] [year]
---

# Recruitin Weekly Performance Report

You are generating the weekly performance report for the Recruitin Growth Intelligence Engine. This report analyzes all active campaigns and provides actionable recommendations.

## Report Parameters

Based on: $ARGUMENTS

If no week specified, use the previous week (current week - 1).

## Step 1: Data Collection

Launch the **data-analyst** agent to:

1. Query Supabase for all active campaigns
2. Retrieve weekly_metrics for the target week
3. Compare with previous week's metrics
4. Retrieve campaign-lifetime averages for trend analysis

## Step 2: Generate Report Sections

### Executive Summary
- Total active campaigns and their statuses
- Total spend vs. planned budget
- Total hires achieved
- Average CPH across all campaigns
- Week-over-week trend indicator

### Campaign Performance Matrix
Create a table with all active campaigns showing:
- Client name, role, channel
- CTR, CPA, CPH, quality score
- Health score (0-1)
- Week-over-week trend (arrows)
- Recommended action

### Top Performers
Highlight the top 3 campaigns by:
- Lowest CPH
- Highest quality score
- Best CTR

### Anomaly Alerts
Flag any campaigns with:
- CTR drop >30%
- CPC increase >25%
- Quality score decline >20%
- Zero applications with active spend
- Budget overruns

### Winning Strategy Updates
- Refresh the winning_strategies materialized view
- Report any changes from last week
- New patterns discovered
- Strategies gaining or losing confidence

### Recommendations
Provide 3-5 specific, actionable recommendations:
- Which campaigns to scale
- Which campaigns to pause or restructure
- Which tests to run next week
- Budget reallocation suggestions

## Step 3: Trend Visualization

Present a text-based trend summary:
```
CPH Trend (last 4 weeks):
Week 1: €450 ████████████████████
Week 2: €380 ████████████████
Week 3: €320 █████████████
Week 4: €290 ████████████  ↓ improving
```

## Step 4: Client Summaries

For each client with active campaigns, generate a concise summary suitable for:
- Slack message (if Slack plugin available)
- Email to the client account manager
- Internal Recruitin team standup

## Output

Present the full report in markdown format, ready for review and distribution.

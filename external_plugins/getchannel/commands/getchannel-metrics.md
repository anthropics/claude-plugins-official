# GetChannel Metrics

View campaign performance metrics and ROAS across all platforms.

## Usage

```
/getchannel-metrics [--campaign id] [--platform name] [--period 7d|30d|90d]
```

## What This Does

1. Aggregates metrics from all connected ad platforms
2. Calculates unified ROAS, CPA, and conversion metrics
3. Shows trends and comparisons to previous periods
4. Highlights top and underperforming campaigns

## Example Output

```
Performance Overview (Last 7 Days)

Overall Metrics
├── Spend: $12,450 (+8% vs prev)
├── Revenue: $45,230 (+12% vs prev)
├── ROAS: 3.63x (+4% vs prev)
├── Conversions: 234
└── CPA: $53.21 (-3% vs prev)

By Platform
───────────────────────────────────
Google Ads      $5,200    4.1x ROAS
Meta Ads        $4,100    3.8x ROAS
TikTok Ads      $2,150    2.9x ROAS
LinkedIn Ads    $1,000    2.2x ROAS

Top Campaigns
1. Retargeting - Cart (Meta) - 5.8x ROAS
2. Brand Search (Google) - 5.2x ROAS
3. Product Launch (TikTok) - 4.1x ROAS

Needs Attention
⚠️ Competitor Keywords (Google) - 1.2x ROAS (below target)
⚠️ B2B Webinar (LinkedIn) - 0.8x ROAS (unprofitable)
```

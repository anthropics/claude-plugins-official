---
description: Analyze ad campaign performance across Google Ads, Meta Ads, LinkedIn Ads, or TikTok Ads
argument-hint: [platform] [time_period]
---

# Campaign Performance Analysis

Analyze advertising campaign performance for the user:

1. Ask which platform to analyze if not specified (Google Ads, Meta Ads, LinkedIn Ads, or TikTok Ads)
2. Default to last 30 days if no time period is specified
3. Use the appropriate performance tool for the platform:
   - Google Ads: `get_campaign_performance`
   - Meta Ads: `get_meta_campaign_performance`
   - LinkedIn Ads: `get_linkedin_campaign_performance`
4. Present results in a clear table format with key metrics:
   - Impressions, clicks, CTR
   - Spend, conversions, cost per conversion
   - ROAS where available
5. Highlight top-performing and underperforming campaigns
6. Provide actionable optimization recommendations

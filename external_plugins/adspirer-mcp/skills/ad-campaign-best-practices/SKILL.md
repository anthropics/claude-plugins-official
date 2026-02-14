---
name: ad-campaign-best-practices
description: Best practices for creating and managing ad campaigns across Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads. Use when planning campaigns, setting budgets, choosing targeting, or optimizing performance.
---

When creating ad campaigns with Adspirer MCP, follow these best practices:

## Campaign Creation Workflow

Always follow this order when creating Google Ads campaigns:
1. Research keywords first using `research_keywords` - never skip this step
2. Discover existing assets using `discover_existing_assets` before uploading new ones
3. Validate assets with `validate_and_prepare_assets` before campaign creation
4. Create the campaign with all validated assets and researched keywords

For Meta Ads campaigns:
1. Check connected accounts with `get_connections_status`
2. Use `search_meta_targeting` or `browse_meta_targeting` to find audiences
3. Create the campaign - it will be in PAUSED status for review

For LinkedIn Ads campaigns:
1. Define your professional audience (job titles, industries, company sizes)
2. Choose campaign objective (awareness, consideration, conversions)
3. Set appropriate budget - LinkedIn CPCs are typically higher than other platforms

## Budget Guidelines

- Google Ads Search: minimum $10/day, recommended $50+ for meaningful data
- Google Ads Performance Max: minimum $10/day, recommended $50+ for meaningful data
- Meta Ads: minimum $5/day per ad set, recommended $20+ for optimization
- LinkedIn Ads: minimum $10/day, recommended $50+ due to higher CPCs
- TikTok Ads: minimum $20/day at campaign level

## Safety Rules

- Campaign creation tools create REAL campaigns that cost REAL money
- Always confirm with the user before creating campaigns
- Never retry campaign creation automatically on error - report to user instead
- All campaigns are created in PAUSED status when possible for user review
- Avoid policy-violating keywords (health conditions, financial hardship, political topics)

## Google Ads Specific

- Use `research_keywords` before every Search campaign - do not use generic SEO keywords
- For Performance Max, always discover existing assets first to avoid duplicate uploads
- Add sitelinks and structured snippets to improve ad quality score
- Use `suggest_ad_content` for AI-generated headlines and descriptions

## Multi-Platform Strategy

When users want to advertise across multiple platforms:
- Google Ads for high-intent search traffic (people actively searching)
- Meta Ads for awareness and retargeting (visual, interest-based)
- LinkedIn Ads for B2B targeting (job titles, industries, company sizes)
- TikTok Ads for younger demographics and brand awareness (video-first)

Always check which platforms are connected using `get_connections_status` before suggesting a multi-platform strategy.

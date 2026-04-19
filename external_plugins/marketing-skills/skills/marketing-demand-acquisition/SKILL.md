---
name: marketing-demand-acquisition
description: >
  Multi-channel demand generation, paid media optimization, SEO strategy, and
  partnership programs for Series A+ startups
license: MIT + Commons Clause
metadata:
  version: 1.1.0
  author: borghei
  category: marketing
  domain: demand-generation
  updated: 2025-01
---
# Marketing Demand & Acquisition

Acquisition playbook for Series A+ startups scaling internationally (EU/US/Canada) with hybrid PLG/Sales-Led motion.

## Table of Contents

- [Role Coverage](#role-coverage)
- [Core KPIs](#core-kpis)
- [Demand Generation Framework](#demand-generation-framework)
- [Paid Media Channels](#paid-media-channels)
- [SEO Strategy](#seo-strategy)
- [Partnerships](#partnerships)
- [Attribution](#attribution)
- [Tools](#tools)
- [References](#references)

---

## Role Coverage

| Role | Focus Areas |
|------|-------------|
| Demand Generation Manager | Multi-channel campaigns, pipeline generation |
| Paid Media Marketer | Paid search/social/display optimization |
| SEO Manager | Organic acquisition, technical SEO |
| Partnerships Manager | Co-marketing, channel partnerships |

---

## Core KPIs

**Demand Gen:** MQL/SQL volume, cost per opportunity, marketing-sourced pipeline $, MQL→SQL rate

**Paid Media:** CAC, ROAS, CPL, CPA, channel efficiency ratio

**SEO:** Organic sessions, non-brand traffic %, keyword rankings, technical health score

**Partnerships:** Partner-sourced pipeline $, partner CAC, co-marketing ROI

---

## Demand Generation Framework

### Funnel Stages

| Stage | Tactics | Target |
|-------|---------|--------|
| TOFU | Paid social, display, content syndication, SEO | Brand awareness, traffic |
| MOFU | Paid search, retargeting, gated content, email nurture | MQLs, demo requests |
| BOFU | Brand search, direct outreach, case studies, trials | SQLs, pipeline $ |

### Campaign Planning Workflow

1. Define objective, budget, duration, audience
2. Select channels based on funnel stage
3. Create campaign in HubSpot with proper UTM structure
4. Configure lead scoring and assignment rules
5. Launch with test budget, validate tracking
6. **Validation:** UTM parameters appear in HubSpot contact records

### UTM Structure

```
utm_source={channel}       // linkedin, google, meta
utm_medium={type}          // cpc, display, email
utm_campaign={campaign-id} // q1-2025-linkedin-enterprise
utm_content={variant}      // ad-a, email-1
utm_term={keyword}         // [paid search only]
```

---

## Paid Media Channels

### Channel Selection Matrix

| Channel | Best For | CAC Range | Series A Priority |
|---------|----------|-----------|-------------------|
| LinkedIn Ads | B2B, Enterprise, ABM | $150-400 | High |
| Google Search | High-intent, BOFU | $80-250 | High |
| Google Display | Retargeting | $50-150 | Medium |
| Meta Ads | SMB, visual products | $60-200 | Medium |

### LinkedIn Ads Setup

1. Create campaign group for initiative
2. Structure: Awareness → Consideration → Conversion campaigns
3. Target: Director+, 50-5000 employees, relevant industries
4. Start $50/day per campaign
5. Scale 20% weekly if CAC < target
6. **Validation:** LinkedIn Insight Tag firing on all pages

### Google Ads Setup

1. Prioritize: Brand → Competitor → Solution → Category keywords
2. Structure ad groups with 5-10 tightly themed keywords
3. Create 3 responsive search ads per ad group (15 headlines, 4 descriptions)
4. Maintain negative keyword list (100+)
5. Start Manual CPC, switch to Target CPA after 50+ conversions
6. **Validation:** Conversion tracking firing, search terms reviewed weekly

### Budget Allocation (Series A, $40k/month)

| Channel | Budget | Expected SQLs |
|---------|--------|---------------|
| LinkedIn | $15k | 10 |
| Google Search | $12k | 20 |
| Google Display | $5k | 5 |
| Meta | $5k | 8 |
| Partnerships | $3k | 5 |

See [campaign-templates.md](references/campaign-templates.md) for detailed structures.

---

## SEO Strategy

### Technical Foundation Checklist

- [ ] XML sitemap submitted to Search Console
- [ ] Robots.txt configured correctly
- [ ] HTTPS enabled
- [ ] Page speed >90 mobile
- [ ] Core Web Vitals passing
- [ ] Structured data implemented
- [ ] Canonical tags on all pages
- [ ] Hreflang tags for international
- **Validation:** Run Screaming Frog crawl, zero critical errors

### Keyword Strategy

| Tier | Type | Volume | Priority |
|------|------|--------|----------|
| 1 | High-intent BOFU | 100-1k | First |
| 2 | Solution-aware MOFU | 500-5k | Second |
| 3 | Problem-aware TOFU | 1k-10k | Third |

### On-Page Optimization

1. URL: Include primary keyword, 3-5 words
2. Title tag: Primary keyword + brand (60 chars)
3. Meta description: CTA + value prop (155 chars)
4. H1: Match search intent (one per page)
5. Content: 2000-3000 words for comprehensive topics
6. Internal links: 3-5 relevant pages
7. **Validation:** Google Search Console shows page indexed, no errors

### Link Building Priorities

1. Digital PR (original research, industry reports)
2. Guest posting (DA 40+ sites only)
3. Partner co-marketing (complementary SaaS)
4. Community engagement (Reddit, Quora)

---

## Partnerships

### Partnership Tiers

| Tier | Type | Effort | ROI |
|------|------|--------|-----|
| 1 | Strategic integrations | High | Very high |
| 2 | Affiliate partners | Medium | Medium-high |
| 3 | Customer referrals | Low | Medium |
| 4 | Marketplace listings | Medium | Low-medium |

### Partnership Workflow

1. Identify partners with overlapping ICP, no competition
2. Outreach with specific integration/co-marketing proposal
3. Define success metrics, revenue model, term
4. Create co-branded assets and partner tracking
5. Enable partner sales team with demo training
6. **Validation:** Partner UTM tracking functional, leads routing correctly

### Affiliate Program Setup

1. Select platform (PartnerStack, Impact, Rewardful)
2. Configure commission structure (20-30% recurring)
3. Create affiliate enablement kit (assets, links, content)
4. Recruit through outbound, inbound, events
5. **Validation:** Test affiliate link tracks through to conversion

See [international-playbooks.md](references/international-playbooks.md) for regional tactics.

---

## Attribution

### Model Selection

| Model | Use Case |
|-------|----------|
| First-Touch | Awareness campaigns |
| Last-Touch | Direct response |
| W-Shaped (40-20-40) | Hybrid PLG/Sales (recommended) |

### HubSpot Attribution Setup

1. Navigate to Marketing → Reports → Attribution
2. Select W-Shaped model for hybrid motion
3. Define conversion event (deal created)
4. Set 90-day lookback window
5. **Validation:** Run report for past 90 days, all channels show data

### Weekly Metrics Dashboard

| Metric | Target |
|--------|--------|
| MQLs | Weekly target |
| SQLs | Weekly target |
| MQL→SQL Rate | >15% |
| Blended CAC | <$300 |
| Pipeline Velocity | <60 days |

See [attribution-guide.md](references/attribution-guide.md) for detailed setup.

---

## Tools

### scripts/

| Script | Purpose | Usage |
|--------|---------|-------|
| `calculate_cac.py` | Calculate blended and channel CAC | `python scripts/calculate_cac.py --spend 40000 --customers 50` |

### HubSpot Integration

- Campaign tracking with UTM parameters
- Lead scoring and MQL/SQL workflows
- Attribution reporting (multi-touch)
- Partner lead routing

See [hubspot-workflows.md](references/hubspot-workflows.md) for workflow templates.

---

## References

| File | Content |
|------|---------|
| [hubspot-workflows.md](references/hubspot-workflows.md) | Lead scoring, nurture, assignment workflows |
| [campaign-templates.md](references/campaign-templates.md) | LinkedIn, Google, Meta campaign structures |
| [international-playbooks.md](references/international-playbooks.md) | EU, US, Canada market tactics |
| [attribution-guide.md](references/attribution-guide.md) | Multi-touch attribution, dashboards, A/B testing |

---

## Channel Benchmarks (B2B SaaS Series A)

| Metric | LinkedIn | Google Search | SEO | Email |
|--------|----------|---------------|-----|-------|
| CTR | 0.4-0.9% | 2-5% | 1-3% | 15-25% |
| CVR | 1-3% | 3-7% | 2-5% | 2-5% |
| CAC | $150-400 | $80-250 | $50-150 | $20-80 |
| MQL→SQL | 10-20% | 15-25% | 12-22% | 8-15% |

---

## MQL→SQL Handoff

### SQL Criteria

```
Required:
✅ Job title: Director+ or budget authority
✅ Company size: 50-5000 employees
✅ Budget: $10k+ annual
✅ Timeline: Buying within 90 days
✅ Engagement: Demo requested or high-intent action
```

### SLA

| Handoff | Target |
|---------|--------|
| SDR responds to MQL | 4 hours |
| AE books demo with SQL | 24 hours |
| First demo scheduled | 3 business days |

**Validation:** Test lead through workflow, verify notifications and routing.

## Proactive Triggers

- **Over-relying on one channel** -- Single-channel dependency is a business risk. Diversify acquisition across 3+ channels.
- **No lead scoring** -- Not all leads are equal. Route to revenue-operations for scoring setup.
- **CAC exceeding LTV** -- Demand gen is unprofitable. Optimize or cut underperforming channels.
- **No nurture for non-ready leads** -- 80% of leads aren't ready to buy. Nurture sequences convert them later.

## Related Skills

- **campaign-analytics**: For measuring demand gen effectiveness with attribution and ROI.
- **marketing-strategy-pmm**: For positioning and GTM strategy that feeds demand gen campaigns.
- **social-media-analyzer**: For analyzing social channel performance within demand gen mix.
- **revenue-operations**: For pipeline analysis and forecast accuracy downstream of demand gen.

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| CAC exceeding LTV ratio (below 3:1) | Over-spending on high-cost channels without sufficient conversion optimization | Audit channel-specific CAC against benchmarks. Cut or pause channels with CAC >$400 for B2B SaaS. Shift budget toward lower-CAC channels (SEO, email, organic social). A 3:1 LTV:CAC ratio is the minimum for sustainability; below 2:1 indicates immediate problems |
| LinkedIn Ads delivering low CTR (<0.4%) | Audience too broad, creative fatigue, or wrong ad format | Narrow targeting to Director+ titles at 50-5,000 employee companies. Refresh creative every 2-3 weeks. Test Thought Leader Ads before scaling standard formats -- they deliver 10-20% CTR at premium CPMs, which frequently beats standard LinkedIn ads' 0.5-1% rates |
| Google Ads CPA rising above target | Insufficient conversion data for automated bidding, or keyword competition increasing | Stay on Manual CPC until you have 50+ conversions, then switch to Target CPA. Google Ads CPC increased 164% from 2019-2024. Expand negative keyword list (maintain 100+). Focus on long-tail, high-intent keywords to reduce competition |
| MQL-to-SQL conversion rate below 15% | Lead scoring too loose, or MQL criteria not aligned with sales expectations | Tighten MQL scoring criteria. Require minimum engagement score (demo request or equivalent high-intent action). Align with sales on SQL criteria: Director+ title, 50-5,000 employees, $10k+ budget, buying within 90 days |
| UTM parameters not appearing in HubSpot contact records | Tracking script not firing, form stripping UTM values, or redirect losing parameters | Verify HubSpot tracking code is on all pages. Ensure forms pass hidden UTM fields. Test by clicking a UTM-tagged link and checking the contact record. Use server-side UTM capture if client-side tracking is blocked by privacy tools |
| Partner channel not generating pipeline | Partner enablement insufficient, or wrong partner tier selection | Ensure partners have completed demo training and have access to co-branded assets. Focus on Tier 1 strategic integration partners (high effort, very high ROI) before scaling to Tier 2 affiliates. Set clear success metrics and revenue model before launch |
| Single-channel dependency risk | Over 50% of pipeline from one channel | Diversify acquisition across 3+ channels immediately. Recommended 2026 allocation: AI-enhanced paid search 28-33%, omnichannel social 22-28%, content + experience marketing 20-25%. No single channel should exceed 40% of total pipeline |

---

## Success Criteria

- **Blended CAC**: Target <$300 for B2B SaaS Series A (2026 benchmark). Channel-specific targets: LinkedIn $150-400, Google Search $80-250, SEO/Organic $50-150, Email $20-80. Average B2B SaaS CAC reached $1,200 in 2026 for all segments; self-serve targets $100-500 while enterprise can reach $5,000+
- **CAC Payback Period**: Achieve payback within 6-12 months (2026 median). Elite performers reach payback in under 80 days. Payback exceeding 18 months signals unsustainable unit economics
- **LTV:CAC Ratio**: Maintain minimum 3:1 ratio. Below 2:1 requires immediate intervention. Top-quartile SaaS companies spend $1.10 or less to acquire $1 of new ARR; median spends $2 per $1 ARR
- **MQL-to-SQL Conversion**: Target 15-25% for Google Search, 12-22% for SEO, 10-20% for LinkedIn, 8-15% for email. Overall blended target >15%
- **Pipeline Velocity**: Close marketing-sourced deals within 60 days average. SDR response to MQL within 4 hours, AE demo booking within 24 hours, first demo within 3 business days
- **Channel Diversification**: No single channel should represent more than 40% of pipeline. Maintain active campaigns across minimum 3 channels. LinkedIn generates highest quality B2B leads (40% of marketers cite it as most effective)
- **Marketing Budget Efficiency**: SaaS companies under $10M ARR should spend 20-35% of revenue on marketing; $10-50M spend 18-25%; $50-100M spend 15-20%. For 2026, allocate 18-28% of revenue total with clear channel allocation ratios

---

## Scope & Limitations

**In Scope:**
- Multi-channel demand generation strategy for B2B SaaS (Series A+) with hybrid PLG/sales-led motion
- Paid media channel selection, budget allocation, and CAC calculation (LinkedIn, Google Search, Google Display, Meta)
- SEO strategy including technical foundation, keyword strategy, on-page optimization, and link building priorities
- Partnership program planning (strategic integrations, affiliates, referrals, marketplace listings)
- Attribution model selection (first-touch, last-touch, W-shaped) with HubSpot integration guidance
- UTM structure standards and campaign tracking
- MQL/SQL criteria definition and handoff SLA

**Out of Scope:**
- Campaign creative design (ad copy, images, video production)
- Platform-specific campaign management UI guidance (use LinkedIn Campaign Manager, Google Ads, Meta Ads Manager directly)
- Product-led growth (PLG) product instrumentation (freemium flows, in-app upgrade prompts)
- Sales process optimization beyond MQL-to-SQL handoff (see revenue-operations or sales-success skills)
- Advanced predictive analytics or ML-based lead scoring
- International regulatory compliance for advertising (GDPR consent, CCPA disclosures)
- Brand marketing and awareness campaigns without direct pipeline attribution

**Market Context (2026):**
- CAC is rising 40-60% since 2023 across B2B SaaS
- Google Ads CPC increased 164% from 2019-2024; LinkedIn costs up 89%
- Privacy regulations and cookie deprecation are reducing attribution accuracy
- AI-enhanced bidding strategies (Google Performance Max, LinkedIn Maximize Conversions) are becoming standard

---

## Integration Points

| Integration | Purpose | How to Connect |
|-------------|---------|----------------|
| **HubSpot CRM** | Campaign tracking, lead scoring, MQL/SQL workflows, attribution reporting | Create campaigns with UTM structure (`utm_source={channel}`, `utm_medium={type}`, `utm_campaign={campaign-id}`). Configure W-shaped (40-20-40) attribution model. Set 90-day lookback window. Validate with weekly metrics dashboard |
| **Google Ads** | Paid search campaign management | Structure: Brand > Competitor > Solution > Category keywords. 3 responsive search ads per ad group (15 headlines, 4 descriptions). Start Manual CPC, switch to Target CPA after 50+ conversions. Weekly search term review |
| **LinkedIn Campaign Manager** | B2B paid social campaigns | Structure: Awareness > Consideration > Conversion campaigns. Target Director+, 50-5,000 employees. Start $50/day per campaign. Scale 20% weekly if CAC < target. Verify LinkedIn Insight Tag on all pages. Test Thought Leader Ads for higher CTR |
| **Google Search Console** | SEO performance tracking | Monitor indexing, Core Web Vitals, keyword positions. Target page speed >90 mobile. Submit XML sitemap. Track non-brand traffic percentage as key SEO health metric |
| **campaign-analytics skill** | Attribution modeling and ROI calculation | Export HubSpot journey data as JSON for `attribution_analyzer.py`. Use `campaign_roi_calculator.py` for cross-channel ROI comparison. Feed funnel data into `funnel_analyzer.py` for bottleneck detection |
| **social-media-analyzer skill** | Social channel performance within demand gen mix | Analyze paid social campaign performance with `calculate_metrics.py`. Compare social channel CAC against other acquisition channels |
| **Partner Platforms (PartnerStack, Impact, Rewardful)** | Affiliate and partner program management | Configure 20-30% recurring commission. Create affiliate enablement kit. Set up partner UTM tracking. Test affiliate link tracking through to conversion |

---

## Tool Reference

### calculate_cac.py

**Type:** CLI script (runs with example data or edit inline)

**Usage:**
```bash
python calculate_cac.py
```

**Note:** This script uses hardcoded example data. To analyze your own data, edit the `example_data` list in the script with your channel-specific spend and customer counts.

**Input Format (edit in script):**
```python
example_data = [
    {'channel': 'LinkedIn Ads', 'spend': 15000, 'customers': 10},
    {'channel': 'Google Search', 'spend': 12000, 'customers': 20},
    {'channel': 'SEO/Organic', 'spend': 5000, 'customers': 15},
    {'channel': 'Partnerships', 'spend': 3000, 'customers': 5},
]
```

**Functions:**

| Function | Parameters | Returns |
|----------|-----------|---------|
| `calculate_cac()` | `total_spend: float`, `customers_acquired: int` | Basic CAC as float. Returns 0.0 if customers is 0 |
| `calculate_channel_cac()` | `channel_data: List[Dict]` (each dict: channel, spend, customers) | Dict with per-channel breakdown (spend, customers, cac) plus `blended` key with total_spend, total_customers, blended_cac |
| `print_results()` | `results: Dict` | Prints formatted table to stdout with per-channel and blended CAC |

**Built-in Benchmarks (printed at end of output):**
- LinkedIn Ads: $150-$400
- Google Search: $80-$250
- SEO/Organic: $50-$150
- Partnerships: $100-$300
- Blended Target: <$300

**2026 Context:** These benchmarks reflect Series A B2B SaaS. Overall B2B SaaS CAC has risen to $1,200 average across all segments (up 40-60% since 2023). Self-serve models target $100-500; enterprise segments can exceed $5,000. The median SaaS company spends $2 to acquire $1 of new ARR.

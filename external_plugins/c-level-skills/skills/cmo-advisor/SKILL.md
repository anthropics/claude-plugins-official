---
name: cmo-advisor
description: >
  Marketing leadership advisor for CMOs on brand strategy, demand generation,
  marketing operations, growth marketing, and revenue marketing alignment. Use
  when building a marketing strategy, planning demand-gen campaigns, designing
  lead scoring models, allocating marketing budget, or aligning marketing with
  revenue targets.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: executive-leadership
  updated: 2026-03-31
  tags: [marketing, brand, demand-gen, growth, revenue]
---
# CMO Advisor

The agent acts as a fractional CMO, providing strategic marketing guidance grounded in B2B SaaS benchmarks and proven frameworks.

## Workflow

1. **Gather context** -- Identify company stage, ICP, current ARR, and marketing team size. Validate that at least stage and ICP are defined before proceeding.
2. **Audit current performance** -- Collect funnel metrics (visitors, MQLs, SQLs, pipeline, revenue). Flag any stage where conversion is below the benchmarks in the Channel Performance table.
3. **Define positioning** -- Draft a positioning statement using the template below. Confirm differentiation against the top two competitors.
4. **Build channel plan** -- Select channels from the Channel Performance Framework, allocate budget using the B2B SaaS Budget Allocation split, and set per-channel CAC targets.
5. **Design lead scoring** -- Configure the Lead Scoring Model and set the MQL threshold. Validate that the threshold produces a manageable volume for the sales team.
6. **Create campaign plan** -- Fill in the Campaign Planning Template for the first priority campaign. Include success metrics and required assets.
7. **Establish measurement cadence** -- Set daily, weekly, monthly, and quarterly review rhythms using the Reporting Cadence below.

## Positioning Statement Template

```
For [target customer]
Who [statement of need or opportunity]
[Product name] is a [product category]
That [statement of key benefit]
Unlike [primary competitive alternative]
Our product [statement of primary differentiation]
```

## Marketing Budget Allocation (B2B SaaS Typical)

| Function | % of Budget |
|----------|-------------|
| Demand Generation | 35-45% |
| Content & Brand | 15-20% |
| Marketing Ops & Tech | 15-20% |
| Events & Field | 10-15% |
| People & Overhead | 15-20% |

## Channel Performance Framework

| Channel | CAC | Volume | Quality | Scalability |
|---------|-----|--------|---------|-------------|
| Organic Search | $ | High | Medium | Medium |
| Paid Search | $$ | Medium | High | High |
| Social Organic | $ | Medium | Low | Medium |
| Social Paid | $$ | High | Medium | High |
| Content | $ | High | High | Medium |
| Events | $$$ | Low | High | Low |
| Partnerships | $$ | Medium | High | Medium |

## Lead Scoring Model

| Action | Points |
|--------|--------|
| Website visit | 1 |
| Content download | 5 |
| Email open | 1 |
| Email click | 3 |
| Webinar registration | 10 |
| Webinar attendance | 15 |
| Demo request | 25 |
| Pricing page visit | 10 |

**MQL Threshold**: 50 points

## Lead Stages

Visitor > Known > Engaged > MQL > SAL > SQL > Opportunity > Customer

## Campaign Planning Template

```
CAMPAIGN: [Name]
OBJECTIVE: [Specific goal]
AUDIENCE: [Target segment]
CHANNELS: [Distribution channels]
TIMELINE: [Start - End dates]
BUDGET: [Total investment]

KEY MESSAGES:
- Primary: [Main message]
- Secondary: [Supporting points]

SUCCESS METRICS:
- Leads: [Target]
- Pipeline: [Target]
- Cost per lead: [Target]

ASSETS REQUIRED:
- [ ] Landing page
- [ ] Email sequence
- [ ] Ad creative
- [ ] Content pieces
```

## Messaging Framework

| Audience | Pain Point | Solution | Proof Point |
|----------|------------|----------|-------------|
| Buyer 1 | [Problem] | [How we help] | [Evidence] |
| Buyer 2 | [Problem] | [How we help] | [Evidence] |
| User 1 | [Problem] | [How we help] | [Evidence] |

## Reporting Cadence

- **Daily**: Campaign performance (spend, clicks, conversions)
- **Weekly**: Pipeline and stage-over-stage conversion
- **Monthly**: Full funnel analysis, MQL-to-SQL conversion, CAC trend
- **Quarterly**: Channel ROI review, budget reallocation decisions

## Multi-Touch Attribution Model

| Touch | Weight |
|-------|--------|
| First Touch | 30% |
| Lead Creation | 20% |
| Opportunity Creation | 30% |
| Closed Won | 20% |

## Content Types by Funnel Stage

| Stage | Formats |
|-------|---------|
| Awareness | Blog posts, social content, podcasts, industry reports |
| Consideration | Ebooks/guides, webinars, case studies, comparison guides |
| Decision | Product demos, ROI calculators, testimonials, implementation guides |

## Example: Series-B SaaS Demand-Gen Plan

A Series-B SaaS company ($8M ARR, 12-person marketing team) targeting mid-market DevOps buyers:

```
Budget: $2.4M annual ($200K/mo)
Allocation:
  Demand Gen (40%):  $960K -- Paid search ($300K), LinkedIn Ads ($250K),
                               Content syndication ($200K), Events ($210K)
  Content & Brand (18%): $432K
  Ops & Tech (17%):      $408K
  People (25%):          $600K

Targets:
  MQLs/month: 400  |  SQL conversion: 25%  |  Pipeline/quarter: $6M
  Blended CAC: $18K  |  CAC Payback: 14 months
```

## Marketing Org by Stage

| Stage | Roles |
|-------|-------|
| Series A (5-10) | Head of Marketing, Content/Brand, Demand Gen, Marketing Ops |
| Series B (10-20) | CMO, Director Brand, Director Demand Gen, Manager Content, Manager Ops, ICs |
| Series C+ (20+) | CMO, VP Brand, VP Demand Gen, VP Revenue Marketing, VP Marketing Ops, Specialized teams |

## Scripts

```bash
# Campaign performance analyzer
python scripts/campaign_analyzer.py --campaign Q1-ABM

# Lead scoring calculator
python scripts/lead_scoring.py --leads leads.csv

# Content calendar generator
python scripts/content_calendar.py --pillars topics.yaml

# Attribution reporter
python scripts/attribution.py --period monthly
```

## References

- `references/brand_guidelines.md` -- Brand standards and usage
- `references/demand_gen_playbook.md` -- Campaign execution guide
- `references/content_strategy.md` -- Content planning framework
- `references/martech_stack.md` -- Technology recommendations

---

## Tool Reference

### marketing_roi_calculator.py

Calculates per-channel ROI, blended CAC, Marketing Efficiency Ratio (MER), pipeline contribution, and multi-touch attribution. Produces board-ready marketing performance reports.

```bash
# Run with demo data (6-channel mix)
python scripts/marketing_roi_calculator.py

# From JSON with channel data
python scripts/marketing_roi_calculator.py --input marketing_data.json

# JSON output
python scripts/marketing_roi_calculator.py --json
```

### brand_health_tracker.py

Monitors brand health across 5 dimensions: awareness, perception, differentiation, engagement, and loyalty. Tracks competitive share of voice.

```bash
# Run with demo data
python scripts/brand_health_tracker.py

# From JSON with brand metrics
python scripts/brand_health_tracker.py --input brand_data.json

# JSON output
python scripts/brand_health_tracker.py --json
```

### channel_mix_optimizer.py

Optimizes marketing budget allocation across channels based on ROI, efficiency frontiers, and diminishing returns. Projects impact of reallocation.

```bash
# Run with demo data (ROI optimization)
python scripts/channel_mix_optimizer.py

# Optimize for pipeline
python scripts/channel_mix_optimizer.py --goal pipeline

# Set total budget
python scripts/channel_mix_optimizer.py --budget 800000

# From JSON with channel performance
python scripts/channel_mix_optimizer.py --input channels.json

# JSON output
python scripts/channel_mix_optimizer.py --json
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Blended CAC increasing quarter over quarter | Channel saturation or scaling into less efficient channels | Run channel_mix_optimizer.py; cut lowest-ROI channels; increase investment in highest-ROI |
| Marketing sourced pipeline below 40% of total | Over-reliance on outbound/sales-sourced; marketing underinvesting in demand gen | Shift budget: target 40-60% marketing-sourced pipeline; invest in content + paid channels |
| Brand awareness below 30% in target market | Insufficient top-of-funnel investment; brand treated as afterthought | Allocate 15-20% of budget to brand; measure aided awareness quarterly |
| MQL-to-SQL conversion below 20% | Lead scoring threshold too low or ICP mismatch | Recalibrate MQL threshold; audit scoring model; tighten ICP definition |
| Marketing Efficiency Ratio (MER) below 1.0x | Spending more on marketing than generating in new ARR | Audit channel mix; pause negative-ROI channels; focus on proven converters |
| No brand tracking in place | Half of B2B SaaS companies don't track brand at all | Implement quarterly brand health survey using brand_health_tracker.py framework |

---

## Success Criteria

- Marketing Efficiency Ratio (MER) above 1.5x -- every $1 of marketing generates $1.50+ in new ARR
- Blended CAC below target for company stage (Series A: $15K, Series B: $25K, Series C: $35K)
- Pipeline coverage at 3-4x of quarterly new ARR target (measured monthly)
- Marketing-sourced pipeline contribution above 40% of total pipeline
- CAC payback under 18 months (under 12 months for top-quartile performance)
- Brand health score improving quarter-over-quarter (tracked via brand_health_tracker.py)
- Channel mix optimization reviewed quarterly with budget reallocation acting on data

---

## Scope & Limitations

**In Scope**: Marketing ROI calculation, channel performance analysis, brand health tracking, lead scoring, campaign planning, budget allocation optimization, multi-touch attribution, competitive share of voice.

**Out of Scope**: Content creation, creative design, social media posting, email campaign execution, event logistics, PR execution, website development.

**Limitations**: Marketing ROI calculator uses provided attribution data -- accuracy depends on attribution model quality. Brand health tracker relies on survey data which may have sampling bias. Channel mix optimizer uses historical performance with diminishing returns modeling -- future performance may differ due to market changes. MER calculation requires accurate new ARR attribution which many companies struggle to measure precisely.

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `cro-advisor` | Pipeline contribution alignment; marketing-sourced vs sales-sourced targets |
| `cfo-advisor` | Marketing budget as % of revenue; CAC payback for unit economics |
| `ceo-advisor` | Brand positioning alignment with company vision |
| `cpo-advisor` | Product marketing alignment; feature launch campaigns |
| `board-deck-builder` | Growth/marketing section with CAC, pipeline, channel performance |
| `chief-of-staff` | Routes market strategy and brand questions |
| `competitive-intel` | Competitive positioning; share of voice vs competitors |

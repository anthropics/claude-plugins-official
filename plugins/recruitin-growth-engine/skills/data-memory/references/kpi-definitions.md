# KPI Definitions for Recruitin Growth Engine

## Primary KPIs (Decision Metrics)

### Cost Per Hire (CPH)
- **Definition:** Total campaign spend divided by the number of confirmed hires
- **Formula:** `spend / hires`
- **Target:** < €500 for standard roles, < €1000 for specialist/senior roles
- **Frequency:** Calculated per campaign lifetime, tracked weekly
- **Priority:** Highest - this is the north star metric for performance campaigns

### Quality Score
- **Definition:** Ratio of qualified applications to total applications
- **Formula:** `qualified_applications / applications`
- **Target:** > 60%
- **What "qualified" means:** Applicant meets minimum requirements (experience, education, location, availability)
- **Priority:** High - prevents optimizing for volume at the expense of quality

### Cost Per Qualified Application (CPQA)
- **Definition:** Total spend divided by qualified applications only
- **Formula:** `spend / qualified_applications`
- **Target:** < €40
- **Priority:** High - more actionable than CPH for ongoing optimization

## Secondary KPIs (Optimization Metrics)

### Click-Through Rate (CTR)
- **Definition:** Percentage of people who clicked after seeing the ad
- **Formula:** `clicks / impressions`
- **Benchmarks by channel:**
  - Meta Ads: > 1.2% (good), > 2.0% (excellent)
  - LinkedIn Ads: > 0.5% (good), > 0.8% (excellent)
  - LinkedIn Organic: > 3% engagement rate (good)
- **Usage:** Indicates creative/copy effectiveness

### Cost Per Click (CPC)
- **Definition:** Average cost for each click
- **Formula:** `spend / clicks`
- **Benchmarks:**
  - Meta Ads: < €2.50
  - LinkedIn Ads: < €6.00
- **Usage:** Indicates audience targeting efficiency

### Cost Per Application (CPA)
- **Definition:** Total spend per application received
- **Formula:** `spend / applications`
- **Target:** < €25 for volume roles, < €75 for specialist roles
- **Usage:** Landing page and funnel effectiveness

### Conversion Rate (Application Rate)
- **Definition:** Percentage of clickers who complete an application
- **Formula:** `applications / clicks`
- **Target:** > 3%
- **Usage:** Landing page optimization indicator

## Engagement KPIs (Authority Campaigns)

### LinkedIn Engagement Rate
- **Definition:** Total reactions + comments + shares divided by impressions
- **Formula:** `(reactions + comments + shares) / impressions`
- **Target:** > 3% (good), > 5% (excellent)
- **Not tracked in weekly_metrics** - manually reported in notes field

### Newsletter Open Rate
- **Target:** > 40%
- **Tracked externally** in LinkedIn newsletter analytics

### Follower Growth Rate
- **Definition:** New followers per week attributed to content
- **Target:** > 2% weekly growth

## Composite Scores

### Campaign Health Score
A weighted composite for quick campaign assessment:

```
health_score = (
  (ctr_score * 0.20) +
  (quality_score * 0.30) +
  (cpa_score * 0.25) +
  (budget_efficiency * 0.25)
)

Where:
  ctr_score = min(actual_ctr / target_ctr, 1.0)
  quality_score = min(actual_quality / 0.6, 1.0)
  cpa_score = min(target_cpa / actual_cpa, 1.0)
  budget_efficiency = 1.0 - abs(actual_spend - planned_spend) / planned_spend
```

| Score | Rating | Action |
|-------|--------|--------|
| 0.8 - 1.0 | Excellent | Scale budget, replicate strategy |
| 0.6 - 0.8 | Good | Minor tweaks, continue |
| 0.4 - 0.6 | Needs attention | Review underperforming metrics |
| 0.0 - 0.4 | Critical | Pause and restructure |

### Industry Benchmarks (Netherlands Recruitment)

| Role Category | Avg CPH | Avg CPA | Avg CTR (Meta) | Avg Quality Score |
|--------------|---------|---------|----------------|-------------------|
| IT / Tech | €600-900 | €30-50 | 1.0-1.5% | 50-65% |
| Sales / Commercial | €300-500 | €15-25 | 1.5-2.5% | 55-70% |
| Operations / Logistics | €200-400 | €10-20 | 1.8-3.0% | 60-75% |
| Healthcare | €400-700 | €20-35 | 0.8-1.2% | 45-60% |
| Finance / Admin | €250-450 | €12-22 | 1.2-2.0% | 60-75% |
| Engineering | €500-800 | €25-45 | 0.8-1.5% | 50-65% |
| Executive / Management | €800-1500 | €50-100 | 0.5-1.0% | 40-55% |

These benchmarks serve as initial targets before the engine has enough historical data to generate its own baselines.

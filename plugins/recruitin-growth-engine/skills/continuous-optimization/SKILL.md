---
name: continuous-optimization
description: This skill should be used when the user wants to "optimize a campaign", "find the winning strategy", "improve campaign performance", "reduce cost per hire", "analyze what works best", "run the optimization cycle", "determine best performing content", "compare campaign strategies", or needs guidance on A/B test analysis, strategy selection based on historical data, or continuous improvement of recruitment marketing campaigns.
version: 0.1.0
---

# Continuous Optimization for Recruitin Growth Engine

The Continuous Optimization skill closes the feedback loop of the Growth Engine. Before generating any new campaign content, it queries historical performance data to determine the most effective strategy for the given context.

## The Optimization Cycle

```
┌─────────────────────┐
│  New Campaign Brief  │
│  (client + vacancy)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Query Historical    │
│  Performance Data    │
│  (Supabase)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Determine Winning   │
│  Strategy            │
│  (tone + format +    │
│   channel + budget)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Generate Content    │
│  Using Strategy      │
│  (Campaign Skill)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Deploy + Monitor    │
│  (Weekly Metrics)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Analyze Results     │
│  Update Database     │
│  (Data Memory Skill) │
└──────────┬──────────┘
           │
           └──────→ [Back to top for next campaign]
```

## Winning Strategy Determination

When a new campaign request comes in, execute this decision process:

### Step 1: Context Matching

Identify the closest historical matches by querying these dimensions in order of priority:

1. **Exact match:** Same client + same role type + same channel
2. **Industry match:** Same industry + same role category + any channel
3. **Role match:** Any industry + same role category + same channel
4. **General:** Overall best performers across all dimensions

```sql
-- Priority 1: Exact match
SELECT * FROM winning_strategies
WHERE industry = :target_industry
  AND target_role_category = :target_role
  AND confidence IN ('high', 'medium');

-- Priority 2: Industry match (if no exact match)
SELECT * FROM winning_strategies
WHERE industry = :target_industry
  AND confidence IN ('high', 'medium');

-- Priority 3: Role match (if no industry match)
SELECT * FROM winning_strategies
WHERE target_role_category = :target_role;

-- Priority 4: General best (fallback)
SELECT * FROM winning_strategies
ORDER BY avg_cph ASC
LIMIT 5;
```

### Step 2: Strategy Composition

Based on the historical data, compose a recommended strategy:

```
Recommended Strategy:
├── Tone of Voice: [from winning_strategies.best_tone]
├── Content Type: [from winning_strategies.best_content_type]
├── Primary Channel: [from winning_strategies.best_channel]
├── Budget Allocation: [derived from historical spend/performance ratio]
├── Confidence Level: [high/medium/low based on sample_size]
└── Exploration Recommendation: [see exploration vs exploitation below]
```

### Step 3: Exploration vs. Exploitation

Balance known winners with testing new approaches:

| Confidence Level | Exploitation % | Exploration % | Strategy |
|-----------------|---------------|---------------|----------|
| High (>10 campaigns) | 80% | 20% | Run winning strategy on 80% budget, test 1 new variant on 20% |
| Medium (5-10) | 60% | 40% | Run best-known on 60%, test 2 variants on 40% |
| Low (<5) | 40% | 60% | Test 3 variants with equal budget split |
| No data | 0% | 100% | Use industry benchmarks, run 3 variants equally |

## Optimization Dimensions

### Dimension 1: Tone of Voice

Track performance across these tone categories:

| Tone | Description | Best For |
|------|-------------|----------|
| formal | Professional, structured, corporate language | Executive/finance roles, traditional industries |
| semi-formal | Approachable but professional, industry terms allowed | Most roles, default choice |
| informal | Conversational, energetic, direct address | Junior roles, creative industries, startups |
| bold | Contrarian, provocative, opinion-driven | Authority content, brand differentiation |
| empathetic | Understanding pain points, supportive language | Healthcare, education, career changers |

### Dimension 2: Content Type

| Type | Platform | Typical CTR Range | Best For |
|------|----------|------------------|----------|
| Single image | Meta + LinkedIn | 1.0-2.5% | Quick testing, broad reach |
| Carousel | Meta + LinkedIn | 1.2-3.0% | Story-telling, culture showcase |
| Video (short) | Meta Reels/Stories | 1.5-4.0% | High engagement, younger audiences |
| Text-only | LinkedIn | 2.0-5.0% | Authority content, thought leadership |
| Lead form | Meta | 0.8-1.5% | Passive candidates, lower friction |

### Dimension 3: Budget Distribution

Optimize budget allocation based on historical channel performance:

```
Channel Score = (1 / avg_cph) * quality_score * confidence_weight

Recommended Split:
  Meta % = meta_score / (meta_score + linkedin_score) * 100
  LinkedIn % = linkedin_score / (meta_score + linkedin_score) * 100
```

## Weekly Optimization Report

Generate this analysis every week for all active campaigns:

### Report Structure

```markdown
# Weekly Optimization Report - Week [N], [Year]

## Executive Summary
- Total active campaigns: [N]
- Total spend this week: €[X]
- Total hires this week: [N]
- Average CPH this week: €[X] (vs €[X] last week, [+/-X%])

## Campaign Performance Matrix

| Campaign | Client | CTR | CPA | CPH | Health Score | Action |
|----------|--------|-----|-----|-----|-------------|--------|
| [name]   | [client]| [%] | €[X]| €[X]| [0-1]      | [action]|

## Top Performing Combinations This Week
1. [Tone] + [Content Type] on [Channel] → CPH: €[X]
2. [Tone] + [Content Type] on [Channel] → CPH: €[X]
3. [Tone] + [Content Type] on [Channel] → CPH: €[X]

## Underperformers (Action Required)
- [Campaign name]: [Issue description] → Recommendation: [Action]

## Strategy Updates
- Winning strategies view refreshed: [N] entries updated
- New high-confidence strategies discovered: [list]
- Strategies downgraded due to recent underperformance: [list]

## Recommendations for Next Week
1. [Specific action for specific campaign]
2. [Budget reallocation suggestion]
3. [New test to run]
```

## Feedback Loop Integration

### Content Generation Feedback

After the optimization skill determines the winning strategy, pass it to the campaign-strategy skill:

```json
{
  "optimization_context": {
    "recommended_tone": "semi-formal",
    "recommended_content_type": "carousel",
    "recommended_channel": "meta",
    "budget_split": {"meta": 70, "linkedin": 30},
    "confidence": "high",
    "exploration_variant": {
      "test_tone": "bold",
      "test_content_type": "video",
      "budget_percentage": 20
    },
    "historical_benchmarks": {
      "expected_ctr": 1.8,
      "expected_cpa": 18.50,
      "expected_cph": 370.00
    },
    "avoid_strategies": [
      {"tone": "formal", "reason": "Consistently underperforms for this industry (-40% vs average)"}
    ]
  }
}
```

### Learning Rate

The engine adjusts its confidence in strategies over time:

- **New data weighs more than old data:** Apply a time decay factor (recent 4 weeks = 1.0x, 5-8 weeks = 0.8x, 9-12 weeks = 0.6x, 13+ weeks = 0.4x)
- **Outlier handling:** Exclude campaigns with <€100 total spend from strategy calculations
- **Minimum sample size:** Require at least 3 campaigns before forming a strategy recommendation
- **Recalculation frequency:** Refresh winning_strategies materialized view every Monday after weekly import

# A/B Testing Framework for Recruitment Campaigns

## Testing Principles

1. **Test one variable at a time** - Isolate the effect of each change
2. **Sufficient sample size** - Minimum 1000 impressions per variant before concluding
3. **Statistical significance** - Wait for 95% confidence before declaring a winner
4. **Time controls** - Run variants simultaneously, never sequentially
5. **Document everything** - Log all tests and results in the content_log table

## Test Priority Matrix

Test variables in this order for maximum learning efficiency:

| Priority | Variable | Expected Impact | Minimum Test Budget |
|----------|----------|----------------|-------------------|
| 1 | Ad Creative (image vs video vs carousel) | High | €100 per variant |
| 2 | Primary Text (benefit vs pain-point vs social proof) | High | €75 per variant |
| 3 | Audience Targeting (direct vs lookalike vs interest) | Medium-High | €150 per variant |
| 4 | Call-to-Action (direct apply vs learn more vs lead form) | Medium | €75 per variant |
| 5 | Landing Page (direct job page vs culture page vs lead form) | Medium | €100 per variant |
| 6 | Posting Time (morning vs midday vs evening) | Low-Medium | €50 per variant |
| 7 | Hashtags/Keywords | Low | €50 per variant |

## Statistical Significance Calculator

Use this simplified approach for recruitment campaigns where sample sizes are typically small:

### For CTR Comparison

```
Required sample per variant:
  n = (Z² × p × (1-p)) / E²

Where:
  Z = 1.96 (for 95% confidence)
  p = expected CTR (use 0.015 as default)
  E = minimum detectable effect (use 0.005)

  n = (1.96² × 0.015 × 0.985) / 0.005²
  n ≈ 2,263 impressions per variant
```

### For Conversion Rate Comparison

```
With typical conversion rates of 3%:
  n = (1.96² × 0.03 × 0.97) / 0.01²
  n ≈ 1,118 clicks per variant

Note: This requires significant budget. For smaller budgets,
use directional data with 80% confidence (Z = 1.28):
  n ≈ 477 clicks per variant
```

### Quick Decision Rules

When statistical significance is impractical due to budget:

| Scenario | Decision Rule |
|----------|--------------|
| Budget < €200 total | Run 2 variants, choose winner after €100 each based on directional CPA |
| Budget €200-500 | Run 3 variants, kill worst after €100 each, run remaining 2 equally |
| Budget €500-1000 | Proper A/B: 2 variants, wait for 1000 impressions each minimum |
| Budget > €1000 | Full testing protocol with statistical significance |

## Test Documentation Template

Log each test in the following format for the content_log and add a structured note to weekly_metrics:

```json
{
  "test_id": "TEST-[YYYY]-[WW]-[sequential]",
  "campaign_id": "uuid",
  "hypothesis": "Informal tone will reduce CPA by >15% compared to formal tone for junior developer roles",
  "variable_tested": "tone_of_voice",
  "control": {
    "description": "Formal tone ad copy",
    "content_log_id": "uuid"
  },
  "variant": {
    "description": "Informal tone ad copy",
    "content_log_id": "uuid"
  },
  "start_date": "2026-02-10",
  "end_date": "2026-02-24",
  "budget_per_variant": 150.00,
  "success_metric": "cpa",
  "minimum_sample": 1000,
  "results": {
    "control_impressions": null,
    "control_metric": null,
    "variant_impressions": null,
    "variant_metric": null,
    "winner": null,
    "confidence": null,
    "learning": null
  }
}
```

## Interpreting Results

### When Control Wins
- Reinforce the current strategy
- Increase confidence score for the winning approach
- Log the failed variant to avoid retesting the same hypothesis

### When Variant Wins
- Gradually shift budget: 70% → variant, 30% → new test
- Update winning_strategies materialized view
- Design next test building on the winning variant

### When Results Are Inconclusive
- Extend test duration by 1 week if budget allows
- If still inconclusive, choose the variant with better quality score (not just CPA)
- Log as "inconclusive" and revisit with larger budget in future campaign

## Cross-Campaign Learnings

After every completed test, update the collective intelligence:

1. Add result to the `content_log` with test metadata
2. Refresh `winning_strategies` materialized view
3. Check if the result contradicts any existing high-confidence strategy
4. If a strategy is contradicted by 2+ tests, downgrade its confidence level
5. Generate a "learning summary" for inclusion in the weekly optimization report

---
description: Run the optimization cycle to determine winning strategies and improve campaigns
argument-hint: [campaign-id or "all"]
---

# Recruitin Optimization Cycle

You are running the optimization cycle for the Recruitin Growth Intelligence Engine. This process analyzes historical data, determines winning strategies, and generates improvement recommendations.

## Optimization Target

Based on: $ARGUMENTS

If "all" or no argument: optimize all active campaigns.
If a specific campaign ID or name: focus on that campaign.

## Step 1: Data Audit

Launch the **data-analyst** agent to verify:
1. All active campaigns have up-to-date weekly metrics
2. No missing data points for the past 4 weeks
3. The winning_strategies view is current

If data is missing, prompt the user to import before continuing.

## Step 2: Strategy Analysis

Launch the **optimization-engine** agent to:

### For Each Active Campaign:
1. Score the current strategy against historical performance
2. Compare with alternative strategies in the same context
3. Identify if the campaign is in exploitation or exploration phase
4. Calculate the strategy's confidence level

### Cross-Campaign Analysis:
1. Which strategies are consistently winning across campaigns?
2. Which strategies are declining in effectiveness?
3. Are there untested strategy combinations that look promising?
4. Are there seasonal patterns emerging?

## Step 3: Generate Optimization Plan

For each campaign, produce:

```
Campaign: [Name]
Current Strategy: [tone + format + channel]
Current Performance: CPH €[X], CTR [X]%, Quality [X]%
Health Score: [0-1]

Diagnosis: [What's working / what's not]

Recommended Changes:
1. [Change 1 with expected impact]
2. [Change 2 with expected impact]
3. [Change 3 with expected impact]

New Test Proposal:
- Variable: [what to test]
- Hypothesis: [expected outcome]
- Budget allocation: [amount for test]
- Duration: [weeks]
- Success criteria: [metric and target]
```

## Step 4: Budget Reallocation

Based on the analysis, recommend budget shifts:

```
Current Allocation:
  Campaign A: €[X]/week → [performing well/poorly]
  Campaign B: €[X]/week → [performing well/poorly]

Recommended Reallocation:
  Campaign A: €[X]/week (+/-€[X]) — Reason: [why]
  Campaign B: €[X]/week (+/-€[X]) — Reason: [why]

Expected Impact:
  Projected total CPH change: [direction and magnitude]
  Projected additional hires: [number] over [timeframe]
```

## Step 5: Update & Track

After the optimization plan is approved:
1. Update campaign strategies in Supabase
2. Refresh the winning_strategies materialized view
3. Set up tracking for the new tests
4. Schedule the next optimization review (1 week)
5. Log the optimization decisions for future reference

## Step 6: Summary

Present a clear, concise summary:
- What changed and why
- Expected impact on overall performance
- Key metrics to watch next week
- Any manual actions required (budget changes in Meta/LinkedIn ad managers)

---
description: Create a new recruitment marketing campaign (authority or performance)
argument-hint: <campaign-type> [client-name] [vacancy-description]
---

# Recruitin Campaign Creator

You are helping create a new recruitment marketing campaign using the Recruitin Growth Intelligence Engine. Follow this systematic approach to produce a complete, data-informed campaign package.

## Step 1: Determine Campaign Type

Based on: $ARGUMENTS

If no arguments provided, ask:
- **Authority campaign** (for Recruitin's own LinkedIn presence)?
- **Performance campaign** (for a client vacancy)?

## Step 2: Gather Requirements

### For Authority Campaigns:
1. What week are we in the 12-week cycle? (1-12, or start fresh)
2. Any specific topic or theme to cover?
3. Which content formats this week? (post, article, carousel, newsletter)

### For Performance Campaigns:
1. Client name and industry
2. Vacancy details: role title, location, salary indication, key requirements
3. Company culture highlights (3-5 unique selling points)
4. Budget and duration
5. Target audience specifics (if beyond standard ICP)

## Step 3: Consult Historical Data

Before generating content:
1. Launch the **optimization-engine** agent to query Supabase for winning strategies
2. Review the recommendation: best tone, content type, channel allocation
3. Determine the exploration/exploitation split

## Step 4: Generate Content Package

Launch the **campaign-planner** agent with the gathered context and optimization recommendation.

For **authority campaigns**, produce:
- 2 LinkedIn posts with visual prompts
- 1 article/newsletter outline (if applicable for this week)
- Engagement strategy for the week
- Content calendar with posting times

For **performance campaigns**, produce:
- 3 ad variants (benefit-led, pain-point-led, social proof)
- Each variant with Meta Ad copy + LinkedIn version
- Visual prompt per variant per platform
- Budget allocation recommendation
- A/B testing plan
- Landing page recommendations

## Step 5: Quality Review

Before presenting the final package:
- Verify tone-of-voice consistency
- Check all visual prompts are complete
- Confirm Dutch language quality
- Validate that optimization recommendations are reflected
- Ensure all CTAs are specific and actionable

## Step 6: Log and Track

After approval:
1. Log the generated content to Supabase `content_log` table
2. Create the campaign entry in the `campaigns` table
3. Set up the weekly tracking cadence
4. Schedule the first optimization review

Present everything in a clean, copy-paste-ready format.

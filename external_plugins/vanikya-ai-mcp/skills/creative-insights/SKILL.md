---
name: creative-insights
description: Use this skill when the user asks for creative or visual analysis of images, branding feedback, visual critique, creative scores, design quality assessment, batch analysis of multiple images for creative insights, ad creative analysis, marketing image review, or product photo feedback.
version: 1.0.0
---

# Vanikya Creative Insights

Get AI-powered creative and visual analysis of images using Vanikya's creative insights tools.

## Cost

Each creative insight costs **0.75 credits**. Always inform the user of this cost before running analysis.

## Available Tools

| Tool | Purpose |
|---|---|
| `creative_insights_create` | Analyze a single image for creative insights |
| `creative_insights_batch_create` | Analyze multiple images at once |
| `creative_insights_batch_status` | Poll the status of a batch job |
| `creative_insights_get` | Get a specific insight result by ID |
| `creative_insights_list` | List past creative insights |
| `creative_insights_delete` | Delete an insight |

## Workflow — Single Image

1. **Inform the user** of the 0.75 credit cost and confirm.
2. **Run analysis:**
   ```
   creative_insights_create({ image_url: "<url>" })
   ```
   The `image_url` must be a publicly accessible URL. To use a Vanikya generation, first call `imagine_get_generation({ id: "<id>" })` and use the returned image URL from the result.
3. **Poll until complete**. Stop after 5 retries:
   ```
   creative_insights_get({ id: "<insight_id>" })
   ```
   Repeat until `status` is `"completed"` or `"failed"`.
4. Present the creative analysis to the user.

## Workflow — Multiple Images

1. **Inform the user** of the total cost (0.75 credits × number of images) and confirm.
2. **Start batch:**
   ```
   creative_insights_batch_create({ image_urls: ["<url1>", "<url2>", ...] })
   ```
3. **Poll batch status:**
   ```
   creative_insights_batch_status({ batch_id: "<batch_id>" })
   ```
4. Once complete, retrieve individual results with `creative_insights_get`.

## Browsing Past Insights

```
creative_insights_list({ limit: 10, offset: 0 })
```

## Deleting an Insight

Only delete when the user explicitly requests it:
```
creative_insights_delete({ id: "<insight_id>" })
```

Always confirm with the user before deleting — deletions are permanent.

## Rules

- **Always** inform the user of the credit cost (0.75 per image) and get confirmation before running.
- For batch jobs, poll `creative_insights_batch_status` until status is `"completed"` or `"failed"`.
- Present insights in a structured format — highlight key creative strengths and improvement areas.

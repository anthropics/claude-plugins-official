---
name: seo-analysis
description: Use this skill when the user asks to analyze SEO of a URL or website, run an SEO audit, get SEO insights or recommendations, check a page's search engine optimization, batch-analyze multiple URLs for SEO, or compare the SEO of multiple pages.
version: 1.0.0
---

# Vanikya SEO Analysis

Analyze web pages for SEO quality using Vanikya's AI-powered SEO analysis tools.

## Available Tools

| Tool | Purpose |
|---|---|
| `seo_analysis_create` | Run SEO analysis on a single URL |
| `seo_analysis_batch_create` | Run SEO analysis on multiple URLs at once |
| `seo_analysis_batch_status` | Poll the status of a batch job |
| `seo_analysis_get` | Get a specific analysis result by ID |
| `seo_analysis_list` | List past SEO analyses |
| `seo_analysis_delete` | Delete an analysis |

## Workflow — Single URL

1. **Start analysis:**
   ```
   seo_analysis_create({ url: "<url>" })
   ```
2. **Poll status** until `status` is `"completed"` or `"failed"`. Stop after 5 retries:
   ```
   seo_analysis_get({ id: "<analysis_id>" })
   ```
3. Present the results to the user.

## Workflow — Multiple URLs

1. **Start batch:**
   ```
   seo_analysis_batch_create({ urls: ["<url1>", "<url2>", ...] })
   ```
2. **Poll batch status:**
   ```
   seo_analysis_batch_status({ batch_id: "<batch_id>" })
   ```
3. Once complete, retrieve individual results with `seo_analysis_get` for each ID in the batch.

## Browsing Past Analyses

```
seo_analysis_list({ limit: 10, offset: 0 })
```

Returns the user's past analyses. Use `seo_analysis_get` to fetch full results for any entry.

## Deleting an Analysis

Only delete when the user explicitly requests it:
```
seo_analysis_delete({ id: "<analysis_id>" })
```

Always confirm with the user before deleting — deletions are permanent.

## Rules

- Always confirm the URL with the user before running analysis.
- For batch jobs, poll `seo_analysis_batch_status` until status is `"completed"` or `"failed"` before fetching results.
- Present results in a structured, readable format — highlight critical issues first.

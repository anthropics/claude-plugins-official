---
description: Start comprehensive website crawling job with sitemap support
argument-hint: <url> [depth] [max-pages]
allowed-tools: []
---

# Crawl Command

Initiate comprehensive website crawling with sitemap support. Supports both AI extraction mode and markdown conversion mode.

## Usage

```
/crawl <url> [depth] [max-pages]
```

## Arguments

- **url** (required): Starting URL for crawling
- **depth** (optional): Maximum crawl depth from starting URL (default: 1)
- **max-pages** (optional): Maximum number of pages to crawl (default: 20)

## Examples

```
/crawl https://example.com 2 50
/crawl https://docs.example.com 3 100
```

## Features

- Comprehensive website crawling
- Sitemap support
- AI extraction or markdown conversion modes
- Depth and page limits
- JavaScript rendering support
- Custom crawl rules

## Options

- `extraction_mode`: Use AI extraction (true) or markdown conversion (false)
- `sitemap`: Use sitemap for crawling (default: false)
- `render_heavy_js`: Enable heavy JavaScript rendering
- `stealth`: Enable stealth mode
- `prompt`: Extraction prompt (required if extraction_mode is true)
- `schema`: Output schema for extraction
- `rules`: Crawl rules (exclude patterns, same_domain)

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Returns task_id for async operations
- Check status with: `GET /crawl/{task_id}`
- Use for large-scale website crawling
- More cost-effective than individual scraping requests


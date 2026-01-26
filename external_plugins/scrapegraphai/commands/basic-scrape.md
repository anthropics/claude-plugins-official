---
description: Basic web scraping to get raw HTML content from a website
argument-hint: <url>
allowed-tools: []
---

# Basic Scrape Command

Simple web scraping endpoint that fetches raw HTML content from a website without LLM processing.

## Usage

```
/basic-scrape <url>
```

## Arguments

- **url** (required): The website URL to scrape

## Examples

```
/basic-scrape https://example.com
/basic-scrape https://news.example.com/article
```

## Features

- Fast HTML retrieval
- No LLM processing overhead
- Supports JavaScript rendering
- Stealth mode available
- Mock mode for testing

## Options

- `render_heavy_js`: Enable full JavaScript rendering for SPAs
- `stealth`: Enable stealth mode to avoid bot detection
- `mock`: Return mock data for testing

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Costs 1 credit per page (most cost-effective)
- Returns raw HTML content
- Use this for simple HTML extraction without AI processing



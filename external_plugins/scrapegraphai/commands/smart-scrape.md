---
description: Scrape and extract structured data from a website using AI
argument-hint: <url> [prompt]
allowed-tools: []
---

# Smart Scrape Command

Scrape a website and extract structured data using ScrapeGraphAI's LLM-powered extraction.

## Usage

```
/smart-scrape <url> [extraction-prompt]
```

## Arguments

- **url** (required): The website URL to scrape
- **extraction-prompt** (optional): Natural language description of what to extract. If not provided, you'll be prompted.

## Examples

```
/smart-scrape https://example.com/product "Extract product name, price, and description"
/smart-scrape https://news.example.com/article "Extract headline, author, date, and article content"
```

## Features

- LLM-powered content extraction
- Supports custom output schemas
- Handles JavaScript-heavy sites
- Infinite scrolling support
- Pagination support
- Stealth mode available

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Costs 10 credits per page
- Returns async request ID - check status with the request ID if needed


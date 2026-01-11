---
description: Convert a webpage to clean Markdown format
argument-hint: <url>
allowed-tools: []
---

# Markdownify Command

Convert a webpage to clean, readable Markdown format using ScrapeGraphAI.

## Usage

```
/markdownify <url>
```

## Arguments

- **url** (required): The website URL to convert to Markdown

## Examples

```
/markdownify https://example.com/article
/markdownify https://docs.example.com/getting-started
```

## Features

- Clean Markdown conversion
- Preserves structure and formatting
- Handles complex HTML layouts
- Supports JavaScript-heavy sites
- Stealth mode available

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Costs 2 credits per page
- Returns async request ID - check status with the request ID if needed


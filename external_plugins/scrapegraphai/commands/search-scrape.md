---
description: Search the web and scrape multiple websites with AI extraction
argument-hint: <query> [num-results]
allowed-tools: []
---

# Search Scrape Command

Search the web and scrape content from multiple websites using ScrapeGraphAI's search scraper.

## Usage

```
/search-scrape <query> [num-results]
```

## Arguments

- **query** (required): Search query and extraction instructions (e.g., "Find latest AI news and extract headlines and summaries")
- **num-results** (optional): Number of websites to scrape (3-20, default: 3)

## Examples

```
/search-scrape "Find latest Python tutorials and extract title, description, and difficulty level" 5
/search-scrape "Get current cryptocurrency prices for top 10 coins" 10
```

## Features

- Multi-site scraping from search results
- AI-powered structured extraction
- Markdown conversion mode available
- Automatic query refinement
- Results merging from multiple sources

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Costs 10 credits per website (AI extraction mode)
- Costs 2 credits per website (markdown mode)
- Returns async request ID - check status with the request ID if needed


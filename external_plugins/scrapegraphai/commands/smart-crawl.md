---
description: Intelligent website crawling with AI-powered content extraction
argument-hint: <url> <queries...>
allowed-tools: []
---

# Smart Crawl Command

Initiate intelligent website crawling with AI-powered content extraction or markdown conversion. Supports custom queries and batch processing.

## Usage

```
/smart-crawl <url> <query1> [query2] [query3]...
```

## Arguments

- **url** (required): Starting URL for crawling
- **queries** (required, 1-50): List of queries to answer during crawling

## Examples

```
/smart-crawl https://docs.example.com "What are the main API endpoints?" "What authentication methods are supported?"
/smart-crawl https://blog.example.com "What are the latest posts?" "Who are the authors?"
```

## Features

- Intelligent website crawling
- AI extraction or markdown conversion modes
- Custom queries for targeted extraction
- Batch processing
- Session management
- Stealth mode available

## Options

- `extraction_mode`: Use AI extraction (true) or markdown conversion (false)
- `cache_website`: Cache website content (default: true)
- `stealth`: Enable stealth mode to avoid bot detection

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Returns session_id for async operations
- Check status with: `GET /smartcrawler/{session_id}`
- Supports up to 50 queries per session
- Use for comprehensive website analysis



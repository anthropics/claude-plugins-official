---
description: Discover all URLs on a website
allowed-tools: firecrawl_map
---

# Map Website URLs

Use the Firecrawl map tool to discover all accessible URLs on a website.

## When mapping:

1. Take the starting URL from the user
2. Use the `firecrawl_map` tool to discover all pages
3. Present the URL structure in an organized way (by section, type, or hierarchy)
4. Offer to crawl or scrape specific discovered pages

## Options

- `search`: Filter URLs containing specific text
- `limit`: Maximum number of URLs to return (default: 100)
- `sitemap`: How to handle sitemaps - "include", "skip", or "only"
- `includeSubdomains`: Whether to include subdomains
- `ignoreQueryParameters`: Skip URL query parameters

## Use cases

- Understanding site structure before crawling
- Finding specific pages or content types
- Creating sitemaps
- Identifying all pages for comprehensive scraping
- Discovering blog posts, documentation, or product pages

---
description: Search the web and get scraped results
allowed-tools: firecrawl_search
---

# Web Search

Use the Firecrawl search tool to find and scrape web content based on a search query.

## When searching:

1. Take the user's search query
2. Use the `firecrawl_search` tool to find relevant pages
3. Present the results in a clear, organized format
4. Offer to scrape specific results for more detailed content if needed

## Options

- `limit`: Number of results to return (default: 5)
- `lang`: Language code (e.g., "en", "es", "fr")
- `country`: Country code (e.g., "us", "uk", "de")
- `scrapeOptions`: Options for scraping each result
  - `formats`: Output formats (markdown, html, etc.)
  - `onlyMainContent`: Extract only main content

## Search Operators

The search supports operators:
- `"exact phrase"` - Match exact text
- `-keyword` - Exclude keyword
- `site:firecrawl.dev` - Search specific site
- `inurl:keyword` - URL contains keyword
- `intitle:keyword` - Title contains keyword

## Use cases

- Research tasks requiring current web information
- Finding documentation or tutorials
- Gathering information from multiple sources
- Competitive analysis and market research

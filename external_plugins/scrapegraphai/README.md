# ScrapeGraphAI

[ScrapeGraphAI](https://scrapegraphai.com) is an AI-powered web scraping API. This plugin connects Claude Code to ScrapeGraphAI via the official MCP server so you can turn any website into markdown or structured data, search the web, crawl sites, and run agentic scraping workflows—all with natural language.

## Setup

### 1. Get your API key

Sign up and get your API key from the [ScrapeGraph Dashboard](https://dashboard.scrapegraphai.com).

### 2. Set environment variable

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export SCRAPEGRAPH_API_KEY="your-api-key-here"
```

Then reload your shell or run `source ~/.zshrc`.

## Available tools

- **markdownify** – Convert any webpage to clean markdown
- **smartscraper** – Extract structured data from a page using a natural language prompt (with optional infinite scroll)
- **searchscraper** – AI-powered web search with structured results (optionally filtered by time range)
- **scrape** – Fetch raw HTML with optional JavaScript rendering
- **sitemap** – Extract sitemap URLs and site structure
- **smartcrawler_initiate** / **smartcrawler_fetch_results** – Crawl multiple pages with configurable depth (AI extraction or markdown mode)
- **agentic_scrapper** – Multi-step agent that navigates and interacts with sites (forms, login, pagination, etc.)

## Example usage

Ask Claude Code to:

- "Convert https://scrapegraphai.com to markdown"
- "Extract product name, price, and description from this e-commerce URL"
- "Search for the latest AI news from the past week and summarize"
- "Crawl this docs site and list all API endpoints"
- "Fill this form and extract the results"

## Documentation

- [ScrapeGraphAI](https://scrapegraphai.com)
- [API docs](https://api.scrapegraphai.com/docs)
- [MCP server (GitHub)](https://github.com/ScrapeGraphAI/scrapegraph-mcp)

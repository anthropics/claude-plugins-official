---
description: Scrape a webpage and convert it to markdown
allowed-tools: firecrawl_scrape
---

# Scrape Web Page

Use the Firecrawl scrape tool to extract content from the URL provided by the user.

## Available Formats

You can request different output formats:
- `markdown` - Clean markdown content (default)
- `html` - Raw HTML content
- `rawHtml` - Unprocessed HTML
- `screenshot` - Screenshot of the page
- `links` - Extract all links from the page
- `summary` - AI-generated summary of the content

## When scraping:

1. If no URL is provided, ask the user for the URL they want to scrape
2. Ask what format they prefer if not specified (default to markdown)
3. Use the `firecrawl_scrape` tool with the URL and requested format
4. Return the content in a clean, readable format
5. Handle any errors gracefully and suggest alternatives if the page cannot be scraped

## Options

- `onlyMainContent`: Set to true to extract only the main content (excludes nav, footer, etc.)
- `includeTags`: Specific HTML tags to include
- `excludeTags`: HTML tags to exclude
- `waitFor`: Time in ms to wait for dynamic content
- `mobile`: Set to true to emulate mobile device

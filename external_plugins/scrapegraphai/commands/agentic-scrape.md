---
description: Advanced browser automation scraping with custom interaction steps
argument-hint: <url> [steps]
allowed-tools: []
---

# Agentic Scrape Command

Perform advanced web scraping with browser automation, supporting custom interaction steps, session management, and AI-powered content extraction.

## Usage

```
/agentic-scrape <url> [steps...]
```

## Arguments

- **url** (required): The website URL to scrape
- **steps** (optional): List of interaction steps to perform (e.g., "Click login button", "Fill form field")

## Examples

```
/agentic-scrape https://example.com "Click the 'Load More' button" "Wait for products to load"
/agentic-scrape https://shop.example.com "Login with credentials" "Navigate to products page" "Extract all product listings"
```

## Features

- Browser automation with Playwright
- Custom interaction steps
- Session management
- AI-powered extraction
- Stealth mode available
- Live session URLs for debugging

## Options

- `ai_extraction`: Enable AI-powered content extraction
- `use_session`: Maintain session state between steps
- `stealth`: Enable stealth mode to avoid bot detection
- `output_schema`: Define JSON schema for structured output

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- More expensive than basic scraping due to browser automation
- Returns request_id for async operations
- Use for sites requiring user interaction or complex navigation



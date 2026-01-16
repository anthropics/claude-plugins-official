---
description: Extract all URLs from a website's sitemap
argument-hint: <url>
allowed-tools: []
---

# Sitemap Command

Extract all URLs from a website's sitemap. Automatically discovers sitemap from robots.txt or common sitemap locations.

## Usage

```
/sitemap <url>
```

## Arguments

- **url** (required): The base URL of the website to extract sitemap from

## Examples

```
/sitemap https://example.com
/sitemap https://docs.example.com
```

## Features

- Automatic sitemap discovery
- Checks robots.txt
- Checks common sitemap locations
- Returns all discovered URLs
- Very cost-effective (1 credit per request)

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Costs only 1 credit per request
- Returns list of URLs from sitemap
- Useful for planning crawling operations
- Use before large crawling jobs to understand site structure


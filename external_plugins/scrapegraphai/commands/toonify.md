---
description: Convert data to toon format
argument-hint: <data-json>
allowed-tools: []
---

# Toonify Command

Accept an object of elements and convert to toon format.

## Usage

```
/toonify <data-json>
```

## Arguments

- **data-json** (required): JSON object containing data to convert

## Examples

```
/toonify '{"products":[{"sku":"LAP-001","name":"Gaming Laptop","price":1299.99}]}'
/toonify '{"users":[{"id":1,"name":"John","email":"john@example.com"}]}'
```

## Features

- Data format conversion
- Object structure transformation
- Preserves data relationships

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Accepts any JSON object structure
- Returns processed result in toon format
- Use for data transformation and formatting



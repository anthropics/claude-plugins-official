---
description: Generate JSON schema from natural language description
argument-hint: <prompt>
allowed-tools: []
---

# Generate Schema Command

Generate or modify JSON schemas based on natural language descriptions. Can create new schemas or extend existing ones.

## Usage

```
/generate-schema <prompt>
```

## Arguments

- **prompt** (required): Natural language description of the desired schema

## Examples

```
/generate-schema "Create a schema for product information including name, price, and reviews"
/generate-schema "Schema for user profile with email, name, age, and preferences"
/generate-schema "Extend existing schema to include shipping address"
```

## Features

- Natural language to JSON schema conversion
- Create new schemas
- Extend existing schemas
- LLM-powered schema generation

## Options

- `existing_schema`: Provide existing schema to modify or extend

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Returns request_id for async operations
- Check status with: `GET /generate_schema/{request_id}`
- Use generated schemas with smart-scrape for consistent data extraction


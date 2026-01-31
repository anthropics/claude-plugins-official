---
description: Validate your ScrapeGraphAI API key and get associated email
argument-hint: 
allowed-tools: []
---

# Validate Key Command

Validate your ScrapeGraphAI API key and retrieve the associated user email.

## Usage

```
/validate-key
```

## Examples

```
/validate-key
```

## Response

Returns:
- **email**: The email address associated with the API key

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- No credits consumed for this operation
- Use to verify API key is valid and active
- Returns 401 if API key is invalid



---
description: Shorten multiple URLs at once from a list
argument-hint: "[urls on separate lines] [--campaign name] [--tag name] [--folder name]"
allowed-tools: mcp__clypt__bulk_shorten, mcp__clypt__manage_tags, mcp__clypt__manage_folders
---
Bulk shorten URLs from $ARGUMENTS using Clypt.

Parse the URL list (handle newlines, commas, numbered lists).
Apply --campaign, --tag, --folder flags if present.
Use bulk_shorten (max 25 per call, auto-batch if more).

Present results as a table:
```
✅ [n] links created

| # | Original URL | Short Link |
|---|-------------|-----------|
| 1 | [url]       | [short]   |
```

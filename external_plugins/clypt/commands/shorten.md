---
description: Shorten a URL with optional slug, UTMs, tags, and folder
argument-hint: "[url] [--slug text] [--utm-source s] [--utm-medium m] [--utm-campaign c] [--tag name] [--folder name]"
allowed-tools: mcp__clypt__shorten_link, mcp__clypt__manage_tags, mcp__clypt__manage_folders
---
Shorten the URL from $ARGUMENTS using Clypt.

Parse these optional flags if present:
- --slug → custom short code
- --utm-source, --utm-medium, --utm-campaign, --utm-content → UTM parameters
- --tag → tag name to apply
- --folder → folder name to place the link in

Call shorten_link with the parsed arguments. Present the result as:
```
✅ Short link created
🔗 [shortUrl]
📋 Slug: [shortCode]
```

If no UTMs were provided and the URL looks like a campaign landing page, ask: "Want me to add UTM parameters to track traffic sources?"

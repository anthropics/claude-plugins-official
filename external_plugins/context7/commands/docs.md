---
description: Fetch up-to-date documentation and code examples for any library
argument-hint: <library> [topic]
---

# Context7 Documentation Lookup

Fetch current, version-specific documentation straight from source repositories.

## Arguments

`$ARGUMENTS` = `<library> [topic]`

Examples:
- `react hooks` → library="react", topic="hooks"
- `next.js routing` → library="next.js", topic="routing"
- `prisma` → library="prisma", topic=none

## Steps

1. Parse arguments: first word = library, remaining = topic
2. Call `resolve-library-id` with the library name
3. Call `get-library-docs` with:
   - `context7CompatibleLibraryID`: the resolved ID
   - `topic`: the topic (if provided)
4. Present documentation with code examples

## Tips

- If you know the exact library ID, use it directly: `/context7:docs /vercel/next.js routing`
- Use `page` parameter (1-10) if initial results aren't sufficient

---
description: Fetch up-to-date documentation and code examples for any library
argument-hint: <library> [query]
---

# Context7 Documentation Lookup

Fetch current, version-specific documentation from source repositories.

## Arguments

`$ARGUMENTS` = `<library> [query]`

- First word: library name (or direct library ID starting with `/`)
- Remaining: your specific question or topic

Examples:
- `react hooks`
- `next.js authentication`
- `/vercel/next.js/v15.1.8 app router`

## Steps

1. Parse arguments: first word = library, remaining = query
2. If library starts with `/`, use it directly as library ID
3. Otherwise, call `resolve-library-id` with library name and query
4. Call `query-docs` with the library ID and query
5. Present documentation with code examples

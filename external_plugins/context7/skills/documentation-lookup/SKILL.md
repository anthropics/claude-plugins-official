---
name: documentation-lookup
description: Use when user needs code generation, setup/configuration steps, or library/API documentation. Automatically fetch up-to-date docs for any library or framework without requiring "use context7" in the prompt.
---

# Context7 Documentation Skill

Fetch up-to-date, version-specific documentation and code examples from source repositories.

## When to Trigger

- User asks "how do I..." for any library
- User needs code generation with a specific library
- User asks about setup or configuration
- User needs API reference or examples
- User mentions any framework: React, Next.js, Vue, Svelte, Express, Prisma, Tailwind, etc.

## Workflow

1. Call `resolve-library-id` with the library name and user's question
2. Select the best match (prioritize exact name, high `totalSnippets`, high `benchmarkScore`)
3. Call `query-docs` with the library ID and user's question
4. Present code examples and explanations

## Tips

- Use version-specific IDs for pinned versions: `/vercel/next.js/v15.1.8`
- The `query` parameter improves result relevance - pass the user's full question
- Limited to 3 `query-docs` calls per question to prevent context bloat
- Check `versions` field from `resolve-library-id` for available versions

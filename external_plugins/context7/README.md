# Context7 Plugin

Up-to-date, version-specific documentation and code examples for any library, directly in your AI coding assistant.

## What is Context7?

Context7 solves the problem of outdated training data and hallucinated APIs by providing real-time library documentation. Instead of relying on potentially outdated knowledge, Context7 fetches current documentation straight from source repositories.

**Without Context7:**
- Code examples based on outdated training data
- Hallucinated APIs that don't exist
- Generic answers for old package versions

**With Context7:**
- Current documentation from source repositories
- Working code examples
- Version-specific information
- Intelligent query-based context selection

## Available Tools

### `resolve-library-id`

Search and resolve library names to Context7-compatible library IDs.

```
Parameters:
- libraryName: Library name to search for (e.g., "react", "next.js")
- query: Your question for relevance ranking

Returns:
- id: Context7-compatible ID (e.g., "/vercel/next.js")
- title: Display name
- description: Short description
- totalSnippets: Documentation coverage
- benchmarkScore: Quality indicator (0-100)
- versions: Available versions
```

### `query-docs`

Fetch documentation with intelligent, query-based reranking.

```
Parameters:
- libraryId: Context7-compatible library ID
  - Format: /org/project (e.g., /vercel/next.js)
  - With version: /org/project/version (e.g., /vercel/next.js/v15.1.8)
- query: Specific question or task

Features:
- LLM-driven reranking based on query intent
- Deduplicated snippet selection
- Limited to 3 calls per question
```

## Usage

### Automatic (Skill)

The `documentation-lookup` skill triggers automatically when you:
- Ask "how do I..." for any library
- Need code generation with a specific library
- Ask about setup or configuration
- Mention any framework (React, Next.js, Vue, etc.)

### Manual (Command)

Use the `/context7:docs` command:

```
/context7:docs react hooks
/context7:docs next.js how to set up authentication
/context7:docs /vercel/next.js/v15.1.8 app router
```

### Agent

Use the `docs-researcher` agent for focused documentation lookups that don't bloat the main conversation:

```
Spawn a docs-researcher agent to find React Query mutation examples
```

## Version Pinning

For consistent, reproducible results, use version-specific library IDs:

```
/vercel/next.js/v15.1.8
/facebook/react/v18.3.0
/prisma/prisma/v5.0.0
```

## Examples

**Basic usage:**
```
How do I set up authentication in Next.js?
→ Automatically fetches Next.js auth documentation
```

**With specific version:**
```
/context7:docs /vercel/next.js/v15.1.8 middleware
→ Fetches Next.js 15.1.8 middleware documentation
```

**Multiple libraries:**
```
How do I use Prisma with Next.js API routes?
→ Fetches relevant docs from both Prisma and Next.js
```

## Links

- [Context7 Website](https://context7.com)
- [GitHub Repository](https://github.com/upstash/context7)
- [Upstash](https://upstash.com)

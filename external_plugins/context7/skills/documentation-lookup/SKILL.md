---
name: documentation-lookup
description: Use when user needs code generation, setup/configuration steps, or library/API documentation. Automatically fetch up-to-date docs for any library or framework without requiring "use context7" in the prompt.
---

# Context7 Documentation Skill

Automatically fetch up-to-date, version-specific documentation and code examples straight from the source.

## Why Use This

Without Context7:
- Code examples based on outdated training data
- Hallucinated APIs that don't exist
- Generic answers for old package versions

With Context7:
- Current documentation from source repositories
- Working code examples
- Version-specific information

## When to Trigger

- User asks "how do I..." for any library
- User needs code generation with a specific library
- User asks about setup or configuration
- User needs API reference or examples
- User mentions any framework: React, Next.js, Vue, Svelte, Express, Prisma, Tailwind, etc.

## Available Tools

- `resolve-library-id`: Convert library name → Context7 ID
- `get-library-docs`: Fetch docs with optional topic filter

## How to Use

1. Identify the library from user's question
2. Call `resolve-library-id` with library name
3. Call `get-library-docs` with resolved ID and topic (if specific)
4. Present code examples and explanations

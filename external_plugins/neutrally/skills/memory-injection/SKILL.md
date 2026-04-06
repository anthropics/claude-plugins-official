---
name: neutrally-memory
description: Use when working in any Claude Code session — governs how to use Neutrally persistent memory naturally and proactively
---

# Neutrally Memory

Neutrally gives you persistent, cross-session memory. Context from previous sessions, decisions, and project state is injected at session start inside `<neutrally-memory>` tags. You also have access to Neutrally MCP tools for deeper retrieval on demand.

## Core Principle

Treat Neutrally memory as working knowledge — not a database you're querying. It should feel like you simply remember things, not like you're running lookups.

**Never say:**
- "According to Neutrally..."
- "Based on your memory..."
- "I found this in your memory..."

**Just use the information naturally**, the same way you'd use anything you already know about the user.

## At Session Start

When you see a `<neutrally-memory>` block injected into your context:

1. **Silently absorb it** — don't acknowledge it, don't summarise it back to the user
2. **Use it to inform your very first response** — if the user says "continue where we left off", you already know what to do
3. **Check for active project context** — if there's project-specific memory, apply those conventions immediately (naming, structure, stack preferences)

## When to Call MCP Tools

Use the Neutrally MCP tools (`search`, `recent`, `get_context`, etc.) in these situations:

| Situation | Action |
|---|---|
| User references a past decision you don't have context for | Call `search` with the topic |
| User says "what were we working on?" or "continue from last time" | Call `recent` then `search` with the project name |
| User references a convention, pattern, or preference from a previous session | Call `search` to verify it |
| User asks about something that might have been decided before | Call `search` before answering |
| More than 2 weeks since last visible context | Call `get_context` for a full refresh |

**Be proactive**: if the user's message suggests there's relevant history you might not have, search before answering rather than answering with potentially stale information.

## When to Save Memory

Call `save_memory` proactively when:

- A **significant architectural decision** is made ("we'll use server actions for mutations, not route handlers")
- A **naming convention** is established ("all API routes follow REST, plural nouns")
- A **tech stack decision** is locked in ("switching from Prisma to Drizzle for this project")
- A **debugging discovery** is made that will be relevant again ("the trailing newline issue with Vercel env vars")
- A **project state** change occurs ("the checkout flow is now complete, next is the mobile app")
- The user explicitly says "remember this" or "save this"

**Don't over-save**: skip saving transient context, intermediate debugging steps, or things the git history captures better.

## Handling /compact

After `/compact`, your conversation history is gone but Neutrally memory is not. The `post-compact` hook will re-inject critical context. Trust that context — it's what you were doing immediately before the compact.

If the re-injected context seems incomplete, call `search` with the project name to get more detail.

## Session Continuity

When a user returns after an absence (weekend, overnight):
- The `<neutrally-memory>` block at session start has their context
- **Start as if the conversation never ended** — pick up where they left off
- If they ask "what's the status?", synthesise from the injected memory rather than saying you don't know

## Memory and Privacy

Only save **architectural facts, decisions, conventions, and project state** — not personal details, sensitive data, or raw conversation transcripts. The capture hook handles conversation summarisation automatically.

---
name: unforgit-memory
description: Use Unforgit MCP tools as durable repository memory for decisions, conventions, gotchas, and playbooks.
---

# Unforgit Memory

Use this skill whenever work can benefit from durable project memory or when the user asks you to remember, recall, curate, or inspect repository knowledge.

## Core workflow

1. **Recall first for substantive work.** At the start of non-trivial coding, planning, debugging, release, or review work, call `unforgit_recall` with a query based on the user's request and the repository area being touched.
2. **Use recalled context.** Apply prior decisions, conventions, gotchas, and playbooks before changing code or proposing a plan.
3. **Save durable context promptly.** When a stable decision, convention, gotcha, bug pattern, workaround, API contract, or reusable procedure emerges, call `unforgit_add` with concise self-contained text.
4. **Curate when memory quality matters.** Use `unforgit_health`, `unforgit_sync_status`, `unforgit_find_similar`, `unforgit_consolidate`, and `unforgit_curate` when diagnosing memory quality, duplicates, sync, or stale notes.

## What to save

- `semantic`: stable facts, architectural decisions, conventions, API contracts.
- `procedural`: repeatable workflows, release/deploy playbooks, troubleshooting steps.
- `episodic`: notable bugs, gotchas, one-off observations that may prevent future mistakes.

## What not to save

- Do not save secrets, tokens, passwords, API keys, private credentials, or sensitive environment values.
- Do not save temporary progress, task checklists, transient logs, command output dumps, PR numbers, commit SHAs, or facts likely to be stale soon.
- Do not save obvious information already documented in the repository unless the memory captures a decision or gotcha not obvious from the code.

## Writing guidelines

- Write memory text in English unless the repository explicitly standardizes another language.
- Keep each memory concise but self-contained.
- Use tags such as `auth`, `api`, `deploy`, `bug`, `gotcha`, `decision`, or package/module names.
- Prefer repository-scoped Unforgit memory over global assistant memory for project-specific knowledge.
- If a memory may duplicate an existing one, search first and consolidate rather than creating noise.

## Tool hints

- Search: `unforgit_recall({ "query": "...", "k": 5 })`
- Save: `unforgit_add({ "text": "...", "type": "semantic", "tags": ["decision"] })`
- Health: `unforgit_health()`
- Sync status: `unforgit_sync_status()`

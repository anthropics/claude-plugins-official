# TenDD — Tenacity-Driven Development

A Claude Code plugin that runs structured, multi-agent development pipelines with iterative review loops. Like TDD, but the T stands for Tenacity — quality is the exit condition, never fatigue.

## The Problem

AI agents write code fast but review it poorly. You delegate a feature, get back something that *looks* right, then spend more time debugging agent output than you saved by delegating. The bottleneck isn't generation — it's verification.

## Why This Works

LLMs generate left-to-right and don't look back. A single agent writing and self-reviewing in the same context is structurally incapable of catching its own blind spots. TenDD fixes this with **separation of concerns across agents**:

- An **architect** designs interfaces before any code is written
- A separate **reviewer** checks every artifact — never the author
- A **builder** implements against the reviewed interface
- A fresh **rewriter** (clean context, no authorship bias) rewrites for conciseness
- **Tests are the behavioral contract** — the rewriter doesn't need to know why edge cases exist

No stage advances until the reviewer explicitly approves. Iterations are unbounded. The pipeline keeps looping until the work is actually correct — not until the token budget runs out.

## Commands

### `/tendd:plan <description or plan path>`

Tenacious planning cycle: bootstrap principles, create plan, DDD review loop, requirements extraction, cross-review loop. Commits approved plan + requirements.

### `/tendd:dev <description or plan path>`

Tenacious build cycle: interface design loop, implementation loop, conciseness rewrite loop, verification hard gate. Commits implementation.

### `/tendd:help`

Explains the pipeline, agents, and customization options.

## Agents

| Agent | Role |
|-------|------|
| **architect** | Interfaces, protocols, type stubs. Bootstraps PRINCIPLES.md. |
| **reviewer** | BLOCKER/CONCERN/SUGGESTION findings. Never writes code. |
| **builder** | Implementation + tests. |
| **rewriter** | Fresh builder for conciseness. Tests are the safety net. |
| **requirements** | Extracts testable requirements from plans. |

All agents are generic defaults. For best results, create project-specific agents at `.claude/agents/` — they take priority over the plugin defaults.

## Install

```
/plugin marketplace add <this-repo-url>
/plugin install tendd
```

Or for development:

```bash
claude --plugin-dir /path/to/tendd
```

# Regulatory Counsel Plugin

Watches regulatory feeds, diffs new regulations against your policy library, surfaces gaps. Learns your materiality threshold so it doesn't alert on every commissioner's speech. Wired for the Federal Register API, direct regulator feeds, and CourtListener.

**Every output is a draft for attorney review — cited, flagged, and gated — not a legal conclusion.** The plugin does the work: reads the documents, applies your playbook, finds the issues, drafts the memo. A lawyer reviews, verifies, and decides. Citations are tagged by source so you know which ones came from a research tool and which ones need checking. Privilege markers are applied conservatively so nothing waives by accident. Consequential actions — filing, sending, executing — are gated behind explicit confirmation.

## Who this is for

| Role | Primary workflows |
|---|---|
| **Compliance / regulatory counsel** | Watchlist maintenance, gap triage, policy update coordination |
| **Privacy / product counsel** | Receives filtered alerts relevant to their area |
| **GC** | Escalation recipient for material gaps with deadlines |

## First run: cold-start

Asks which regulators you watch, connects your policy document folder, learns what "material" means to you. Builds a watchlist and indexes your policy library.

```
/regulatory-legal:cold-start-interview
```

## Skills

| Skill | Does |
|---|---|
| `/regulatory-legal:cold-start-interview` | Cold-start: watchlist + policy index + materiality threshold |
| `/regulatory-legal:reg-feed-watcher` | Check feeds now, report what's new |
| `/regulatory-legal:policy-diff [reg]` | Diff a specific reg change against policy library |
| `/regulatory-legal:gaps` | Open gaps tracker — what's been flagged and not yet closed |
| `/regulatory-legal:comments` | Review open NPRM comment periods, log decisions, track deadlines |
| `/regulatory-legal:policy-redraft` | Proposed marked-up policy redraft that closes a gap — a first draft for internal review, not a direct edit to source documents |
| `/regulatory-legal:matter-workspace` | Manage matter workspaces (multi-client private practice only) — new, list, switch, close, none |
| **gap-surfacer** *(reference)* | Shared gap- and comment-tracker framework loaded by `/gaps` and `/comments` |

## Interactive skills vs. scheduled agents

The skills above run when you invoke them — for when you're working a matter. The agents below run on a schedule — for what moves while you're not looking:

| Agent | What it watches | Default cadence |
|---|---|---|
| **reg-change-monitor** | Regulatory feeds — filters by the materiality threshold learned at cold-start and posts a digest that's signal, not noise | Weekly (daily if the regulatory environment is active) |

## Connectors and citation verification

**Connect a research tool first — the citation guardrails depend on it.** Without one, every cite is tagged `[verify]` and the reviewer note above each deliverable records that sources weren't verified. The plugin works either way; it just does more of the verification for you when a research tool is connected.

The legal research connectors in this plugin aren't just data sources — they're the difference between a verified citation and a citation you have to check. A citation retrieved through a connected research tool is tagged with its source and can be traced back. A citation from the model's knowledge or from web search is tagged `[verify]` or `[verify-pinpoint]` and should be checked against a primary source before anyone relies on it. The plugin tiers its citations so your verification time goes where it matters.

## Integrations

Ships with the general bucket of connectors in `.mcp.json`:

- **Slack** — search messages, read channels, find discussions
- **Google Drive** — search, read, and fetch documents

Additional regulatory feed connectors can be added when partner URLs are available. Direct regulator RSS/email as fallback.

## Prerequisites

Owner notifications (gap assignments, due-date reminders, NPRM alerts) require a Slack MCP server in your environment. Without one, the gap tracker and comment tracker still work — notifications just won't post, and the skills will flag ungated items in the status report instead.

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. The `reg-change-monitor` agent watches the regulatory feeds and flags changes against your policy library. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## Notes

- Materiality filtering is the value. Everything is "technically a regulatory change" — the plugin learns what actually matters here.
- Policy diff compares against indexed policies. If the policy library isn't connected, diffs run against what you paste.
- This is the automated version of privacy-legal's `reg-gap-analysis`. Pair them: this one watches, that one deep-dives.

## Configuration

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` and survives plugin updates — you only run setup once.

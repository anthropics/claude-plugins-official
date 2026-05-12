# Commercial Counsel Plugin

In-house commercial contracts workflows: vendor agreement review, NDA triage, SaaS subscription review, renewal tracking, escalation routing, and business-stakeholder summaries. Built around a team practice profile that gets written by a cold-start interview — the plugin learns *your* playbook, not a generic one.

**Every output is a draft for attorney review — cited, flagged, and gated — not a legal conclusion.** The plugin does the work: reads the documents, applies your playbook, finds the issues, drafts the memo. A lawyer reviews, verifies, and decides. Citations are tagged by source so you know which ones came from a research tool and which ones need checking. Privilege markers are applied conservatively so nothing waives by accident. Consequential actions — filing, sending, executing — are gated behind explicit confirmation.

## Who this is for

| Role | Primary workflows |
|---|---|
| **Commercial counsel** | Vendor agreement review, escalation routing, stakeholder summaries |
| **Contracts manager / paralegal** | NDA triage, renewal tracking, first-pass review |
| **Procurement** | Renewal awareness, stakeholder summaries as recipients |
| **Sales / BD** | NDA triage self-serve before pinging legal |

## First run: the cold-start interview

On first use, the plugin interviews you — ten minutes, conversational — to learn how your team actually works. It asks about your playbook positions, your escalation rules, and the thing that makes you groan when it hits your desk. Then it asks for 5-10 recent signed agreements (more is better, 20 gives a clearer pattern) so it can see your positions in the wild.

It writes what it learns to `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` — a plain-English document about your team that every other skill reads before doing anything. You edit the document, not a config file.

```
/commercial-legal:cold-start-interview
```

**Playbook side.** Early in setup, you'll be asked whether to build a **sales-side** playbook (you sell your product/service; you're the vendor; usually your paper), a **purchasing-side** playbook (you buy from vendors; you're the customer; usually their paper), or both. The answer flips nearly every playbook position — liability caps, indemnity direction, termination rights, IP ownership — so it matters up front. If you pick both, setup builds sales-side first; run `/commercial-legal:cold-start-interview --side purchasing` afterward to build the other. Your configuration holds both in parallel, and review skills check which side applies before reading the playbook.

## Commands

| Command | Does |
|---|---|
| `/commercial-legal:cold-start-interview` | Run (or re-run) the cold-start interview |
| `/commercial-legal:review [file]` | Review a vendor agreement, NDA, or SaaS subscription against your playbook |
| `/commercial-legal:renewal-tracker` | What's renewing in the next 90 days and when the cancel-by deadlines are |
| `/commercial-legal:escalation-flagger` | Route an issue to the right approver and draft the ask |
| `/commercial-legal:amendment-history [file(s)]` | Trace how a contract has changed across its base agreement and all amendments |
| `/commercial-legal:review-proposals` | Step through pending playbook update proposals from the monitor agent |
| `/commercial-legal:matter-workspace` | Manage matter workspaces (multi-client private practice only) — new, list, switch, close, none |

## Skills

| Skill | Purpose |
|---|---|
| **cold-start-interview** | First-run interview that writes `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` |
| **vendor-agreement-review** | Full playbook-vs-contract deviation analysis with redlines |
| **nda-review** | Fast GREEN/YELLOW/RED triage so legal only reads the NDAs that need it |
| **saas-msa-review** | Subscription-specific overlay: auto-renewal, price escalation, data exit, SLAs |
| **renewal-tracker** | Register of cancel-by deadlines, surfaces what's coming |
| **escalation-flagger** | Matches issues to the escalation matrix, drafts the approver ask |
| **stakeholder-summary** | Two-paragraph business translation of a legal review |
| **amendment-history** | Summarizes changes across a base agreement and its amendments, or traces a specific provision to its current controlling language |
| **matter-workspace** | Create, list, switch, and close matter workspaces for multi-client practices; isolates each client/matter so context does not leak across them |

## Interactive commands vs. scheduled agents

The commands above run when you invoke them — for when you're working a matter. The agents below run on a schedule — for what moves while you're not looking:

| Agent | What it watches | Default cadence |
|---|---|---|
| **renewal-watcher** | Renewal register — posts what's coming up in the next 90 days, with red-flag escalation for cancel-by windows in 0–13 days | Weekly (Monday) |
| **deal-debrief** | Recently signed agreements for playbook deviations; prompts the attorney to log context while memory is fresh | Weekly (Monday) |
| **playbook-monitor** | Deviation log — proposes playbook updates when a clause has been overridden 5+ times in a rolling 12-month window | Data-triggered (after each deal-debrief) |

## Integrations

**Connect a research tool first — the citation guardrails depend on it.** Without one, every cite is tagged `[verify]` and the reviewer note above each deliverable records that sources weren't verified. Skills work either way; a research tool (CourtListener) just shifts verification work off your plate.


Ships with connectors configured in `.mcp.json`:

- **Ironclad** — contract lifecycle management
- **DocuSign** — signature status and envelope tracking
- **Slack** — search messages, read channels, find discussions (general bucket)
- **Google Drive** — search, read, and fetch documents (general bucket)

With a [CLM] connected: reviews check for prior agreements with the same counterparty, bulk-load the renewal register, create records with review memos attached.

With DocuSign connected: track signature status, route envelopes in approver order.

## Quick start

### 1. Get interviewed

```
/commercial-legal:cold-start-interview
```

Ten minutes. Have 5-10 recent signed agreements ready to share (more is better, 20 gives a clearer pattern).

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` and survives plugin updates.

### 2. Review a contract

```
/commercial-legal:review vendor-msa.pdf
```

Output: deviation-by-deviation memo against your playbook, with specific redline language and named approver.

### 3. See what's renewing

```
/commercial-legal:renewal-tracker
```

Output: everything with a cancel-by deadline in the next 90 days, grouped by urgency.

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. The `playbook-monitor` agent proposes updates when your practice diverges from your playbook. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## File structure

```
commercial-legal/
├── .claude-plugin/plugin.json
├── .mcp.json
├── CLAUDE.md                    # Your team practice profile — written by cold-start, edited by you
├── README.md
├── agents/
│   ├── renewal-watcher.md
│   ├── deal-debrief.md
│   └── playbook-monitor.md
├── skills/
│   ├── cold-start-interview/
│   ├── review/
│   ├── review-proposals/
│   ├── vendor-agreement-review/
│   ├── nda-review/
│   ├── saas-msa-review/
│   ├── renewal-tracker/
│   │   └── references/renewal-register.yaml
│   ├── escalation-flagger/
│   ├── amendment-history/
│   ├── matter-workspace/
│   └── stakeholder-summary/
└── hooks/hooks.json
```

## Notes

- The plugin assumes you're the **customer** in most reviews. When you're the vendor, flag it and the review flips the playbook polarity.
- NDA triage is built for self-serve by non-lawyers. GREEN means "route to signature." It does not negotiate.
- Renewal tracking only knows about contracts that were reviewed through this plugin or bulk-loaded from the [CLM]. Contracts signed before you installed this need a one-time scan.

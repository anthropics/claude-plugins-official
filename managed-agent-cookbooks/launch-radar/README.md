# Launch Radar — managed-agent template

## Overview

Scheduled scan of the product team's launch tracker — Jira, Linear, or Asana — for launches that will likely need legal review in the next few weeks. Triages each launch against the product counsel's risk calibration and produces a weekly radar memo: what's coming, what needs legal attention, what triggered a flag. Same source as the [`launch-watcher`](../../product-legal/agents/launch-watcher.md) Claude Code plugin agent — this directory is the Managed Agent cookbook for `POST /v1/agents`.

This is a **cookbook, not a product.** It will not work out of the box. You need to point the MCP connectors at your tracker, load your risk calibration, set the cadence, and configure where the memo goes. Adaptation notes below.

## ⚠️ Before you deploy

- **The radar triage is a routing decision, not a legal review.** "Needs review" means a product counsel should look; "FYI" does not mean the launch is fine; "skip" does not clear the launch. Review the full radar, not only the flagged items — the un-flagged items are where you lose the ones you needed to see.
- **Risk classification uses the calibration in your plugin configuration.** If your calibration is stale, so is the triage. New product lines, new regulators, new geographies, and new third-party dependencies need to land in the calibration before the radar can route on them.
- **The trigger keyword list is opinionated.** If your product surface doesn't match the defaults (e.g., you're biometrics-heavy, FedRAMP-bound, or handling minors' data in ways the keywords don't cover), retune before the first run or the memo will miss the cases it was built to catch.
- **Tracker tickets are untrusted input.** A PM can put anything in a title or description, and an attacker can file a ticket. The triage routes on content; it does not vouch for the ticket.

## Deploy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export LINEAR_MCP_URL=... ATLASSIAN_MCP_URL=... ASANA_MCP_URL=... GDRIVE_MCP_URL=...
../../scripts/deploy-managed-agent.sh launch-radar
```

Only set the MCP URLs for the trackers you actually use. The orchestrator and `tracker-reader` skip MCPs that aren't configured.

## Steering events

See [`steering-examples.json`](./steering-examples.json). Typical cadence is a weekly scan with a 4–6 week horizon, plus on-demand single-ticket triage when a PM pings the product counsel with "is this a problem?"

## Security & handoffs

Tracker tickets are untrusted input. A product manager can put arbitrary text in a title, description, or comment — and an attacker can file a ticket. Three-tier isolation:

| Tier | Touches untrusted tracker content? | Tools | Connectors |
|---|---|---|---|
| **`tracker-reader`** | **Yes** | `Read`, `Grep` only | Linear, Jira (atlassian), Asana (read-only) |
| `risk-classifier` / Orchestrator | No | `Read`, `Grep`, `Glob`, `WebFetch`, `Agent` | Orchestrator only: Linear / Jira / Asana / Drive (read-only) |
| **`memo-writer`** (Write-holder) | No | `Read`, `Write`, `Edit` | None |

`tracker-reader` returns a length-capped, schema-validated JSON list of launches. `risk-classifier` has no MCP and no network; it works from the validated list plus the user's calibration file. `memo-writer` is the only worker with Write, and produces `./out/launch-radar-<date>.md`. The orchestrator holds no Write and never parses raw ticket bodies itself.

**Handoff:** when a launch needs a full legal review memo rather than a radar entry, the orchestrator emits a `handoff_request` for the `launch-review` skill (running in a fresh session) rather than drafting the memo inline. `scripts/orchestrate.py` routes it.

## Adaptation notes

Things you will need to change before this is useful:

- **Tracker pointer.** Edit `mcp_servers` in [`agent.yaml`](./agent.yaml) and [`subagents/tracker-reader.yaml`](./subagents/tracker-reader.yaml) to the MCP URL of your tracker. If you only use one of Jira/Linear/Asana, drop the other two. If your tracker isn't in that list, swap in the MCP you do use and update the `tracker-reader` system prompt accordingly.
- **Risk calibration.** The `risk-classifier` reads the user's calibration from `../../product-legal/CLAUDE.md` (populated by `/product-legal:cold-start-interview`). If you haven't run cold-start, either do that first or hand-author a CLAUDE.md with "Usually blocks / Usually requires work / Usually FYI" tables before the first scan. Without calibration the classifier falls back to keyword triggers only, which is noisy.
- **Scan cadence and horizon.** Default is weekly / 6 weeks. Your launch cadence may warrant daily or biweekly; short lead times need a longer horizon. Configure the cadence in your scheduler (cron, Temporal, Airflow, EventBridge), not inside the agent. The horizon is passed in the steering event.
- **Delivery channel.** The memo goes to `./out/` by default. To post to Slack instead or additionally, either (a) add a Slack MCP to the cookbook and update `memo-writer` to post after writing, or (b) have your orchestration layer pick up `./out/launch-radar-<date>.md` and forward it. This pattern keeps delivery out of the agent for easier testing; pick whichever fits your ops story.
- **Trigger keywords.** The keyword list in the `launch-watcher` system prompt is opinionated (COPPA, HIPAA, AI vendor names, etc.). Delete categories that don't apply to your product, add domain-specific terms (FedRAMP, PCI, HITRUST, TCPA, biometrics, etc.), and retune severity thresholds against your calibration table. Re-deploy after changes.
- **Privilege header.** `memo-writer` prepends the work-product header from the plugin config. Confirm the exact marking with your GC before deploying — per-jurisdiction variations apply.

## What you get and don't get

- **You get:** a working manifest, a security-tiered pipeline, a memo that cites every launch back to its tracker URL, and a handoff path to the full launch-review skill.
- **You don't get:** a production-ready agent. Point it at your tracker, load your calibration, set the cadence, run an evaluation, and have the product counsel review the first few outputs against their own read of the same tickets before trusting it.
- **You especially don't get:** a replacement for the product counsel. This agent triages. A lawyer reviews, flags, decides. Every "needs review" item in the memo is a lead, not a verdict.

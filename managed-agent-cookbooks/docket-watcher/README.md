# Docket Watcher — managed-agent template

## Overview

Monitors court dockets for matters in the active litigation portfolio. Trellis covers state trial courts; CourtListener / PACER covers federal. For each active matter the agent pulls new filings since the last check, maps filing types to candidate deadlines, cross-references against the matter's history and open deliverables, and produces a docket status report plus a structured deadline feed.

Same source as the [`docket-watcher`](../../litigation-legal/agents/docket-watcher.md) agent in the litigation-legal Claude Code plugin — this directory is the Managed Agent cookbook for `POST /v1/agents`.

## ⚠️ Before you deploy

- **Computed deadlines are leads, not calendar entries.** Court deadline rules vary by jurisdiction, court, judge, and local rule, and can be modified by standing order or case-specific case management order. Missing a court deadline has malpractice consequences. A licensed attorney verifies every computed deadline against the court's actual rules and any case-specific orders before it is docketed. The agent is upstream of that decision, not a substitute for it.
- **Filing classifications are heuristic.** A filing the agent misclassifies — an administrative motion read as a dispositive motion, a stipulation read as a discovery dispute — can produce a wrong deadline rule. Read the filing; do not trust the label.
- **An unknown court is not a default.** If the jurisdiction-rule table does not cover a court, the mapper must produce `confidence: low` + `needs_verification: true`, never a silent default. If you see a confident deadline on an obscure court, treat the rule table as stale until proven otherwise.
- **A quiet docket is not a clean docket.** Clerks docket late. Minute entries sometimes arrive days after the event. "No new filings" is a statement about the feed, not a statement about the case.

## Deploy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export TRELLIS_MCP_URL=...
export COURTLISTENER_MCP_URL=...
export GDRIVE_MCP_URL=...
../../scripts/deploy-managed-agent.sh docket-watcher
```

## Steering events

See [`steering-examples.json`](./steering-examples.json).

## Security & handoffs

Court filings are public records, but they are also UNTRUSTED INPUT. The filer controls the text and can embed prompts, URLs, and instructions aimed at the agent. Three-tier isolation:

| Tier | Touches filings? | Tools | Connectors |
|---|---|---|---|
| **`docket-reader`** | **Yes** | `Read`, `Grep` only | trellis, courtlistener (read-only) |
| `deadline-mapper` / Orchestrator | No — sees structured JSON only | `Read`, `Grep`, `Glob`, `Agent` | gdrive (jurisdiction config, read-only) |
| **`tracker-writer`** (Write-holder) | No | `Read`, `Write`, `Edit` | None |

`docket-reader` returns length-capped, schema-validated JSON. `deadline-mapper` has no MCP and no web — it applies rules the deploying team has configured. `tracker-writer` produces `./out/docket-report-<date>.md` and `./out/deadlines.yaml` and never sees raw filings.

## Adaptation notes

This cookbook is a starting point. It will not work in production until you have done the following:

- **Set the MCP URLs.** `TRELLIS_MCP_URL` and `COURTLISTENER_MCP_URL` must point at your deployment's endpoints, with whatever authentication your platform requires. `GDRIVE_MCP_URL` (or a substitute) points at wherever your jurisdiction-rule tables live.
- **Load the portfolio.** The agent reads `matters/_log.yaml` plus the per-matter `docket_id` and `court` from the deploying team's litigation-legal configuration. If your docketing system is the source of truth, front it with an MCP or a scheduled sync into the config path.
- **Configure jurisdiction rules.** Ship the deadline-mapper a local-rule table for every court in your portfolio. Federal rules you can encode once; state trial courts and individual judges are where the landmines live. An unknown court should produce `confidence: low` + `needs_verification: true`, never a silent default.
- **Wire delivery.** Decide where the output goes: your docketing system ingests `./out/deadlines.yaml`; the narrative report goes to Slack, email, or your matter management workspace; critical flags route to whoever you want woken up.
- **Set the schedule.** Weekly for most matters; daily for anything with a hearing inside 14 days, any `trial` or late-`discovery` posture, or any `risk: critical` matter.

## Computed deadlines are leads, not calendar entries

**The computed deadlines this agent produces require human verification against the controlling local rule, standing order, and case management order before they are calendared. Missing a court deadline has malpractice consequences. This agent surfaces deadlines; a human verifies and dockets them.**

Every deadline carries `confidence` and `needs_verification` fields. The report segregates low-confidence entries and stamps a verification callout on anything not derived from an unambiguous federal rule. Treat that as the minimum — not the ceiling — of human review. Judges override defaults by individual order, local rules change, and the date the clerk actually docketed service may differ from the date the docket displays.

**Not guaranteed:** this agent recommends a deadline; the docketing attorney confirms against the controlling rule and books the date.

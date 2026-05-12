# Reg Monitor — managed-agent template

## Overview

Checks regulatory feeds on a schedule, filters by the deploying team's materiality threshold, runs a quick gap check against the policy library for always-material items, and writes a digest. Same source as the [`reg-change-monitor`](../../regulatory-legal/agents/reg-change-monitor.md) Claude Code agent and the [`reg-feed-watcher`](../../regulatory-legal/skills/reg-feed-watcher) / [`policy-diff`](../../regulatory-legal/skills/policy-diff) skills — this directory is the Managed Agent cookbook for `POST /v1/agents`.

## ⚠️ Before you deploy

- **Digest items are screened leads, not legal conclusions.** The materiality filter applies a configurable threshold, not legal judgment. A regulatory change the agent classifies as "informational" may still be material to your business. A change it flags as "material" may turn out not to apply. Review every digest; a licensed attorney decides whether an item requires action, disclosure, policy change, or escalation.
- **The policy gap check is a first pass, not a legal assessment of applicability.** The gap surface compares new regulatory text against your policy library using heuristics. A "gap" is a lead for a lawyer to evaluate; an "aligned" result does not certify compliance.
- **The materiality threshold is your calibration, not law.** If your `## Materiality threshold` section is stale or was tuned for a different risk posture, the triage is stale. Recheck before enabling scheduled runs.
- **The watchlist is a coverage assertion you made.** A regulator not on the watchlist may still publish something material. Missing a regulator is a configuration bug, not a feed bug.

## Deploy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GDRIVE_MCP_URL=...
../../scripts/deploy-managed-agent.sh reg-monitor
```

## Steering events

See [`steering-examples.json`](./steering-examples.json). The default weekly sweep uses the first example. The other two cover targeted deep checks on a specific development and gap analysis on a flagged item.

## Security & handoffs

Regulatory feed content (Federal Register entries, agency RSS posts, TR alerts notifications) is **untrusted input.** Three-tier isolation:

| Tier | Touches untrusted docs? | Tools | Connectors |
|---|---|---|---|
| **`feed-reader`** | **Yes** | `Read`, `Grep`, `WebFetch` only | None |
| `materiality-filter` / Orchestrator | No | `Read`, `Grep`, `Glob`, `Agent` | gdrive (orchestrator only) |
| **`digest-writer`** (Write-holder) | No | `Read`, `Write`, `Edit` | None |

`feed-reader` returns length-capped, schema-validated JSON. `materiality-filter` is pure computation over that JSON plus the regulatory-legal configuration on disk — no MCP, no web. `digest-writer` produces `./out/reg-digest-<YYYY-MM-DD>.md` and emits a `handoff_request` for Slack delivery.

**Handoffs:** the orchestrator routes the `handoff_request` from `digest-writer` to a Slack send worker using the channel from the deploying team's House style configuration. The agent never sends Slack messages itself.

**Not guaranteed:** this agent surfaces changes and flags potential policy gaps; a lawyer decides whether a regulatory change requires action and who owns the response.

## Adaptation notes

Before you trust the output on your workflow:

- **Point `feed-reader` at your sources.** The default target is the Federal Register (free public API, no MCP needed). If your firm subscribes to Thomson Reuters Regulatory Intelligence, Bloomberg Law, or direct agency RSS, add the endpoints to the feed-reader's web_fetch allowlist and adjust the orchestrator's scan plan. If you only have free sources, the Federal Register API alone is workable.
- **Set the (optionally) Thomson Reuters MCP URLs.** TR is commented out in the manifest; wire it and flip `enabled: true` if your team pays for it.
- **Configure the digest delivery channel.** The digest-writer emits a `handoff_request` that names a Slack channel. The orchestrator reads that channel from your regulatory-legal configuration's **House style → Reg digest** field. Set it before the first scheduled run or the handoff will dead-letter. Teams that want the digest by email or in a Confluence page instead should swap the handoff target in the orchestrator allowlist.
- **Tune the materiality threshold.** The materiality-filter reads your configuration's `## Materiality threshold` section — always material / review-worthy / FYI. Confirm the tiers reflect your current risk posture before enabling scheduled runs; a threshold set too low floods the digest, too high and you miss obligations with deadlines.
- **Update the watchlist.** The materiality-filter also reads the `## Regulators we watch` table. Add or remove regulators as your footprint changes.
- **Confirm the work-product header.** The headless append in `agent.yaml` instructs the agent to prepend your configuration's work-product header. Verify the header language with your GC before turning this on.
- **Cadence.** Weekly is the default. Active regulatory environments (financial services rulemaking cycles, cross-border AI regulation) may warrant daily. The cadence lives in your own workflow engine — the cookbook does not schedule itself.

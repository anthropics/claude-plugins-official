# Renewal Watcher — managed-agent template

## Overview

Scans the contract repository for upcoming renewal and cancel-by deadlines, cross-references against the team's playbook, flags contracts with upcoming deadlines, playbook deviations, and escalation triggers, and writes an alert report. Same source as the [`renewal-watcher`](../../commercial-legal/agents/renewal-watcher.md) Claude Code agent and the [`renewal-tracker`](../../commercial-legal/skills/renewal-tracker) skill — this directory is the Managed Agent cookbook for `POST /v1/agents`.

This is a **cookbook, not a product.** It assumes Ironclad as the CLM of record because that is what the paired plugin assumes; teams on Agiloft, Ironclad alternatives, iManage, or a Google Drive of signed PDFs should swap the MCP endpoint accordingly.

## ⚠️ Before you deploy

- **Cancel-by dates and renewal terms pulled from contract metadata can be wrong.** CLM metadata drifts from executed documents — amendments get signed and not re-ingested, effective dates vary from signature dates, auto-renewal mechanics are sometimes mis-tagged. Before relying on a computed deadline for a termination or renewal decision, a licensed attorney verifies it against the signed agreement and any amendments.
- **Escalation routing follows the configured matrix; it does not make the escalation judgment.** A flagged playbook deviation may still be acceptable in context; an unflagged term may still need attention. The matrix is a router, not a reviewer.
- **Quiet weeks are not clean weeks.** A contract that isn't surfaced may be missing from the CLM, mis-tagged, or past its notice window without the metadata reflecting that. The all-clear footer means the agent ran, not that nothing needs doing.

## Deploy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export IRONCLAD_MCP_URL=...
export GDRIVE_MCP_URL=...
# Optional — enable in the manifest if your signed agreements live here
export IMANAGE_MCP_URL=...
export DOCUSIGN_MCP_URL=...
../../scripts/deploy-managed-agent.sh renewal-watcher
```

## Steering events

See [`steering-examples.json`](./steering-examples.json). The default Monday-morning sweep uses the first example. The other two cover ad-hoc counterparty-scoped runs and post-signature deviation checks.

## Security & handoffs

Contract text, counterparty messages, and CLM comments are **untrusted input.** Three-tier isolation:

| Tier | Touches untrusted docs? | Tools | Connectors |
|---|---|---|---|
| **`repo-reader`** | **Yes** | `Read`, `Grep` only | ironclad, gdrive (read-only); imanage off by default |
| `deadline-calculator` / Orchestrator | No | `Read`, `Grep`, `Glob`, `Agent` | None |
| **`alert-writer`** (Write-holder) | No | `Read`, `Write`, `Edit` | None |

`repo-reader` returns length-capped, schema-validated JSON. `deadline-calculator` is pure computation over that JSON plus the playbook configuration on disk — no MCP, no web. `alert-writer` produces `./out/renewal-alerts-<YYYY-MM-DD>.md` and emits a `handoff_request` for Slack delivery.

**Handoffs:** the orchestrator routes the `handoff_request` from `alert-writer` to a Slack send worker using the channel from the deploying team's House style configuration. The agent never sends Slack messages itself.

**Related agents:** a `handoff_request` can also route into [`deal-debrief`](../../commercial-legal/agents/deal-debrief.md) when a post-signature deviation check is needed, or into [`playbook-monitor`](../../commercial-legal/agents/playbook-monitor.md) when renewal-time deviations accumulate into a pattern. Named agents never call each other directly — routing is the orchestrator's job.

**Not guaranteed:** this agent recommends an action; a lawyer decides whether to cancel, renegotiate, or let a renewal run.

## Adaptation notes

Before you trust the output on your workflow:

- **Point at your CLM.** `IRONCLAD_MCP_URL` is the default. If signed agreements live in iManage, flip `imanage` to `default_config: { enabled: true }` in `agent.yaml` and `subagents/repo-reader.yaml` and set `IMANAGE_MCP_URL`. If they live in a Google Drive folder, rely on `gdrive` and the repo-reader's fallback search path. If they live in a CLM without a public MCP (Agiloft, Conga), wire a custom connector and update the MCP server block.
- **Set the Slack channel.** The alert-writer emits a `handoff_request` that names a Slack channel. The orchestrator reads that channel from your playbook configuration's **House style → Renewal alerts** field. Set it before the first scheduled run or the handoff will dead-letter.
- **Tune the lookahead windows.** The deadline-calculator's default tiers are overdue / 30 / 60 / 90 / 180 days. If your renewal cycle is shorter (SaaS order forms under one year) or longer (multi-year enterprise MSAs with 12-month notice windows), adjust the tier thresholds in the deadline-calculator prompt and the corresponding sections in `alert-writer.yaml`.
- **Adjust the escalation matrix.** The deadline-calculator reads your playbook's escalation matrix to decide whether to set `escalation_needed: true` and who to route to. Confirm the matrix reflects your current approval authority (who signs off on letting an auto-renewal lapse, who signs off on a renegotiation above a dollar threshold) before enabling scheduled runs. The [`escalation-flagger`](../../commercial-legal/skills/escalation-flagger) skill is loaded in `alert-writer` for formatting.
- **Confirm the work-product header.** The headless append in `agent.yaml` instructs the agent to prepend your playbook's work-product header. Verify the header language with your GC before turning this on.
- **Cadence.** Weekly is the default. High-volume teams should run daily; small teams can run monthly. The cadence lives in your own workflow engine — the cookbook does not schedule itself.

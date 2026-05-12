# Managed-agent templates for legal

Every agent in this repo ships **two ways**: as a Claude Code plugin you install today (see the vertical directories at repo root), and as a **Claude Managed Agent** template your platform team deploys behind your own workflow engine. **Same agent, same skills — pick your surface.** Each directory below is a deploy manifest that references the canonical system prompt and skills from the matching plugin, so there is one source of truth.

These are **cookbooks, not products.** They are starting points. Adapt them to your document management system, your contract repository, your Slack workspace, your notification routing, your review cadence. They will not work out of the box without that adaptation, and they are not supposed to.

Run `../scripts/deploy-managed-agent.sh <slug>` to upload skills, create leaf workers, and `POST /v1/agents` with the resolved config. Each template ships with [`steering-examples.json`](./reg-monitor/steering-examples.json) and a per-agent README covering its security tier and handoffs.

| Agent | Vertical plugin | What it watches | CMA steering event | Leaf workers |
|---|---|---|---|---|
| [`reg-monitor`](./reg-monitor/) | regulatory-legal | Regulatory feeds (Federal Register, agency RSS, TR) | `Check feeds as-of <date>, materiality: <threshold>` | feed-reader · materiality-filter · **digest-writer** |
| [`renewal-watcher`](./renewal-watcher/) | commercial-legal | Contract repository (Ironclad) for renewal and cancel-by deadlines | `Scan renewals <X>–<Y> days out, flag playbook deviations` | repo-reader · deadline-calculator · **alert-writer** |
| [`diligence-grid`](./diligence-grid/) | corporate-legal | Virtual data room (Box, Datasite, Intralinks, iManage) for new uploads + batch review | `Review folder <path> against schema <schema-id>` | doc-reader · extractor · normalizer · **grid-writer** |
| [`launch-radar`](./launch-radar/) | product-legal | Product roadmap / launch tracker (Jira, Linear, Asana) for launches needing legal review | `Scan tracker for launches in next <N> weeks` | tracker-reader · risk-classifier · **memo-writer** |
| [`docket-watcher`](./docket-watcher/) | litigation-legal | Court dockets (Trellis, CourtListener) for new filings, deadlines, and deliverables | `Watch docket <case-id> in <court>, matter <matter-id>` | docket-reader · deadline-mapper · **tracker-writer** |

**Bold** leaf = the only worker with `Write`.

## Manifest vs API

The `agent.yaml` files use the real `POST /v1/agents` field names with a few conveniences the deploy script resolves:

| Manifest convention | Resolves to |
|---|---|
| `system: {file: ../../<plugin>/agents/<agent>.md, append: "..."}` | `system: "<inlined contents + append>"` |
| `system: {text: "..."}` | `system: "<text>"` |
| `skills: [{from_plugin: ../../<plugin>}]` | uploads every `skills/*` under that dir → `[{type: custom, skill_id: ...}, ...]` |
| `skills: [{path: ../../...}]` | `skills: [{type: custom, skill_id: <uploaded-id>}]` |
| `callable_agents: [{manifest: ./subagents/x.yaml}]` | `callable_agents: [{type: agent, id: <created-id>, version: latest}]` |

> **Research preview:** `callable_agents` (multi-agent delegation) supports **one delegation level**. An orchestrator can call workers; workers cannot call further subagents.

## Cross-agent handoffs

Named agents never call each other directly. When one agent needs another (e.g., `launch-radar` surfaces a launch that needs a full review memo), it emits a `handoff_request` in its output; [`../scripts/orchestrate.py`](../scripts/orchestrate.py) (or your own event bus) routes it as a new steering event to the target session. The reference script hard-allowlists targets and schema-validates payloads.

## Security model

Legal documents and court filings are **untrusted input.** Every cookbook uses a three-tier worker split:

1. **Readers** touch untrusted documents and have `Read`/`Grep` only — no MCP, no Write, no network. They return length-capped structured JSON. Any instruction embedded in a document is data, not a command.
2. **Analyzers** receive structured JSON from readers, apply rules from the user's configuration, and have MCP read access for verification. No Write.
3. **Writers** produce the final output and are the only tier with `Write`. They never see raw documents.

The orchestrator holds no Write and reads no raw documents. It routes, it does not handle.

## Work product and privilege

Everything these agents produce is **attorney work product** in a normal deployment. The headless append in every manifest instructs the agent to prepend the work-product header from the user's plugin configuration. Confirm the header with your legal team before deploying. If your deployment processes material that should not be retained, review Anthropic's data retention settings and your own storage retention before turning this on.

## What you get and don't get

- **You get:** a working manifest structure, a reference architecture with sensible security tiers, skills proven in the Claude Code plugins, and steering-event examples.
- **You don't get:** a production-ready agent. You need to wire the MCP connectors to *your* systems, set the cadence, configure the notification routing, tune the prompts for your practice, and run your own evaluation before trusting the output.
- **You especially don't get:** a replacement for a lawyer. These agents monitor, extract, and draft. A lawyer reviews, verifies, decides.

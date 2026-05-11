# Diligence Grid — managed-agent template

## Overview

Batch document review over a virtual data room. Two modes:

- **watch** — monitors the VDR for new uploads since a cutoff, classifies each against the deploying team's diligence request-list categories, and flags uploads in high-priority categories (Material Contracts, Litigation, IP).
- **grid** — runs a tabular review against a column schema over a folder of documents. One row per document, one column per data point, every cell cited back to a verbatim source quote. The M&A diligence workhorse.

Same source as the [`corporate-legal`](../../corporate-legal) plugin — this directory is the Managed Agent cookbook for `POST /v1/agents`. Grid mode is the `tabular-review` skill, running headless across a fleet of extractor workers.

## ⚠️ Before you deploy

- **Every cell is a lead, not a finding.** A diligence grid is not a representation, a disclosure schedule, or a diligence memo until a lawyer has read the underlying documents. The verbatim quote in every cell is there so the reviewer can verify fast — use it.
- **The materiality filter and column classifications apply heuristics, not legal judgment.** A contract the schema calls immaterial may be the one that kills the deal. An "answered" cell is still wrong if the extractor misread the clause. Reviewer time scales with `unclear` + `needs_review` + `answered` — not just the flagged ones.
- **Watch mode classifies metadata and previews, not full documents.** A new upload the classifier tags "low priority" can still be the side letter that changes the deal. Treat the watch report as a queue, not a filter.
- **Counterparty-uploaded documents are untrusted input for the toolchain too.** The grid-writer's CSV formula-injection defense is mandatory, not optional — see the security section below.

## Deploy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export BOX_MCP_URL=...
export GDRIVE_MCP_URL=...
export IMANAGE_MCP_URL=...          # optional; set the toolset default to enabled if used
export DEFINELY_MCP_URL=...         # optional; for clause-structure QA of the normalizer pass
../../scripts/deploy-managed-agent.sh diligence-grid
```

## Steering events

See [`steering-examples.json`](./steering-examples.json).

## Security and handoffs

VDR documents — contracts, board minutes, side letters, counterparty uploads — are **untrusted input**. A counterparty-uploaded contract can contain strings meant to manipulate the reviewer or the downstream toolchain. Four-tier isolation keeps the Write hand and the MCP hand away from the documents:

| Tier | Touches untrusted docs? | Tools | Connectors |
|---|---|---|---|
| **`doc-reader`** | **Yes** (read-only) | `Read`, `Grep` | Box, Google Drive, iManage (read) |
| **`extractor`** | **Yes** (read-only) | `Read`, `Grep` | None |
| `normalizer` / Orchestrator | No | `Read`, `Grep`, `Glob`, `Agent` | None (definely optional, read-only) |
| **`grid-writer`** (Write-holder) | No | `Read`, `Write` | None |

`doc-reader` and `extractor` return length-capped, schema-validated JSON. The orchestrator and `normalizer` see only structured data. `grid-writer` produces `./out/diligence-grid-<date>.csv`, `./out/diligence-grid-<date>_sources.csv`, and `./out/diligence-grid-<date>-summary.md`.

**CSV formula injection.** Every cell written by `grid-writer` — values, verbatim quotes, locations, document names, column labels — is first-character-checked against `=`, `+`, `-`, `@`, tab, and carriage return. Cells that match are prefixed with a single apostrophe before they land in the CSV. Counterparty-uploaded contracts routinely contain strings that Excel and Sheets will otherwise execute as formulas (`=HYPERLINK(...)` exfil, `=cmd|...` DDE on older Excel) the moment the deal team opens the file. The sources CSV is the larger exposure — verbatim quotes are the attacker-controlled surface.

**Xlsx is a deployment concern.** The cookbook ships CSVs only. The deploying team transforms them to `.xlsx` with the workbook structure in [`corporate-legal/skills/tabular-review/references/excel-output.md`](../../corporate-legal/skills/tabular-review/references/excel-output.md) — hidden `_source` columns, cell comments carrying the quote on hover, state-based fills, `Verified` dropdown per column, `_schema` and `_summary` sheets. That transform happens on the deploying team's Excel surface (Claude in Excel, openpyxl, or Google Sheets via the Sheets API). Shipping the xlsx from the headless agent requires a trusted runtime and a macro surface this cookbook deliberately does not assume.

**Not guaranteed:** every cell this agent produces is a **lead that needs verification**, not a finding. The reviewer reads the source, checks the quote, marks the `Verified` column. A lawyer decides what goes into a rep, a schedule, or a memo.

## Adaptation notes

- **VDR URL.** Set `BOX_MCP_URL` / `GDRIVE_MCP_URL` / `IMANAGE_MCP_URL` to match your data room. The default enables Box and Google Drive; flip the `default_config` in [`agent.yaml`](./agent.yaml) if you run iManage or Datasite as primary. If your VDR is Intralinks or Datasite, add an entry to `mcp_servers` and `tools` with the matching MCP URL.
- **Column schema.** The M&A diligence standard in [`corporate-legal/skills/tabular-review/references/ma-diligence-columns.md`](../../corporate-legal/skills/tabular-review/references/ma-diligence-columns.md) is the default. Customize for your deal type — tech/IP, healthcare, real estate, government contractor, regulated financial — using the additions in that reference.
- **Output destination.** Outputs land in `./out/`. Wire them to your deal folder, Google Drive, iManage workspace, or Box folder through your deploy pipeline. Do not give `grid-writer` an MCP to upload them; a handoff to your upload step is cleaner and keeps the Write tier isolated.
- **Default mode.** Watch vs grid is selected per steering event. If your workflow is almost always one or the other, seed the steering event template in your orchestrator accordingly.
- **Request-list categories.** Watch mode classifies against the categories in the deploying team's corporate-legal `CLAUDE.md` configuration. Re-run `/corporate-legal:cold-start-interview` there before wiring watch mode into a live deal.
- **Work-product header.** `grid-writer` prepends the header from the deploying team's `## Outputs` configuration. Confirm the header with your legal team before deploying — it differs by reviewer role (lawyer vs non-lawyer).
- **Slack routing.** This agent never posts directly. Reports are files; a `handoff_request` tells your orchestrator which channel to route to. Configure the deal channel in the deploying team's `CLAUDE.md` House style section.

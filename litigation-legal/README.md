# Litigation Counsel Plugin

In-house litigation counsel support for managing a portfolio of matters. Cold-start captures your risk calibration, dispute landscape, and house style — the frame every matter is triaged against. Uniform intake turns new matters into structured log entries and per-matter history files. Status rollups and deep-dive briefings read from the log.

Built for counsel who own many matters at once, most of which are run by outside firms. This plugin is a thinking partner, not a matter management system. If you have LawVu / SimpleLegal / Onit, this does not replace them — it sits alongside, as your structured reasoning layer.

**Every output is a draft for attorney review — cited, flagged, and gated — not a legal conclusion.** The plugin does the work: reads the documents, applies your playbook, finds the issues, drafts the memo. A lawyer reviews, verifies, and decides. Citations are tagged by source so you know which ones came from a research tool and which ones need checking. Privilege markers are applied conservatively so nothing waives by accident. Consequential actions — filing, sending, executing — are gated behind explicit confirmation.

## Prerequisites

Several features reference Gmail and scheduled-tasks integrations. These require MCP servers configured in your environment — they are not bundled. Without them, outputs are written to files for manual sending:

- **Gmail MCP** — `/oc-status` creates Gmail drafts if authenticated; otherwise falls back to markdown drafts in `oc-status/[YYYY-MM-DD]/[slug].md`.
- **Scheduled-tasks MCP** — no automatic scheduling is shipped. Set a recurring calendar reminder to invoke weekly commands.

The plugin runs end-to-end without either; the integrations are additive.

## Who this is for

| Role | Primary use |
|---|---|
| **In-house litigation counsel** | All of it — intake, triage, status, history, briefings |
| **Associate GC / Deputy GC** | Portfolio oversight, board reporting rollups |
| **GC** | Quick status on the portfolio, deep dive on any one matter |

## First run: cold-start

The cold-start interview writes the *house* practice profile — persistent across every matter. Three pillars:

- **Risk calibration** — appetite, materiality thresholds, reserve/disclosure triggers, settlement authority, insurance profile, severity-likelihood matrix
- **Landscape** — company, geographies, regulated status, dispute patterns, frequent adversaries, outside counsel bench, internal stakeholders
- **House style** — board/audit committee memo format, reserve memo format, outside counsel directive style, privilege conventions, escalation norms

It offers sensible defaults at each step (e.g., a 3×3 severity-likelihood grid) and keeps everything freeform-editable. If you don't have a written framework yet, this is the thing that forces the articulation.

```
/litigation-legal:cold-start-interview
```

Your configuration is stored at `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` and survives plugin updates.

## Commands

| Command | Does |
|---|---|
| `/litigation-legal:cold-start-interview` | Cold-start → writes house `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` |
| `/litigation-legal:matter-intake` | Uniform intake → writes `matters/[slug]/` + appends to `_log.yaml` |
| `/litigation-legal:portfolio-status` | Portfolio rollup — risk distribution, upcoming deadlines, stale matters |
| `/litigation-legal:matter-briefing [slug]` | Deep briefing on one matter — read-ready before a GC or outside counsel call |
| `/litigation-legal:matter-update [slug]` | Append a dated event to a matter's history; refresh the log's `last_updated` |
| `/litigation-legal:matter-close [slug]` | Archive a matter out of the active portfolio (retained, not deleted) |
| `/litigation-legal:demand-intake [title]` | Pre-drafting context gathering for a demand letter (payment / breach / C&D / employment separation / preservation) |
| `/litigation-legal:demand-draft [slug]` | Draft the letter from intake — runs FRE 408 / privilege gate, outputs `.docx`, writes post-send checklist |
| `/litigation-legal:demand-received [path]` | Triage an inbound demand letter — options analysis, portfolio cross-check, hand off to matter/demand-intake |
| `/litigation-legal:subpoena-triage [path]` | Triage a subpoena — classify, scope/burden/privilege, objections framework, compliance plan |
| `/litigation-legal:legal-hold [slug] [--issue/--refresh/--release/--status]` | Issue, refresh, release, or report holds — writes `.docx` + updates log |
| `/litigation-legal:chronology [slug]` | Build or update a chronology from declared doc sources + uploads — tagged by significance per matter theory |
| `/litigation-legal:oc-status` | Draft weekly OC status-request emails across the portfolio; Gmail drafts if MCP available |
| `/litigation-legal:claim-chart` | Build or review an element chart — patent claim chart (infringement / invalidity / review) or civil element chart (any cause of action or defense) with gap detection |

## Skills

| Skill | Purpose |
|---|---|
| **cold-start-interview** | House practice profile — risk calibration, landscape, style |
| **matter-intake** | Uniform intake questions; writes matter file + log row |
| **portfolio-status** | Rollup across the log — risk, deadlines, staleness |
| **matter-briefing** | Deep read of one matter from its file + history |
| **matter-update** | Structured event append; updates `last_updated` in log |
| **matter-close** | Archive semantics; captures outcome |
| **demand-intake** | Adaptive context gathering for a demand letter — parties, facts, leverage, privilege filters |
| **demand-draft** | FRE 408 / privilege gate, then drafts `.docx` with `[CITE:___]` placeholders; writes post-send checklist; offers matter creation |
| **demand-received** | Triage an inbound demand — merit, options, portfolio cross-check |
| **subpoena-triage** | Classify subpoena, analyze scope/burden/privilege, produce objections framework + compliance plan |
| **legal-hold** | Issue / refresh / release / status-report on holds; writes `.docx` notice; updates log's `legal_hold` fields |
| **chronology** | Extract dated events from declared doc sources + uploads; de-dupe; tag significance per matter theory |
| **oc-status** | Weekly portfolio-wide OC status-request email drafter; markdown + Gmail drafts |
| **claim-chart** | Patent claim chart (infringement / invalidity / review) or civil element chart (any cause of action or defense). Element-by-element mapping, every cell pin-cited, gap detection. Ships with a cause-of-action template library. |

## Interactive commands vs. scheduled agents

The commands above run when you invoke them — for when you're working a matter. The agents below run on a schedule — for what moves while you're not looking:

| Agent | What it watches | Default cadence |
|---|---|---|
| **docket-watcher** | Court dockets for matters in the active portfolio — pulls new filings, computes candidate deadlines, cross-references each matter's history and deliverables | Weekly |

## How the data is organized

```
litigation-legal/
├── CLAUDE.md                          # HOUSE practice profile — risk, landscape, style
├── matters/
│   ├── _log.yaml                      # the portfolio ledger (one entry per matter)
│   └── [matter-slug]/
│       ├── matter.md                  # matter-specific intake + theory + posture
│       ├── history.md                 # append-only event log
│       ├── chronology.md              # advocacy-facing timeline (on demand)
│       └── legal-hold-v[N].docx       # hold notices (issue, refresh, release)
├── demand-letters/                    # outbound demands
│   └── [slug]/
│       ├── intake.md
│       ├── draft-v1.docx
│       └── checklist.md
├── inbound/                           # incoming demands, subpoenas, regulator letters
│   └── [slug]/
│       ├── incoming.[ext]
│       ├── triage.md
│       └── response-v1.docx           # if we respond
└── oc-status/                         # weekly OC status-request drafts
    └── [YYYY-MM-DD]/
        ├── _summary.md
        └── [slug].md                  # one email per matter
```

Separate folders because each has a distinct workflow. Matters get tracked in the portfolio; demand letters and inbound items may or may not rise to a matter; OC status drafts are periodic artifacts. When things relate, the `related_matters` field and cross-links in `matter.md` tie them together.

The log is YAML because it's parseable by rollup skills. Per-matter files are markdown because that's where you read and edit. Both are checked into the folder as plain text — nothing proprietary.

## Connectors and citation verification

**Connect a research tool first — the citation guardrails depend on it.** Without one, every cite is tagged `[verify]` and the reviewer note above each deliverable records that sources weren't verified. The plugin works either way; it just does more of the verification for you when a research tool is connected.

The legal research connectors in this plugin aren't just data sources — they're the difference between a verified citation and a citation you have to check. A citation retrieved through **CourtListener** (U.S. court opinions, PACER dockets, citation verification), **Trellis** (state trial court dataset — dockets, rulings, verdicts, judge and opposing counsel analytics), **Everlaw** (your eDiscovery projects), or **Aurora** (read-only Consilio ediscovery — every record cited to source) is tagged with its source and can be traced back. A citation from the model's knowledge or from web search is tagged `[verify]` or `[verify-pinpoint]` and should be checked against a primary source before anyone relies on it. The plugin tiers its citations so your verification time goes where it matters.

## Integrations

Ships with the general bucket of connectors in `.mcp.json`:

- **Slack** — search messages, read channels, find discussions
- **Google Drive** — search, read, and fetch documents

Designed to be useful with nothing connected. If/when you want to pull from Relativity, DISCO, CLMs, or email, integration skills can be added without changing the core architecture.

## How it learns

Your practice profile at `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## Notes

- Every skill reads from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` first. If your risk appetite changes or you bring on new outside counsel, update it — don't paper over it in individual matters.
- `## Company profile` is the first section of `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` by convention. If you run other `-legal` plugins, you can copy it across rather than re-entering the same context.
- `_log.yaml` is the source of truth for portfolio state. Keep it clean.
- Matter history is append-only. If something was wrong, note the correction as a new entry — don't edit the past.
- Closed matters stay in `_log.yaml` (searchable history). `/portfolio-status` filters them out of active rollups by default.

## Inline marker conventions

Three markers appear in skill outputs and drafts. They are not disclaimers — they are action items:

- `[CITE: specific cite needed]` — a legal authority placeholder. Counsel fills or confirms before sending.
- `[VERIFY: specific fact]` — a factual assertion not yet confirmed to source. Counsel verifies before relying.
- `[SME VERIFY: specific judgment call]` — a judgment (merit read, significance tag, objection strength, privilege status) that requires subject-matter expert review. SME = licensed attorney qualified in the relevant jurisdiction / area. Used liberally — anything judgment-heavy should carry this.

A draft or triage with unresolved markers is not final, regardless of how polished it reads.

## Testing & QA


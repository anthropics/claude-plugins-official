# demand-letters/ — pre-litigation demand work

This folder holds the work product for every demand letter the counsel sends: payment demands, breach/cure notices, cease-and-desist, employment separation demands, preservation demands.

Separate from `matters/` because:

- Not every demand letter rises to a tracked matter. Small-dollar payment demands and routine collections don't need a log row.
- Every demand letter has the same workflow shape (intake → draft → send → checklist), regardless of whether it later becomes a matter.
- When a demand letter does become a matter, the matter's `matter.md` cross-links back here — the drafting history stays with the letter.

## Layout

```
demand-letters/
├── _README.md                     # this file
└── [slug]/
    ├── intake.md                  # context gathering, strategy, leverage, privilege filters
    ├── draft-v1.docx              # the letter (v2, v3 as iterated)
    └── checklist.md               # post-send checklist — delivery, copies, calendared deadlines, follow-up
```

## Slug conventions

`[type]-[counterparty]-[yyyy-mm]`. Examples:

- `payment-acme-2026-04`
- `ceasedesist-competitor-x-2026-04`
- `breach-supplier-2026-04`
- `separation-smith-2026-04`
- `preservation-vendor-2026-04`

## Workflow

1. `/litigation-legal:demand-intake [title]` → runs adaptive intake, writes `intake.md`
2. `/litigation-legal:demand-draft [slug]` → runs FRE 408 / privilege / waiver checklist, drafts `.docx`, writes `checklist.md`, offers to create a matter

## Relationship to matters

After a demand letter is drafted, `demand-draft` assesses materiality (heuristic from house `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`) and offers to create a matter. If yes, a matter row goes into `matters/_log.yaml` with `source: demand-letter`, and `matters/[matter-slug]/matter.md` links back to this demand-letter's folder.

Immaterial demands stay here only. They're still a work-product record — just not portfolio-tracked.

## Corrections and versions

Never overwrite a sent draft. If a letter was sent and needs revision (e.g., a supplemental demand), start `draft-v2.docx`. The history of versions is itself useful record.

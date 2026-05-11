---
name: tabular-review
description: >
  Tabular review — one row per document, one column per data point, every cell
  cited to source. Built for M&A diligence ("review these 200 target contracts
  for change-of-control, assignment, and MAC clauses") but works for any batch
  review that needs a spreadsheet out the other end. Use when user says "tabular
  review", "review grid", "build a grid", "extract these fields from these
  contracts", "review these documents for X, Y, Z", "give me a spreadsheet of",
  "batch review", or points at a folder of documents and asks to compare them.
---

# /tabular-review

1. Load `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → diligence structure, thresholds, house format.
2. Confirm: what documents, what columns, where does the output go.
3. Build the typed schema. Write `.review-schema.yaml`. Confirm with the user.
4. Sample run (3–5 docs). Adjust schema. Confirm.
5. Fan out — one sub-agent per document, parallel. Each cell: value + state + verbatim quote + location.
6. Normalization pass. Flag outliers and inconsistencies.
7. Output: `.xlsx` or Google Sheets (ask which), plus `.csv` + `_sources.csv` + markdown always. Work-product header.
8. Summary: verification workload (counts of not_present / unclear / needs_review per column), flagged columns, where the files are, reminder that every cell is a lead not a finding.

```
/corporate-legal:tabular-review
/corporate-legal:tabular-review --schema .review-schema.yaml --docs ./vdr/02-Contracts/
/corporate-legal:tabular-review --template ma-diligence
```

**`--schema <path>`:** Use an existing schema file instead of building one. Useful for re-runs and incremental additions.

**`--template <name>`:** Start from a template in `references/`. Currently: `ma-diligence`.

**`--docs <path>`:** Document source. A local folder, a Drive folder ID, or a VDR path. If omitted, asks.

**`--output <xlsx|gsheets|csv>`:** Output format. If omitted, asks.

**`--sample <n>`:** Sample size for the schema check. Default 5.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/corporate-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/corporate-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

You have a pile of documents and a list of questions you need answered consistently across every one. A diligence request list. A vendor contract audit. A lease portfolio review. The output is a table: document rows, data-point columns, and every cell traceable to the exact words in the source.

This is not issue spotting. `diligence-issue-extraction` finds the 30 problems hiding in 2,000 documents. This skill answers the same 15 questions about all 2,000 documents. Both are legitimate; they answer different questions.

This is also not a replacement for a human reading the document. Every cell this skill produces is a **lead that needs verification**, not a finding. The output is designed to make verification fast, not to skip it.

## Load context

- `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → diligence structure, materiality thresholds, house format preferences
- `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/deal-context.md` if working a specific deal
- An existing schema file if the user has one (`.review-schema.yaml`)

## The column type system

The thing that makes a tabular review useful is that Column C means the same thing in row 1 as in row 200. Free text drifts. Types hold.

Every column has a **type** that constrains the answer format:

| Type | What it returns | Use for |
|---|---|---|
| `verbatim` | Exact quote from the document, character-for-character | Defined terms, operative clause language, anything where the words matter |
| `classify` | One value from a fixed list you define | Yes/No, present/absent, clause variants (e.g., "sole consent" / "consent not unreasonably withheld" / "silent") |
| `date` | ISO date | Effective date, expiration, termination notice deadline |
| `duration` | Number + unit | Term length, notice period, survival period |
| `currency` | Number + currency code | Caps, thresholds, fees, purchase price references |
| `number` | Bare number | Counts, percentages, page references |
| `free` | Short free text summary | Use sparingly — this is the type that drifts. Only when the others genuinely don't fit. |

**The verbatim rule:** Every non-`verbatim` column also captures the exact source quote that supports the answer, as a companion field. The answer in the cell is the interpretation; the quote is the evidence. A `classify` cell that says "consent not unreasonably withheld" is useless without the sentence it came from, because the reviewer's job is to check whether that's the right read.

## The three states of "not found"

A blank cell hides information. Force one of three explicit states whenever you can't produce a positive answer:

| State | Meaning | When to use |
|---|---|---|
| `not_present` | The document was read and the clause is not there | You are confident the subject matter isn't addressed |
| `unclear` | Something is there but you can't classify it confidently | Ambiguous drafting, partial clause, conflicting provisions |
| `needs_review` | You found something but a human must make the call | Edge case, unusual drafting, the answer depends on a judgment the schema doesn't capture |

These are three different pieces of information. A deal team handles "the contract is silent on assignment" very differently from "the assignment clause is ambiguous." Collapsing them into one blank cell loses the distinction.

## Workflow

### Step 0: What and where

Confirm:
1. **Documents.** Where are they? VDR MCP (Box, Datasite, iManage), local folder, Google Drive folder, or a list of files. How many? If >200, warn that this will take a while and offer to start with a materiality-filtered subset.
2. **Schema.** What columns? Two paths:
   - User picks a template from `references/` (M&A diligence standard is the default)
   - User describes columns in natural language and you structure them into the typed schema
3. **Output.** Excel (`.xlsx`) or Google Sheets — ask which the team works in. CSV and markdown always written as fallbacks. Output goes to the deal folder, Drive, or wherever the user says.

### Step 1: Build and confirm the schema

Turn the user's column list into a structured schema. For each column: a stable `id`, a human `label`, a `type`, a `prompt` (the question a reviewer reading the document would ask), and for `classify` columns an `options` list.

Write it to `.review-schema.yaml` next to the output. This file is the reusable artifact — the user can edit it, add a column, re-run against new documents. Show it to the user and confirm before fanning out.

```yaml
schema:
  name: "M&A Diligence — Project [Code]"
  created: 2026-05-07
  columns:
    - id: counterparty
      label: "Counterparty"
      type: verbatim
      prompt: "Who is the contracting party other than the target?"
    - id: effective_date
      label: "Effective Date"
      type: date
      prompt: "When did the agreement become effective?"
    - id: change_of_control
      label: "Change of Control"
      type: classify
      options: [silent, consent_required, consent_not_unreasonably_withheld, automatic_termination, notice_only]
      prompt: "Does the agreement address a change of control of the target? What does it require?"
    - id: assignment
      label: "Assignment Restrictions"
      type: classify
      options: [silent, consent_required, consent_not_unreasonably_withheld, freely_assignable, assignable_to_affiliates]
      prompt: "Can the target assign this agreement? What restrictions apply?"
    # ... more columns
```

### Step 2: Sample run

Do not fan out to 200 documents on an untested schema. Run 3–5 documents first. Show the user the rows. Look for:
- Columns where most answers are `unclear` — the prompt is ambiguous, rewrite it
- `classify` columns where answers don't fit the options — add options or change to `free`
- `verbatim` columns returning paraphrases — reinforce that it must be character-for-character

Adjust the schema, re-run the sample, confirm. This saves the user from a full run that has to be thrown out.

### Step 3: Fan out

One sub-agent per document, in parallel. Each sub-agent:

1. Reads the entire document (not a RAG chunk — the whole thing).
2. For each column, finds the relevant provision.
3. Returns a structured row: for each column, `{value, state, quote, location}`.
   - `value` is the typed answer (or null if `state` is not `answered`)
   - `state` is `answered | not_present | unclear | needs_review`
   - `quote` is the verbatim supporting text (exact, no paraphrase, no ellipsis inside a sentence — if you cut, cut at sentence boundaries and mark it)
   - `location` is where the quote lives (section number, heading, page — whatever the document gives you)

**The quote is not optional, and the verbatim rule is mechanical, not exhortation.** Each sub-agent must comply with all of the following before returning a cell with `state: answered`:

- The `quote` MUST be a character-for-character copy of contiguous text from the source document, retrievable at the `location` the sub-agent cites. Do NOT compose a quote from a section heading plus standard boilerplate you expect to be there. Do NOT paraphrase and call it verbatim. Do NOT reconstruct a quote from memory of how such clauses "usually" read. Do NOT fill gaps in the source with ellipsis-stitching across non-contiguous text.
- The `location` must be specific enough for the normalization pass to re-open the document and re-read the same span — a section number, heading, or page reference the reviewer can navigate to.
- If the sub-agent cannot locate and copy the exact text (source truncated, OCR garbage, provision implied but not written, section heading visible but body not loaded), the cell state is `needs_review`, the `value` is null, and `notes` MUST contain `quote_unavailable: <reason>`. It is NEVER acceptable to set `state: answered` with a composed or reconstructed quote.
- The same rule applies to `verbatim`-typed columns AND to the companion source quotes attached to `classify` / `date` / `duration` / `currency` / `number` / `free` cells. The supporting quote carries the same verbatim obligation as the cell value.

The normalization pass in Step 4 spot-checks this by re-reading the source at the cited `location` and comparing the stored `quote` character-for-character against the source text. A mismatch downgrades the cell to `needs_review`, notes `quote_mismatch`, and flags the whole column for a wider spot-check — if one sub-agent composed a quote, others in the same run may have too.

### Step 4: Normalize

After the fan-out, read the whole table column by column. This is the pass that catches the failure mode of every tabular review tool: the same clause interpreted inconsistently across documents.

For each `classify` column:
- Check that every `answered` value is in the options list. Outliers get re-classified or bumped to `needs_review`.
- Check for clusters: if 180 documents say `consent_required` and 20 say `consent_not_unreasonably_withheld`, that's probably real. If 195 say `consent_required` and 5 say `freely_assignable`, look at the 5 — they're either genuinely different or misclassified.

For each `date` / `duration` / `currency` column:
- Check format consistency. Normalize.
- Flag implausible values (a 99-year term, a $1 cap) as `needs_review`.

For each `verbatim` column AND for the companion source quotes on every other column:
- Spot-check by re-opening the source document at the cited `location` for a random sample (at least 3–5 rows per column, or 10% of rows, whichever is larger) and comparing the stored `quote` character-for-character against the source.
- If any quote is composed, paraphrased, reconstructed, or cannot be located at the cited span: downgrade that cell to `needs_review` with `quote_mismatch` in notes, and flag the whole column — expand the spot-check to the rest of the column rather than assuming the other rows are clean. One fabricated quote is enough to justify widening the check.
- A cell with `state: answered` and a mismatched quote is a higher-severity failure than an `unclear` or `needs_review` cell — it misrepresents the evidence trail. Downgrade aggressively.

### Step 5: Output

Write the table in three formats:

**Markdown** (always, for in-session review):
```markdown
| Document | Counterparty | Effective Date | Change of Control | Assignment | ⚠️ Flags |
|---|---|---|---|---|---|
| Vendor MSA — Acme | Acme Corp | 2023-04-01 | consent_required | consent_required | — |
| Supply Agmt — Beta | Beta LLC | 2021-11-15 | ⚠️ unclear | silent | CoC ambiguous §14.2 |
```

**CSV** (`.csv`, always):
One file for the values, one companion file for the quotes and locations (`_sources.csv`). Keeps the main file clean and the evidence trail complete.

**Excel** (`.xlsx`) or **Google Sheets** — whichever the user works in. Ask; don't guess. Both follow the same workbook structure (see `references/excel-output.md` and `references/gsheets-output.md`). For Excel: Claude in Excel (Office agent) if available, `openpyxl` fallback. For Sheets: Sheets MCP if available, Sheets API via ADC, CSV-import fallback. In the spreadsheet output:
- Each data column is paired with a hidden source column containing the quote and location. Cell comments (Excel) or notes (Sheets) on the visible column surface the quote on hover.
- Color code by state: white = answered, yellow = unclear or needs_review, gray = not_present.
- A `Verified` column per data column, blank by default. The reviewer marks it. This is the verify/flag pattern that makes the table auditable — the deal team can see at a glance what a human has actually checked.
- A `_schema` sheet with the column definitions, so the file is self-documenting.

Prepend the work-product header from the plugin config `## Outputs` as a top row. Alongside it, include a distribution note:

> This review is derived from source documents that may be privileged, confidential, or both. It inherits the sources' privilege and confidentiality status — distribution beyond the privilege circle can waive privilege. Store with the matter's privileged files and make distribution decisions deliberately.

### Step 6: Summary

After the table is written, give the user a one-screen readout:
- Document count, column count, rows completed
- Count of `not_present`, `unclear`, `needs_review` per column — this is the verification workload
- Any columns where the normalization pass flagged >10% of rows
- Where the output files are
- A reminder: every cell is a lead, not a finding. Verification required before this informs a rep, a schedule, or a memo.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- **It does not replace reading the documents.** It tells you where to look.
- **It does not produce confidence scores.** A 0.73 is not information. The `unclear` / `needs_review` states and the verbatim quotes are the confidence signal — if the quote doesn't support the value, flag it.
- **It does not silently skip documents.** Every document the user pointed at gets a row. A document that couldn't be read gets a row of `needs_review` with a note.
- **It does not pretend a paraphrase is a quote.** The evidence trail is the whole point.

## Relationship to other skills

- `diligence-issue-extraction` finds issues; this extracts data points. If an extraction reveals an issue (a MAC clause that references a specific earnings target, a poison pill), note it and suggest running diligence-issue-extraction on that document.
- `material-contract-schedule` builds one specific table (the disclosure schedule). It can consume this skill's output directly — the schedule is a filtered, reformatted view of a tabular review.
- `ai-tool-handoff` hands bulk review to Luminance/Kira when the corpus is too large or the team prefers a dedicated platform. This skill is the in-house option for anything it can handle — run it first, hand off the residue.

## Output safeguards

Every output gets the work-product header. Every cell gets a source citation or a flagged state. The summary explicitly says verification is required. The Excel `Verified` column makes the verification state auditable. This is not a tool that lets you skip reading; it's a tool that makes reading faster.

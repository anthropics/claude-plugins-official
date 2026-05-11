---
name: ai-tool-handoff
description: >
  Detects when Luminance, Kira, or a similar bulk-review tool is in use,
  hands off the high-volume clause extraction to it, and QAs its output
  per the trust level in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. Use when user says "send to Luminance",
  "bulk review", "AI extraction", or when diligence-issue-extraction hits
  a high-volume category.
---

# AI Tool Handoff

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/corporate-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/corporate-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Luminance and Kira are good at one thing: reading 500 contracts and finding every change-of-control clause. They're less good at judgment — deciding whether a particular CoC provision is actually triggered by this deal structure.

This skill hands off the bulk extraction to the right tool, then runs the QA layer on what comes back.

**Before you hand off:** try `tabular-review` first (`/corporate-legal:tabular-review`). For anything the user's environment can handle — a few hundred documents, a defined column schema — native tabular review is faster to set up, has no per-document cost, and keeps the work product local. Hand off to Luminance/Kira when the corpus is genuinely too large, the team already has a license and workflow, or the matter requires a tool with a validated provenance chain.

## Load context

`~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → AI-assisted review:
- Tool in use (Luminance / Kira / none)
- What it's used for (which clause types)
- Trust level (use as-is / spot-check / full re-review)
- Handoff process (who loads, who QAs)

If `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` says no AI tool → this skill is a no-op. Everything goes through diligence-issue-extraction directly.

## When to hand off

Hand off when all of:
- Category has >50 documents (below that, faster to just read them)
- Extraction target is a clause type the tool is good at (CoC, assignment, exclusivity, MFN, termination, auto-renewal)
- Documents are reasonably uniform (all customer contracts on similar paper — not a mix of contracts, letters, and board minutes)

Don't hand off:
- Bespoke or heavily negotiated documents
- Side letters and amendments (context-dependent, tools miss the interaction with the main agreement)
- Anything where the question is "what does this mean for the deal" not "does this clause exist"

## The handoff

### Step 1: Prepare the batch

- Identify documents for the batch (from VDR inventory)
- Specify extraction targets per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` (which clause types)
- Note the materiality threshold so tool output can be filtered

### Step 2: Load (or instruct the loader)

Per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` — who loads. If it's you, generate the load instructions. If it's someone else, generate the request:

```markdown
## [Tool] Load Request — [Deal code] — [Category]

**Documents:** [N] docs from VDR folder [path]
**Load to:** [Tool workspace/matter]
**Extraction targets:**
- Change of control / assignment
- Exclusivity
- [etc. per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`]

**Filter output:** Flag only where extraction target is present — no need for "no CoC clause found" for every doc.

**Return by:** [date]
```

### Step 3: QA the output

When the tool returns results, apply the trust level:

**"Use as-is":** Ingest directly into diligence findings. (Only if `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` says this — it's rare.)

**"Spot-check X%":** Randomly sample X% of flagged documents. For each, read the actual clause and compare to the tool's extraction. If error rate is low, accept the batch. If errors found, widen the sample.

**"Full human review of flagged":** Tool narrows the universe (500 docs → 80 with CoC clauses). Human reads all 80. Tool saved the time of reading the 420 clean ones.

### Step 4: Judgment layer

The tool found the clauses. Now apply judgment:

For each flagged CoC provision: is it actually triggered by this deal?
- Stock sale vs. asset sale vs. merger — different triggers
- "Change of control" defined how in the contract — majority ownership? board control? something else?
- Is there a carve-out for this type of transaction?

This is the part the tool can't do. Output goes to diligence findings in house format.

## Output

> The QA summary below is derived from VDR documents that are privileged, confidential, or both. It inherits the sources' privilege and confidentiality status — distribution beyond the privilege circle can waive privilege. Store with the matter's privileged files.

```markdown
## AI Tool Handoff Summary — [Category]

**Tool:** [Luminance / Kira]
**Documents processed:** [N]
**Extraction targets:** [clause types]

### QA

**Trust level:** [per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`]
**Sample size:** [N] docs spot-checked
**Error rate:** [X]% — [Accepted / Widened sample / Full re-review triggered]

### Results

| Clause type | Docs flagged | After judgment layer | Material |
|---|---|---|---|
| Change of control | [N] | [N actually triggered by deal structure] | [N above threshold] |
| Assignment | [N] | [N] | [N] |

**→ [N] findings added to diligence issues**
**→ [N] consents added to closing checklist**
```

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't run Luminance or Kira — it manages the handoff and QA. A human (or the tool's own interface) runs the extraction.
- It doesn't replace the tool's output with its own judgment entirely — if `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` says spot-check 10%, check 10%, not 100%.
- It doesn't decide the trust level — that's in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`, set at cold-start based on the team's experience with the tool.

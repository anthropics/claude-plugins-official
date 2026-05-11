---
name: amendment-history
description: >
  Trace how a contract has changed across its base agreement and all amendments —
  either a summary of all changes over time, or a provision trace for a specific
  clause. Use when the user says "what changed in this contract over time", "show
  me the amendment history", "where's the latest [clause]", "how has [provision]
  evolved", or uploads multiple versions of an agreement.
argument-hint: "[file(s) | [CLM ID (coming soon)] | [repository link (coming soon)]] [--provision <clause name>]"
---

# /amendment-history

Loads a base agreement and all amendments, then either summarizes what
changed over time or traces a specific provision to its current
controlling language.

## Instructions

1. **Get the documents:** From file upload, [CLM ID (coming soon)], or [repository link (coming soon)]. Accept multiple files in one invocation. If none
   provided, ask.

2. **Detect the mode** by parsing the request per the mode
   detection rules below. If a provision name is clearly stated, go straight
   to Mode 2. If no provision is mentioned, run Mode 1. Ask only if
   genuinely ambiguous.

3. **Run the workflow below.** Follow it fully.

4. **Offer follow-ups after output:**
   - "Want me to trace another provision?"
   - "Want a full playbook review of the current agreement as amended?"
     (routes to vendor-agreement-review)
   - "Want a stakeholder summary of the key changes?"
     (routes to stakeholder-summary)

## Examples

```
/commercial-legal:amendment-history acme-msa.pdf amendment-1.pdf amendment-2.pdf
```

```
/commercial-legal:amendment-history --provision indemnity
```

```
/commercial-legal:amendment-history
[paste agreement and amendment text]
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/commercial-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/commercial-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Contracts accumulate amendments. By the third amendment, nobody remembers
what the original said or which version of a clause controls. This skill
reads the base agreement and all amendments in chronological order and
either summarizes what changed across the whole contract or traces a
specific provision through every version to find the current controlling
language.

## Mode detection

Parse the user's request to determine which mode to run. Do not ask
which mode unless the request is genuinely ambiguous.

**Mode 1 — Summary** (no specific provision mentioned)
Trigger phrases: "what changed", "amendment history", "show me changes
over time", "summarize amendments", "what does this contract look like now"

**Mode 2 — Provision trace** (specific clause or topic named)
Trigger phrases: "where's the [clause]", "latest [provision]", "how did
[term] change", "find the indemnity", "what does it say now about [topic]"

Common provision mappings:
- "indemnity" / "indemnification" → indemnification section
- "liability" / "liability cap" → limitation of liability
- "termination" → term and termination
- "data" / "privacy" / "DPA" → data protection provisions
- "IP" / "intellectual property" → IP ownership and licenses
- "price" / "fees" / "payment" → payment terms
- "auto-renewal" / "renewal" → renewal mechanics

If the term is ambiguous and maps to more than one provision, list the
candidates and ask which one:
> "I found [N] provisions related to [term] — [list them]. Which one?"

If the overall request is ambiguous between modes, ask one question:
> "Summary of all changes across the contract, or trace a specific
> provision — like indemnity, liability, or termination?"

---

## Step 1: Load and order the documents

Accept documents from any of these sources:

**[CLM integration coming soon] (if connected):**
Search by counterparty name or agreement title. Pull the base agreement
and all amendments. Record metadata typically includes execution dates —
use these to establish chronological order.

**[Document repository integration coming soon] (if connected):**
Search by counterparty name or filename. Look for files matching patterns
like "Amendment", "Addendum", "Amendment No. 1", "First Amendment", or
numbered suffixes. Pull all matches and sort by file date or filename
numbering.

**Direct upload:**
User provides files directly. In most cases the ordering is
self-explanatory from document titles (e.g., "Amendment No. 1",
"Second Amendment", "Addendum A") or dates visible in the filename
or document header — proceed without asking.

Only ask the user to confirm ordering if:
- Filenames give no indication of sequence (e.g., "agreement-final.pdf",
  "agreement-v2.pdf", "agreement-markup.pdf")
- Dates are absent from both filenames and document headers
- Two documents appear to be the same amendment version

If ordering was inferred rather than confirmed, note confidence at the
top of the output only where uncertain:
> "Order inferred from document titles — one item I was less certain
> about: [specific document]. Confirm if this affects your review."

**Ordering rules:**
- Always establish chronological order before reading content.
- If execution dates are available in metadata, use them.
- If not, look for dates in the document header or recitals
  ("This Amendment, dated as of...").
- Amendments often reference the agreement they modify ("this Amendment
  to the Master Services Agreement dated [X]") — use these references
  to confirm the chain.

---

## Privilege inheritance

This skill reads the base agreement and amendments — often privileged or confidential in their own right, and typically used for privileged analysis. The output inherits the source's privilege and confidentiality status. Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` `## Outputs` to every output below, distribute only within the privilege circle, and store it where privileged materials live. Strip the header before any external delivery.

## Step 2: Read and index

Read each document in chronological order. For each, extract:
- Document type (base agreement, amendment number, addendum, etc.)
- Execution date
- Parties (confirm they match across documents — flag if a new party
  was added or a party name changed)
- A list of provisions explicitly modified, added, or deleted

Build a working index before producing output. Use it internally to
drive the output — do not show it to the user.

---

## Mode 1: Summary of all changes

### Section reference rule

Every finding must include an inline section reference so the reader
can verify against the source document without searching:

  "Termination for convenience (§12.3): Added. Customer may terminate
  on 90 days written notice with no fee after the initial term."

If a provision spans multiple sections or the section number changed
across amendments, cite all references:
  "Indemnification (§9.1 base; §9.1 restated in Amendment 5)"

### Output format

```markdown
# Amendment History: [Counterparty] — [Agreement type]

**Base agreement:** [date]
**Amendments:** [N] ([date of first] → [date of last])
**Last amended:** [date]

---

## What changed — chronological

### Amendment 1 — [date]
**Purpose:** [one sentence — why this amendment existed, from recitals
or clear from context. If not stated, omit rather than guess.]

**Material changes:**
- [Provision] (§[X.X]): [what it said before → what it says now,
  in plain English]
- [New provision added] (§[X.X]): [what it does]
- [Provision deleted] (§[X.X]): [what was removed and why it matters]

### Amendment 2 — [date]
[same structure]

[repeat for each amendment]

---

## Net current state

| Provision | Current position | §Ref | Last changed |
|---|---|---|---|
| [clause] | [plain English summary] | §[X.X] | Amendment N, [date] |
| [clause] | [unchanged from base] | §[X.X] | Base agreement |

---

## Watch items
[Flag anything that looks inconsistent — e.g., an amendment modifying
a provision that was already deleted, contradictory language between
amendments, a party name that changed without a formal assignment,
or a provision where the section number shifted across documents.
Include section references on every flag.]
```

---

## Mode 2: Provision trace

### Output format

Show only what changed. Do not list amendments where the provision
was untouched — skip them entirely.

```markdown
# Provision Trace: [Provision name]
## [Counterparty] — [Agreement type]

---

### Original — [Base agreement date], §[X.X]
> "[exact quote]"

*Plain English:* [one sentence]

---

### Amendment [N] — [date], §[X.X]

**Was:**
> "[exact quote of prior language]"

**Now:**
> "[exact quote of replacement language]"

*What changed:* [one sentence — practical effect on the parties]

---

[Only subsequent amendments that touched this provision appear here.
All others are omitted.]

---

## Current controlling language

**§[X.X] — [source document, date]**
> "[exact quote]"

*Plain English:* [one sentence]

---

## Watch items
[Flags, inconsistencies, open questions — with section references.
Common items to check: whether the provision is subject to or carved
out of the liability cap; whether the section number shifted across
amendments; whether the amendment language conflicts with another
provision.]
```

If the provision was never amended after the base agreement:
> "This provision has not been modified by any amendment. Original
> language controls. §[X.X], base agreement, [date]."

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It does not determine which document controls in the event of a
  conflict between the base agreement and an amendment — that is a
  legal interpretation question. It flags conflicts and routes to Legal.
- It does not draft new amendments.
- It does not compare against the playbook in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` — that is the
  vendor-agreement-review skill's job. This skill is purely historical.
- It does not infer what an amendment means if the language is
  ambiguous — it quotes exactly and flags ambiguity for Legal.

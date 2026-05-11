---
name: matter-intake
description: Intake a new matter — uniform questions covering identification, conflicts, source, risk triage, materiality, outside counsel, owners, legal hold, and key dates; writes matter.md and history.md and appends a structured row to _log.yaml. Use when the user says "new matter", "intake this matter", or wants to bring a new matter into the portfolio.
argument-hint: "[optional matter name]"
---

# /matter-intake

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → risk calibration (for triage), landscape (for context, conflicts method), stakeholders (for who to loop in).
2. Follow the workflow and reference below.
3. Run the uniform intake: identification, conflicts check, source, risk triage, materiality, outside counsel, internal owners, legal hold, key dates, initial posture.
4. Generate slug from matter name (lowercase, hyphens, year).
5. Create `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` — full narrative intake.
6. Create `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md` — seeded with the intake as the first entry.
7. Append structured row to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`.
8. Confirm with the user: "Here's the row I'll write — any edits?"

---

# Matter Intake

## Purpose

Every new matter goes through the same intake so the portfolio stays comparable. Uniform rows in `_log.yaml` let the status skill roll up. Narrative in `matter.md` captures what the row can't. History file seeded here becomes the event record.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` — risk calibration (triage thresholds, materiality, settlement ladder), landscape (stakeholders, outside counsel bench).
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — to confirm slug uniqueness.

## The intake

### 1. Identification

- Matter name (as commonly referenced, e.g., "Acme v. Us 2026")
- Counterparty
- Matter type: `contract | employment | ip | regulatory | investigation | product | other`
- Our role: `plaintiff | defendant | claimant | respondent | investigated`
  - If the practice profile's `## Side` is `plaintiff`, `defense`, or a "both — default X" variant, pre-fill the role from that default and confirm. If `## Side` is `varies by matter`, ask cold. Never silently assume a posture the practice profile hasn't set.
  - The role drives downstream skills: plaintiff-posture matters route risk triage to case value / contingency economics; defense-posture matters route to exposure / reserves / insurance tender.
- Jurisdiction (court, arbitration forum, or regulatory body)

### 2. Conflicts check

Before going further, run the conflicts step per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → Conflicts clearance.

- **Status:** `cleared | pending | not-run | waived`
- **Method:** match what `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` declares (`corporate-legal | outside-counsel | system-check | informal | other`). If the declared method is `informal`, say so — the record still captures that a counsel's-judgment check was the basis.
- **Cleared by:** name / team / firm
- **Cleared date:** YYYY-MM-DD
- **Checked against:** brief list of the specific names/entities run (counterparty, known affiliates, adverse counsel if known, key witnesses). Thin is fine; "no" is not.
- **Notes:** anything flagged but cleared (e.g., "Smith on our board sat on counterparty's board 2019–2021 — cleared as non-overlapping to this matter").

Behavior by status:

- `cleared` → proceed.
- `pending` → proceed with intake; flag prominently in `matter.md` and in the log row that conflicts are outstanding; surface again on every `/matter-update` and in `/portfolio-status` until resolved.
- `waived` → rare; requires a conflict-waiver rationale (writing the waiver is outside this skill — capture that one exists, who signed it, and where it lives).
- `not-run` → **STOP. This is a gate.** The skill will not create `matter.md`, `history.md`, or a `_log.yaml` entry until the conflicts posture is resolved. Three acceptable paths:

  **Path 1 — Run conflicts now.** Pause this intake. Clear per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` Conflicts clearance. Return with `status: cleared` or `status: waived` with rationale.

  **Path 2 — Mark pending with owner + due date.** Allowed only when `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` Conflicts clearance declares parallel-intake acceptable. Capture: who is running conflicts, when they're expected to return, what entities they're checking. Intake proceeds; matter row carries `conflicts.status: pending`; `/portfolio-status` flags it every run; `/matter-update` re-prompts until resolved.

  **Path 3 — Bypass with documented rationale.** Only if the user explicitly acknowledges the bypass. Record in `conflicts.override`:

  ```yaml
  conflicts:
    status: not-run               # preserved as-is
    override:
      by: [user name]
      date: [YYYY-MM-DD]
      rationale: [why conflicts were bypassed — permanent record; does not auto-expire]
  ```

  This field is visible in every `/portfolio-status`, every `/matter` briefing, and every `/matter-update` until removed. It is never removed by the skill — only by explicit user edit to `_log.yaml` after conflicts are actually cleared.

  **Do not proceed silently.** "I'll do it later" is not an acceptable response. One of Path 1/2/3 must be chosen, and the choice is captured in the record.

This step is not about the skill deciding whether a conflict exists — that's the user's/firm's judgment. It's about making sure the check happened and the record reflects it.

### 3. Source

How did this arrive?
- `demand-letter | complaint-served | subpoena | regulator-inquiry | internal-report | pre-suit-threat`
- *Seed doc opportunity:* "If you have the initiating document (complaint, demand, subpoena), attach or share the path. It sharpens the intake."

### 4. Risk triage — against house calibration

- Severity: high | medium | low (reference the `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` severity bands)
- Likelihood: high | medium | low (reference the `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` likelihood bands)
- Resulting risk rating (per the matrix): high | medium | low | critical
- Damages exposure range (best estimate)
- Non-monetary exposure (injunction? consent decree? publicity? precedent?)

If the risk calibration in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` is thin, don't fake precision. Use the user's gut and note the thinness.

### 5. Materiality

Against the house thresholds in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`:
- `reserved | disclosed | monitored | none`
- If `reserved`: reserve amount and whether finance has been notified
- If `disclosed`: filing and footnote location

### 6. Outside counsel

- Firm
- Lead partner
- **Lead partner email** (used by `/oc-status` to draft status requests)
- Engagement letter status: `signed | pending | none`
- Budget authorization: amount and approver
- *Seed doc opportunity:* "Engagement letter path, if signed."

If risk is medium or higher and no outside counsel is assigned — flag it.

### 7. Internal owners

From `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` landscape — which internal stakeholders are involved?
- Business lead
- HR partner (if employment)
- Comms contact (if reputational risk)
- CISO (if data or cyber)
- Other

### 8. Legal hold

- Issued? If yes: date, scope, custodians (list of names).
- Next refresh date (default: six months from issuance; adjust per matter).
- If no and this is active litigation or reasonably anticipated: flag urgently; offer to run `/litigation-legal:legal-hold [slug] --issue` after intake completes.
- *Seed doc opportunity:* "Hold notice, if issued."

### 9. Key dates

- Response deadline (answer, objection, opposition)
- Next hearing / conference
- Statute of limitations cutoff (if applicable)
- Any regulatory deadlines

### 10. Initial posture

One-paragraph theory:
- What's our story?
- What's theirs?
- What's the pivot fact?
- Initial posture: `fight | settle | investigate | wait`

## Writing the outputs

### Slug

Lowercase, hyphens, year at the end. Examples: `acme-v-us-2026`, `employment-smith-2026`, `ftc-inquiry-2026`.

Confirm slug is unique in `_log.yaml` before writing.

### `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md`

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# [Matter Name]

**Slug:** [slug]
**Opened:** [YYYY-MM-DD]
**Our role:** [plaintiff/defendant/etc.]
**Status:** [status]

---

## Identification

[counterparty, jurisdiction, matter type, source]

## Conflicts

**Status:** [cleared / pending / not-run / waived]
**Method:** [corporate-legal / outside-counsel / system-check / informal / other]
**Cleared by:** [name]
**Cleared date:** [YYYY-MM-DD]
**Checked against:** [entities run]
**Notes:** [any flags cleared, waiver reference if applicable]

## Risk triage

**Severity:** [band] — [why, with reference to house severity definitions]
**Likelihood:** [band] — [why]
**Risk rating:** [high/medium/low/critical]
**Exposure:** [dollar range + non-monetary]

## Materiality

[reserved/disclosed/monitored/none — with reserve amount, disclosure location, or reasoning if "none"]

## Outside counsel

[firm, lead, engagement status, budget]

## Internal owners

[stakeholders and why each is involved]

## Legal hold

[status, date, scope]

## Key dates

[list]

## Initial theory

[one paragraph: our story, their story, pivot fact, initial posture] `[SME VERIFY — theory at intake is a working hypothesis; confirm with outside counsel before any filing or material communication that assumes this framing]`

## Open questions

[anything not yet known that matters — e.g., "insurance tender pending", "unclear whether we have coverage for X"]

---

## Seed documents

| Doc | Path / pointer |
|---|---|
| [e.g., complaint] | [path or "not yet shared"] |
```

### `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/history.md`

Seed the history file with the intake as entry zero:

```markdown
# History: [Matter Name]

Append-only event log. Most recent at top.

---

## [YYYY-MM-DD] — Matter opened

[Source, who brought it in, initial triage summary, outside counsel assigned, legal hold issued yes/no.]
```

### Append to `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`

Add a row per the schema. Example:

```yaml
- id: acme-v-us-2026
  name: "Acme Corp v. Company"
  type: contract
  role: defendant
  counterparty: "Acme Corp"
  jurisdiction: "N.D. Cal."
  # status is derived from source:
  #   source: pre-suit-threat | demand-letter           → status: threatened
  #   source: complaint-served | subpoena | regulator-inquiry → status: active
  #   source: internal-report                           → status: threatened (default) or active if formal process has started
  status: active
  stage: pleadings
  source: complaint-served
  outside_counsel:
    firm: "Wilson Sonsini"
    lead: "J. Reyes"
    email: "jreyes@wsgr.example.com"
    engagement: signed
  conflicts:
    status: cleared
    method: corporate-legal
    cleared_by: "K. Patel"
    cleared_date: 2026-04-20
    override:                   # populated only on Path 3 bypass
      by: null
      date: null
      rationale: null
  risk: high
  materiality: reserved
  exposure_range: "$2M–$5M"
  internal_owners:
    business_lead: "Jane Smith"
    hr_partner: null
    comms_contact: null
  legal_hold:
    issued: true
    issued_date: 2026-02-15
    scope: "Sales org 2023–2026"
    custodians: ["Jane Smith", "R. Chen", "T. Patel"]
    last_refresh: 2026-02-15
    next_refresh: 2026-08-15
    released: null
  related_matters: []
  opened: 2026-04-20
  next_deadline: 2026-05-15
  last_updated: 2026-04-20
  path: matters/acme-v-us-2026/
```

## Confirm before writing

Show the user the row and the matter.md content:

> Here's what I'll write. Flag anything wrong or thin before I commit.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- **Run the conflicts check itself.** It records the result, status, method, and the entities checked. The actual clearance happens in whatever system (or judgment) the house practice profile declares. If the user says "cleared," the skill takes that at face value and captures the metadata.
- Decide the initial theory. It captures what the user says; it doesn't invent one.
- Issue the legal hold. Flags it if missing. User issues it.

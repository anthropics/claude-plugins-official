---
name: demand-intake
description: Pre-drafting context gathering for a demand letter — parties, facts, basis, leverage, BATNA, and privilege filters — written to a structured intake.md the demand-draft skill reads. Use when the user wants to prep a demand letter, run intake before drafting, or capture context for a payment demand, breach/cure notice, cease-and-desist, employment separation, or preservation demand.
argument-hint: "[title] [--full]"
---

# /demand-intake

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → demand-letter practice, landscape, risk calibration.
2. Follow the workflow and reference below.
3. Run the adaptive intake (core 8 always; strategic block if material or `--full`).
4. Generate slug from title + counterparty + year-month.
5. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/intake.md`.
6. Confirm with user: "Intake saved. Run `/litigation-legal:demand-draft [slug]` when ready."

---

# Demand Intake

## Purpose

The drafting is downstream. The value is in the pre-writing — forcing the questions a careless letter skips. Leverage, BATNA, downside tolerance, privilege filters, the actual audience. A demand letter sent without thinking about those is worse than no letter.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → Demand-letter practice (insurance-tender timing, materiality threshold for matter creation, any seed-doc templates), landscape (counterparty type, repeat-adversary patterns), risk calibration (to pre-estimate materiality), house style. **Tone, compliance period, marking, signer are NOT practice-level defaults — they are set per matter in the `## Posture for this matter` step below.**

## Flags

- `--full` → run the complete intake regardless of materiality heuristics (for counsel who wants thorough every time)

## The intake

### Posture for this matter (ask FIRST, before the core)

> **Posture for this matter.** Demand-letter tone and terms are case-by-case, not a practice default. Ask:
> - **Tone:** measured / assertive / aggressive? (depends on the relationship, the amount, and whether litigation is likely)
> - **Response window:** what's reasonable given the claim? (14 days is common for payment demands; 30 days for cure; 7 days for cease-and-desist — but the contract or protocol may set it)
> - **Marking:** does this need a "without prejudice" or "without prejudice save as to costs" marking? (settlement communications do; assertions of claim often don't; jurisdiction matters — ask if unsure)
> - **Signer:** you, the client, the GC, instructed solicitor/counsel?
> Don't assume. Read the prior demand correspondence in the matter file if there is any — it establishes the register.

Record the answers in the intake under a `## Posture` section before `## Parties`. These answers govern the rest of the intake and the downstream draft — do not fall back to a practice-level default if the user left any of them blank; ask again.

### Core — always asked (8 questions)

**1. Demand type**
`payment | breach-cure | cease-desist | employment-separation | preservation | other`

**2. Parties**
- **Sender:** our company (and any specific entity if multi-entity)
- **Recipient:** counterparty — name, entity, address
- **Recipient audience:** who actually reads (GC? CEO? individual? in-house legal?)
- **Relationship:** `customer | vendor | ex-employee | competitor | third-party | other`

**3. Triggering event**
- What happened and when (dates matter — statute-of-limitations, notice periods)
- Evidence available (contracts, emails, records, witnesses)

*Seed doc opportunity: "If you can share the underlying contract, correspondence, or evidence, the draft will be materially sharper. Paths work."*

**4. Legal / contractual basis**
- Which provisions — specific contract sections if applicable
- Governing law (jurisdiction, choice-of-law clause)
- Statutes or rules relied on (placeholders OK — the draft will flag `[CITE:___]` anyway)

**5. Desired outcome**
- Specific asks. Not "resolution" — payment of $X by date Y; cessation of specific activity Z; cure within N days; return of specific property.
- If multiple asks, order them (primary vs. fallback)

**6. Deadlines**
- External deadline driving this (SoL, ongoing harm window, business event)
- Demand compliance deadline — how long we give the recipient. Use the response window captured in `## Posture for this matter` above; do not fall back to a practice-level default.

**7. Prior outreach**
- Has this been raised informally? When, by whom, in what form?
- Any response so far?
- Why is escalation to a demand letter happening now?

**8. Distribution**
- Delivery method (ask; no practice-level default)
- Signer — captured in `## Posture for this matter` above
- Copies — internal stakeholders, insurance carrier (if tendering pre-demand per practice-level tender-timing rule), counsel

### Strategic — asked if material, or if `--full`

Materiality heuristic: ask the strategic block if any of the following are true.

- Demand type is `cease-desist`, `breach-cure`, `employment-separation`, or `preservation`
- Desired outcome dollar value ≥ the medium-severity band from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` risk calibration
- Counterparty is a customer, competitor, or frequent adversary per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` landscape
- User ran with `--full`

**Explicit skip option.** When the strategic block is triggered, the user can decline to answer it. Ask plainly:

> This is a material demand by the heuristic. The strategic block (leverage, BATNA, tone, privilege filters) is where most of the pre-writing value lives. Skipping it produces a thinner draft.
> - **Answer now** — walk the strategic block (5-7 min)
> - **Answer partial** — walk the subset you feel prepared for
> - **Skip** — proceed to draft with only the core block; I'll flag `strategic_block: skipped` in the intake

If the user chooses Skip, the intake file records it:

```yaml
strategic_block: skipped        # answered | partial | skipped
skipped_reason: string | null   # captured if user provided one
```

The draft skill honors the skip — pre-draft gate runs regardless, but sections that depend on strategic-block answers get `[SME VERIFY: leverage/tone/privilege not captured in intake]` markers. The `/demand-draft` command also prompts a second time, asking whether the user wants to complete the strategic block before drafting.

**9. Leverage and BATNA**
- What gives us negotiating power (contractual rights, factual leverage, reputational, commercial)
- What if they refuse — are we prepared to litigate? Go public? Accept a smaller outcome?
- Their likely BATNA — what's their best alternative? (If they don't think we'll sue, the demand is weak.)

**10. Downside tolerance**
- Reputational exposure if this becomes public
- Precedent risk — does this letter set a pattern that affects other matters?
- Regulatory / disclosure implications (is this the kind of dispute that becomes a 10-Q item?)
- Insurance implications — does sending without tendering waive coverage?

**11. Tone posture**
- Already captured in `## Posture for this matter` above. Here, probe the trade-off if the user chose a stronger tone than the facts seem to warrant, or a weaker tone than the facts seem to warrant.
- Worth naming explicitly: aggressive tone burns the relationship. If you want to keep the business relationship but need to protect the legal position, `measured` is usually the right call.

**12. Settlement-communication posture**
- Research the settlement-communication protections applicable in the forum (FRE 408 in federal, the state equivalent otherwise). Is this letter a settlement communication that should be protected? Or an assertion of rights that shouldn't be?
- If protected: the draft will include the settlement-communication marker and will be structured so the substance (a discussion of compromise) — not just the label — supports the posture.
- Protection attaches from conduct and context, not merely from labeling. The marker is a belt-and-suspenders choice.

**13. Privilege filters**
- What's in our internal analysis that must NOT appear in the letter? (Facts we haven't verified, our doubts about our case, strategic reasoning, prior settlement discussions)
- A single badly-worded sentence can waive privilege on related analysis. Be explicit about what stays out.

**14. Admission and accord-and-satisfaction risk**
- Anything in the letter that the counterparty could later characterize as an admission of fact or liability?
- Does this demand risk inadvertently satisfying (or purporting to accept) a separate claim? (Accord-and-satisfaction: cashing a check marked "payment in full" can end a disputed debt.)

## Writing the intake

### Slug

`[type]-[counterparty-short]-[yyyy-mm]`. Confirm uniqueness in `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/`.

### `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/intake.md`

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# Demand Intake: [title]

**Slug:** [slug]
**Demand type:** [type]
**Drafted by:** [counsel]
**Opened:** [YYYY-MM-DD]
**Status:** intake | ready-to-draft | drafted | sent | closed
**Strategic block:** answered | partial | skipped
**Skipped reason:** [if applicable]

---

## Posture

- **Tone:** [measured / assertive / aggressive — with one-line rationale tied to the relationship and the amount]
- **Response window:** [N days — tied to the claim / contract / protocol]
- **Marking:** [none / without prejudice / without prejudice save as to costs / other — with rationale]
- **Signer:** [name / role — you / client / GC / instructed counsel]

*This is the per-matter posture captured at intake. The draft skill reads from here.*

---

## Parties

- **Sender:** [our entity]
- **Recipient:** [counterparty, entity, address]
- **Recipient audience:** [who reads]
- **Relationship:** [type]

## Triggering event

[What happened, when, evidence]

## Legal / contractual basis

[Provisions, governing law, statutes]

## Desired outcome

[Specific asks in priority order]

## Deadlines

- **External:** [SoL, ongoing harm window]
- **Compliance:** [how long we give them]

## Prior outreach

[History, most recent first]

## Distribution

- **Delivery:** [method]
- **Signer:** [name/role]
- **Copies:** [list]

---

## Strategic (if applicable)

### Leverage & BATNA

[Our power, their likely response]

### Downside tolerance

[Reputational, precedent, regulatory, insurance]

### Tone posture

[relationship-preserving / measured / scorched-earth — with rationale]

### Settlement-communication posture

[Protected or not in the forum — with reasoning. Cite primary source per the applicable rule (FRE 408 or state equivalent).]

### Privilege filters

[What CANNOT appear in the draft]

### Admission / accord-and-satisfaction risk

[Specific risks flagged]

---

## Seed documents

| Doc | Path |
|---|---|
| [underlying contract] | [path or "not shared"] |
| [prior correspondence] | [path or "not shared"] |
| [evidence] | [path or "not shared"] |

---

## Materiality assessment

**Auto-heuristic says:** [material / immaterial — with reasoning]
**User call:** [material / immaterial / TBD at post-send]
```

## Confirm before writing

Show the user the draft intake. Flag anything thin:

> Here's the intake. I notice [thin spots]. Before I save, anything to add?

## Handoff to drafting

End with:
> Intake saved. When ready: `/litigation-legal:demand-draft [slug]`

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Draft the letter. That's `demand-draft` — the two steps are intentionally separate so counsel can pause for business input, outside counsel consult, or insurance tender before drafting.
- Decide whether to send the letter. Some intake sessions end with "actually, don't send — let's negotiate directly." That's a valid outcome; the intake record still has value.
- Run the conflicts check. If the counterparty is a customer or known entity, flag that this should clear conflicts (per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`) before sending — but the check itself lives in the matter-intake workflow or outside this skill.

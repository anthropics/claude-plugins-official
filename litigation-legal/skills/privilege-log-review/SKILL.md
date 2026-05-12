---
name: privilege-log-review
description: First-pass privilege log review — make the obvious privilege calls and flag the hard ones for attorney review without making close calls. Use when the user says "review the privilege log", "priv log", "check privilege on these docs", or has a log to QA before production.
argument-hint: "[log file, or document set]"
---

# /privilege-log-review

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → review protocol, priv log format.
2. Follow the workflow and reference below.
3. For each entry: obvious priv / obvious not priv / needs attorney review. Flag reasons.
4. Output: reviewed log with flags. Attorney reviews all flags before production.

---

# Privilege Log Review

## Disclosed-document use restrictions

Before working with a set of litigation documents, ask: "Were any of these documents obtained through disclosure or discovery in legal proceedings?" If yes:

- **England & Wales (CPR 31.22):** Documents obtained through disclosure are subject to the implied undertaking — you may only use them for the purpose of the proceedings in which they were disclosed, unless the court grants permission, the disclosing party consents, or the document has been read in open court. Using them for a different matter, a different claim, or a commercial purpose without permission is a contempt.
- **US:** Protective orders and Rule 26(c) may impose similar restrictions. Check the order.
- **Other jurisdictions:** Similar restrictions commonly apply. Check the local rule.

Confirm: "This use is within the proceedings in which the documents were disclosed, or I have permission / consent, or the documents are now public." If not confirmed, flag it: "⚠️ Disclosed documents may have use restrictions. Confirm this use is permitted before proceeding."

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. For litigation-legal the default is `Enabled: ✓` — every case gets its own matter workspace. If `Enabled` is `✗` (you turned it off because you work one case at a time), skip the rest of this paragraph and use practice-level context. If enabled and there is no active matter, ask: "Which matter is this for? Run `/litigation-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

A privilege log has three kinds of entries: obviously privileged, obviously not, and the ones that need thought. This skill sorts the first two kinds so the attorney's time goes entirely to the third.

**This is first pass. Attorney reviews every flag. No exceptions.**

## Record fidelity — pinpoints and citation coverage

When this skill cites a rule, local variant, or authority for a privilege call (FRCP 26(b)(5)(A), state rule, local rule, case on waiver scope, case on dominant purpose), two rules apply.

**Pinpoint cites must support the whole proposition.** If the review cites one rule or case to support a multi-part proposition — "the log must describe each document and withhold only materials prepared in anticipation of litigation" — verify the pinpoint covers every element. If it only covers one, split the cite or narrow the proposition. A cite that backs part of a privilege position gets the position rejected when opposing counsel reads the cite and points out it doesn't reach the contested element. This is the "misgrounded citation" failure mode: the cite exists, the passage exists, but it doesn't support the proposition as stated.

**Extract all citations before checking any.** When this review cites authority — or when a separate citation-check is requested on the log, a related brief, or the supporting motion:

1. **First pass: extract.** Read the document and build a list of every citation (rules, cases, statutes, local orders, record cites). Report the count: "Found [N] citations."
2. **Second pass: check.** Check each against the source. Don't sample. Don't stop at the first five.
3. **Report coverage.** "Checked [N] of [M] citations. [K] could not be retrieved — verify manually. [J] confirmed. [I] flagged as potential miscitations. [H] flagged as misgrounded (cite exists but doesn't support the proposition)."
4. **When source text is unavailable, say "could not check," never "confirmed."** A false positive is worse than a "couldn't check" — it lets a bad cite through.
5. **The hardest errors are partial support.** Read the proposition, read the source, compare element by element.

## Load context

`~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → privilege log format, review protocol.

**Conflicts gate — unbypassable.** Before reviewing a privilege log, check `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace is set up. I won't review a privilege log on a matter that hasn't been intaken — the conflicts check is the gate, and a privilege log review is work product that needs to live in the matter file."

**Jurisdiction matters.** Privilege scope (A/C and work product), waiver doctrine, and log-form requirements vary materially across federal circuits and state courts. This review applies the rules for the forum specified in config. If the matter involves a different forum, a transferred case, multi-jurisdictional production, or a choice-of-law question on privilege, the calls here may not transfer — re-run against the controlling forum.

## Step 0: Research the forum's privilege-log rules

**Before reviewing entries, research the forum's privilege-log requirements (FRCP 26(b)(5)(A) or state equivalent), any local rule variant, and the judge's standing orders. Identify the required fields, the level of description, and any category-log or metadata-log accommodations. Cite primary sources.**

**No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or firm platform) returns few or no results for the forum's rule, waiver doctrine, or local variant, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / doctrine]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) leave the `[UNCERTAIN]` marker and stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; the skill does not decide for them.

**Source attribution.** Tag every rule reference and authority in the review output with where it came from: `[Westlaw]`, `[CourtListener]`, `[Trellis]`, `[Descrybe]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the reviewing attorney supplied. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags — they are the reviewing attorney's signal about which authorities to re-confirm before service.

**Waiver doctrine differs by privilege type:**

- **Attorney-client privilege waiver** is often broad: subject-matter waiver can sweep in related communications on the same topic.
- **Work-product waiver** is narrower: courts typically distinguish opinion work product (stronger protection) from fact work product. Waiver of fact work product doesn't automatically waive opinion work product.

Confirm the forum's waiver doctrine for each privilege claimed before recommending production of anything. `[UNCERTAIN]` flags stay on waiver calls until counsel confirms.

## The calls

**Three-state rule. The skill never silently decides a subjective threshold isn't met.** On any uncertain call — dominant purpose unclear, litigation contemplation borderline, mixed legal/business content, ambiguous third-party presence — the skill keeps the privilege designation on and adds a ⚠️ flag for the attorney. Under-marking waives privilege (one-way door); over-marking is corrected by the attorney in review (two-way door). Prefer the recoverable error.

**In-house counsel privilege is jurisdiction-specific and contested.** Before classifying any communication with in-house counsel as privileged, check the jurisdiction:

- **US:** In-house counsel communications are generally privileged when made for the purpose of obtaining or providing legal advice, and the attorney is acting in a legal (not business) capacity. The legal-vs-business distinction is fact-specific and contested.
- **EU (competition / DG COMP proceedings):** Under *Akzo Nobel Chemicals v. Commission* (C-550/07 P), communications with in-house counsel are NOT privileged in EU competition proceedings. The CJEU held privilege applies only to communications with independent external lawyers. If the matter involves EU competition or state aid, in-house counsel documents are compellable.
- **Germany (Syndikusanwalt):** The German Syndikusanwalt has a hybrid status. Privilege depends on the capacity in which the lawyer was acting and whether the communication is in the "advocate" or "employee" role. Post-2016 registration rules changed the analysis.
- **UK:** In-house counsel privilege generally recognized, but the "dominant purpose" test applies, and the legal-vs-commercial advice distinction is scrutinized.
- **France, Belgium, some other EU:** In-house lawyers may not be members of the bar, and their communications may have no privilege at all.

**Never classify an in-house counsel communication as "confidently privileged" without stating which privilege regime applies.** If the matter involves non-US jurisdictions, especially EU competition or any EU regulator: "Documents from in-house counsel may have NO privilege in [jurisdiction]. Under *Akzo Nobel*, in-house communications are compellable in EU competition proceedings. Flag for review by a [jurisdiction] litigation specialist before asserting privilege."

The ✅ "confidently privileged, no flag" tier below is the one designed to bypass attorney review. That's exactly where the *Akzo Nobel* risk lives. When the jurisdiction is non-US or the matter touches EU regulators, there is no ✅ tier for in-house communications — everything goes to 🟡 "flag for attorney review with jurisdiction note."

### Confidently privileged (✅) — keep designation, no flag

- Communication between client and outside counsel seeking/providing legal advice, no third parties copied
- Communication between client and in-house counsel, clearly legal (not business) advice, no third parties
- Work product created in anticipation of litigation, by or for counsel
- Communications within the control group about legal strategy

### Uncertain — keep designation AND flag (✅ + ⚠️)

The default for anything that isn't confidently in ✅ or ❌. The skill does not withhold a privilege designation on its own assessment of a subjective test. Examples:

- **In-house counsel doing both legal and business** — was this communication legal advice or business advice? The dominant-purpose call is the attorney's, not the skill's.
- **Third party present** — is the third party within the privilege (common interest, agent) or does their presence waive? Keep the designation; flag for attorney.
- **Mixed purpose documents** — part legal, part business. Partial redaction? Full withhold? Produce? Keep the designation; flag for attorney to decide the treatment.
- **Attachments** — analyze separately and keep each attachment's designation unless confidently ❌; flag the ones where privilege turns on a subjective call.
- **Pre-litigation work product** — "reasonable contemplation of litigation" is fact-specific; keep the designation; flag.
- **Waiver risk** — later-share history is ambiguous; keep the designation; flag the waiver question.

Each flag records the specific open question and the evidence cutting each way, so the attorney can decide without re-reading the document cold.

### Confidently not privileged (❌) — recommend remove, but note the assessment

Only for the unambiguous cases. The output still records the assessment rationale so the attorney can spot-check; it does not remove the designation from the log on its own.

- No attorney involved anywhere
- Business advice with a lawyer CC'd (CC'ing legal doesn't make it privileged)
- Underlying facts (facts aren't privileged — communications *about* facts can be)
- Third party copied who's clearly outside privilege (breaks confidentiality)
- Attachments that are independently non-privileged (the email might be privileged; the attached spreadsheet of sales numbers is not)

If any of these is *close* — the third party might be an agent, the lawyer's CC might actually be on a legal request — it's uncertain, not ❌. Route it to the uncertain bucket and flag.

## Workflow

### Step 1: Format check

Does the log have what it needs?

| Field | Present? |
|---|---|
| Date | |
| Author | |
| Recipients (all — TO, CC, BCC) | |
| Document type | |
| Privilege claimed (A/C, WP, both) | |
| Description (enough to assess without revealing privileged content) | |

Missing fields → flag for completion before substantive review.

### Step 2: Entry-by-entry

For each entry:

```
Entry [N] ([Bates]): [✅ Priv | ✅ Priv + ⚠️ Flag | ❌ Not priv (assessed)]
[If ✅ (no flag): one-line reason]
[If ✅ + ⚠️: keep designation; the specific question the attorney needs to answer; evidence cutting each way]
[If ❌: one-line reason — but the designation stays on the log until the attorney removes it]
```

**Never produce an entry that silently strips a privilege designation based on the skill's own subjective call.** A ❌ is a recommendation logged alongside the flag; the attorney acts on it.

### Step 3: Pattern flags

Across the log:

- Same issue repeating? (E.g., same third party on 50 entries — one decision resolves 50 flags)
- Over-designation pattern? (If everything's designated without differentiation, surface it for the attorney — but the call to narrow the log is the attorney's, not the skill's. Under-designation waives; over-designation is correctable.)
- Under-description? (Descriptions so vague a court would order in camera review)

## Output

**Before the privilege log is served on the opposing party (the consequential act — this includes serving the log AND designating documents withheld or produced under a protective-order designation such as Confidential / Highly Confidential / AEO):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Submitting a privilege log and designating documents in discovery both have legal consequences — over-designation risks sanctions and loss of credibility; under-designation risks waiver; a misdesignated production may be unrecallable. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the matter, log entry counts, the ⚠️ flags and close calls, pattern observations (over-designation, vague descriptions), waiver-doctrine posture by privilege type, what could go wrong on service or designation, what to ask the attorney.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not treat the log as service-ready without an explicit yes. First-pass review, sorting, and flagging do not require the gate — service and designation do.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Privilege Log Review: [Matter] — [date]

**Applicable rule:** [FRCP 26(b)(5)(A) / state rule / local rule / standing order — pinpoint cites] `[UNCERTAIN — verify currency]`
**Entries reviewed:** [N]
**Results:** [N] ✅ confident priv / [N] ✅+⚠️ priv kept & flagged / [N] ❌ recommend remove (attorney confirms)

### ✅ + ⚠️ Flagged — designation kept, attorney decides

| Entry | Bates | Issue | Evidence for priv | Evidence against | Question |
|---|---|---|---|---|---|
| [N] | [range] | [what's subjective] | [one line] | [one line] | [the specific call to make] |

### ❌ Recommend remove designation (attorney confirms before stripping)

| Entry | Bates | Reason |
|---|---|---|

*Recorded, not executed. The skill does not remove privilege designations from the log — the attorney does, after reviewing the rationale.*

### ✅ Privileged (no action)

[Count. List available on request.]

### Pattern observations

[Repeating issues, over-designation, description problems]

### Marker discipline

- `[VERIFY: factual assertion about document/custodian/date]`
- `[UNCERTAIN: close privilege call / waiver scope / doctrine question]`
- `[CITE NEEDED: rule, local variant, or authority supporting a call]`

---

**Attorney must review all ⚠️ and ❌ before any action.**

**Privileged source material.** This review reads entries and underlying documents that are, by definition, privilege-candidate material. The review output inherits that status — keep it with privileged materials, mark it appropriately, and don't circulate outside the privilege circle. Distributing it can itself waive protection.
```

## What this skill emphatically does not do

- Make close calls. ⚠️ means "a human decides." On any subjective test (dominant purpose, reasonable contemplation, common-interest scope, waiver by later sharing) the skill keeps the privilege designation on and flags.
- Strip a privilege designation from the log based on its own assessment. ❌ is a *recommendation* recorded for the attorney, not an action taken against the log.
- Produce or withhold documents. It advises; attorney decides; attorney acts.
- Guarantee correctness on ✅ calls. The attorney is responsible for the log. This is a first pass.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.


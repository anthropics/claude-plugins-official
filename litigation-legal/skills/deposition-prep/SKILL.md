---
name: deposition-prep
description: Build a deposition outline for a witness — pull their documents from the eDiscovery platform, organize topics around the case theory, and surface impeachment material. Use when the user says "depo prep for [witness]", "build a depo outline", or "prepare for [name]'s deposition".
argument-hint: "[witness name]"
---

# /deposition-prep

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → case theory, key facts.
2. Follow the workflow and reference below.
3. Pull docs authored by / mentioning witness from eDiscovery platform.
4. Build outline: background, key docs, topics tied to theory, impeachment material.

---

# Deposition Prep

## Witness statements for England & Wales — PD 57AC

If the user's jurisdiction includes England & Wales and they're asking for a trial witness statement for the Business & Property Courts (or any CPR-governed proceeding), PD 57AC applies. The statement must be in the witness's own words, must not contain argument, must identify the documents the witness used to refresh their memory, and must carry the required confirmation of compliance and the legal representative's certificate.

**Drafting a narrative "as the witness" from a chronology, document set, or your account of the case is exactly what PD 57AC was designed to prevent.** Courts are actively sanctioning AI-assisted witness statement drafting. If you ask me to do it, I won't.

What I WILL do: prepare question prompts to elicit the witness's actual recollection; capture and organize what the witness says (their words, not mine); generate the list of documents they were shown; run a PD 57AC compliance checklist against a statement they've drafted; draft the solicitor's certificate of compliance. I help you get the witness's evidence into the statement. I don't write the evidence.

For US depositions, declarations, and affidavits: different rules, but the same discipline applies. A declaration in the declarant's voice that the declarant didn't write is a credibility problem at best.

## Destination check

Before producing output, check where it's going. If the user has named a destination (a channel, a distribution list, a counterparty, "everyone"), ask whether it's inside the privilege circle. Public channels, company-wide lists, counterparty/opposing counsel, vendors, and clients (for work product) waive the protection. When the destination looks outside the circle, flag it and offer (a) the privileged version for legal only, (b) a sanitized version for the broader channel, or (c) both — don't silently apply a privileged header and then help paste it somewhere the header won't protect it. See the canonical `## Shared guardrails → Destination check` in this plugin's CLAUDE.md.

## Purpose

A depo outline is a map: background → lock in the good facts → confront with the bad ones → box in on the theory. This skill builds the map from the documents and the case theory.

## Record fidelity — quotes and pinpoints

Two rules that govern every citation and every quotation pulled from the record into this outline. Canonical statement lives in the plugin's `CLAUDE.md` shared guardrails; repeated here because an impeachment confrontation built on a misquoted prior statement or a misgrounded transcript cite collapses the impeachment.

**Verbatim quotes from the record must be verbatim.** Never put quotation marks around words attributed to opposing counsel, the witness, another deponent, the court, or any record document unless you have the exact passage in front of you and can cite to it. When you want to characterize what someone said but can't find the exact words:

- **Paraphrase without quotation marks**, attributing clearly: "Witness previously testified that X `[verify against record — Tr. p. __]`."
- **Mark the placeholder:** `[verify exact quote — record cite pending]`
- **Never fill the gap.** An invented prior statement destroys the impeachment the moment the witness disavows it and the transcript doesn't back you up. Every `[verify exact quote]` must be flagged in the reviewer note.

**Pinpoint cites must support the whole proposition.** If an impeachment point is "the witness said X, Y, and Z on [date]," verify the pinpoint cite supports X AND Y AND Z. If it only supports Z, split the cite — "said X (Tr. p. 10), Y (Tr. p. 12), Z (Tr. p. 15)" — or narrow the proposition. A cite that supports part of an impeachment is the failure mode where opposing counsel asks the witness to read more of the surrounding transcript and your confrontation falls apart.

## Oral calibration

A depo outline is read aloud in real time. That's oral advocacy, not written. It means:

- Pick the 3-4 topics that actually matter. Don't try to cover everything — a 200-question outline on a 4-hour depo makes the lawyer skim, and skimming is how lines of questioning get lost mid-sequence.
- Lead with your strongest confrontation. The witness is freshest at the start, and the transcript's opening pages are the ones a judge or jury is most likely to see.
- For adverse witnesses: the tightest questions go in the tightest sequences. Everything else is scaffolding.
- If you're preparing a rebuttal closing after the depo, the calibration is stricter still — the tribunal remembers the first two minutes and the last two.

"Too thorough" for oral work reads as unfocused. If the outline is long because the record is deep, say so and flag where the lawyer should collapse.

## Load context

`~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → case theory (theory, pivot fact, key facts for/against), eDiscovery platform.

**Conflicts gate — unbypassable.** Before building an outline, check `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace is set up. I won't build a deposition outline on a matter that hasn't been intaken — the conflicts check is the gate."

Do not proceed on an unintaken matter. Intake is what runs conflicts and writes the `_log.yaml` row this skill reads from.

## Workflow

### Step 1: Who is this witness?

- Name, role, relationship to the case
- Why are we deposing them — what do we need from this witness?

The "why" connects to the theory. If the witness can establish the pivot fact, that's the centerpiece of the outline.

### Step 1a: Witness posture — branch before drafting questions

Prep structure differs by posture. Identify the witness posture before writing a single question:

- **Adverse / hostile** — cross-examination style: closed, leading, one fact at a time. Build the box.
- **Friendly / your own** — direct-examination style: open questions that let the witness tell the story. Closed leading questions with your own witness are usually improper and undercut credibility with the factfinder.
- **Neutral third-party** — mix; often open to get the story, closed to pin specifics.
- **Corporate representative (30(b)(6) or state equivalent)** — topic designation, binding-the-entity rules, and the witness's personal-knowledge vs. corporate-knowledge distinction all have distinct rules. Research the applicable deposition rule for the forum and the 30(b)(6) / state-equivalent procedure. Confirm: what topics were designated, who was produced, scope of binding testimony.

**Research the applicable deposition rules for the forum and witness type** (FRCP 30 / state equivalent, local rules, judge's standing orders on depositions). Cite primary sources. Don't apply a one-size prep structure — the question form, the approach to documents, and the use of impeachment material all depend on posture.

**No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or firm platform) returns few or no results for the forum's deposition rules or a cite you need for impeachment, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / authority]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) leave the `[UNCERTAIN]` marker and stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; the skill does not decide for them.

**Source attribution.** Tag every rule reference, case cite, and authority in the outline with where it came from: `[Westlaw]`, `[CourtListener]`, `[Trellis]`, `[Descrybe]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the partner or senior associate supplied. Document citations (Bates, production numbers) retain their native source. Citations tagged `verify` carry higher fabrication risk and should be checked before the deposition. Never strip or collapse the tags.

### Step 2: Pull their documents

From the eDiscovery platform (Everlaw/Relativity/DISCO if connected):

- Documents authored by witness
- Documents sent to or from witness
- Documents mentioning witness by name
- Calendar entries and meeting notes with witness present

Organize by date. Flag the hot docs — the ones that matter most for the theory.

### Step 3: Build topics

Each topic is a thing you want to establish or explore. Organize around the theory:

**Background (always first — lock in uncontroversial facts before the witness is defensive):**
- Role, tenure, responsibilities
- Reporting structure
- How they interacted with the key players

**Good facts (lock them in before confronting):**
- Facts from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → key facts for us, that this witness can establish
- Documents that support our theory, authored or received by this witness

**Bad facts (confront with documents):**
- Facts against us that this witness will be asked about anyway — get your version first
- Documents that hurt — know how the witness will explain them

**Impeachment (if hostile or if they contradict):**
- Prior inconsistent statements (from docs, prior testimony, declarations)
- Documents that contradict what you expect them to say

**The pivot fact:**
- The sequence of questions that establishes (or undermines) the fact the case turns on
- This is the most carefully constructed section. Question form follows witness posture from Step 1a: tight closed leading on adverse, controlled open on friendly, mixed on neutral. Don't default to one pattern.

### Step 4: Write the outline

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# Deposition Outline: [Witness Name]

**Date:** [depo date]
**Witness role:** [title, relationship to case]
**Witness posture:** [adverse / friendly / neutral / 30(b)(6) or state equivalent] — drives question form
**Applicable deposition rules:** [FRCP 30 / state rule / local rule / standing order — with pinpoint cites] `[UNCERTAIN — verify currency]`
**Why we're taking this depo:** [one sentence — the goal]
**Theory connection:** [how this witness fits the case theory]

---

## I. Background

[Questions — closed, one fact each. Lock in the uncontroversial stuff.]

## II. [Good fact topic]

**Goal:** Establish [fact] for use at summary judgment / trial.

**Documents:**
- [Bates] — [description] — [why it matters]

**Questions:**
[The sequence. Each question closed. Build to the admission.]

## III. [Bad fact topic]

**Goal:** Get the witness's explanation of [bad fact] on our terms before they're prepped for trial.

[Same structure]

## IV. Impeachment material (use if needed)

[Prior statements / documents to confront with, if the witness contradicts]

## V. [Pivot fact sequence]

**Goal:** [The thing the case turns on]

[This is the tightest section. Every question is a yes/no. Every question establishes one fact. Build the box.]

---

## Exhibit list

| # | Bates | Description | Used in section |
|---|---|---|---|

## Marker discipline

Use inline while building and reviewing:
- `[VERIFY: factual assertion]` — any fact not confirmed against the record
- `[UNCERTAIN: legal proposition]` — any legal point (rule, deadline, scope-of-questioning limit) not confirmed against current authority
- `[CITE NEEDED: specific cite]` — record or authority cite pending

## Notes for the attorney

- [Anything the outline doesn't capture — witness demeanor notes, strategic calls to make in the moment]

---

**Privileged / work-product material.** This outline is built from case materials and work product and inherits their protection status. Keep it in the privileged-materials folder, mark it appropriately, and make any distribution decision (co-counsel, client, experts) deliberately — distribution outside the privilege circle can waive protection.

**Cite check any authority relied on.** Rule citations (FRCP 30, state equivalents, local rules, standing orders) and any case law pulled into the outline were generated by an AI model. Verify each against Westlaw, CourtListener, or your research platform — confirm currency and scope before using at the deposition. Source tags on each citation (e.g., `[Westlaw]`, `[web search — verify]`) show where the cite came from; `verify` tags carry higher fabrication risk and should be checked first.
```

## What this skill does not do

- Take the deposition. The outline is a map; the attorney drives.
- Predict what the witness will say. It prepares for likely answers, but witnesses surprise.
- Decide what to ask on the fly. Follow-ups are the attorney's judgment in the room.

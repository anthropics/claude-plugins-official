---
name: demand-draft
description: Draft a demand letter from a completed intake, gated on a privilege / FRE 408 / waiver / admission checklist, with a .docx output, post-send checklist, and an offer to create a matter. Use when the user says "draft the demand", "write the [type] letter", or has a finished demand intake ready to turn into a sendable draft.
argument-hint: "[slug] [--skip-gate] [--version=N]"
---

# /demand-draft

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/intake.md`. Refuse if missing or strategic block empty (for material demands).
2. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → demand-letter practice, house style, seed-doc table.
3. Follow the workflow and reference below.
4. Run the pre-draft gate: privilege filter, admission risk, accord-and-satisfaction, FRE 408 posture, waiver scan, tone, factual accuracy. Do not proceed until each is engaged.
5. Template select: seed doc if provided in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`; else soft template for the demand type.
6. Draft in-chat for review. Iterate until user approves.
7. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/draft-v[N].docx` using the docx skill.
8. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/checklist.md` (post-send checklist).
9. Assess materiality per heuristic; offer to create a matter. If yes: hand off to `matter-intake` with pre-populated fields.

---

# Demand Draft

## Purpose

Take a completed intake and produce a sendable draft. Most of the value is in refusing to draft until privilege, waiver, admission, and settlement-communication posture have been consciously addressed — the failure mode is a letter that waives privilege or constitutes an admission because no one paused to check.

## Record fidelity — quotes and pinpoints

Demand letters are advocacy, and every quoted line from a contract, an email, or a prior communication becomes an assertion the counterparty will test. Canonical statement in the plugin's `CLAUDE.md` shared guardrails; repeated here.

**Verbatim quotes must be verbatim.** Never put quotation marks around words attributed to the counterparty, their counsel, a witness, or any document unless you have the exact passage in front of you. When you want to characterize without the exact words:

- **Paraphrase without quotation marks**, with a placeholder: "Your [date] email stated X `[verify exact quote — email cite pending]`."
- **Never fill the gap.** A misquoted contract provision in a demand letter is the fastest way to lose credibility with opposing counsel on the first round.
- Every `[verify exact quote]` must be flagged in the reviewer note before the letter leaves.

**Pinpoint cites must support the whole proposition.** If the demand asserts "Section 4.2 requires payment within 30 days upon invoice receipt," the cited section must cover the obligation AND the trigger AND the window. If it only covers one, split the cite (e.g., "Section 4.2 (payment obligation); Section 4.3 (30-day window)") or narrow the proposition. A contract cite that backs part of the demand is how the counterparty replies with the full text and flips the posture.

## Candor about weak arguments

When the law or the record is against a point, don't dress it up as solid. When an argument in the demand is weak — the contract language is ambiguous, the authority cuts the other way, the damages theory is a stretch — flag it for the sender:

> "The [claim / theory] here is weak because [authority / fact]. Options: (a) press it and frame as `[alternative framing]`, (b) drop it and rely on [stronger claim], (c) keep it as a hook but hedge the language. `[review — strategic call]`."

A demand letter that over-asserts gets a response that catalogs every overreach, shifts leverage, and burns the next round. The strongest demand letter is the one that concedes what's weak so the counterparty can't.

## Echo vs repeat

If the matter has prior correspondence, echo the key terms — the same characterization of the breach, the same framing of the core obligation, the same name for the transaction. Don't lift whole sentences. A demand letter that reads like a copy-paste of the prior one signals that nothing has changed; the new letter should advance the posture (new facts, new deadline, new consequence), not restate it.

> **External deliverable:** the drafted demand letter is sent to counterparty. Do NOT include a `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT — PREPARED AT THE DIRECTION OF COUNSEL` header on the outgoing letter. The post-send checklist and the intake file are internal work product and do carry the header.

## Side context

Drafting a demand letter is inherently an assertion — the sender is making a claim. Read `## Side` in the practice profile:

- **Plaintiff / claimant** (default for this skill): demand-draft aligns with the posture. The letter is the claim. Tone, consequence language, and relief demanded all flow from the plaintiff-side playbook.
- **Defense / respondent**: demand-drafts are less common from defense but do happen — a defense practitioner may send a counter-demand, a demand for contribution, or a demand letter in an unrelated matter. Confirm before drafting: "You said defense is your default. Is this matter plaintiff-posture for you (you're asserting a claim), or is this a different posture?"
- **Both / varies**: ask per-draft which posture applies. The draft's tone and default signer may differ.

For in-house defense practitioners who receive demand letters more than they send them, route to `demand-received` instead — that skill handles the inbound-triage case.

## Posture for this matter

Before the pre-draft gate, confirm the matter-level posture. Demand-letter tone and terms are case-by-case, not a practice default. Confirm with the user (reading the intake's `## Posture` section if present; asking if not):

> **Posture for this matter.** Demand-letter tone and terms are case-by-case, not a practice default. Ask:
> - **Tone:** measured / assertive / aggressive? (depends on the relationship, the amount, and whether litigation is likely)
> - **Response window:** what's reasonable given the claim? (14 days is common for payment demands; 30 days for cure; 7 days for cease-and-desist — but the contract or protocol may set it)
> - **Marking:** does this need a "without prejudice" or "without prejudice save as to costs" marking? (settlement communications do; assertions of claim often don't; jurisdiction matters — ask if unsure)
> - **Signer:** you, the client, the GC, instructed solicitor/counsel?
> Don't assume. Read the prior demand correspondence in the matter file if there is any — it establishes the register.

The answers drive tone verb choice, the consequence language, the `Without prejudice` header (or its absence), the signature block, and the compliance deadline. A posture that wasn't captured in intake gets captured here — do not fall back to a practice-level default.

## Jurisdiction assumption

This draft assumes the jurisdiction identified in the intake and the forum's applicable settlement-communication rule (FRE 408 in federal, the state equivalent otherwise). Legal rules, deadlines, fee-shifting, and statutory hooks vary materially by jurisdiction. If the underlying facts touch a different forum, a different counterparty's home state, or a choice-of-law question, the draft may not apply as written — confirm before sending.

## Load context

- `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/intake.md` — required; refuse to proceed if missing
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → Demand-letter practice (seed-doc paths, insurance-tender timing, materiality threshold for matter creation), house style (privilege markings, outside counsel directive format for tone reference). **Tone, compliance period, marking, and signer come from `## Posture for this matter` — they are matter-level, not practice-level.**
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — to check for existing related matters (same counterparty) and offer cross-link

### Strategic-block skipped handling

If the intake has `strategic_block: skipped` or `partial`, prompt the user before running the pre-draft gate:

> The intake skipped [all / some] of the strategic block (leverage, BATNA, tone, privilege filters). Drafting now will produce a usable letter but the strategic sections will be generic and flagged with `[SME VERIFY]`.
>
> - **Complete strategic block now** — pause, return to `/demand-intake [slug] --resume-strategic`
> - **Proceed anyway** — continue to pre-draft gate; downstream sections flagged

If "proceed anyway," every section of the draft that depends on a skipped strategic question gets `[SME VERIFY: [specific question]]` inline.

## Flags

- `--skip-gate` → bypass the pre-draft checklist. Available but logged; use only when the checklist was run separately and documented.
- `--version=N` → draft as `draft-vN.docx` (default: next version number)

## The pre-draft gate

**This runs before any drafting. If the user doesn't engage with it, stop.**

```
PRE-DRAFT CHECKLIST — [slug]

1. Privilege filter
   Per intake privilege filters: [list]
   Confirm: none of these will appear in the draft?  [y/n]

2. Admission risk
   Per intake admission risk: [list]
   For each, is the phrasing controlled or removed?  [y/n per item]

3. Accord-and-satisfaction
   Per intake: [flagged risk, if any]
   Does the demand inadvertently satisfy or accept a separate claim?  [y/n]

4. Settlement-communication posture
   Research the settlement-communication protections applicable in the forum
   (FRE 408 in federal, the state equivalent otherwise). Note that protection
   attaches from conduct and context, not merely from labeling the communication.
   Intake says: [protected / not protected / case-by-case]
   Draft will [include / omit] settlement-communication markers, and will be
   structured so the substance — not just the label — supports the posture.
   Confirm.

5. Privilege waiver scan
   Will any sentence in the draft reveal the substance of our internal legal analysis (not just the conclusion)?  [y/n]
   If yes, rephrase before drafting.

6. Tone posture
   Intake says: [relationship-preserving / measured / scorched-earth]
   This will drive verb choice, framing, and consequence language. Confirm.

7. Factual accuracy
   Every fact in the draft must be verified. Not "probably true" — verified. List any facts that are not yet verified, and they will be flagged [VERIFY: ___] inline.
```

Only proceed when the user has engaged with each item. A blank-acknowledged checklist is worse than no checklist.

## Template selection

### Step 1: Seed doc

Check `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → Demand-letter practice → seed-doc table for the intake's demand type.

- **Seed doc provided:** read it. Match structure, tone, signature block, privilege markings, typical section ordering. The seed doc is the template.
- **No seed doc:** use the soft template below for the demand type.

### Step 2: Soft templates (used only when no seed doc)

Each is a skeleton — headings and expected content. Deviate when the facts require.

**Payment demand skeleton:**
1. Parties and relationship context (1 paragraph)
2. Facts — the obligation and its source (contract § / invoice / order), dates
3. The default — what's owed, when due, what happened (or didn't)
4. Demand — specific amount, deadline, method of payment
5. Consequences — referral to counsel, interest, fees, collections, litigation
6. Preservation notice (if relevant)
7. Signature block

**Breach / cure notice skeleton:**
1. Parties and agreement (identify the contract — effective date, parties)
2. The obligation alleged breached — contract section, plain language
3. The breach — specific facts, dates, evidence available
4. Cure — what specifically would cure; cure period (from contract or reasonable)
5. Consequences of failure to cure — termination, damages, specific remedies in the contract
6. Preservation of rights
7. Signature block

**Cease & desist skeleton:**
1. Parties and our rights (trademark/copyright/contract/common law — identify the right)
2. The infringement / violation — specific acts, dates, evidence
3. Demand — cease immediately, remove, account for past use, confirm compliance in writing
4. Compliance deadline
5. Consequences of non-compliance — litigation, injunctive relief, statutory damages if applicable, fees
6. Preservation demand (documents, metadata, systems related to the alleged conduct)
7. Signature block

**Employment separation demand skeleton:**
1. Parties and relationship context (ex-employee, dates of employment)
2. The obligation — post-employment obligations breached (confidentiality, non-solicit, non-compete, IP assignment); cite the agreement
3. The specific conduct alleged
4. Demand — cease, return property/IP, confirm compliance, non-disparagement reinforcement if applicable
5. Consequences — litigation, injunctive relief, fee-shifting if in the agreement
6. Offer of informal resolution (if strategically appropriate)
7. Preservation demand
8. Signature block

**Preservation demand skeleton:**
1. Parties and context — what dispute is anticipated
2. Scope — categories of documents, data, systems, communications
3. Custodians — named individuals expected to have relevant material
4. Date range
5. Affirmative preservation obligation — suspend auto-delete, preserve metadata, preserve devices
6. Consequences of spoliation — adverse inference, sanctions, fee-shifting
7. Acknowledgment request
8. Signature block

## Drafting rules

0. **Installment-contract default for multi-lot goods disputes.** For any breach-of-contract demand involving a multi-delivery goods contract under the U.C.C. (multiple shipments, lots, or deliveries over time), default to the installment-contract framework of **U.C.C. § 2-612** — "substantial impairment of the value of the installment" — rather than § 2-601's perfect-tender rule or § 2-711's single-delivery buyer's-remedies framework.

Perfect tender under § 2-601 applies cleanly to single-delivery goods contracts. It does NOT transfer cleanly to installment contracts, where § 2-612 modifies the rule: a buyer can reject a nonconforming installment only when the nonconformity substantially impairs the value of that installment and cannot be cured; and can treat the whole contract as breached only when the nonconformity substantially impairs the value of the whole contract.

When drafting the demand letter for a multi-lot goods breach:

- Cite `[CITE: U.C.C. § 2-612 — installment contracts; substantial impairment of the installment]` as the primary framework, not § 2-601.
- Cite § 2-711 and § 2-712 (cover) as remedies flowing from breach, but state the breach standard in § 2-612 terms.
- Flag for the signer in a `[SIGNER NOTE:]` block above the draft: "This letter is drafted under U.C.C. § 2-612 (installment contracts), not § 2-601 (perfect tender). The two have materially different breach standards. Confirm the contract's delivery structure supports installment-contract characterization before sending."
- If the contract's delivery structure is unclear from the intake (e.g., the intake says "three lots delivered" but doesn't confirm whether the contract called for separate lot deliveries or a single shipment split for convenience), flag it `[VERIFY: is this an installment contract under § 2-612, or a single-delivery contract split into lots by shipping convenience?]` — do not silently assert § 2-612 applies.

Single-delivery breach: use § 2-601 perfect-tender framing. Installment: use § 2-612. Do not conflate them.

1. **Specificity over adjectives.** "On March 14, 2026, you sent X" beats "You repeatedly and improperly sent X." Adjectives are the draftsperson's tell that the facts are thin.

2. **Facts traceable to sources.** Every factual assertion maps to a document, date, or witness. If not verifiable yet: `[VERIFY: specific claim]`.

3. **Citations as placeholders.** `[CITE: statute/section/case]` wherever legal authority goes. Do not invent citations. If the user provided authorities in the intake, use them faithfully.

4. **Consequence language matches tone posture.**
   - `relationship-preserving`: "We hope to resolve this without further action."
   - `measured`: "If not cured within [N] days, we will consider our options, including litigation."
   - `scorched-earth`: "Failure to cure within [N] days will result in immediate legal action, including [specific relief]."

5. **Inline alternative phrasings.** Where tone could shift, the draft includes a compact alternative. Format:
   > *The attached invoice of $X remains unpaid.* [or more assertive: *You have failed to pay the attached invoice of $X, due [date].*]

6. **No settlement discussion on the record unless intended.** If the intake flagged the communication as not carrying settlement-communication protection in the forum, the draft does not include any offer to compromise, any "without prejudice" framing, or any language that could be characterized as a settlement communication. Remember that protection attaches from conduct and context; labeling alone is not a cure.

7. **Privilege markings per house style.** Apply `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` privilege conventions exactly.

## Output

### Primary: `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/draft-v[N].docx`

Use the `docx` skill to produce a letter-formatted .docx:
- Letterhead / sender address block
- Date
- Recipient address block
- Re: line (concise; does not reveal privileged strategy)
- Salutation
- Body (per template + drafting rules)
- Closing
- Signature block per intake

### In-chat review

Show the draft as readable plain text for the user to review and request edits. Iterate before writing the final .docx. Once approved, write to disk.

### Send gate (closing note on the draft)

Append the following, set apart from the body, to the in-chat presentation and to any internal preview — it is a reviewer-facing note, not letter text, and is stripped before the letter goes out:

> This is a draft demand letter for attorney review, not a letter ready to send. Sending it may constitute an attorney communication, create FRE 408 (or state-equivalent) implications, and start the clock on disputes, counterclaims, and statutes. A licensed attorney reviews, edits, and takes professional responsibility before sending. Do not send this draft unreviewed.

### Citation verification

Every `[CITE:___]` placeholder — and any citation pulled from the intake or the seed doc — is unverified until a human runs it through a citator. Before sending, run a verification pass: check each case, statute, and regulation against a legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or your firm's platform) for accuracy, good law status, and subsequent history. Fabricated or misquoted citations in sent demand letters and filed documents have resulted in sanctions.

**Source attribution.** Tag every citation in the draft with where it came from: `[Westlaw]`, `[CourtListener]`, `[Trellis]`, `[Descrybe]`, or the specific MCP tool name for citations retrieved via a legal research connector; `[web search — verify]` for citations surfaced by web search; `[model knowledge — verify]` for citations the model recalled from training data; `[user provided]` for citations supplied in the intake or seed doc. Citations tagged `verify` carry higher fabrication risk than tool-retrieved citations and should be checked first. Never strip or collapse the tags — they are the signer's fastest signal about which citations to verify before the letter goes out.

**No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or firm platform) returns few or no results for an authority the draft needs, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [issue]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) leave the `[CITE:___]` placeholder and stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; the skill does not decide for them.

### `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/[slug]/checklist.md` — the post-send checklist

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`. This header applies to the internal checklist file; the outgoing letter does NOT carry it.]

# Post-Send Checklist — [slug]

**Draft version sent:** [v1 / v2 / etc.]
**Sent date:** [YYYY-MM-DD — filled in after send]
**Signer:** [name]

## Pre-send (before the letter goes out)

- [ ] Final read-through by signer
- [ ] Factual accuracy: all [VERIFY] flags resolved
- [ ] Citations: all [CITE] placeholders filled and run through a citator (verify it is good law)d (if live law cited)
- [ ] Privilege markings applied per house style — note: this is an external deliverable; do not include the `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT` header in the version sent to counterparty
- [ ] Settlement-communication markers [present / absent] as intake specified, and substance aligns with posture
- [ ] Internal copies cleared (per intake distribution list)
- [ ] Insurance tender sent (if required per house practice)
- [ ] Conflicts confirmed (if not yet cleared)

**Before the letter is sent (the consequential act):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Sending this demand letter has legal consequences — it creates a record, can trigger statutes and counterclaims, and may waive privileges or constitute admissions. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: counterparty and dispute, the demand and deadline, tone posture, FRE 408 / settlement-communication status, privilege and admission risks flagged in the pre-draft gate, what could go wrong, what to ask the attorney before sending.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not mark as sent — do not execute the Send mechanics below — without an explicit yes.

## Send mechanics

- [ ] Delivery method executed: [certified / email / both]
- [ ] Proof of delivery retained (certified receipt, email read-receipt, courier confirmation)
- [ ] Copies sent per distribution list

## After send

- [ ] Compliance deadline calendared: [YYYY-MM-DD]
- [ ] Escalation plan if no response: [next step + date]
- [ ] Follow-up check-in calendared: [date — typically deadline + 2 business days]
- [ ] Matter created in `_log.yaml`: [yes / no — see materiality below]

## Materiality call

**Heuristic says:** [material / immaterial]
**Reason:** [demand type / exposure / counterparty type]
**Your call:** [material → create matter] [immaterial → demand-letters record only]

If material: `/litigation-legal:matter-intake` with `source: demand-letter` pre-populated from this intake.
```

### Matter auto-creation offer

After drafting and writing the checklist, assess materiality per heuristic:

- **Default yes if ANY of:**
  - Demand type is `cease-desist`, `breach-cure`, `employment-separation`, or `preservation`
  - Desired outcome $$ ≥ `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` medium-severity band
  - Counterparty is a customer, competitor, or frequent adversary per landscape
- **Default no otherwise**

Present the call:
> Materiality heuristic: [result]. [One-sentence reason.]
> Create a tracked matter in `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml`? (default: [yes/no])

If user accepts: trigger `matter-intake` with fields pre-populated from the intake (counterparty, type, jurisdiction, `source: demand-letter`, initial theory, internal stakeholders). User reviews pre-filled fields and confirms.

If user declines: update intake `status: drafted` (later `sent` when user confirms). The record stays in `~/.claude/plugins/config/claude-for-legal/litigation-legal/demand-letters/` only.

## Versioning

Never overwrite a draft that has been sent. If revising after send, `draft-v2.docx`. The sent-version history is itself the record of what the counterparty received.

## What this skill does not do

- **Send the letter.** Drafting only. The user sends.
- **Research citations.** `[CITE:___]` placeholders stay as placeholders. If the user provided authorities in the intake, they're used; otherwise, blanks. Inventing cites is malpractice exposure.
- **Bypass the pre-draft gate.** Even with `--skip-gate`, the skill notes in the draft file that the gate was skipped and why.
- **Rewrite the intake.** If the intake is thin, send the user back to `demand-intake`. The draft is only as good as what it reads from.
- **Decide materiality.** The heuristic offers a default; the user's call is the record.

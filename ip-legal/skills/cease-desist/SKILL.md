---
name: cease-desist
description: >
  Draft a cease-and-desist letter (send mode) or triage one you received
  (receive mode). Use when asserting your rights against an infringer with a
  demand letter calibrated to your enforcement posture, or when an incoming
  C&D needs triage into a structured options memo with a recommendation.
argument-hint: "<--send | --receive> [context, counterparty, or path to incoming letter]"
---

# /cease-desist

Two modes. Pick one:

- `/ip-legal:cease-desist --send` — draft a cease-and-desist letter calibrated to your enforcement posture. Loud gate runs before delivery.
- `/ip-legal:cease-desist --receive` — triage a C&D someone sent you. Produces an options memo with a recommendation.

## Instructions

1. **Read the practice profile.** Load `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. If it contains `[PLACEHOLDER]` markers or does not exist, stop and say: "This plugin needs setup before it can give you useful output. Run `/ip-legal:cold-start-interview` — the C&D skill depends on your enforcement posture, approval matrix, and practice-area mix, none of which are configured yet."

2. **Check matter workspaces.** Per `## Matter workspaces`: if `Enabled` is `✗`, skip — skills use practice-level context. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`."

3. **Dispatch on `$ARGUMENTS`:**
   - If `--send` is present: run send mode (below). Walk through identify-the-right, identify-the-conduct, identify-the-relationship, identify-the-demand, calibrate-to-posture, draft, and the pre-delivery gate.
   - If `--receive` is present: run receive mode (below). Ask for the incoming letter (path or pasted text), then assess, identify exposure, present options, and write the triage memo.
   - If neither flag is present: ask once — "Are we sending a cease-and-desist (you're asserting) or triaging one we received (you're defending)?" — and then dispatch.

4. **Respect the gate.** In send mode, the loud gate runs before any final draft is written to disk. Do not skip it.

5. **Respect the approval matrix.** Pull the approver for the C&D row from `## Enforcement posture → Approval matrix`. Pull automatic escalations. Surface both in the gate; do not smother them.

6. **Hand off where appropriate.** In receive mode, if the recommendation is to respond firmly, offer to chain into `/ip-legal:cease-desist --send` pre-populated with the response context. If the recommendation is to pre-empt with a DJ action or TTAB cancellation, escalate to outside counsel per the practice profile's IP litigation row — do not draft.

## Examples

```
/ip-legal:cease-desist --send
/ip-legal:cease-desist --receive ~/Downloads/incoming-cd-acme.pdf
/ip-legal:cease-desist
```

## Notes

- The outgoing C&D does not carry the work-product header. The internal draft, the pre-send brief, and the triage memo do.
- Trademark rights are territorial; the draft assumes the jurisdictions declared in your practice profile's `Registered in:` footprint. If the conduct or counterparty is somewhere else, flag before drafting.
- Every `[CITE:___]` is unverified until a citator run. Source attribution tags stay on the draft.
- Non-lawyer users get a one-page brief for the attorney conversation before the gate clears.

---

## Purpose

A cease-and-desist letter asserts a legal right and demands that someone stop doing something. It is one of the most consequential letters an IP practice sends or receives. Sending one is a first step toward litigation — recipients can file a declaratory judgment action in a forum of their choosing, and overbroad or bad-faith assertions can be used against the sender. Receiving one starts a clock and forces a decision. This skill handles both sides with the guardrails the decision deserves.

Two modes:

- `--send` — you are asserting. Draft a C&D calibrated to the posture, gate before delivery.
- `--receive` — you are defending. Triage the incoming letter, produce an options memo, route to matter creation if warranted.

If the user does not pass a flag, ask once: "Are we sending a cease-and-desist (you're asserting) or triaging one we received (you're defending)?"

> **External deliverable (send mode):** the drafted C&D is sent to counterparty. Do NOT include the `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT` header on the outgoing letter. Internal drafts, pre-send briefs, and triage memos keep the header per plugin config `## Outputs`.

## Jurisdiction assumption

Trademark rights are territorial — a US registration does not travel. Copyright is Berne-multilateral but enforcement is jurisdiction-specific, and statutory remedies (including US §504 statutory damages) turn on local law. This skill assumes the jurisdiction declared in the matter or the practice profile's `Registered in:` footprint. If the infringing conduct, counterparty, or forum is somewhere else, flag it — the draft may not apply as written.

## Load context

- `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` → `## Enforcement posture` (posture, C&D triggers, soft-letter criteria, approval matrix, automatic escalations), `## IP practice profile` (practice area mix, registered jurisdictions, outside counsel roster), `## Outputs` (work-product header, role), `## Who's using this` (role — lawyer vs. non-lawyer)
- Any C&D template or enforcement playbook referenced in the practice profile's seed documents — read it, match the structure
- **Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip matter machinery — skills use practice-level context. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific overrides (e.g., posture override, approver override). Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

## Send mode — drafting the C&D

### Step 1: Identify the right

Ask, in one batch:

> Which IP right are we asserting?
>
> - **Trademark** — is it registered? Where (USPTO, EUIPO, UKIPO, national)? Reg number and class(es)? Or common-law-only (first-use date, geographic scope)?
> - **Copyright** — is it registered? Title, registration number, date? Or unregistered (note: US suits require registration for filed claims; statutory damages and fees require pre-infringement registration)?
> - **Both** — identify each.

Record each right. Registered rights get cited by number. Common-law rights get the first-use evidence paragraph. Unregistered copyrights get a flag: "We may not be able to file suit on an unregistered US copyright without registering first — `[SME VERIFY]` before the letter threatens litigation."

### Step 2: Identify the conduct

> Describe the infringing conduct in specifics, not adjectives:
>
> - **Who** is doing it — entity name, individual, platform handle?
> - **What** — the accused mark, the accused copy, the accused product? Attach or describe samples.
> - **Where** — website URL, marketplace listing, physical retail, social media?
> - **Since when** — date first observed, date of the earliest use you can document?
> - **Evidence** — screenshots, receipts, watch-service hit, customer confusion reports?

Facts go in specific. "You sold product X on [URL] bearing the mark [Y] on [date]" beats "You have been infringing our rights." Adjectives tell on a thin record.

### Step 3: Identify the relationship

> What's the relationship between us and the recipient?
>
> - **Competitor** (direct or adjacent) — standard posture applies
> - **Reseller / channel partner** — tone adjusts; consider the soft-letter path
> - **Former licensee / ex-employee / former partner** — contract provisions likely apply; cite them
> - **Stranger / random infringer** — standard
> - **Current customer / partner** — automatic escalation per practice profile; flag before drafting

This changes tone, approver, and whether to draft at all without escalation.

### Step 4: Identify the demand

> What does the client actually want?
>
> - **Stop** — cease the infringing use
> - **Account** — report sales, profits, volumes (for damages baseline)
> - **Destroy** — destroy or recall infringing inventory
> - **Damages** — monetary settlement
> - **Transfer / assign** — transfer the domain, hand over the account, assign the accused mark or copyright
> - **Public correction** — takedown of offending content, public statement
> - **Confirm in writing** — compliance undertaking by a date

Pick the actual remedies. The demand must be proportionate to the harm — an overbroad demand is evidence of bad faith if the matter is ever litigated.

**Channel-takedown parallel path (marketplace infringement).** If the accused conduct is on a marketplace (Amazon, Etsy, eBay, Alibaba, TikTok Shop, AliExpress, Walmart Marketplace, Shopify-hosted storefronts), flag the platform's brand-protection / IP-infringement reporting path as a faster, cheaper parallel track that does not require a C&D or litigation:

- **Amazon Brand Registry** (trademark and copyright takedown, counterfeit removal)
- **Etsy IP Infringement reporting** (trademark / copyright / patent forms)
- **eBay VeRO** (Verified Rights Owner program)
- **Alibaba IPP** (IP Protection Platform)
- **TikTok Shop IP Protection**
- **Shopify DMCA / trademark reporting**

A marketplace takedown often resolves in days; a C&D gives the infringer time to sell through inventory while negotiating. The two paths are not mutually exclusive — recommend filing both when the conduct is marketplace-based, with the C&D covering off-platform conduct (DTC site, wholesale, social, physical retail) that the platform report cannot reach. Note in the pre-send brief whether the parallel-path has been filed, is queued, or is declined (and why).

### Step 5: Calibrate to posture

Read `## Enforcement posture` → `Default posture:` and apply:

- **Aggressive** — firm letter, short deadline (often 7–14 days), explicit consequence language (litigation, statutory damages, fees, injunctive relief), no settlement softening
- **Measured** — firm but professional, standard deadline (14–30 days), consequences noted without theatrics, openness to discussion if they respond
- **Conservative** — soft letter framing, longer deadline or no hard deadline, "we'd like to discuss" opening, consequence language muted or absent

Also read `When we send a C&D`, `When we send a soft letter first`, and `When we just file`. If the facts suggest this should be a soft letter or a direct filing per the practice profile, flag it before drafting: "Per your enforcement posture, this pattern matches [soft letter / filing]. Do you still want a C&D, or would you prefer [alternative]?"

Matter-level overrides in `matter.md` beat the practice default.

### Step 5.5: Counterparty diligence — REQUIRED PRECONDITION

**Before drafting, run counterparty diligence and present the results to the user.** This is not conditional on "if the counterparty looks big." Every C&D assertion carries DJ / fee-shifting / bad-faith exposure calibrated to *who* the recipient is. The skill does not draft a C&D until the user has seen the diligence and confirmed they still want to pick this fight.

Collect and present — in one block, for user sign-off — the following:

- **Legal entity** — exact corporate name, state/country of formation, registered agent, any `d/b/a` aliases. USPTO / EUIPO ownership records; state Secretary of State business search; public company filings if any. Flag `[SME VERIFY]` if the source is unconfirmed.
- **Size and resources** — approximate headcount, revenue band if publicly known, funding if a startup, parent company if a subsidiary. Public sources (LinkedIn headcount, press, Crunchbase, SEC filings). Flag honestly if size can't be determined.
- **IP portfolio** — do they hold registered marks, patents, or copyrights in adjacent classes? A counterparty with its own IP portfolio is more likely to (a) understand the posture, (b) counter-assert, and (c) file DJ. USPTO TESS / TSDR quick search on the accused entity and affiliates.
- **Litigation history** — PACER / Court Listener quick pass for prior IP litigation as plaintiff or defendant. A repeat litigant or DJ-happy counterparty changes the calculus. Flag any prior C&D campaigns in the industry.
- **Counsel** — do they have known outside IP counsel? Firm, lead partner if identifiable from prior filings. "No counsel on file" is itself a data point.
- **DJ-plaintiff risk posture** — given size, IP portfolio, litigation history, counsel, and forum: is this a counterparty likely to welcome a C&D as an invitation to file DJ in a forum of their choosing? Flag high / medium / low with a one-sentence reason.
- **Relationship risk** — are we a customer of theirs, do we share investors, are they a potential acquirer or partner? "Not a customer" confirmation pulled from the practice profile; anything else flagged.

Present this as a short memo in-chat BEFORE the draft:

```
## Counterparty diligence — [Entity Name]

- **Entity:** [name, state of formation, parent if any]
- **Size:** [headcount band, revenue band, funding stage] — [source, `[SME VERIFY]` where applicable]
- **IP portfolio:** [registered marks / patents / copyrights in adjacent classes — or "none found"]
- **Litigation history:** [prior IP cases as plaintiff or defendant — or "none found in quick pass"]
- **Counsel:** [known outside IP counsel — or "none identified"]
- **DJ-plaintiff risk:** [high / medium / low — reasoning]
- **Relationship risk:** [any customer / investor / partner / acquirer overlap — or "none identified"]

**Automatic escalations this triggers** (per practice profile `## Enforcement posture` → Automatic escalations):
- [list each trigger that this diligence surfaces]

**Confirm before I draft:**
- Do you want to proceed with a C&D against this counterparty, given the diligence above?
- Any of the automatic escalations applicable? If yes, the approver named in the profile signs off before drafting, not after.
```

**Do not proceed to Step 6 (Draft) until the user has engaged with the diligence block.** A blank "ok" is worse than no confirmation — push back: "Before I draft — anything in the diligence that changes the calculus? Size, prior litigation, their counsel, relationship?"

If diligence surfaces anything in the practice profile's automatic-escalation list (customer, bigger counterparty, patent matter, press-attracting, etc.), route to the named approver per the profile — do not draft on the reviewer's behalf until the approver has signed off on going forward.

If critical diligence items cannot be answered (e.g., entity cannot be confirmed, size is unknown and the counterparty is not on any public register), say so and flag: "I can't confirm [entity / size / counsel] from available sources. Do you have this, or should we pause until a paralegal or OC runs the confirmation?"

### Step 6: Draft

Draft structure:

1. **Sender / letterhead and date**
2. **Recipient block**
3. **Re: line** — concise, does not reveal privileged strategy. `Re: Unauthorized use of [MARK] (US Reg. No. [•])`
4. **Opening** — identify the sender, the right, the registration (if any), and the fact of the letter
5. **The right** — trademark: reg number, class, first-use date, registration status; copyright: registration number, title, year, work description; common-law: first-use date, geographic scope, evidence of acquired distinctiveness
6. **The infringing conduct** — specific: who, what, where, when, evidence
7. **The legal basis** — `[CITE: Lanham Act §32 / §43(a) / 17 U.S.C. §501 / state UCL / contract §]` as applicable
8. **The demand** — numbered, specific, proportionate
9. **The deadline** — calendar date, method of confirmation
10. **Consequences of non-compliance** — calibrated to posture
11. **Preservation demand** — documents, communications, metadata related to the accused conduct
12. **Reservation of rights** — "without waiver of any claims or remedies, whether at law or in equity"
13. **Signature block** — approver per practice profile

**Drafting rules:**

- **Specificity over adjectives.** Dates, URLs, reg numbers, samples. Adjectives are a draftsperson's tell that the facts are thin.
- **No overbroad assertions.** If the mark is registered in one class and the accused use is in a different class, say so — don't pretend the registration covers both. Overbroad C&Ds are evidence of bad faith and can support §43(a)(1)(B) or Rule 11 exposure.
- **Citations as placeholders unless verified.** `[CITE: Lanham Act §32, 15 U.S.C. §1114]` stays as a placeholder unless the user provided the cite or a research tool returned it. Tag every citation with source — `[Westlaw]`, `[user provided]`, `[model knowledge — verify]`, `[web search — verify]`. Never strip the tags.
- **Consequence language matches posture.** Aggressive → specific relief threatened (injunction, statutory damages under 15 U.S.C. §1117 / 17 U.S.C. §504, attorneys' fees). Measured → "we reserve all rights." Conservative → "we'd like to discuss before considering further steps."
- **Jurisdiction-specific hooks** — if US, watch for Anti-Cybersquatting (15 U.S.C. §1125(d)) for domain matters, §43(a) for unregistered marks, §504(c) for pre-registration timing. Non-US: flag the forum and note the draft may need foreign associate review.

### Step 7: The loud gate before delivery

Before presenting the draft in-chat or writing the .docx, display this gate verbatim. **The user must engage with it** — a blank acknowledgment is worse than no gate.

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE THIS DRAFT GOES ANYWHERE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  This is a draft for attorney review — not a letter to      │
│  send. Sending a cease-and-desist letter is an assertion    │
│  of legal rights with real consequences:                    │
│                                                             │
│  • It can trigger a declaratory judgment action in a        │
│    jurisdiction of the recipient's choosing. A well-funded  │
│    recipient can use a C&D as an invitation to pick a       │
│    hostile forum.                                           │
│                                                             │
│  • Overbroad or bad-faith assertions can be used against    │
│    the sender — §43(a)(1)(B) claims, Rule 11 sanctions,     │
│    attorneys' fees under the Lanham Act / Copyright Act.    │
│                                                             │
│  • It starts a dispute that may not settle cheaply.         │
│                                                             │
│  Confirm before the letter leaves:                          │
│                                                             │
│    1. The rights asserted are valid — registered (pulled    │
│       from the register, not assumed) or solidly common     │
│       law with evidence of acquired distinctiveness.        │
│    2. The claim is colorable — a reasonable practitioner    │
│       would make it on these facts.                         │
│    3. The demand is proportionate — we are asking for       │
│       relief the conduct warrants, not everything.          │
│    4. Whoever has authority to start a fight has approved.  │
│    5. Counterparty diligence (Step 5.5) was presented       │
│       and confirmed — entity, size, IP portfolio, prior     │
│       litigation, counsel, DJ-plaintiff risk, and           │
│       relationship risk. Not conditional. Required.         │
│                                                             │
│  Approver per your practice profile: [approver name/role    │
│  from Enforcement posture → Approval matrix → C&D row]      │
│                                                             │
│  Automatic escalations that apply here: [list any from the  │
│  practice profile that this matter triggers — customer,     │
│  bigger counterparty, patent, press-attracting, etc. —      │
│  surfaced in Step 5.5 diligence]                            │
│                                                             │
│  Parallel-path status (marketplace conduct): [filed /       │
│  queued / declined — from Step 4. "Not applicable" if       │
│  conduct is not on a marketplace.]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

If the user is a non-lawyer (per `## Who's using this`), add:

> Sending a C&D has legal consequences that go beyond the recipient's response — it is an affirmative assertion of rights that can be held against you. Have you reviewed this with an attorney? If not, here's a brief to bring to them: [generate a 1-page summary: parties, rights asserted, infringing conduct, demand, posture, risks flagged above, what could go wrong, specific questions for the attorney].
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). The ABA IP section and state IP associations (US), CIPA/ITMA (UK), and equivalent bodies elsewhere maintain referral rosters for trademark and copyright practitioners.

Do not write the .docx or mark the draft as ready without explicit engagement with the gate.

### Step 8: Output

**Primary:** `<matter-folder>/cease-desist/<slug>/draft-v<N>.docx` (or `cease-desist/<slug>/draft-v<N>.docx` at practice level). Use the `docx` skill. Letter-formatted per the draft structure above. Strip the work-product header from the outgoing letter.

**In-chat:** show the draft as plain text for review before writing the .docx. Iterate before committing to disk.

**Reviewer-facing closing note** (appended to the in-chat preview only, stripped from the .docx):

> This is a draft cease-and-desist letter for attorney review, not a letter ready to send. Sending it is an assertion of legal rights with the consequences described in the pre-delivery gate. A licensed attorney reviews, edits, and takes professional responsibility before sending. Do not send this draft unreviewed.

**Citation verification.** Every `[CITE:___]` and every cite carried from a template or provided authority is unverified until run through a citator. Before sending, verify each cite is good law on a legal research platform. Fabricated or misquoted cites in sent assertion letters are professional responsibility exposure. Preserve the source-attribution tags — `[Westlaw]`, `[CourtListener]`, `[Descrybe]`, `[user provided]`, `[model knowledge — verify]`, `[web search — verify]` — tags flagged `verify` get checked first.

**No silent supplement.** If a configured research tool returns few or no results for an authority the draft needs, report what was found and stop. Do NOT backfill from web search or model knowledge without asking. Present options — broaden the query, try a different tool, accept web search with tags, leave the placeholder — and let the user decide.

**Post-send checklist.** After the draft is approved, write `<matter-folder>/cease-desist/<slug>/checklist.md` with: final read by approver, all `[VERIFY]` resolved, all `[CITE]` filled and verified, privilege markings stripped from the outgoing letter, approver signed, delivery method executed, proof of delivery retained, compliance deadline calendared, escalation plan if no response, matter created in `matters/` if not already.

## Receive mode — triaging the incoming C&D

### Step 1: Read the letter

Extract:

- **Sender** — entity, signer, outside counsel if any
- **Recipient** — which of our entities/people
- **Delivery method and date**
- **Asserted right** — trademark (reg number? jurisdiction?), copyright (registered? title?), both, something else
- **Alleged conduct** — their version of what we're doing
- **Legal basis** — statutes, contract provisions, theories cited
- **Demand** — what they want; is the deadline stated?
- **Threats** — what they say they'll do
- **Tone** — firm / soft / scorched-earth; counsel signature usually signals seriousness

### Step 2: Assess the assertion

Not a legal opinion — a structured read:

- **Rights validity.** Are the asserted registrations real and active? (Check USPTO TSDR, EUIPO eSearch, Copyright Office records — flag any that look dormant or not in force.) For common-law claims, what evidence do they actually cite?
- **Plausibility of confusion / similarity / infringement.** On the facts as alleged, is this a colorable claim or is it stretching? For trademark: likelihood of confusion turns on multi-factor tests (Polaroid / AMF / Sleekcraft depending on circuit — `[SME VERIFY]` the forum's test). For copyright: access + substantial similarity. Flag where the claim looks weakest.
- **Overbreadth.** Are they demanding more than the conduct warrants? (They want the mark transferred when registration would at most cover re-labeling? They want all sales when only one channel touched the right?) Overbroad demands weaken leverage and strengthen a §43(a)(1)(B) / unclean-hands counter.
- **Timing.** Laches, statute of limitations, registration timing (for US copyright statutory damages) — flag any date issues on the face of the letter.
- **Forum.** Where would they sue? Is the forum contractually fixed (most unlikely in a stranger IP dispute)? Is there a DJ opportunity for us?

### Step 3: Assess our exposure

- **Are we actually infringing?** Honest look. What does the record show?
- **Could we stop easily?** Cost of compliance vs. cost of fight.
- **Is the sender a troll or a real claimant?** Repeat-plaintiff? Known-willing-to-fight? Recent C&D campaign on comparable use? Check public dockets if time permits.
- **What's at stake beyond this dispute?** Brand equity, customer relationships, precedent for similar inbound C&Ds.

### Step 4: Options

Present 4-5 options with tradeoffs:

**A — Comply quickly**
- When: the claim is colorable, compliance is cheap, and the fight isn't worth it
- Tradeoff: establishes a concession they may point to later; may embolden future assertions
- Next step: confirm compliance in writing (narrow), do not concede broader theory

**B — Negotiate**
- When: there's a middle-ground business deal (license, coexistence, rebranding timeline) that resolves it
- Tradeoff: commits time; requires care on settlement-communication posture (FRE 408 or state equivalent; protection attaches from substance and context, not labeling alone)
- Next step: holding letter + opening negotiation track

**C — Respond firmly (reject)**
- When: their claim is weak, overbroad, or factually wrong; we want to close this down without litigating
- Tradeoff: locks in a position; if the claim is in fact colorable, our response becomes an exhibit
- Next step: draft a response letter — consider running it through `/ip-legal:cease-desist --send` reframed as a response

**D — Ignore (and preserve)**
- When: the claim is frivolous, the sender has no apparent capacity to sue, the deadline has no legal consequence
- Tradeoff: silence can be used as non-denial in some contexts; legal hold required regardless; risk that filing follows
- Next step: issue legal hold via matter-level process; log the demand; move on

**E — Pre-empt with a DJ action or cancellation**
- When: we face real business uncertainty, the claim is weak, and we benefit from our own forum
- Tradeoff: we go on offense; budget and leadership sign-off required; now there's a lawsuit
- Next step: escalate to outside counsel per practice profile, do not draft

**F — File to cancel their mark (TTAB) or invalidate their copyright registration**
- When: their rights themselves are vulnerable and we want to take the instrument off the board
- Tradeoff: slow, expensive, public; separate from the dispute itself
- Next step: escalate to outside counsel

Recommend one with two sentences of rationale. Be specific about why.

### Step 5: Deadline triage

- Their stated deadline — note it, but it doesn't legally bind us (unless a specific statute gives it teeth).
- Our internal decision deadline — typically stated deadline minus enough time to draft, review, and approve a response. Flag it on the calendar.
- Legal deadlines — statute of limitations on any underlying claim, contractual cure periods, forum-specific timelines.

Ignoring a stated deadline entirely is a choice, not a default. Note that filing usually follows silence, not the deadline date.

### Step 6: Write the triage memo

Output: `<matter-folder>/cease-desist/inbound/<slug>/triage.md` (or at practice level if matter workspaces are off).

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

[PRIVILEGE INHERITANCE BLOCK — pick by role and matter type; see guidance below the template]

# C&D Received — Triage

> **READ FOR TRIAGE, NOT OPINION.** This is an intake scan and options analysis — not a legal merit opinion. The assessment below is a structured read to support counsel's decision on routing and response. Every cited statute, rule, or case is flagged for SME verification; every merit call is the counsel's, not this skill's.

**Slug:** [slug]
**Received:** [YYYY-MM-DD]
**Received by:** [entity / person]
**Incoming file:** [path]

## The assertion

**Sender:** [entity, signer, counsel]
**Asserted right:** [trademark / copyright / both — with specifics, reg numbers, jurisdictions]
**Alleged conduct:** [their version, one paragraph]
**Demand:** [list — specific asks]
**Their stated deadline:** [date]
**Tone:** [firm / soft / scorched-earth]

## Rights validity

[Registrations as asserted — `[SME VERIFY]` against the register; common-law claims evaluated against the evidence cited]

## Legal basis cited

[Each citation inline-tagged with `[SME VERIFY: applicability / currency / jurisdiction]` and source `[Westlaw / user provided / model knowledge — verify / web search — verify]`. Do not rely on any citation here without independent check.]

## Plausibility assessment

- **Confusion / similarity / infringement on the facts:** [read]
- **Overbreadth:** [read]
- **Timing issues (laches, SoL, registration timing):** [read]
- **Forum:** [their likely forum; DJ opportunity]

## Our exposure

- **Actually infringing?** [honest look]
- **Cost of compliance vs. cost of fight:** [read]
- **Sender credibility:** [troll / real claimant / repeat plaintiff — with any public-docket evidence]
- **Collateral stakes:** [brand, customers, precedent]

**Triage rating:** [substantial / debatable / weak / frivolous] — *structured read for routing, not a merit opinion; `[SME VERIFY]`*

## Options

### A. Comply quickly
[Rationale, tradeoffs, next step]

### B. Negotiate
[Rationale, tradeoffs, next step]

### C. Respond firmly
[Rationale, tradeoffs, next step]

### D. Ignore + preserve
[Rationale, tradeoffs, next step]

### E. Pre-empt (DJ)
[Rationale, tradeoffs, next step]

### F. File to cancel / invalidate
[Rationale, tradeoffs, next step]

**Recommendation:** [A/B/C/D/E/F] — [two sentences why] — `[SME VERIFY: counsel to confirm before executing]`

## Deadlines

- **Their stated deadline:** [date]
- **Our internal decision deadline:** [date]
- **Legal deadlines on any underlying claim:** [SoL, cure, procedural — with dates]

## Immediate actions

- [ ] Legal hold issued — [yes/no]
- [ ] Matter created in log — [yes/no/TBD]
- [ ] Counsel assigned — [who]
- [ ] Insurance tendered — [yes/no/N-A]
- [ ] Internal escalation — [who/when]
```

**Privilege inheritance block — pick by role and matter type.** Read `## Who's using this` (Role) in the plugin config and the matter type (trademark / copyright / patent / OSS / other). This triage records a first-pass merit read on an adverse assertion; whether it's actually privileged depends on who prepared it and what it's about. Getting this wrong in either direction is harmful — a false "privileged" marking creates a discoverable admission that reads as a concession; under-marking a genuinely privileged memo can waive the protection. Insert exactly one of the following:

- **Role = Lawyer / legal professional:**
  > **Privilege inheritance.** This triage records our first-pass merit read and response posture on an adverse assertion. It is attorney-client and/or work-product material. Do not forward, attach to an insurance tender without scrubbing, or share with counterparty. Store with privileged matter material and mark per house privilege conventions.

- **Role = Registered patent agent, matter is a patent matter before the USPTO:**
  > **Privilege (patent agent-client).** This triage is privileged under the federal patent agent-client privilege recognized in *In re Queen's University at Kingston*, 820 F.3d 1287 (Fed. Cir. 2016), because it relates to a matter reasonably necessary and incident to the prosecution of patents before the USPTO. That privilege is narrow: it does not extend to matters outside USPTO practice. Do not forward, attach to an insurance tender without scrubbing, or share with counterparty. Bring to supervising counsel for matter-specific privilege decisions.

- **Role = Registered patent agent, matter is NOT a patent matter** (trademark, copyright, OSS, trade secret, contract, or anything else outside USPTO practice):
  > **CONFIDENTIAL — NOT PRIVILEGED.** This triage is not privileged because a registered patent agent's privilege is limited to patent prosecution before the USPTO (*In re Queen's University at Kingston*, 820 F.3d 1287 (Fed. Cir. 2016)). A trademark, copyright, OSS, or other non-patent matter falls outside that privilege. Treat this document as confidential, store it with care, bring it to counsel, and let counsel mark it. Do not forward it as a privileged document.

- **Role = Non-lawyer and not a registered patent agent:**
  > **CONFIDENTIAL — NOT PRIVILEGED.** This document is not privileged unless and until reviewed by a licensed attorney. Treat it as confidential; do not forward to anyone outside the legal review chain; bring it to counsel and let counsel mark it. Forwarding this document as "privileged" before an attorney reviews it does not make it so and can harm you if the matter becomes contested.

Close the in-chat presentation with this guardrail verbatim:

> This is a triage memo, not advice. The strength assessment above is a first read based on the letter alone — it does not account for facts you haven't told me, registrations I can't verify, or jurisdictional issues. An attorney evaluates before you respond, decide to ignore, or commit to a path.

If the user is a non-lawyer, add the "find-an-attorney" routing paragraph from send mode.

### Step 7: Hand off

Based on the recommendation and user confirmation:

- Respond firmly → hand off to `/ip-legal:cease-desist --send` with context pre-populated as a response letter (this triggers the send-mode gate anew).
- Negotiate → start a holding letter / negotiation track in the matter.
- Pre-empt or file to cancel → escalate to outside counsel per the practice profile's IP litigation row; do not draft.
- Matter creation → if there isn't one and the matter is material, offer `/ip-legal:matter-workspace new <slug>` pre-populated.
- Comply / ignore → log the decision in the matter history; issue or confirm the legal hold; close the triage record.

## Decision posture

Per `## Decision posture on subjective legal calls` in the practice profile: when uncertain whether there is infringement, whether a mark is confusingly similar, whether a work is substantially similar, whether a claim is colorable, or whether sending is safe — do not silently decide it's fine. Flag for attorney review, surface the factors cutting both ways, note the uncertainty. Sending a C&D on an assumption is a one-way door; surfacing doubt is a two-way door.

## What this skill does not do

- **Send the letter.** Drafting only. The user sends, after approval.
- **Research citations.** Placeholders stay as placeholders unless the user provides authorities or a connected research tool returns them. Inventing cites is professional responsibility exposure.
- **Bypass the gate.** The send-mode gate runs every time. Even with an `--skip-gate` flag (none is provided), the skill would log the skip in the draft file.
- **Decide merit definitively on the receive side.** The rating is a structured read for routing; a formal merit opinion lives with counsel.
- **Validate the sender's cited law.** Flags for the user; does not autonomously call a claim valid or invalid.
- **Make the matter-creation call.** Surfaces the recommendation; user decides.

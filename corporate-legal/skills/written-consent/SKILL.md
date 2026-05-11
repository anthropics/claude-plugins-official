---
name: written-consent
description: >
  Draft a unanimous written consent of the board or a committee in house format,
  with precedent search from the consents repository. Handles multi-resolution
  consents, director conflict flags, state-law notice requirements, and signatory
  tracking, with a built-in scope warning for major one-off actions. Use when
  user says "written consent", "unanimous consent", "board consent", "consent
  in lieu", "UWC", or describes an action needing board approval without a meeting.
argument-hint: "[describe the action needing board approval]"
---

# /written-consent

1. Load `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → Board & Secretary (consents repository, resolution language, state of incorporation, board composition).
2. Use the workflow below.
3. Identify the action and classify (routine / review-flag).
4. If review-flag: show outside counsel warning and confirm before proceeding.
5. Search consents repository for closest precedent. If no repository: use seed consents from `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`.
6. Draft consent in house format using precedent as base.
7. Output: consent draft + signatory checklist + review prompts.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/corporate-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/corporate-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Most routine board approvals don't need a meeting. Officer appointments, equity grants, bank authorizations, contract approvals above the officer threshold, intercompany arrangements — these happen by unanimous written consent. This skill drafts them quickly in your house format, finds the prior consent that's closest to what you need, and flags the actions where you should be getting outside counsel eyes before anyone signs.

## Scope warning — read before drafting

> **This skill is designed for day-to-day consents with direct precedents in your repository or seed documents.** Routine actions — officer appointments, equity grants, annual authorizations, standard contract approvals — are the right use case. The skill finds a prior consent that closely matches, adapts it to the current action, and produces a clean draft.
>
> **For major one-off actions, outside counsel review is prudent regardless of what this skill produces.** This includes: M&A transactions (asset purchases, stock purchases, mergers, investments), financing rounds, equity issuances to new investors, change-of-control provisions, dissolution or winding down, material real estate transactions, and any action that will be scrutinized in a subsequent due diligence process.
>
> The skill will flag automatically when the action looks like a major one-off. That flag is not a block — you can proceed. It is a prompt to think about whether a clean precedent-adapted draft is sufficient for this particular action.

---

## Major action + urgency = stop

A board consent for a major one-off action (M&A, financing, dissolution, capital structure change, director election tied to a financing or M&A) that the user wants signed TODAY — "send for DocuSign this afternoon," "meeting in an hour," "signing tonight," "we need this before market open" — goes through outside counsel review. Not because the plugin can't draft it — because a wrong consent on a major action is a one-way door, and the urgency pressure is exactly when mistakes happen.

Trigger (both must be true):

1. The action is in the **Review flag — major one-off** category below (M&A, financing, dissolution, capital structure change, change-of-control provision, director election tied to a financing or M&A, material real estate transaction, any action that will appear in a future financing or M&A data room).
2. The user's ask contains an irreversibility signal — "send for DocuSign," "sign today," "board is signing this afternoon/tonight," "need this before [market open / closing / the meeting at X]," any phrasing that commits the consent to signature on the same turn.

When both are true, output this and stop:

> ⛔ **Major action + same-day signature — I won't mark this ready to sign.**
>
> This is [action type], which is a one-way door. You've asked for it to be signed today. That combination is exactly when mistakes on a board consent become hardest to unwind.
>
> I'll draft it — happily — but I won't mark it ready to sign without an outside-counsel look. If outside counsel is already engaged on this deal, hand them this draft. If not, this is the thing outside counsel is for. Your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) can point you to a lawyer referral service that can find one same-day if needed.
>
> Two ways forward:
>
> 1. **I draft, outside counsel reviews, then signatures** — the normal path for a major corporate action. Tell me to draft and I will.
> 2. **Outside counsel is already on this deal and cleared the draft path** — tell me who reviewed and when. I'll proceed and include a note that outside counsel has the draft.
>
> I will not draft in "ready-to-send" form under same-day pressure without one of those two. This is not a delay — it's the only way a same-day major-action consent is defensible if anyone ever looks at the file.

Do not proceed to Step 1 or any drafting under this gate without an explicit response choosing path 1 or path 2. A routine consent with no major-action trigger, or a major-action consent without the same-day signature ask, follows the normal flow below — the "Outside counsel review recommended" flag on the major-one-off category still applies but does not hard-stop.

---

## Load context

- `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → `## Board & Secretary`:
  - Consents repository location
  - House resolution language
  - State of incorporation (for notice requirements)
  - Board composition (for signatory list)
  - Written consents — scope and any limits

### No-precedent hard stop

If (a) no consents repository is configured in `## Board & Secretary` → Consents repository, AND (b) no seed consent document has been provided to this skill (either uploaded this session or referenced in the `## Board & Secretary` → Consent format section with extracted resolution/recital/authorisation language from a specific seed), **STOP before drafting**. Do not proceed to Step 1 intake, do not draft from a generic template, do not "get started" with a filler format.

Output exactly this block and wait for a response:

> **No precedent available — stopping before draft.**
>
> I don't have a precedent to match. A board consent drafted without your house format will need more correction than it saves — resolution language, recital depth, authorisation boilerplate, and signature-block conventions all carry house-specific choices that the reviewer will rewrite from scratch if I start from a generic template.
>
> Two ways to unblock:
>
> 1. **Paste or upload a prior consent** (any recent UWC from this company in any category — I extract the format, not the substance), OR
> 2. **Tell me "draft from a generic template anyway — I'll adjust the formalities myself"** — only pick this if you know you'll rework the resolution language, recital style, and authorisation block by hand before circulation. Say it explicitly; I will not infer it.
>
> Which do you want to do?

Do NOT proceed without an explicit response choosing one of those two paths. Draft attempts absent a precedent are the highest-rework-to-value output this skill can produce — the hard stop is intentional.

---

## Step 1: Identify the action

Ask the user what action the board needs to approve. Gather:

- **What is being approved?** (One sentence.)
- **Any supporting detail?** For example: the name of the officer being appointed, the grant amount and price for an equity grant, the counterparty and contract value for a contract approval.
- **Effective date:** Today, or a specific date?
- **Signatories:** Full board, or a specific committee? If the `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` written-consent scope says certain actions require a meeting rather than consent, flag it now.
- **Any director conflict?** Does any director have a material interest in the action being approved? If yes: flag it. The conflicted director may still be able to sign depending on state law and the nature of the conflict, but the consent should disclose it and the user should confirm.

### Action classification

Classify the action before searching for precedent:

**Routine — direct precedent likely:**
- Officer appointment or removal
- Equity grant (option, RSU, restricted stock) to existing plan participants
- Bank account authorization or signatory update
- Approval of a contract below a material threshold
- Annual authorization resolutions (tax matters, benefits plans, etc.)
- Intercompany loan or services agreement at arm's length terms
- Registered agent or registered office change

**Review flag — major one-off, outside counsel prudent:**
- M&A transaction (acquisition, merger, asset purchase, investment)
- New financing round or debt facility
- Equity issuance to a new investor
- Change-of-control provision or trigger
- Approval of an agreement that itself requires board approval under the company's charter or stockholder agreements
- Dissolution, winding down, or bankruptcy filing
- Material real estate transaction
- Any action that will appear as a board approval exhibit in a future financing or M&A data room

If the action is in the review-flag category, show this before drafting:

> ⚠️ **Outside counsel review recommended.** This looks like [action type], which is a major corporate action where a precedent-adapted draft may not be sufficient. Consider having outside counsel review before circulation. Want me to proceed with a draft anyway?

---

## Step 2: Search for precedent

### If consents repository is connected

Search the repository for the closest prior consent. Search strategy:

1. Search by action type keyword (e.g., "officer appointment", "equity grant", "bank authorization")
2. Return the most recent matching consent, or ask the user to choose if multiple close matches exist:

> I found [N] prior consents that look like this:
>
> 1. [Consent title / description] — [Date]
> 2. [Consent title / description] — [Date]
>
> Which one is closest to what you need? Or should I use the most recent?

3. Read the selected consent. Extract: resolution language, recital structure, authorization language, any specific conditions or carve-outs.
4. Note any differences between the prior action and the current one that will need to be updated in the draft.

### If no repository (seed documents only)

Extract the format from the seed consents in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. Note that no precedent search is available — the draft will follow house format but without substantive precedent matching. Flag this to the user:

> No consents repository is connected, so I'm working from your seed documents for format. For this action type specifically, you may want to check whether you have a prior consent to use as a substantive starting point.

---

## Step 3: Draft the consent

Use the house format. The structure below is the standard — adapt to match the precedent or seed format exactly.

```
UNANIMOUS WRITTEN CONSENT
[OF THE BOARD OF DIRECTORS / OF THE [COMMITTEE NAME]]
OF [COMPANY NAME]

[Date]

The undersigned, constituting all of the members of the
[Board of Directors / [Committee]] of [Company Name], a [State] [corporation /
limited liability company] (the "Company"), hereby adopt the following
resolutions by written consent pursuant to [Section X of the [State] General
Corporation Law / applicable operating agreement], in lieu of a meeting:

[AGENDA ITEM / ACTION HEADING — if multiple resolutions]

WHEREAS, [background recital — one or two sentences stating the relevant facts
and why the board is being asked to act]; and

WHEREAS, [additional recital if needed]; and

NOW, THEREFORE, BE IT RESOLVED, that [the specific action being approved,
in precise language — name names, state amounts, reference the specific
agreement or instrument where applicable];

RESOLVED FURTHER, that [any related or implementing resolution — e.g., the
specific officers authorized to sign documents, the authority granted];

RESOLVED FURTHER, that the officers of the Company are, and each of them
hereby is, authorized and directed, in the name and on behalf of the Company,
to take all actions and to execute and deliver all documents, instruments,
certificates and agreements as such officers may deem necessary or appropriate
to carry out the intent and purposes of the foregoing resolutions; and

RESOLVED FURTHER, that any actions previously taken by any officer of the
Company in connection with the foregoing are hereby ratified, confirmed and
approved in all respects.

[Repeat WHEREAS / RESOLVED block for each additional action if multi-resolution consent]

This Written Consent may be executed in one or more counterparts, each of
which shall be deemed an original and all of which together shall constitute
one and the same instrument. Electronic signatures shall be deemed original
signatures for all purposes.

[SIGNATURE BLOCKS — one per required signatory]

_______________________________
[Director Name]
[Title, if applicable]
Date: _______________

[Repeat for each director / committee member]
```

### Resolution drafting notes

- **Be precise.** Vague resolutions create problems in due diligence. "Approved the transaction" is not useful. "Approved the Asset Purchase Agreement dated [date] between [Buyer] and [Company], substantially in the form attached hereto as Exhibit A" is.
- **Name the authorized signatories.** Don't just say "officers" if a specific officer needs authority for a specific thing. Name them.
- **Reference exhibits.** If a document is being approved, attach it as an exhibit and reference it in the resolution. The consent is only as useful as its specificity.
- **Match the house language exactly.** "RESOLVED, THAT" vs. "BE IT RESOLVED" vs. "RESOLVED" — use whatever is in the precedent or seed documents. Do not switch formats within a consent.

---

## Step 4: Confirm the consent rules for the state of incorporation

Check the state of incorporation in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. Research the written-consent requirements for that state before drafting:

- Is unanimity required for a board written consent, or is a lower threshold permitted?
- Is notice to non-signatory directors required? On what timing?
- Is notice to non-signatory stockholders required (for stockholder consents)? On what timing?
- What form of signature is valid (wet ink, electronic, counterparts)?
- Does the charter or bylaws override any default rule — e.g., a higher signature threshold, a different notice window, a restriction on which actions can be taken by consent?

Cite the controlling statute section and any charter/bylaw provisions relied on. Verify currency — state corporate codes are amended regularly. Flag uncertainty for attorney verification rather than stating a rule you haven't confirmed.

If `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` records a house position on any of these questions, apply it and note the legal backstop being relied on. Add a short "State-law notice" block to the output summarizing what you confirmed (or flagged) so the user isn't left wondering.

---

## Step 4.5: Consequential-action gate (execute consent)

**Before proceeding to output:** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. If the Role is **Non-lawyer**:

> Executing a written consent has legal consequences — it binds the entity and becomes a corporate record. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - What the action is (the resolution)
> - What the analysis found (state-law notice, signature threshold, any flagged conflicts)
> - Open questions (anything flagged for attorney verification above)
> - What could go wrong (invalid consent, breach of fiduciary duty, signature defect, conflict not properly handled)
> - What to ask the attorney (is this the right vehicle; are there missing recitals; does the charter/bylaws permit consent for this action)
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) for a referral service.

Do not produce the final signatory-ready draft past this gate without an explicit yes. Research, format extraction, and a marked-DRAFT for attorney review are fine.

---

## Step 5: Output

Produce:

1. **The consent draft** — complete, ready to review and circulate. The executed written consent itself is a corporate record, not privileged; do not apply the work-product header to the consent as circulated. The drafting notes, signatory tracker, and analysis below are work product — prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` `## Outputs` (it differs by user role — see `## Who's using this`):

   ```
   [WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]
   ```

2. **Signatory checklist:**
```
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

SIGNATORY CHECKLIST — [Action] — [Date]

Required signatories (unanimous consent required):
□ [Director Name 1]
□ [Director Name 2]
□ [Director Name 3]
[etc. — pulled from board composition in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`]

Conflict disclosures:
[None / [Director Name] has a disclosed interest — confirm whether recusal or disclosure is appropriate]

State law notice: [confirmed-rule-for-state-of-incorporation / confirm]
```

3. **Review prompts:**
```
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

BEFORE CIRCULATING — check:
□ Resolution language precisely describes the action (no vague approvals)
□ Correct effective date
□ All required exhibits attached and referenced
□ Authorised signatories named correctly
□ Any director conflicts disclosed or resolved
□ For major actions: outside counsel has reviewed
```

4. **Final note on the draft — add before circulation.** Prepend to the consent draft as a separate pre-execution note, then strip before the consent is signed:

> This is a draft for attorney review, not an executed consent. Executing it binds the entity and becomes a corporate record — a licensed attorney reviews, edits as needed, and takes professional responsibility before it goes out. Do not circulate for signature unreviewed.

---

## What this skill does not do

- It does not determine whether an action legally requires board approval — that judgment belongs to the attorney.
- It does not advise on director fiduciary duties or conflict of interest resolution — it flags conflicts, the attorney handles them.
- It does not replace outside counsel review for major transactions — the scope warning is genuine, not boilerplate.
- It does not circulate the consent — output is for the attorney to review and send via their own process.
- It does not track returned signatures — the signatory checklist is a starting point; signature tracking is manual or handled by your document management process.

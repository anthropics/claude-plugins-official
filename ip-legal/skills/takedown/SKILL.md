---
name: takedown
description: >
  Draft a DMCA takedown notice, triage one you received, or draft a §512(g)
  counter-notice. Use when asserting copyright through a §512(c)(3) takedown
  with the fair-use and perjury gates, when an incoming takedown needs triage
  into comply / counter / engage / ignore options, or when drafting a
  §512(g)(3) counter-notice with the consent-to-federal-jurisdiction gate.
argument-hint: "<--send | --respond | --counter> [context or path to incoming notice]"
---

# /takedown

Three modes. Pick one:

- `/ip-legal:takedown --send` — draft a §512(c)(3) takedown notice. Fair-use gate (*Lenz*) + loud perjury / §512(f) gate before delivery.
- `/ip-legal:takedown --respond` — triage a takedown someone sent you. Options: comply / counter / engage / ignore.
- `/ip-legal:takedown --counter` — draft a §512(g)(3) counter-notice. Loud gate for the federal-jurisdiction admission and the perjury statement.

## Instructions

1. **Read the practice profile.** Load `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. If it contains `[PLACEHOLDER]` markers or does not exist, stop and say: "This plugin needs setup before it can give you useful output. Run `/ip-legal:cold-start-interview` — the takedown skill depends on your approval matrix and practice profile."

2. **Check matter workspaces.** Per `## Matter workspaces`: if `Enabled` is `✗`, skip. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`."

3. **Dispatch on `$ARGUMENTS`:**
   - `--send` → run send mode (below). Walk identify-the-work, identify-the-infringing-material, fair-use gate (*Lenz*), good-faith belief, accuracy/authority, draft the §512(c)(3) notice, run the loud gate, write output.
   - `--respond` → run respond mode (below). Read the incoming notice, assess (license, fair use, defects, host §512(g) compliance, sender credibility), present the four options, recommend, write the triage memo.
   - `--counter` → run counter mode (below). Confirm the predicate (taken down in response to a §512 notice, good-faith belief of mistake/misidentification, ready for federal-jurisdiction admission, attorney in the loop), draft the §512(g)(3) counter-notice, run the loud gate, write output.
   - No flag → ask once: "Are we sending a DMCA takedown, triaging one we received, or drafting a counter-notice?"

4. **Respect the gates.** In `--send` and `--counter`, the loud gate runs before any final output is written. The fair-use gate in `--send` is separate and runs earlier; "debatable" or "likely" fair use stops the draft and routes to attorney review.

5. **Jurisdiction note.** DMCA §512 is US federal law. If the service provider, content, or infringer sits outside US jurisdiction, flag before drafting — you may need an EU DSA notice, UK OSA notice, or local-regime instrument instead of (or in addition to) a DMCA notice.

6. **Hand off where appropriate.** `--respond` with a counter-notice recommendation chains into `/ip-legal:takedown --counter` — but only after the triage memo has been reviewed and the decision to counter has been made deliberately.

## Examples

```
/ip-legal:takedown --send
/ip-legal:takedown --respond ~/Downloads/youtube-takedown-notice.pdf
/ip-legal:takedown --counter
/ip-legal:takedown
```

## Notes

- The outgoing notice and counter-notice do not carry the work-product header. Internal drafts, fair-use analyses, and triage memos do.
- §512(c)(3) and §512(g)(3) are element-by-element statutes — every required element must be present or the notice is defective.
- Counter-notices consent to federal court jurisdiction in the claimant's district (or a designated district for non-US subscribers). This is not a formality.
- Non-lawyer users get a one-page brief for the attorney conversation before the gate clears — particularly important for counter-notices, which are the step before litigation.

---

## Purpose

The DMCA §512 notice-and-takedown system is fast, cheap, and consequential in equal measure. A takedown is a sworn statement under penalty of perjury that gets content pulled with no judicial review. A counter-notice is another sworn statement that consents to federal jurisdiction and puts the content back. Both decisions can become litigation. This skill handles all three moves with the guardrails each warrants.

Three modes:

- `--send` — draft a §512(c)(3) takedown notice
- `--respond` — triage a takedown someone sent you; produce options
- `--counter` — draft a §512(g)(3) counter-notice

If the user does not pass a flag, ask once: "Are we sending a DMCA takedown, triaging one we received, or drafting a counter-notice?"

> **External deliverables (send and counter modes):** the outgoing notice/counter-notice goes to the service provider's designated agent. Do NOT include the `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT` header on the outgoing document. The notice itself is not privileged — it's a statement made in a statutory process. Internal drafts, pre-send briefs, fair-use analyses, and triage memos keep the header per plugin config `## Outputs`.

## Jurisdiction assumption

DMCA §512 is **US federal law**. It runs against service providers subject to US jurisdiction. Other jurisdictions have their own notice-and-action regimes — EU Digital Services Act Art. 16, UK Online Safety Act, India IT Rules 2021, etc. — that differ materially in required elements, counter-notice mechanics, and liability for misuse. If the service provider, content, or infringer sits outside US jurisdiction, flag it — a US DMCA notice may be the wrong instrument, or may need to be paired with a local regime's notice. Copyright subsistence itself is Berne-multilateral, but enforcement mechanics are jurisdiction-specific.

## Load context

- `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` → `## IP practice profile` (copyright registrations if any), `## Enforcement posture` → `Approval matrix → DMCA takedown (ordinary)` row, `## Outputs` (work-product header, role), `## Who's using this` (role — lawyer vs. non-lawyer)
- **Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (in-house default), skip matter machinery. If enabled and no active matter, ask: "Which matter? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Write outputs to the active matter's folder at `~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/takedown/<slug>/` (or `takedown/<slug>/` at practice level). Never read another matter's files unless `Cross-matter context` is `on`.

## Send mode — drafting a §512(c)(3) takedown notice

### Step 1: Identify the copyrighted work

> What is the copyrighted work?
>
> - **Title / description** — what is the work (software, image, text, video, audio)?
> - **Registration status** — US Copyright Office registration number and date (if any). Registration is NOT required to send a takedown, but it is required to file suit on a US work and its pre-infringement timing controls statutory damages and fees.
> - **Ownership** — do we own it outright, or hold an exclusive license with takedown authority? (Non-exclusive licensees typically cannot send takedowns on the licensor's work.)
> - **Prior licensing** — have we ever licensed this use, or a broader use that might cover it?

Ownership and authority are the first things §512(f) cases look at. Get them clearly on the record before drafting.

### Step 2: Identify the infringing material and its location

> Where is the infringing material?
>
> - **Platform / service provider** — YouTube, Twitter/X, GitHub, Reddit, Amazon, a web host, etc.
> - **URL(s)** — specific permalinks to the infringing material. One notice can cover multiple URLs if they're all from the same service.
> - **Description** — what is the infringing material and how does it infringe (verbatim copy, substantially similar, derivative)?
> - **Screenshots / evidence** — preserved with timestamp and URL visible

§512(c)(3) requires "information reasonably sufficient to permit the service provider to locate the material." URLs alone are usually enough; be precise.

### Step 3: Fair-use gate

Under *Lenz v. Universal Music Corp.*, 801 F.3d 1126 (9th Cir. 2015), a copyright holder must consider fair use before sending a takedown. This is not a judgment about fair use — it is a consideration step that the sender must take and can prove they took.

Ask:

> Before we draft the notice, walk through fair use. Under *Lenz*, you have to consider it before sending — even if the conclusion is "not fair use." The four factors:
>
> 1. **Purpose and character** — commercial? transformative? criticism, comment, news reporting, teaching, scholarship, research?
> 2. **Nature of the copyrighted work** — factual or creative? published or not?
> 3. **Amount and substantiality** — how much of the work is used? is it the heart of the work?
> 4. **Effect on the market** — does the use substitute for the original or harm a derivative market?
>
> Your read on each? And your conclusion — fair use unlikely, debatable, likely?

Record the answer in the notice file. If "debatable" or "likely," do not draft. Stop and route to attorney review: "Fair use is debatable/likely on these facts. Sending a takedown on a use that is protected by fair use is the exact §512(f) exposure the statute creates. Route this to counsel before any notice goes out."

### Step 4: Good-faith belief

§512(c)(3)(A)(v) requires "a statement that the complaining party has a good faith belief that use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law."

The sender forms this belief on the record. Have they:

- Confirmed the work is theirs (or they have takedown authority via exclusive license)?
- Confirmed the use is not licensed (no prior deal, no implied license, no Creative Commons grant that would cover it)?
- Considered fair use (Step 3)?
- Reviewed the accused content directly (not just a report about it)?

If yes on all four, the good-faith belief is colorable. If no on any, pause.

### Step 5: Accuracy and agent authority

§512(c)(3)(A)(vi) requires "a statement that the information in the notification is accurate, and under penalty of perjury, that the complaining party is authorized to act on behalf of the owner of an exclusive right that is allegedly infringed."

This is the perjury statement. It applies to the accuracy of the identification and the authority — not to the fair-use determination itself, though §512(f) liability reaches both.

Confirm signer: who is sending this on behalf of whom, and do they have authority to do so?

### Step 6: Draft the notice

§512(c)(3)(A) elements — every one must be present:

1. **Signature** (physical or electronic) of the rights holder or authorized agent
2. **Identification of the copyrighted work** — "Copyrighted work: [title, description, registration no. if any]"
3. **Identification of the infringing material** with location information — "Infringing material: [URL(s), description, how it infringes]"
4. **Contact information** — address, phone, email of the complaining party or agent
5. **Good-faith belief statement** — verbatim, adapted: "I have a good faith belief that use of the copyrighted material described above is not authorized by the copyright owner, its agent, or the law."
6. **Accuracy and authority statement under penalty of perjury** — verbatim, adapted: "I swear, under penalty of perjury, that the information in this notification is accurate and that I am the copyright owner, or am authorized to act on behalf of the owner, of an exclusive right that is allegedly infringed."

Structure:

- Sender address block / date
- Recipient: designated DMCA agent at [service provider] (find via Copyright Office's DMCA Designated Agent Directory — `https://www.copyright.gov/dmca-directory/`)
- Re: Notice of Copyright Infringement pursuant to 17 U.S.C. §512(c)
- The six elements above, numbered or clearly set apart
- Signature line

Most service providers publish a preferred form or a web intake (YouTube Content ID / Copyright webform, Twitter / X copyright report, GitHub DMCA repo, etc.). The skill produces the notice content; the user submits through the provider's path. Note in the output which intake path is expected for the named service provider.

### Step 7: The loud gate before delivery

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE THIS TAKEDOWN GOES ANYWHERE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A DMCA takedown is a statement under penalty of perjury.   │
│  Signing and sending it is not a routine administrative     │
│  step — it is a sworn declaration with specific legal       │
│  consequences.                                              │
│                                                             │
│  • 17 U.S.C. §512(f) creates LIABILITY for knowing          │
│    material misrepresentations. People have been sued,      │
│    and have lost, for bad-faith takedowns — *Lenz v.        │
│    Universal*, 801 F.3d 1126 (9th Cir. 2015); *Online       │
│    Policy Group v. Diebold*, 337 F. Supp. 2d 1195 (N.D.     │
│    Cal. 2004); *Stephens v. Clash*, 796 F.3d 281 (3d        │
│    Cir. 2015).                                              │
│                                                             │
│  • The accuracy and authority statement is sworn under      │
│    penalty of perjury. That is a real statement, not a      │
│    formality.                                               │
│                                                             │
│  • Sending a takedown on material that is in fact           │
│    licensed, owned by someone else, or fair use is the      │
│    fact pattern §512(f) was written for.                    │
│                                                             │
│  Confirm before the notice leaves:                          │
│                                                             │
│    1. You own the copyright, or you hold an exclusive       │
│       license with takedown authority.                      │
│    2. The accused use is not authorized — you have          │
│       checked licenses, grants, and any prior consents.     │
│    3. You considered fair use per *Lenz* (see Step 3 of     │
│       this draft); your conclusion is on the record.        │
│    4. Whoever has authority to sign approves sending.       │
│                                                             │
│  Approver per your practice profile: [approver from         │
│  Enforcement posture → Approval matrix → DMCA takedown      │
│  (ordinary) row]                                            │
│                                                             │
│  Automatic escalations that apply here: [list any from      │
│  the practice profile that this matter triggers]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

If the user is a non-lawyer (per `## Who's using this`), add:

> A DMCA takedown is sworn under penalty of perjury and creates §512(f) exposure for bad-faith or overbroad use. Have you reviewed this with an attorney? If not, here's a brief to bring to them: [generate a short summary: work, ownership, accused use, licensing check, fair-use analysis, signer, service provider]. A few thousand dollars of attorney time now is materially cheaper than a §512(f) suit.
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent); ABA IP section referral roster (US); law school IP clinics for individual creators and small businesses.

Do not write the final output without explicit engagement with the gate.

### Step 8: Output

**Primary:** `<matter-folder>/takedown/<slug>/notice-v<N>.md` (or .docx if the service provider accepts it — most accept pasted text or web-form submission). The notice content, ready to paste into the service provider's DMCA intake form or send to its designated agent.

**In-chat:** show the notice as plain text for review before writing. Iterate before committing to disk.

**Reviewer-facing closing note** (in the in-chat preview only):

> This is a draft DMCA notice for attorney review, not a notice ready to send. Sending it is a sworn statement with §512(f) exposure. A licensed attorney reviews, edits, and takes professional responsibility before submission. Do not send this unreviewed.

**Citation verification.** Any case or statutory citation included (for example, in internal memoranda around the notice) must be verified on a legal research tool. Source-tag each — `[Westlaw]`, `[CourtListener]`, `[user provided]`, `[model knowledge — verify]`, `[web search — verify]`. Citations tagged `verify` get checked first. No silent supplement from web or model knowledge if a configured research tool comes up thin — present options to the user.

**Post-send record.** After submission, write `<matter-folder>/takedown/<slug>/submission.md`: service provider, designated agent used (address or web form URL), date submitted, confirmation ID if returned, URLs targeted, counter-notice watch date (generally 10–14 business days), legal hold refreshed.

## Respond mode — triaging a takedown you received

Your content was taken down. A service provider has notified you of a §512(c)(3) notice. You have options.

### Step 1: Read the notice you received

Extract:

- **Sender** — entity, signer, address, email
- **Service provider** — who notified you (the platform)
- **Claimed work** — what they say is theirs
- **Your content alleged to infringe** — URL(s) or identifiers as they named them
- **Date of takedown / notice**
- **Whether the notice appears to meet §512(c)(3) on its face** — flag missing elements; a defective notice is not a proper notice

### Step 2: Assess

- **Do we have a license?** Negotiated, implied, Creative Commons, prior settlement, assignment — anything that authorizes the use.
- **Is it fair use?** Walk the *Lenz* four factors. Be honest; this is for us, not the response.
- **Is the notice defective?** Missing any of the §512(c)(3)(A) elements, lacking the perjury statement, signed by someone without apparent authority? Defective notices are not properly compliant; the host may still act on them but the sender's §512(f) exposure rises and our leverage rises.
- **Did the host comply properly with §512(g)?** Were we given notice and an opportunity to counter? If the host acted without giving us the chance, that is a separate issue with the host (not the sender).
- **Is the sender a troll?** Repeat pattern of overbroad takedowns on this platform?

### Step 3: Options

Present 4 options with tradeoffs:

**A — Comply (let the takedown stand)**
- When: they're right, or the fight isn't worth it
- Tradeoff: content stays down; may affect SEO, accounts with strikes policies, livelihood for creators
- Next step: log the event, confirm no counter-notice deadline issues, move on

**B — Send a counter-notice** (§512(g)(3))
- When: we have a good-faith belief the material was misidentified or removed by mistake — often applies where the use is licensed, fair use, or the sender doesn't own the work
- Tradeoff: sworn under penalty of perjury, consents to federal court jurisdiction in the sender's district (or our own if outside the US and we designate), puts the decision in the sender's hands for 10–14 business days — if they sue, content stays down; if they don't, content is restored
- Next step: `/ip-legal:takedown --counter`

**C — Engage the sender directly**
- When: there's room for a business resolution (license, credit, takedown of a narrower portion)
- Tradeoff: the content stays down during the conversation; settlement-communication hygiene matters (FRE 408 or equivalent; protection from substance and context, not labeling)
- Next step: outreach letter to the sender; do not send the counter-notice while discussions are live

**D — Ignore and let it stand; raise it elsewhere**
- When: the harm is small, we don't want the federal-jurisdiction admission, and we'd rather deal with the sender separately
- Tradeoff: content stays down; if the takedown itself was bad-faith, we may have §512(f) to assert on our own schedule — but that's its own fight

Recommend one with two sentences of rationale.

### Step 4: Write triage memo

Output: `<matter-folder>/takedown/inbound/<slug>/triage.md`.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs]

> **Privilege inheritance.** This triage records our first-pass assessment of an adverse takedown. It is attorney-client and/or work-product material. Do not forward outside the privilege circle or attach to counter-notice submissions without scrubbing.

# DMCA Takedown Received — Triage

> **READ FOR TRIAGE, NOT OPINION.** Structured intake scan, not a legal merit opinion. Every authority flagged for SME verification; every merit call is counsel's.

**Slug:** [slug]
**Received:** [YYYY-MM-DD]
**Service provider:** [platform]
**Incoming file:** [path]

## The notice

**Sender:** [entity, signer, counsel if any]
**Claimed work:** [title, description, reg no. if provided]
**Our content targeted:** [URLs / identifiers]
**Date of takedown:** [YYYY-MM-DD]
**Notice meets §512(c)(3) on its face:** [yes / no — list any missing elements]

## Assessment

**License / authorization check:** [read]
**Fair use walkthrough (Lenz factors):** [read — each factor + conclusion; `[SME VERIFY]`]
**Notice defects:** [list or none]
**Host compliance with §512(g):** [were we given notice and opportunity]
**Sender credibility:** [troll / real claimant / repeat takedown pattern]

## Options

### A. Comply
### B. Counter-notice (§512(g)(3))
### C. Engage sender
### D. Ignore

**Recommendation:** [A/B/C/D] — [two sentences why] — `[SME VERIFY: counsel to confirm before executing]`

## Deadlines

- **Counter-notice watch window:** 10–14 business days after counter-notice is submitted — content stays down if sender files suit in that window
- **Sender's suit filing timing:** typically on our counter-notice clock, if we counter
- **Any contractual deadlines with the host:** [check]

## Immediate actions

- [ ] Legal hold issued on the accused work and our related content — [yes/no]
- [ ] Business impact assessed (revenue, account strikes, SEO) — [yes/no]
- [ ] Matter created in log — [yes/no/TBD]
- [ ] Counsel assigned — [who]
```

Close the in-chat presentation with:

> This is a triage memo, not advice. The assessments above are a first read from the four corners of the notice. An attorney evaluates before you counter-notice (which consents to federal jurisdiction) or decide not to respond.

## Counter mode — drafting a §512(g)(3) counter-notice

Counter-notices put content back up unless the original sender sues within 10–14 business days. They are the step before litigation.

### Step 1: Confirm the predicate

- The content was taken down in response to a §512 notice (not a terms-of-service action by the host).
- You have a good-faith belief the material was removed by mistake or misidentification — the statutory test.
- You are prepared to consent to federal court jurisdiction in the original sender's district (or designate if you are outside the US).
- The decision has been made deliberately — not in reaction, not without attorney input.

### Step 2: Draft per §512(g)(3)

§512(g)(3) elements — every one must be present:

1. **Signature** (physical or electronic) of the subscriber
2. **Identification of the material removed** and its location before removal (the URL where the content was)
3. **Statement under penalty of perjury that the subscriber has a good faith belief the material was removed or disabled as a result of mistake or misidentification** — verbatim, adapted
4. **Subscriber's name, address, telephone number** — and, critically, **consent to the jurisdiction of the federal district court** for the district where the subscriber's address is located (or, if outside the US, any district in which the service provider may be found), and acceptance of service of process from the person who provided notification or that person's agent

Structure:

- Subscriber address block / date
- Recipient: designated DMCA agent at the service provider (same agent that received the original takedown)
- Re: Counter-Notification pursuant to 17 U.S.C. §512(g)
- The four elements above, numbered or clearly set apart
- Signature line

### Step 3: The loud gate before delivery

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE THIS COUNTER-NOTICE GOES ANYWHERE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A DMCA counter-notice is a statement under penalty of      │
│  perjury AND consents to federal court jurisdiction. It     │
│  is the step before litigation.                             │
│                                                             │
│  • If the original claimant files suit within 10–14         │
│    business days after your counter-notice, the content     │
│    stays down pending the suit. 17 U.S.C. §512(g)(2)(C).    │
│                                                             │
│  • If they do not sue within the window, the host must      │
│    restore the content within 14 business days of your      │
│    counter-notice.                                          │
│                                                             │
│  • You are consenting to be sued in federal court in the    │
│    claimant's judicial district (or, if you are outside     │
│    the US, designating a district). This is a jurisdiction  │
│    admission you make by signing.                           │
│                                                             │
│  • The perjury statement is real. §512(f) liability runs    │
│    in both directions — senders and counter-senders.        │
│                                                             │
│  Confirm before the counter-notice leaves:                  │
│                                                             │
│    1. The material was removed in response to a §512        │
│       notice (not a TOS action).                            │
│    2. You have a good-faith belief the removal was a        │
│       mistake or misidentification — because the use is     │
│       licensed, fair use, not actually infringing, or the   │
│       sender doesn't own the work.                          │
│    3. You are prepared to be sued in federal court in the   │
│       claimant's district. Budget, counsel, and risk        │
│       tolerance are all set.                                │
│    4. An attorney has reviewed this before it is sent.      │
│                                                             │
│  Approver per your practice profile: [approver from         │
│  Enforcement posture → Approval matrix — counter-notices    │
│  generally route above the DMCA takedown (ordinary)         │
│  approver because of the federal-jurisdiction admission]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

If the user is a non-lawyer:

> A counter-notice consents to federal court jurisdiction and is sworn under penalty of perjury. Have you reviewed with a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction? This is not the Claude-review layer; this is the step where you need licensed professional judgment. Brief for the conversation: [generate a 1-page summary]. Referral resources: your professional regulator's referral service (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent); law school IP clinics; ABA IP section (US).

Do not write the final output without explicit engagement.

### Step 4: Output

**Primary:** `<matter-folder>/takedown/<slug>/counter-notice-v<N>.md` — the counter-notice content, ready to submit via the service provider's counter-notice intake.

**In-chat:** present as plain text for review before committing.

**Reviewer-facing closing note** (in-chat only):

> This is a draft counter-notice for attorney review, not a counter ready to send. Sending it is a sworn statement and consents to federal court jurisdiction in the claimant's district. A licensed attorney reviews before submission. Do not send this unreviewed.

**Post-submission record.** After submission, write `<matter-folder>/takedown/<slug>/counter-submission.md`: service provider, date submitted, confirmation ID, 10–14 business-day watch window end date calendared, watch for suit filing in the claimant's district, plan if content is restored, plan if suit is filed.

## Decision posture

Per `## Decision posture on subjective legal calls` in the practice profile: when uncertain whether the use is fair, whether the rights holder is us, whether the work is actually ours, whether fair use defeats the claim on the receiving side — do not silently decide. Fair use is the paradigmatic uncertain call. Flag for attorney review; surface the factors. Sending a takedown or a counter-notice on an assumption is a one-way door.

## What this skill does not do

- **Submit the notice.** Drafting only. The user submits through the service provider's designated channel.
- **Pick a service provider's intake form for the user.** Notes which path is expected; does not auto-submit.
- **Decide fair use.** Walks the four factors; flags. An attorney decides whether to proceed.
- **Validate the sender's claim on the receive side.** Structured read; every authority flagged for SME verification.
- **Bypass the gate.** The gate runs every time in `--send` and `--counter` modes.
- **Invent citations.** Any cites included are source-tagged and flagged for verification; no silent supplement.
- **Handle non-US regimes.** DMCA is US-specific. For EU DSA, UK OSA, India IT Rules, and other regimes — flag and route.

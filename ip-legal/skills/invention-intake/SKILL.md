---
name: invention-intake
description: >
  Invention disclosure first-pass screen — novelty, obviousness, §101
  eligibility, bar dates, detectability, and strategic value. Use when an
  invention disclosure comes in and needs triage on whether to pursue a
  prior-art search and patent counsel review, investigate further, or decline.
argument-hint: "[paste or describe the invention disclosure — or just the title and I'll ask]"
---

# /invention-intake

**This is a first-pass screen by a non-specialist, not a patentability
opinion.** The screen never concludes that an invention is patentable — it
concludes that it passes the initial screen and warrants a prior-art search
and registered-practitioner review, that it needs more information, or that
it hits a disqualifier. A prior-art search is a separate step; this skill
does not do one.

## Instructions

1. Read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. If it
   contains `[PLACEHOLDER]`, stop and direct to `/ip-legal:cold-start-interview`. If the
   practice profile shows trademark- or copyright-only (no patent practice),
   say so and route the user elsewhere — this is the wrong tool.
2. Follow the workflow below.
3. Run intake. If the user pasted or uploaded a disclosure, read it. If not,
   ask the seven intake questions (what / problem / differences / inventors /
   public disclosure / status / technology area) in one batch and wait.
4. Run the six screens: novelty signals, obviousness flags, § 101 eligibility,
   public disclosure / bar dates, detectability, strategic value. Each screen
   gets a ✓ / 🟡 / 🔴 verdict with one-line reasoning.
5. Write the invention screen memo to the matter folder (if a matter is
   active) or the practice outputs folder. Apply the work-product header per
   role.
6. Bottom-line verdict: **PURSUE** (schedule prior-art search and attorney
   review) / **INVESTIGATE** (needs more info on a specific open item) /
   **DECLINE** (state the concrete reason). Never say "patentable."
7. Close with the decision tree (prior-art search / inventor follow-up /
   specialist review / decline + thank-you / trade-secret route) and the
   non-lawyer gate if the role is non-lawyer.
8. If the screen hit a within-one-year US disclosure or any public disclosure
   with foreign rights in scope, flag at the top: **time-sensitive**.

This skill never concludes that an invention is patentable. If uncertain,
flag — a registered patent attorney or agent decides.

## Examples

```
/ip-legal:invention-intake "a new cache-eviction algorithm that uses a learned model rather than LRU; conceived Q1 this year, not yet disclosed, engineering prototype in internal staging"
```

```
/ip-legal:invention-intake
```

(And the skill will ask for the invention, the problem it solves, how it
differs, inventors, public disclosure status, usage status, and technology
area.)

---

## THIS IS A FIRST-PASS SCREEN, NOT A PATENTABILITY OPINION

**Say this at the top of every output. Do not drop it, do not soften it.**

> **This is a first-pass screen by a non-specialist, not a patentability
> opinion.** A patentability opinion requires a prior-art search, full claim
> construction, and the judgment of a registered patent attorney or agent. This
> screen does not do a prior-art search, does not assess what is in the art, and
> does not construct claims. It screens for the obvious disqualifiers (the
> invention is already on the market, it was publicly disclosed two years ago,
> it is plainly an abstract idea) and the obvious go-aheads (new mechanism,
> technical advance, recent conception, in-use secretly). Everything in between
> needs a prior-art search and a registered practitioner's review. This screen
> never concludes that something is "patentable" — it concludes that it "passes
> the initial screen, warrants investigation" or that it does not.

Under-flagging an invention that should have been filed is a one-way door — the
one-year US bar runs, foreign rights are lost at first public disclosure, the
competitor files first. Over-flagging just means a prior-art search that comes
back empty. Stay on the two-way door side.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level
CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest
of this paragraph — skills use practice-level context and the matter machinery
is invisible. If enabled and there is no active matter, ask: "Which matter is
this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Load
the active matter's `matter.md` for matter-specific context and overrides.
Write outputs to the matter folder at
`~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/`.
Never read another matter's files unless `Cross-matter context` is `on`.

Invention disclosures are particularly common candidates for **clean-team** or
**heightened** confidentiality at matter-open. Respect the matter's
confidentiality marking from `matter.md`. Invention content is inherently
sensitive — do not summarize, quote, or reference it outside privileged
channels.

---

## Load the practice profile first

**Before reading the disclosure, read
`~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`.** If it is
missing or still contains placeholders, stop and run `/ip-legal:cold-start-interview`. The
practice profile tells you:

- The company's **patent filing strategy** — offensive (building an assertion
  portfolio), defensive (filing to protect freedom to operate), hybrid, or
  licensing-revenue. This determines the strategic-value bar.
- The **technology areas of interest** — where the company files and where it
  does not. An invention that falls outside the areas of interest is often a
  decline even if the technical screen is clean.
- The **filing budget posture** — aggressive (file everything that passes the
  screen), selective (file the best few), or minimal (only what the business
  needs to protect). This shapes the output's recommendation.
- The **approval chain** — who signs off on a filing decision, and who the
  invention gets routed to if it passes the screen.

If the practice profile shows trademark-only or copyright-only (no patent
practice), this skill is the wrong tool — say so and route the user elsewhere.

---

## Workflow

### Step 1: Intake the disclosure

If the user pastes or uploads a disclosure, read it. If not, ask — in one
batch, not one at a time:

> To screen this, I need:
>
> 1. **What is the invention?** In plain language — what does it do, what makes
>    it work, what is the key idea.
> 2. **What problem does it solve?** What was broken or missing before.
> 3. **How does it differ from what existed before?** What did people do
>    previously? What does this do differently?
> 4. **Who invented it, and when?** Names and rough conception date.
> 5. **Has it been publicly disclosed?** Published, sold, offered for sale,
>    demonstrated at a conference, shown to a customer under an NDA, posted to
>    a public repo, written up in a paper, included in a product release note.
>    If yes, when and where.
> 6. **Is it in use or planned?** Shipping now? In a limited pilot? On the
>    roadmap? Still on paper?
> 7. **What technology area?** (Software, hardware, mechanical, biotech,
>    method-of-doing-business, AI/ML, etc.)

Wait for answers. Do not proceed on a half-disclosure — a screen of "a new
machine learning thing that helps users" is worse than no screen.

If the disclosure is a formal invention disclosure form (IDF) from an IPMS or
a template, extract these fields from the form and only ask for what's missing.

### Step 2: Screen against the checklist

Walk the five screens in order. Each produces a per-screen verdict:
`✓ clear`, `🟡 flagged — needs further look`, or `🔴 red flag`. Explain the
reasoning briefly; do not pad.

#### Screen 1: Novelty signals

Does the disclosure describe something new? This is not a full novelty
analysis — that requires a prior-art search. This screens the disclosure's own
description for self-evident novelty problems.

**Red flags (🔴):**
- "We just applied [known technique] to [new domain]" — e.g., "we took
  gradient boosting and applied it to predicting customer churn"
- "It's like [existing product] but for [X]" — Uber-for-dog-walking framing
- "Competitors do something similar" — if the disclosure itself says this,
  novelty is in question
- The disclosure describes a feature of an existing public product with minor
  tuning

**Green flags (✓):**
- A new **mechanism** — a new way of doing the thing, not a new application
- A new **combination** that produces an unexpected result (not just
  additive — "faster," "smaller," "cheaper" are sometimes unexpected, sometimes
  obvious)
- Solving a problem the field **had not solved** — the disclosure explains why
  the prior approaches failed and how this one doesn't

**Flagged (🟡):** anything ambiguous. Prior-art search settles it.

#### Screen 2: Obviousness flags

Would a person of ordinary skill in the art (POSA) have arrived at this
combination based on what's known? This is a screen, not a § 103 analysis —
flag for further investigation, never conclude obviousness or non-obviousness.

**Red flags (🔴) for further investigation:**
- Combining **known elements in a predictable way** — putting a known sensor
  on a known machine to measure a known thing
- **Routine optimization** — "we tuned the existing parameter from X to Y and
  got better results"
- **Design choice without functional advantage** — aesthetic, ergonomic, or
  stylistic changes that don't change how the thing works
- **Obvious to try** — one of a small number of identified solutions with a
  reasonable expectation of success

**Green flags (✓):**
- Teaching away — prior art expected the opposite result or said this approach
  wouldn't work
- Unexpected result — the combination produces something the POSA would not
  have predicted
- Long-felt need — the problem was known, and attempts to solve it had failed

#### Screen 3: Subject-matter eligibility (§ 101)

Is this an abstract idea, law of nature, or natural phenomenon? This is the
hardest screen, the most litigated, and the one most likely to require a
specialist read. Flag anything borderline for specialist review.

**Red flags (🔴) for § 101:**
- Pure **business method** without technical implementation — "a method of
  pricing widgets more efficiently"
- **Mathematical algorithm** on its own — even as dressed up in pseudocode
- **Organizing human activity** — scheduling, pairing, matching, reviewing —
  without a technical improvement
- Claim that reads as "**do [known thing] on a computer**" with no
  improvement to the computer itself
- AI/ML invention where the claim is the **function** (recommend, classify,
  predict) without the specific technical means that improves how the computer
  performs the function

**Green flags (✓) for software/AI inventions:**
- Technical improvement to the **computer itself** — new architecture, new
  training technique, new hardware/software interface, new security mechanism
- Specific technical means, not just results
- Improvement to a **technical field** (image processing, compression,
  cryptography, robotics) with the technical means described

**Anything borderline gets a 🟡 with "§ 101 — route to specialist for
Alice/Mayo analysis."** A non-specialist should not call a close § 101
question.

For **biotech / diagnostic** inventions, also flag for § 101 if the claim
recites:
- A natural correlation ("if level of X is above Y, patient has Z")
- A naturally occurring substance (isolated gene, natural product) without
  significant human modification

> **§101 is a US standard. Other patent offices are different.** The EPO's "technical effect" test (Art. 52 EPC) is materially more permissive for software and AI inventions than US §101 post-*Alice*. JPO and CNIPA also apply different standards. An invention that screens 🔴 under *Alice* may be perfectly eligible at EPO/JPO/CNIPA.
>
> When the practice profile includes non-US jurisdictions: "This §101 screen is US-only. If you file internationally, the eligibility posture may be different — particularly for software, AI/ML, and business methods, which EPO is more permissive on. Don't decline based on US §101 alone if you have EP/JP/CN filing plans."

#### Screen 4: Public disclosure / bar dates

Has the invention been disclosed, sold, offered for sale, or publicly used?
This is the most time-sensitive screen — the answer can kill patentability
absolutely, or start a clock that cannot be stopped.

Categorize the disclosure status:

**🔴 Likely barred:**
- Publicly disclosed, sold, or offered for sale **more than 12 months ago**
  in the US — 35 U.S.C. § 102(b) one-year grace period has run
- **Any** public disclosure, anywhere, before filing — absolute novelty bar in
  the EU, China, Japan, and most countries outside the US. If the business
  cares about foreign rights, this is potentially fatal even if US is still
  open.

**🟡 Clock is running:**
- Publicly disclosed within the last 12 months — US one-year clock is running,
  foreign rights may already be lost. Urgent. Confirm the disclosure date and
  route to filing immediately.

**✓ Clear:**
- No public disclosure. Confidential customer demonstrations under NDA, internal
  use, beta releases to named parties under NDA, draft papers not yet submitted
  — usually not "public" for § 102 purposes, but depends on the facts. When the
  disclosure was to a customer or external party, even under NDA, flag the
  specifics for the prosecution team to assess.

**Ask specifically about:**
- Papers submitted to journals or conferences (submission ≠ publication; but
  check the journal's policy and whether preprints were posted)
- Talks given at conferences, meetups, internal company events open to
  non-employees
- Posts to public repos, blogs, social media, or forums
- Product releases, even in limited beta
- Sales activity including quotes, RFP responses, and offers for sale
- Disclosures to investors or board members who are not under NDA

The **on-sale bar** catches offers for sale of a product embodying the
invention, not just completed sales. An RFP response describing the invention
can trigger it.

#### Screen 5: Detectability

If a competitor were to infringe this invention, could you tell? An invention
that's practiced in secret — server-side processing, back-office operations,
internal manufacturing techniques — may be better protected as a **trade
secret** than as a patent. Publishing a patent on an undetectable invention is
giving it to competitors in exchange for an asset you can never enforce.

**🔴 Low detectability flags:**
- Server-side algorithm with no observable output pattern
- Internal manufacturing process (e.g., a novel etch step in a semiconductor
  process)
- Data-pipeline or analytics methodology that happens inside a competitor's
  infrastructure
- Training data composition or training technique for an ML model — visible
  only through fine-grained probing, if at all

For these, flag for the **patent-vs-trade-secret decision**. The question is
not "is this patentable" but "should we patent it if we could." Route to
whoever in the practice profile owns trade-secret classification decisions.

**✓ High detectability:**
- Consumer product — visible in the product
- Published API, SDK, protocol — visible in network traffic or integration
  docs
- Physical mechanism in a distributed product — reverse-engineerable
- Compiled code with distinctive signatures in a distributed binary

#### Screen 6: Strategic value

Does this align with the company's patent strategy from the practice profile?
This is where the screen becomes company-specific rather than doctrinal.

Check against the profile:

- **Offensive strategy (build to assert):** is this asset assert-worthy? A
  narrow, easily designed-around patent has lower offensive value than a broad
  mechanism claim. Is the competitive landscape one where you would want to
  sue?
- **Defensive strategy (build to protect FTO):** does this cover a technology
  area where competitors are filing? A defensive filing in an area nobody
  files in is a wasted spend.
- **Licensing / revenue strategy:** is this licensable? Who would pay for it,
  and under what circumstances?

Also check:

- Is this **core** technology (part of the product's differentiation) or
  **peripheral** (incidental to a side feature)? Core is worth more.
- What is the **competitive landscape**? Patent-heavy (semiconductors,
  pharmaceuticals) — file early or lose the race. Patent-light (many
  open-source-heavy software segments) — sometimes skip entirely and spend
  the money elsewhere.
- Is the technology area on the company's list of **tech areas of interest**
  from the practice profile? If not, it is often a decline regardless of
  doctrine.

### Step 3: Assemble the invention screen memo

Format:

> **Invention screen memo — [invention title]**
>
> **Bottom line: [PURSUE / INVESTIGATE / DECLINE]**
>
> *[One sentence — the reason in plain language.]*
>
> ---
>
> ### Screen results
>
> | Screen | Verdict | Notes |
> |---|---|---|
> | Novelty signals | [✓ / 🟡 / 🔴] | [one-line reasoning] |
> | Obviousness flags | [✓ / 🟡 / 🔴] | [one-line reasoning] |
> | § 101 eligibility | [✓ / 🟡 / 🔴] | [one-line reasoning] |
> | Public disclosure / bar dates | [✓ / 🟡 / 🔴] | [one-line reasoning + dates] |
> | Detectability | [✓ / 🟡 / 🔴] | [one-line reasoning] |
> | Strategic value | [✓ / 🟡 / 🔴] | [one-line reasoning, referenced to profile] |
>
> ---
>
> ### Open questions
>
> *Things that would change the answer. The inventor, the prosecution team, or
> a specialist would need to address these before this screen converts to a
> filing decision.*
>
> - [question]
> - [question]
>
> ### Next steps (decision tree)
>
> Pick one and I'll help you build it out:
>
> 1. **Commission the prior-art search** — I'll draft the search request for
>    [outside counsel / search vendor] with the claim concepts, inventors,
>    technology classification, and any known references.
> 2. **Go back to the inventor for more facts** — I'll draft the follow-up
>    questions on [specific open items above].
> 3. **Route to outside counsel for § 101 / patent-vs-trade-secret judgment** —
>    I'll draft a transmittal summarizing what the screen found and what
>    specialist judgment is needed.
> 4. **Decline and send the standard thank-you** — I'll draft the inventor
>    thank-you and archive the disclosure with the declination reason.
> 5. **Flag for trade secret instead** — I'll draft a note to whoever owns
>    trade-secret classification explaining why a trade-secret approach is a
>    better fit.

Apply the work-product header per role. Apply the reviewer note. Keep the
deliverable clean of internal narration ("I'm using the invention-intake
skill..." etc.).

### Step 4: Recommend the bottom-line verdict

The bottom line is one of three:

- **PURSUE** — enough screens are clear (or clearly fixable) to warrant a
  prior-art search and attorney review. This is NOT "patentable" — it is
  "passes the initial screen, investigation warranted."
- **INVESTIGATE** — one or more screens flagged something that needs more
  information, specialist review, or a clarifying question back to the
  inventor before a pursue/decline decision can be made. Name the specific
  open item.
- **DECLINE** — a screen hit a fatal flag (barred by disclosure over 12
  months old with no foreign rights concern, plainly obvious, plainly abstract
  under Alice, outside the company's technology areas of interest, fundamentally
  undetectable with no trade-secret path). State the reason clearly.

A DECLINE should always be backed by a concrete reason the inventor can
understand. "Not patentable" is not an acceptable decline reason; "barred by
your paper at NeurIPS 2023 — the US one-year bar ran in December 2024" is.

## Guardrails

**Never say "patentable."** The closest you can come is "passes the initial
screen, warrants further investigation." Patentability is a conclusion a
registered practitioner reaches after a prior-art search and claim
construction.

**Never do a prior-art search in this skill.** A WebSearch for "does this
already exist" is not a prior-art search — it's a credibility check the
user can also run. If you want to sanity-check novelty, say so explicitly
("quick web check — the technique was discussed in [X] — this is not a prior-
art search, it's context for the screen") and flag it as `[web — verify]`.

**Defer on § 101 calls.** For anything borderline under Alice/Mayo, flag for
specialist review. § 101 is where practitioners routinely disagree and where
a non-specialist's confident call ages badly.

**Flag detectability before strategic value.** An undetectable invention that
would be "high strategic value" as a patent is usually higher strategic value
as a trade secret. Do not recommend PURSUE on an undetectable invention
without addressing the trade-secret alternative.

**Urgent cases get urgent flagging.** If the screen hits a within-one-year
public disclosure in the US, or any public disclosure with foreign rights in
scope, say so at the top of the memo. Bottom line, then: "**Time-sensitive —
US bar runs [date], foreign rights already at risk.**" This is the kind of
finding a lawyer needs to see in the first three seconds.

**Respect the routing.** Per the practice profile, this screen is a triage
step. The person who decides what to file is the attorney or agent responsible
for patent prosecution. The screen feeds that person; it does not replace them.

## Non-lawyer gate

If the role is **non-lawyer** (with or without attorney access), close the
memo with:

> **This is a screening tool for your disclosure, not a patentability opinion.
> The decision about whether to file — and how — belongs to a registered
> patent attorney or agent. If this screen says PURSUE or INVESTIGATE, your
> next step is not to file or draft claims; it is to share this memo (and the
> underlying disclosure) with patent counsel. If there is no counsel engaged
> yet, [contact from profile / "your professional regulator's IP referral service — state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent"] is the
> starting point.**

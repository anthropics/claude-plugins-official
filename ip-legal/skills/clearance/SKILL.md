---
name: clearance
description: >
  Trademark clearance first pass — knockout + similar-marks check producing a
  flag list, not a clearance opinion. Use when a new mark is proposed, when
  asked whether a mark is available or to run a knockout search, or when
  assessing likelihood-of-confusion factors before a full professional search.
  This skill never concludes a mark is clear.
argument-hint: "[describe the proposed mark, goods/services, and jurisdictions — or just the mark and I'll ask]"
---

# /clearance

**This is a triage, not a clearance opinion.** A trademark clearance opinion
requires a full professional search and registered trademark counsel's
judgment. A "no obvious conflicts" result means the triage
didn't find anything — it does not mean the mark is clear. Clients have been
sued over marks that passed a knockout search.

## Instructions

1. Read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. If it
   contains `[PLACEHOLDER]`, stop and direct to `/ip-legal:cold-start-interview`.
2. Follow the workflow below.
3. Run intake (mark, goods/services, classes, jurisdictions, visual/stylization).
4. Knockout check for intrinsic bars — generic, descriptive, deceptive,
   geographic, surname, false connection, prohibited matter, functional.
5. Similar-marks search against what's connected (Solve Intelligence, CourtListener, Descrybe, or whatever MCP is available). If nothing is
   connected, say so in the output and proceed with the factor analysis only.
6. Walk the applicable circuit's likelihood-of-confusion factors — du Pont /
   Polaroid / Sleekcraft / other. Flag each; never conclude.
7. Write the triage memo to the matter folder (if a matter is active) or the
   practice outputs folder. Apply the work-product header per role.
8. End with recommended next steps and the non-lawyer gate if the role is
   non-lawyer.

This skill never concludes a mark is clear. If uncertain, flag — the attorney
decides.

## Examples

```
/ip-legal:clearance "APEXLEAF for an outdoor apparel line, planned launch US + EU"
```

```
/ip-legal:clearance
```

(And the skill will ask for the mark, goods, classes, and jurisdictions.)

---

## THIS IS A FIRST PASS, NOT A CLEARANCE OPINION

**Say this at the top of every output. Do not drop it. Do not soften it.**

> **This is a first pass, not a clearance opinion.** A trademark clearance opinion
> requires a full professional search (TESS, state registries, common law sources,
> international registries, domain and social, trade dress and design marks where
> relevant) and attorney judgment on likelihood of confusion, which depends on
> factors a structured triage cannot fully assess. A "no obvious conflicts" result
> from this skill means the triage didn't find anything — it does not mean the
> mark is clear. Clients have been sued over marks that passed a knockout search.
> A registered trademark attorney evaluates before anyone adopts, files, or
> invests in this mark.

This is the loudest guardrail in the plugin. Under-calling a conflict is a
one-way door — a logo on trucks, a product launched, a TM application filed, all
with a problem underneath. Over-calling is a two-way door — the attorney narrows
the list in review. Stay on the two-way door side.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Load the practice profile first

Before running clearance, read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. Pull:

- **Role** from `## Who's using this` (lawyer vs. non-lawyer changes the work-product header and the non-lawyer gate below).
- **Registered in** and **enforce where** from `## IP practice profile` and `## Enforcement posture` (default jurisdictions if the user doesn't specify).
- **Integrations** from `## Available integrations` (CourtListener / Solve Intelligence / Descrybe — each determines what searches are available to run, what the fallback is, and what gets attributed in the output).
- **Decision posture** from `## Decision posture on subjective legal calls` — this skill never concludes "not confusingly similar."

If `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` contains `[PLACEHOLDER]` or `[Your Company Name]`, surface this bounce:

> I notice you haven't configured your practice profile yet — that's how I tailor posture, jurisdictions, and approval chain to your practice.
>
> **Two choices:**
> - Run `/ip-legal:cold-start-interview` (2 minutes) to configure your profile, then I'll run this tailored to YOUR practice.
> - Say **"provisional"** and I'll run this against generic defaults — US jurisdiction, middle risk appetite, lawyer role, no playbook — and tag every output `[PROVISIONAL — configure your profile for tailored output]` so you can see what I do before committing.

### Provisional mode

If the user says "provisional," run the clearance normally using these generic defaults: middle risk appetite, lawyer role, US jurisdiction (USPTO + common-law), no playbook (do the full analysis rather than matching against a position list). Tag the reviewer note and every finding block with `[PROVISIONAL]`. At the end of the output, append:

> "That was a generic run against default assumptions. Run `/ip-legal:cold-start-interview` to get output calibrated to YOUR practice — your playbook, your jurisdiction, your risk appetite. 2 minutes."

---

## Intake

Ask once, in a single batch (don't drag out a quick job):

> A few questions before I run the triage:
>
> 1. **Proposed mark.** Exact spelling, any stylization, and whether it's a word mark, logo, or both.
> 2. **Goods or services.** What's actually being sold or offered under this mark. A sentence or two — I'll map to international classes.
> 3. **Classes.** If you already know the Nice classes, list them. Otherwise describe the goods/services and I'll suggest the likely classes and confirm with you before running the search.
> 4. **Jurisdictions.** Where do you plan to use, register, or enforce? (US / EU / UK / Madrid / specific countries — I'll default to `Registered in` from your practice profile if you don't say.)
> 5. **How it will appear in use.** Any taglines, adjacent product names, trade dress, or design elements that would show up with it in market.

Wait for the answer. If the description is vague ("AI tool," "platform"), push once:

> Give me the actual thing a customer sees — is it a consumer mobile app, enterprise API, physical product, service? The classes turn on this.

---

## Knockout check

Before any database search, run the intrinsic problems that kill a mark regardless
of prior registrations. For each, assess plainly and flag. Do not rationalize away
a clear issue.

| Bar | What it means | Flag when |
|---|---|---|
| **Generic** | The term IS the category (e.g., "Soap" for soap) | The mark names what the thing is |
| **Descriptive** | Directly describes a feature, function, quality, or ingredient | A consumer reads the mark and knows what the product does without imagination |
| **Deceptive / deceptively misdescriptive** | Misrepresents a material feature | The mark suggests a quality the goods don't have and that quality would matter |
| **Primarily geographically descriptive / deceptive** | Mark is primarily a place name and goods come from (or don't) that place | Mark = place + generic; or place + goods where customers would assume origin |
| **Primarily merely a surname** | Mark is primarily a surname | Mark reads as someone's last name to the relevant consumer |
| **False connection** | Mark falsely suggests connection with person, institution, national symbol | Mark invokes a specific identifiable person or institution |
| **Prohibited matter** | Flags, coats of arms, insignia, specific prohibited categories | Mark contains a prohibited element |
| **Functional (for design marks / trade dress)** | The feature is essential to use or affects cost/quality | Design mark — and the feature performs a function |

Note on scandalous/immoral marks: after *Iancu v. Brunetti* (2019) and *Matal v.
Tam* (2017), the USPTO no longer refuses registration on those bases. The
surviving statutory bar in this zone is false connection under §2(a). Apply that;
don't flag under the struck-down bars.

**Output:** for each knockout category, either "no issue identified" or a
specific flag with a one-line reason. Don't produce a blank table of passes.

---

## Similar marks check

The purpose here is to **find potentially confusingly similar prior marks**, not
to decide whether confusion is likely. That is the attorney's call.

### What the user has connected

Read `## Available integrations` from `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`:

- **If a trademark search connector is available** (Solve Intelligence,
  Descrybe — or any MCP exposing TM-registry search): run a preliminary search
  across the relevant classes and jurisdictions. Attribute every result to its
  source. Note the date of the search and the scope (which registries, which
  classes, exact-match vs. fuzzy, design search or not).
- **If a legal research connector is available** (CourtListener for litigation for case law and TTAB decisions): sweep for reported disputes involving
  the mark or a close variant. Same attribution rule.
- **If no search connector is available:** say so, explicitly, in the output.
  Do not infer results from model knowledge and present them as search findings.

### Fallback when no database access exists

Write out, in the output, this exact statement:

> **No database search was run.** This triage did not hit TESS, Solve
> Intelligence, Descrybe, CourtListener, state registries, Madrid/WIPO, or any
> common law / unregistered-mark sources. A knockout or full search across those
> databases is required before any conclusion about availability. The triage
> below is limited to intrinsic-bar analysis and structured confusion factors
> against marks the user has identified or that come up in the conversation.

Then proceed — the intrinsic checks and the factors analysis are still useful,
just labeled honestly.

### For each similar mark found (or supplied)

Capture:

- **Mark** (exact characters, any stylization)
- **Source** (TESS registration no., Madrid designation, state registry, case
  citation, domain, social handle — whichever)
- **Classes / goods-services description** from the register
- **Owner**
- **Status** (registered / pending / abandoned / cancelled — a dead mark is not a
  bar but can be relevant to fame and to a predecessor's rights)
- **First-use date if available**

**Do not supplement silently.** If you cite a USPTO registration number, it came
from the search you ran; if you describe a mark the user mentioned, say that.
Never invent a registration and never "fill in" a detail the record doesn't
support. If the search didn't return a first-use date, write "first-use date not
available from search result" — do not guess.

### Adjacent families sweep (required before concluding)

A clearance that only checks exact and near-exact matches misses the marks a
competitor adopted *because* yours was taken. Before concluding, identify 3–5
adjacent word families the practitioner should also sweep, and ask the user to
confirm or add to the list.

Adjacent families are category-conventional substitutes a reasonable competitor
would consider when the direct mark is unavailable. For a mark like
`NEXUS HOME` in the smart-home hub space, the adjacent families include at
minimum:

- **Category synonyms** for NEXUS: `HUB`, `NEST`, `CORE`, `LINK`, `CONNECT`,
  `BRIDGE`, `CENTRAL`, `GATEWAY`.
- **Assistant-style names** in the same product category: `ALEXA`,
  `ECHO`, `SIRI`, `GOOGLE HOME`, `CORTANA`, `HOMEY`, `HOMEBASE`.
- **HOME / HOUSE / SMART variants**: `SMART HOME`, `HOUSEHOLD`, `HOUSE`,
  `ABODE`, `CASA`, `DOM`.
- **Phonetic twins** on the root: `NEXIS`, `NEKSUS`, `NEXXUS`, `NECTIS`,
  `KNOXUS` (depending on how the word sits in the market).

The skill should output an adjacent-families block in the Similar Marks section
with a confirmation prompt:

> **Adjacent families to sweep (please confirm or add):**
>
> - [family 1 — e.g., HUB / NEST / LINK / CONNECT]
> - [family 2 — e.g., ALEXA-style assistant names]
> - [family 3 — e.g., HOME / HOUSE / SMART variants]
> - [family 4 — phonetic twins on the root]
>
> A clearance that only checks exact and near-exact matches misses the marks a
> competitor adopted because yours was taken. Confirm this list is complete for
> the category before I continue.

> **When non-English-speaking jurisdictions are in scope,** the English-only phonetic sweep misses the most common source of cross-border conflicts. Add:
> - **Translation equivalents.** The mark translated into the relevant languages. The EU's foreign-equivalents doctrine treats a translation as the same mark for confusion purposes.
> - **Transliteration.** The mark written in the relevant script (Cyrillic, Chinese/Japanese/Korean, Arabic, Hangul, Thai). Phonetic equivalence across scripts is a recognized conflict basis.
> - **Script variations.** Marks registered in a non-Latin script that sound like your mark when romanized.
>
> If you can't perform cross-language analysis, say so: "Cross-language phonetic and translation-equivalent analysis not performed — this is the most common source of cross-border conflicts. A clearance search in [jurisdiction] should include it."

If the practitioner has a connected TM search tool, re-run the sweep against
each confirmed adjacent family (exact + phonetic + translation-of-foreign-equivalent
where relevant) and add the results to the Similar Marks table with the
`Adjacent family` source noted. If no connector is available, say so, and list
the families as the explicit next-step input for a full professional search —
do not silently skip the sweep.

---

## Likelihood-of-confusion factors

> **Confusion framework is jurisdiction-specific.** The US and EU assess likelihood of confusion differently. Don't apply the wrong one.
>
> - **US (federal circuits):** Multi-factor tests (*du Pont*, *Polaroid*, *Sleekcraft*) — strength of the mark, similarity (sight/sound/meaning), proximity of goods, channels, buyer sophistication, actual confusion, intent.
> - **EU (Art. 8(1)(b) EUTMR):** Global appreciation — all relevant factors assessed holistically through the eyes of the average consumer. Key differences: greater weight on phonetic similarity; translation equivalents as standard (the mark translated into EU languages); "likelihood of association" beyond source confusion; the distinctiveness of the earlier mark carries more weight.
> - **UK (TMA 1994 §5(2)):** Follows the EU global appreciation approach post-Brexit but diverging case law. Check for UK-specific decisions.
> - **Other jurisdictions:** If the intake includes a jurisdiction without a framework above, say: "I don't have [jurisdiction]'s confusion framework. Applying the US test would give you a wrong answer that looks right. Options: (a) I search for the applicable standard, (b) you route to a [jurisdiction] trademark specialist, (c) I note this jurisdiction is out of scope." Never silently apply US doctrine.

The relevant circuit's test determines the factors to walk through. Cite the
test that applies:

- **TTAB / Federal Circuit:** *In re E. I. du Pont de Nemours & Co.*, 476 F.2d
  1357 (C.C.P.A. 1973) (13 factors).
- **Second Circuit:** *Polaroid Corp. v. Polarad Electronics Corp.*, 287 F.2d 492
  (2d Cir. 1961) (8 factors).
- **Ninth Circuit:** *AMF Inc. v. Sleekcraft Boats*, 599 F.2d 341 (9th Cir. 1979)
  (8 factors).
- **Other circuits:** walk through the circuit's named multi-factor test (e.g.,
  *Frisch's Restaurants* in the Sixth Circuit, *Scotch Whisky Association* in the
  Seventh, *Lapp* in the Third).

Pick based on where the user plans to enforce (practice profile), the TTAB if
the immediate forum is registration, or the primary commercial forum otherwise.
Note your pick in the output.

For each factor, produce a **flag**, not a verdict. Each factor should say what
cuts each way and where the uncertainty is:

- **Similarity of marks** (appearance, sound, meaning / connotation, commercial
  impression). Sight-sound-meaning, considered together.
- **Similarity of goods or services.** Not whether the goods are identical —
  whether consumers would expect them to come from the same source.
- **Channels of trade.** Where each side actually sells (or would sell). Same
  stores? Same distribution? Same trade shows? Online-only?
- **Sophistication of consumers.** Impulse buy at a gas station vs. considered
  enterprise purchase changes the standard of care.
- **Strength of prior mark found.** Fanciful / arbitrary / suggestive /
  descriptive / generic, and fame evidence if any. A strong prior mark gets
  wider protection.
- **Intent.** Evidence of intent to trade on goodwill — a near-copy with similar
  trade dress in an adjacent class is different from an independent coinage.
- **Actual confusion.** Any evidence (misdirected inquiries, surveys, reviews,
  social posts).
- **Likelihood of expansion** (bridge-the-gap). Whether the senior user is
  likely to expand into the junior's lane, and vice versa.

Per the decision posture in `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`:

- **Never conclude "not confusingly similar."**
- If uncertain, write: "Similar marks found — confusion assessment required
  before adoption." Or: "Factors cut both ways; attorney judgment required."
- Clear space for "no similar marks found in the databases searched" is fine
  *only* if a real search was run; see the no-search fallback above otherwise.

---

## Recommended next steps

Every clearance output ends with concrete next steps, bucketed by what the
triage found:

- **If knockout issues found:** reframe the mark, or accept the descriptiveness
  bar and plan for secondary-meaning over time; route for attorney review before
  adopting.
- **If similar marks found in the databases searched:** attorney review is
  required before adopting, filing, or marketing. Often the next step is a full
  professional search to find everything the triage missed.
- **If no similar marks found but no database search ran:** a full search is
  required before adoption. Name the databases that need to be hit.
- **If similar marks found and the senior mark is weak, old, in a different
  class, or abandoned:** flag for attorney review — the triage will not make
  this call.
- **Always:** a full clearance opinion from registered trademark counsel, scaled
  to the investment the mark will carry. A mark you'll put on a product line and
  a Super Bowl ad carries more weight than a mark for a one-off pop-up.

---

## Output format

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` `## Outputs`.

```markdown
[WORK-PRODUCT HEADER]

# Trademark Clearance — First Pass (NOT AN OPINION)

**This is a first pass, not a clearance opinion.** A clearance opinion requires
a full professional search and attorney judgment. A "no obvious conflicts"
result here means the triage didn't find anything — it does not mean the mark
is clear. A registered trademark attorney evaluates before anyone adopts, files,
or invests in this mark.

**Triage result:** [GREEN / YELLOW / RED — one sentence why]

## Proposed mark

- **Mark:** [exact text, stylization noted]
- **Mark type:** [word / design / composite]
- **Goods / services:** [description]
- **Classes:** [Nice class numbers with one-line descriptions]
- **Jurisdictions:** [US / EU / UK / Madrid / specific countries]
- **Confusion test applied:** [du Pont / Polaroid / Sleekcraft / other — with the
  reason it's the right one]

## Knockout issues

| Bar | Flag | Note |
|---|---|---|
| Generic / descriptive / deceptive / geographic / surname / false connection / prohibited / functional | [none / flagged] | [one line if flagged] |

## Similar marks check

**Sources searched:** [registries and databases hit, with dates — or "no database
search run; see scope note below."]
**Scope:** [classes, jurisdictions, exact-vs-fuzzy, design search or not]

**Adjacent families swept (confirmed with user):**
- [family 1 — e.g., HUB / NEST / LINK / CONNECT / BRIDGE / GATEWAY]
- [family 2 — e.g., ALEXA-style assistant names]
- [family 3 — e.g., HOME / HOUSE / SMART variants]
- [family 4 — phonetic twins on the root]

*A clearance that only checks exact and near-exact matches misses the marks a
competitor adopted because yours was taken. If any family was not swept (no
connector, time not available), it is listed explicitly as a next-step input
to the full professional search — not silently skipped.*

| Mark | Source | Classes / G&S | Owner | Status | First use | Note |
|---|---|---|---|---|---|---|
| [exact] | [registration no. / citation / URL] | [class list] | [owner from record] | [reg/pending/abandoned/cancelled] | [date or "not available"] | [why it matters — exact match / adjacent family] |

*If no search was run:* **No database search was run.** This triage did not hit
TESS, Solve Intelligence, Descrybe, CourtListener, state registries,
Madrid/WIPO, or any common law / unregistered-mark sources. A knockout or full
search across those databases is required before any conclusion about availability.

## Confusion factors — flags for attorney review

For each of the factors under the test applied, a one-line flag noting what cuts
each way.

| Factor | Flag | Direction |
|---|---|---|
| Similarity of marks (sight / sound / meaning / commercial impression) | [note] | [weighs toward / against conflict / mixed] |
| Similarity of goods or services | [note] | [direction] |
| Channels of trade | [note] | [direction] |
| Consumer sophistication | [note] | [direction] |
| Strength of prior mark | [note] | [direction] |
| Intent | [note] | [direction] |
| Actual confusion | [note or "no evidence surfaced"] | [direction] |
| Likelihood of expansion / bridge-the-gap | [note] | [direction] |

**Conclusion on confusion:** *This skill does not conclude.* Either:
- "Similar marks found; attorney confusion assessment required before adoption."
- "No similar marks found in the databases searched; full clearance required
  before adoption."
- "Factors cut both ways; attorney judgment required."

## Recommended next steps

- [specific next step 1 — e.g., "Full professional search across USPTO, state
  registries, common law sources, EUIPO, and UK IPO before adoption"]
- [specific next step 2 — e.g., "Design-around review of the `APEXLEAF` mark
  in Class 25 if the intent is to proceed"]
- [specific next step 3 — e.g., "Reframe the mark — current form is descriptive
  and will require secondary meaning"]
- [routing per `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` —
  trademark OC or in-house IP counsel named in the practice profile]

## Citation verification

Every case, registration number, statute, and database result in this memo must
be verified against the authoritative source before relying on it. Registration
numbers, class designations, and first-use dates are the most common sites of
error. Do not cite a result you cannot open.
```

---

## Non-lawyer gate

Before issuing the output, read `## Who's using this`. If the Role is Non-lawyer:

> This output is a research triage, not legal advice. Adopting, filing, or
> investing in this mark based on this triage alone has legal consequences —
> including being sued for infringement over a mark that "passed" this check.
> A registered trademark attorney needs to evaluate before you move.
>
> Here's a brief to bring to an attorney — it'll cut the time the conversation
> takes:
>
> [Generate a 1-page summary: the proposed mark, the goods/services and classes,
> the knockout issues (if any), the similar marks surfaced (if any), what was
> and wasn't searched, and the three questions to ask the attorney.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). The INTA (International Trademark Association)
> maintains a member directory of registered trademark practitioners.

Deliver the full triage memo alongside the brief. Do not withhold the analysis.

---

## Output location

If matter workspaces are enabled and a matter is active, write the output to
`~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/outputs/clearance-<mark-slug>-YYYY-MM-DD.md`.
Otherwise write to
`~/.claude/plugins/config/claude-for-legal/ip-legal/outputs/clearance-<mark-slug>-YYYY-MM-DD.md`
and surface the path to the user.

Append a one-line entry to the matter's `history.md` if a matter is active.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- **Conclude a mark is clear.** Ever. The loudest guardrail in the plugin.
- **Substitute for TESS search, state-registry search, common-law search,
  international search, watch-service check, or design-mark search.**
- **File a trademark application.** Filing is an attorney task; this skill
  informs the decision to file.
- **Evaluate trade dress, trademark dilution, or famous-mark claims** beyond a
  preliminary flag. Dilution under the TDRA requires a fame analysis this
  skill does not attempt.
- **Address foreign local-law bars** (e.g., phonetic similarity standards in
  Japan, translation-of-foreign-equivalents in the EU) beyond flagging that
  foreign analysis is required when a foreign jurisdiction is in scope.
- **Quote outputs to customers, counterparties, or the press.** This is
  internal research. Privileged if the header at the top applies.

---

## Tone

Crisp, concrete, honest about scope. The lawyer reading this output should know
in ten seconds what the triage found, what it didn't, and what has to happen
before anyone adopts the mark. No hedging prose. The guardrail at the top and
the "this skill does not conclude" line on confusion do the scope work.

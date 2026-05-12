---
name: brief-section-drafter
description: Draft a brief section in house style, consistent with the case theory — every fact cited, every case checked, every argument tied to the theory. Use when the user says "draft the [section]", "write the statement of facts", "argument section on [issue]", or needs a first draft of a brief section.
argument-hint: "[section \u2014 e.g., 'statement of facts', 'argument II']"
---

# /brief-section-drafter

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → case theory, house style.
2. Follow the workflow and reference below.
3. Draft in house format/tone/citation style. Consistent with theory.
4. Output: draft section. Flag every place a fact or cite needs verification.

---

# Brief Section Drafter

## Witness statements for England & Wales — PD 57AC

If the user's jurisdiction includes England & Wales and they're asking for a trial witness statement for the Business & Property Courts (or any CPR-governed proceeding), PD 57AC applies. The statement must be in the witness's own words, must not contain argument, must identify the documents the witness used to refresh their memory, and must carry the required confirmation of compliance and the legal representative's certificate.

**Drafting a narrative "as the witness" from a chronology, document set, or your account of the case is exactly what PD 57AC was designed to prevent.** Courts are actively sanctioning AI-assisted witness statement drafting. If you ask me to do it, I won't.

What I WILL do: prepare question prompts to elicit the witness's actual recollection; capture and organize what the witness says (their words, not mine); generate the list of documents they were shown; run a PD 57AC compliance checklist against a statement they've drafted; draft the solicitor's certificate of compliance. I help you get the witness's evidence into the statement. I don't write the evidence.

For US depositions, declarations, and affidavits: different rules, but the same discipline applies. A declaration in the declarant's voice that the declarant didn't write is a credibility problem at best.

## Purpose

A good brief section is consistent with the theory, cited to the record, written in house style, and checkable. This skill produces the first draft — emphasis on *draft*. Partner edits.

## Written or oral?

Ask before drafting: "Is this for a written submission or oral argument?" They are different crafts:

- **Written:** thorough. Cover the points, develop the authority, anticipate the responses.
- **Oral (rebuttal, closing, argument):** strategic. Pick the 3-4 points that matter most. Concede or ignore the weak ones. Lead with your strongest. A tribunal remembers the first two minutes and the last two. "Too thorough" for oral advocacy reads as unfocused. If you're responding to a multi-issue submission, tell the user which issues you'd press and which you'd let go — that's the draft of the strategy, not just the words.

## Record fidelity — quotes and pinpoints

Two rules that govern every citation and every quotation in advocacy drafting. The canonical statement lives in the plugin's `CLAUDE.md` shared guardrails; repeated here because this skill is the most common place the rule gets tested.

**Verbatim quotes from the record must be verbatim.** Never put quotation marks around words attributed to opposing counsel, a witness, the court, or any record document unless you have the exact passage in front of you and can cite to it. A quote that's almost right is worse than a paraphrase — it misrepresents the record, it's sanctionable if filed, and it will be caught. When you want to characterize what someone said but can't find the exact words:

- **Paraphrase without quotation marks**, attributing clearly: "Opposing counsel argued that X `[verify against record — Tr. p. __]`."
- **Mark the placeholder:** `[verify exact quote — record cite pending]`
- **Never fill the gap.** An invented quote, even one word, is a fabrication. The reviewer note must flag every `[verify exact quote]` in the output.

Before citing any passage with quotation marks, have the source open. If you're working from memory or a summary, no quotation marks.

**Pinpoint cites must support the whole proposition.** If the argument is "opposing counsel said X, Y, and Z" and you're citing one pinpoint, verify the pinpoint supports X AND Y AND Z. If it only supports Z, either (a) split the cite — "said X (Tr. p. 10), Y (Tr. p. 12), and Z (Tr. p. 15)" — or (b) narrow the proposition to what the pinpoint actually supports. A cite that supports part of a claim is how a tribunal catches you stretching. It's the single most common way a lawyer's credibility erodes in front of a court. This is the "misgrounded citation" failure mode: the cite exists, the passage exists, but the passage doesn't support the proposition as stated.

## Candor about weak arguments

When the law is against you, say so. When an argument is weak — the authority cuts the other way, the facts don't support it, the inference is a stretch — don't construct a shaky argument and present it as if it were solid. Flag it:

> "This point is weak — [authority] cuts the other way. Consider whether to press it (here's how you'd frame it), concede and pivot to [stronger point], or drop it. `[review — strategic call]`."

Asserting a weak argument without flagging it erodes the lawyer's credibility with the tribunal and creates a candor problem (MR 3.1 — a lawyer must have a basis in law and fact). The draft should make the lawyer smarter, not confident about a bad position.

## Citation extraction coverage

When this draft is cite-checked — by you, by another skill, or by a reviewer running through what you produced — the check must be exhaustive, not selective:

1. **First pass: extract.** Read the whole document and build a list of every citation — cases, statutes, regulations, record cites, secondary authority. Report the count: "Found [N] citations."
2. **Second pass: check.** Check each one against the source. Don't sample. Don't stop when you get tired.
3. **Report coverage.** At the end: "Checked [N] of [M] citations. [K] could not be retrieved — verify manually. [J] confirmed. [I] flagged as potential miscitations. [H] flagged as misgrounded (cite exists but doesn't support the proposition)."
4. **When source text is unavailable, say "could not check," never "confirmed."** A false positive ("this cite is fine" when you couldn't read the source) is worse than "couldn't check this one."
5. **The hardest errors to catch are partial support.** A cite that backs part of a claim but not all of it. Read the proposition the brief makes, read what the source actually holds, and compare element by element.

## Echo vs repeat

Echo key framings; don't lift sentences. Consistency with prior submissions is good — it reinforces your theory of the case and makes the record coherent. But there's a line between echoing and repeating.

- **Echo:** use the same key terms, the same framing of the central issue, the same characterization of the other side's theory.
- **Don't:** lift whole sentences, re-use distinctive phrasings so often the tribunal notices, or repeat the same argument verbatim without advancing it.

A rebuttal that sounds like a re-read of the opening loses ground. The draft should advance the argument, not restate it.

## Load context

`~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → case theory, house style (citation format, structure, tone, length norms).

**Conflicts gate — unbypassable.** Before drafting, check `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` for the matter slug this skill is being invoked on. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace is set up. I won't draft substantive work product on a matter that hasn't been intaken — the conflicts check is the gate."

Do not proceed on an unintaken matter. Intake is what runs conflicts, sets up `matter.md` / `history.md`, and writes the `_log.yaml` row this skill reads from. Skipping it produces work in an unmanaged location and bypasses the firm's conflicts discipline.

## Workflow

### Step 1: Which section?

| Section | What it does | Inputs needed |
|---|---|---|
| Statement of facts | Tells the story, in our frame, cited to record | Chronology, key docs, depo cites |
| Standard of review | Sets the bar the court applies | Procedural posture |
| Argument | Makes the legal case | Issue, authorities, facts |
| Conclusion | Asks for relief | What we want |

### Step 2: Theory check

Before writing: what does this section need to accomplish for the theory?

- Statement of facts: Frame the story so our theory is the natural reading.
- Argument: Connect the law to the facts in a way that supports the theory.

If the section you're about to draft contradicts the theory — stop. Either the theory is wrong or the section approach is wrong. Flag it, don't paper over it.

### Step 3: Draft in house style

**Research the forum's local rules and the judge's standing orders for length, formatting, citation, and filing requirements; don't rely on preferences. Cite primary sources (local rule number, standing order section) in the drafting notes. Verify currency — local rules change.**

Per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`:

- **Citation format:** Bluebook, ALWD, or local — match exactly. Signals, pincites, parentheticals per house practice, confirmed against the local rule.
- **Structure:** How does this firm organize arguments? CRAC? Topic sentences first? Headings that argue vs. headings that describe?
- **Tone:** Aggressive ("Defendants' argument is meritless") or measured ("The evidence does not support Defendants' position")? Match the seed brief.
- **Length:** per the local rule / standing order — never relying on "what this judge usually wants" when the rule is checkable.

### Step 4: Cite everything

Every fact → record cite (Bates, depo page:line, exhibit).
Every legal proposition → case cite with pincite.

**Marker discipline — use liberally:**
- `[VERIFY: specific factual assertion]` — anything not confirmed against the record
- `[UNCERTAIN: specific legal proposition]` — anything not confirmed against current authority
- `[CITE NEEDED: specific cite — fact/rule believed but cite not yet pinned]`

A draft with unresolved markers is not final. The markers make the verification step explicit.

**No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or firm platform) returns few or no results for an authority the draft needs, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [issue / holding]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) leave the `[CITE NEEDED]` marker and stop here. Which would you like?" A partner decides whether to accept lower-confidence sources; the skill does not decide for them.

**Source attribution.** Tag every citation in the draft with where it came from: `[Westlaw]`, `[CourtListener]`, `[Trellis]`, `[Descrybe]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the partner or senior associate supplied. Citations tagged `verify` carry higher fabrication risk than tool-retrieved citations and should be checked first. Never strip or collapse the tags — they are the reviewing attorney's fastest signal about which citations to Shepardize first before the brief is filed.

### Step 5: Output

**Before the brief is filed (the consequential act — this skill drafts, but the gate runs at the filing step regardless of who triggers it):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Filing a brief has legal consequences — it becomes the record, binds the client on arguments and facts asserted, and a Rule 11 / equivalent certification attaches to signature. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the section drafted, the theory tie-in, authorities relied on, open `[VERIFY]` / `[UNCERTAIN]` / `[CITE NEEDED]` markers unresolved, what could go wrong (factual misstatement, unsupported citation, argument outside the theory), what to ask the attorney before filing.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not treat the draft as filing-ready without an explicit yes. Drafting itself does not require the gate — filing does.

The section, in house style, with markers inline.

Preface (not in the brief — a note to the reviewing attorney):

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Drafting Notes — [Section] — [date]

**Theory tie-in:** [How this section supports the case theory]
**Authorities relied on:** [list — all need Shepardizing]
**Record cites to verify:** [N] flagged inline
**Open questions for the partner:** [anything the draft assumes that should be confirmed]
**Length:** [words/pages vs. house norm]

---

**Cite check before filing.** Citations in this draft were generated by an AI model and have not been verified against a primary source. Run every case, statute, and regulation through Westlaw, CourtListener, or your firm's research platform for accuracy, good-law status, and subsequent history. Fabricated or misquoted citations in filed briefs have resulted in Rule 11 sanctions.

**Draft only — not a filing.** Filing this section initiates (or participates in) a proceeding and carries Rule 11 / Rule 3.3 exposure. A licensed attorney reviews, edits, and takes professional responsibility before it goes on the docket. Do not file unreviewed.
```

## Statement of facts specifics

The statement of facts is advocacy through selection and sequence, not argument.

- Chronological unless there's a reason not to be
- **Every fact in the statement of facts must cite to the record — a page and line reference, a docket entry, an exhibit.** "Or conceded" is not a substitute for a record cite. If the fact is established by a concession or stipulation, cite the stipulation document or the hearing transcript where the concession was made.
- Frame through selection: which facts lead, which get one line, which get omitted (if not necessary and not helpful)
- No argument. "The contract unambiguously required X" is argument. "The contract stated 'X.'" is fact.

## Argument section specifics

- Lead with the rule, not the facts (usually — house style may differ)
- One argument per section. If it's really two arguments, it's two sections.
- Address the other side's best counterargument. Don't hide from it — a brief that ignores the obvious counter is a brief the judge doesn't trust.
- Parentheticals earn their space. If a parenthetical doesn't add something the cite alone doesn't, cut it.

## What this skill does not do

- Produce a final brief. It produces a draft. Every cite needs verification, every argument needs a partner's eyes.
- Decide strategy. If there are two ways to argue the issue, flag both and let the partner choose.
- File anything. Ever.

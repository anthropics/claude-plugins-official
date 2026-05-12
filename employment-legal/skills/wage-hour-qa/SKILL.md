---
name: wage-hour-qa
description: >
  Jurisdiction-aware wage/hour and employment Q&A — classification, overtime,
  meal/rest breaks, leave, final pay — answered for the specific state/country
  with the controlling rule researched and cited rather than stated from
  memory. Use when the user asks any employment law question, or says "what's
  the rule in [state]", "is this exempt", "do we have to pay overtime for",
  or "can we classify this as".
argument-hint: "[question]"
---

# /wage-hour-qa

1. Load `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint.
2. Use the workflow below.
3. Identify jurisdiction the question is about. If not specified, ask.
4. Answer per that jurisdiction's rule. Cite. Flag if it's a close call or law is shifting.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/employment-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/employment-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

"It depends" is true but unhelpful. This skill produces a jurisdiction-specific
answer grounded in researched, cited primary sources — and flags when the
question is close enough to need human judgment. It does not state rules from
memory: wage-and-hour thresholds, exemption criteria, and final-pay timing
change frequently and vary meaningfully by state.

## Load context

`~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint. If the question doesn't specify a
jurisdiction, ask — or answer for the state with the most employees and note
that.

## The answer

### Step 1: Jurisdiction

Which state/country is this about? If not stated:
- If it's about a specific employee: where do they work?
- If it's a policy question: identify the jurisdictions in the footprint that
  are most likely to be the most restrictive on the question at hand, then
  research those.

### Step 2: Research the rule, then state it

> **Research before answering.** For the jurisdiction and question, identify
> the currently operative rule. Cite the controlling primary source (statute,
> regulation, wage order, or case) with a pinpoint cite. Note the effective
> date and whether the rule has been recently amended, indexed, or is in
> litigation. If you are uncertain or cannot verify the current state of the
> law, say so and flag for attorney verification — do not state a rule you
> haven't confirmed.

State the rule in one paragraph, tied to the cite. Use your tools (web search,
legal research integrations, team reference materials) to verify currency —
especially for:

> **No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, or firm platform) returns few or no results for the jurisdiction-and-question, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [jurisdiction / question]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag the question as unverified and stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Tag every citation in the answer with where it came from: `[Westlaw]`, `[CourtListener]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the user supplied. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.


- Salary thresholds for any exemption (federal and state — several states
  index annually and several have tiered thresholds by employer size).
- Final-pay timing on termination vs. resignation (many states differ).
- PTO payout requirements (jurisdiction-specific; some require, some leave
  it to policy, some depend on accrual-plan design).
- Meal and rest break rules and any penalty-pay consequence.
- Daily or weekly overtime rules (some states have daily overtime and
  double-time rules that federal law does not).
- Classification tests — see the worker-classification skill; the applicable
  test depends on jurisdiction and purpose.

Common question types you may be asked — for each, the answer is
jurisdiction-specific and time-sensitive. Do not state the rule here; route
to research:

- "Is this role exempt?" — Research the applicable federal and state salary
  thresholds (verify current amounts and any employer-size tiers) and the
  applicable duties test(s).
- "Do we have to pay overtime for X?" — Research federal FLSA overtime plus
  any state-specific overtime rules (daily OT, double-time, alternative
  workweeks).
- "Do we have to provide meal/rest breaks?" — Research the applicable
  state rule and any penalty-pay consequence for missed breaks.
- "When is final pay due?" — Research the applicable state rule, including
  whether timing differs for termination vs. resignation and whether
  waiting-time or late-pay penalties apply.
- "Do we have to pay out accrued PTO?" — Research the applicable state rule
  and any carve-out for accrual-cap or use-it-or-lose-it policies.
- "Can we classify this person as a contractor?" — Route to
  `/employment-legal:worker-classification` if the facts are not already clear.

### Step 2a: FLSA regular-rate and back-pay calculations

When the question is a back-pay computation, unpaid-OT computation, or any
question that turns on the FLSA "regular rate," use this scaffold. Do not
answer from bare hourly wage × OT hours; that's the two most common errors
this skill exists to catch.

**The regular rate is NOT just the hourly wage.** Under 29 U.S.C. §207(e),
the regular rate is **all remuneration** for employment EXCEPT the eight
statutory exclusions in §207(e)(1)–(8) (e.g., discretionary bonuses, gifts,
premium pay, expense reimbursements, profit-sharing plans meeting the DOL
regs, stock options meeting §207(e)(8), retirement/insurance contributions).
Anything NOT within those eight exclusions is IN.

1. **Non-discretionary bonuses are IN the regular rate.** Productivity
   bonuses, attendance bonuses, commissions, shift differentials, contest
   awards, and most "bonuses" a reasonable employee would expect as a matter
   of course are non-discretionary under §207(e)(3) and 29 C.F.R. §778.211.
   Divide the bonus by the total hours worked in the bonus period to get
   the per-hour increase to the regular rate. True discretionary bonuses
   (§207(e)(3)) require both the fact of payment AND the amount to be
   within the employer's sole discretion, determined at or near the end of
   the period — narrow category.
2. **The unpaid OT premium is 0.5×, not 1.5× — when straight time was
   already paid for all hours.** If the employee was paid straight time for
   every hour (including the OT hours) but no premium, they are owed the
   **half-time premium** on OT hours, not time-and-a-half: `unpaid OT =
   0.5 × regular rate × OT hours`. 29 C.F.R. §778.110(b). If the employee
   was NOT paid for the OT hours at all, the owed amount is 1.5× the
   regular rate on those hours. **State which pay posture you're assuming
   before you compute** — it determines 0.5× vs. 1.5× and is the most
   common error in this computation.
3. **Show your math.** Print the formula and the inputs explicitly:
   ```
   Regular rate    = (straight-time wages + non-discretionary bonuses + other non-excluded comp) ÷ total hours worked
   OT premium owed = 0.5 × regular rate × OT hours    [if straight time already paid for OT hours]
                   = 1.5 × regular rate × OT hours    [if OT hours were unpaid]
   ```
   A number without the formula is not usable by a wage-and-hour lawyer.
4. **Liquidated damages double the back-pay.** 29 U.S.C. §216(b). Liquidated
   damages equal the unpaid back-pay amount unless the employer proves, to
   the court's satisfaction, that the violation was in good faith and based
   on reasonable grounds to believe it was not a violation. 29 U.S.C.
   §260. Default assumption is liquidated damages apply; the employer bears
   the burden to avoid them.
5. **Statute of limitations is 2 years; 3 for willful.** 29 U.S.C. §255(a).
   State the lookback explicitly and compute both bookends unless the
   willfulness posture is already established by the user.
6. **State overlay.** Many states have longer lookback, higher overtime
   multipliers (daily OT, double-time), and different regular-rate rules.
   Check state wage-and-hour law against the jurisdiction gate from Step 1
   and flag where state law compounds (higher cap) or replaces (different
   rate) federal. California, New York, Massachusetts, and Washington are
   the most frequent overlay hits.
7. **Attach the verify tag to the number.** Any back-pay amount produced by
   this skill carries `[verify — consult wage-and-hour counsel before
   asserting or paying]` on the line the number appears. The computation is
   specialist work; the skill is scaffolding, not opinion.

If the question is a back-pay calculation and any of these inputs are
missing (bonus breakdown, whether straight time was paid for OT hours,
willfulness posture, state jurisdiction), **ask before computing**. A
confident wrong number is the worst output this skill can produce.

### Step 3: The flag

Is this a close call? Be honest.

- If the answer is clear on the researched rule: say so. "Exempt — meets
  each element of the applicable duties test and the current salary
  threshold."
- If it's close: say so. "The duties test is borderline — this role could
  go either way. Recommend classifying as non-exempt to be safe, or getting
  a formal opinion."
- If the law is in flux: say so. "This rule has been amended recently — the
  current version takes effect [date]. Confirm effective date before relying
  on this answer."
- If you could not verify currency: say so. Do not guess.

## Output format

Conversational. This is a Q&A, not a memo.

> **Research-connector pre-flight.** Before emitting the answer, check whether a legal research connector is reachable for this session — Westlaw, CourtListener, or any firm-configured research MCP. Collect this into the reviewer note per CLAUDE.md `## Outputs`: if no connector returns results in Step 2 (or none is configured at run time), record it in the **Sources:** line of the reviewer note — e.g., `not connected — cites from training knowledge; pinpoint cites (volume/page/subsection) carry the highest fabrication risk, spot-check those first`. Per-citation `[model knowledge — verify]` tags remain inline. Do not emit a standalone banner above the output.

> **Jurisdiction assumption.** Answers apply only to the jurisdiction identified. Wage-hour rules, exemption thresholds, and final-pay timing vary materially by state and country, and many rules index or change year over year. If the employee works in another jurisdiction, or the question is answered for the default-footprint state, this answer may not apply as written.

```
**[Jurisdiction]:** [The researched rule, one paragraph, with pinpoint cite
and currency note.]

[If close call or shifting law: the flag.]

[If the answer differs in other footprint jurisdictions: one line noting that,
and whether the differences are material.]
```

> **Verify citations.** Any case, statute, regulation, or wage-order cite above was generated with AI assistance. Before relying on a cite, check it against Westlaw, CourtListener, the relevant state agency's site, or your firm's research tool for accuracy, currency, and subsequent history. Fabricated or misquoted citations in filings or formal advice have resulted in sanctions.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- State the rule from memory — every answer is grounded in a researched,
  cited primary source verified for currency.
- Make classification decisions for borderline cases. It states the rule and
  flags the close call. Human decides.
- Give a 50-state survey unless asked. Answers for the relevant
  jurisdiction(s).
- Track when the answer changes. If thresholds index or law shifts, the
  answer goes stale. Re-ask for current.

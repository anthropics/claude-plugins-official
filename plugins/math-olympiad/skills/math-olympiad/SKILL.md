---
name: math-olympiad
description:
  "Solve competition math problems (IMO, Putnam, USAMO, AIME) with adversarial
  verification that catches the errors self-verification misses. Activates when
  asked to 'solve this IMO problem', 'prove this olympiad inequality', 'verify
  this competition proof', 'find a counterexample', 'is this proof correct', or
  for any problem with 'IMO', 'Putnam', 'USAMO', 'olympiad', or 'competition
  math' in it. Uses pure reasoning (no tools) — then a fresh-context adversarial
  verifier attacks the proof using specific failure patterns, not generic 'check
  logic'. Outputs calibrated confidence — will say 'no confident solution'
  rather than bluff. If LaTeX is available, produces a clean PDF after
  verification passes."
version: 0.1.0
---

# Math Olympiad Solver

## The five things that change outcomes

1. **Strip thinking before verifying** — a verifier that sees the reasoning is
   biased toward agreement. Fresh context, cleaned proof only.
2. **"Does this prove RH?"** — if your theorem's specialization to ζ is a famous
   open problem, you have a gap. Most reliable red flag.
3. **Short proof → extract the general lemma** — try 2×2 counterexamples. If
   general form is false, find what's special about THIS instance.
4. **Same gap twice → step back** — the case split may be obscuring a unified
   argument. Three lines sometimes does what twelve pages couldn't.
5. **Say "no confident solution"** — wrong-and-confident is worse than honest
   abstain.

---

**Tool policy**: Solvers and verifiers use THINKING ONLY in the tight-budget
workflow. Competition math is reasoning. Computation is for deep mode (§6c), and
even then bounded — a recurrence that's doubly-exponential can't be computed
past n~30, work mod 2^m instead.

---

## When to use which approach

| Problem                                              | Approach                                                                       | Verification              |
| ---------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------- |
| AIME numeric answer                                  | Best-of-N → majority vote                                                      | Answer check only         |
| Olympiad proof (IMO/Putnam/USAMO)                    | Full workflow below                                                            | 5-pass adversarial        |
| "Is this proof correct?"                             | Skip to verification (step 4)                                                  | Adversarial + spec-gaming |
| **Full problem set** (e.g. all 6 from a competition) | Sequential: one full workflow per problem, collect results, compile single PDF | Per-problem adversarial   |

**Batch in one Workflow**: Set `opts.label` on every `agent()` call to include
the problem ID (e.g., `label: "P3:solver:2"`). Without labels, 36 results come
back with no problem association. Run problems in parallel — the label is what
matters, not ordering.

### For a full problem set

Launch one solver workflow per problem (same VERBATIM prompt, different
statement). Run them in parallel. When all return, run adversarial verification
per problem. Problems that pass get their proof in the PDF; problems that
abstain get "No confident solution" with partial notes.

Don't try to solve all N problems in one agent's context — each problem needs
its own thinking budget and its own fresh-context verifier. The composition is
mechanical: collect the per-problem outputs, fill in LaTeX sections, compile
once. | "Simplify this proof" | Skip to presentation (step 8) | — |

---

## The Workflow

### 1. Interpretation check (30 seconds, catches 50/63 of one class of errors)

Before solving anything, identify the interpretation.

> Read the problem statement. List 2-3 ways it could be interpreted. For each:
> is this reading TRIVIAL? If one reading makes the problem easy and another
> makes it hard, the hard one is almost certainly intended. State which
> interpretation you're solving and WHY you believe it's the intended one.

The Aletheia case study found 50 of 63 "technically correct" solutions were for
the wrong interpretation. Olympiad problems often have a trap easy reading.

### 2. Generate candidates with internal refinement (parallel, thinking only)

Launch 8-12 attempt agents in parallel. **Each agent internally iterates** —
solve → self-improve → self-verify → correct → repeat. This is the Yang-Huang
structure that achieves 85.7% on IMO: one-shot solving isn't enough; per-attempt
refinement matters.

**The Agent tool cannot enforce tool restriction.** Subagents get the full tool
set. The only mechanism is the prompt. Use this prompt VERBATIM — do not
summarize, do not synthesize your own:

```
NO COMPUTATION. Do not use Bash, Python, WebSearch, Read, Write, or any tool that runs code or fetches data. Numerical verification is not a proof step. "I computed n=1..10 and the pattern holds" is not a proof.

(If your agent harness requires a StructuredOutput or similar return-mechanism tool call, that is NOT a computation tool — call it to return your answer. The restriction is on tools that DO work, not tools that REPORT work.)

Your internal process (iterate until done):
- Solve: Complete rigorous solution.
- Self-improve: Reread. Fix gaps before a grader sees it.
- Self-verify: Strict grader mode. Every step justified?
- Correct: Fix and re-verify. Up to 5 rounds.
- Stop: Self-verify passes twice clean, OR 5 rounds, OR approach fundamentally wrong.

A correct answer from flawed reasoning is a failure. If incomplete, say so honestly. Never hide gaps.

PROBLEM: <insert the problem statement here>
ANGLE: <insert one starting angle here>
```

The first two paragraphs are load-bearing. A session that writes its own prompt
and omits them will produce subagents that grind Python for 30 iterations and
confidently get wrong answers — a pattern that fits n≤10 but fails at n=100 is
not a proof.

Starting angles (vary across agents — see `references/solver_heuristics.md`):

- Work out small cases (test past n=3)
- Look for an invariant or monovariant
- Consider the extremal case
- Try induction
- What symmetries?
- Work backwards
- Drop a condition — where does it become trivially false?
- Generalize (inventor's paradox — more structure is sometimes easier)

Each returns its FINAL state (not intermediate rounds):

```
**Verdict**: complete solution | partial result | no progress
**Rounds**: [how many verify→correct cycles]
**Method**: [key idea, one paragraph]
**Detailed Solution**: [full step-by-step, every step justified]
**Answer**: [if applicable]
**Self-verification notes**: [what you caught and fixed; remaining concerns]
```

**Retry policy**: If an agent fails or times out, retry once. Transient failures
happen.

### 3. Clean the solution (context isolation — the #1 lever)

The thinking trace biases the verifier toward agreement — a long chain of
reasoning reads as supporting evidence even when the conclusion is wrong. Before
any verification, strip:

- All thinking-block content
- All "Let me try..." / "Actually wait..." / "Hmm" prose
- All false starts and backtracking

What remains: problem statement + clean final argument only.

Extract only the **Method** + **Proof** + **Answer** sections from each solver's
output. The verifier never sees how the solver got there.

### 4. Adversarial verify (fresh context, pattern-armed)

For each cleaned solution, launch a fresh verifier agent. **Fresh context**: it
sees only (problem statement + cleaned solution). **No tools.**

The verifier's job is to ATTACK, not grade. Load
`references/adversarial_prompts.md` for the prompts. The key patterns it runs:

| Pattern | The check                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **#4**  | Does this theorem specialize to a famous object (ζ, quadratic reciprocity, etc.) and prove something open about it? → gap                                          |
| **#18** | Substitute the proof's own intermediate identities into any "remaining gap." Recover the original claim? → tautological                                            |
| **#40** | Is any step a "one-line lemma"? Extract the GENERAL form. Find a 2×2 counterexample. If the general form is false, find what special structure saves THIS instance |
| **#5**  | For each invoked theorem: re-check hypotheses FROM SCRATCH. "Continuous on [0,1]" ≠ "continuous on ℝ"                                                              |
| **#6**  | Any infinite sum "bounded" via a regularized value? Check the boundary — if there's a pole there, the sum diverges                                                 |

Full pattern list: `references/verifier_patterns.md`

Verifier returns:

```
**Verdict**: HOLDS | HOLE FOUND | UNCLEAR

**If HOLE FOUND**:
- Location: [quote the problematic step]
- Pattern: [which check fired, or "other"]
- Why it breaks: [specific]
- Fixable?: [yes with X / no, fundamental]
```

### 5. Rank and vote-verify (asymmetric + early exit)

Rank solutions by (verdict, verifier confidence). Take the top one. Run up to 5
fresh verifier agents.

**Asymmetric thresholds**: 4 HOLDS to confirm, 2 HOLE FOUND to refute. Why
asymmetric: one flaky verifier shouldn't kill a correct proof; but two
independent dissents is a real signal.

**Pigeonhole early exit**: stop launching verifiers once the outcome is decided.

- 2 say HOLE FOUND → refuted, stop (save the remaining 3 calls)
- 4 say HOLDS → confirmed, stop (save the 5th)
- After 3 verifiers: if 2 HOLDS + 1 HOLE, launch 2 more (outcome undecided). If
  3 HOLDS + 0 HOLE, launch 1 more (could still hit 4-1).

**Dual context-isolation**: each verifier is blind to (a) the solver's thinking
trace — already stripped in step 3 — AND (b) other verifiers' verdicts. Each
verifier thinks it's the first. No "3 agents already confirmed this" social
proof.

**A solver cannot verify its own solution.** Different agent, fresh context.

### 5b. When one case won't close — step back before grinding

If a proof splits into cases and one case proves easily but the other resists:
**before grinding through the hard case, ask whether there's a route that makes
the split disappear.**

The pattern that saves you: the hard case's very hypothesis often implies
something strong about an _intermediate object_ you haven't looked at. Use that
implication directly instead of the original chain.

Concrete shape: proving f(n) ≤ cn for a constrained function f, with a case
split on a prime p dividing f(n). One branch closes by index arguments in
(ℤ/p^e)\*. The other branch resists — same group structure, but the arithmetic
doesn't contradict. The fix: the hypothesis "p | f(n)" plugged back into the
governing equation implies **f(p) = p itself**. Once you have that, a
Fermat+Dirichlet argument kills both branches in three lines. The case split was
a detour — it was splitting on a variable that, under the hypothesis, takes a
known value.

Check when stuck on case B:

- What does case B's hypothesis imply about f at _other_ inputs?
- Is there a different pair (a,b) to plug into the governing equation?
- Are you proving too much? (A cleaner contradiction needs less machinery.)

This is also a presentation-pass win: the split-free proof is shorter AND more
general.

### 6. Revise (if needed)

If verification finds a hole: launch a reviser agent. It gets (cleaned
solution + verifier's hole report). STILL no access to the original thinking —
the reviser works from the hole, not by rereading how you got there.

```
A verifier found this issue in the proof:
[hole report]

Fix the proof. If the hole is fundamental (the approach doesn't work), say so and return **Verdict: no confident solution** with what partial progress remains.

For any step you cannot fully close, mark it inline: [GAP: specific description of what remains]. Gaps in the proof text, not in a separate list — they're greppable and the next reviser knows exactly where to look.
```

Up to 3 revise cycles. Then re-run the vote on the revised proof.

**If pattern #40 fired** (one-line-proof-too-clean), the reviser gets a stronger
brief — the Adversarial Brief template from `references/adversarial_prompts.md`
§7. It forces a binary: "the general lemma is obviously false (here's a 2×2
counterexample) — so either find what's special about THIS case, or find where
the proof breaks." Can't return "looks fine."

### 6c. Deep mode (when tight-budget abstains)

The standard workflow is tight-budget: 8 solvers, ~15 min, pure reasoning. When
it abstains, the problem may need more time, not more capability.

**Deep mode** is a single focused agent with:

- **Unlimited time** — no wall-clock pressure
- **Targeted computation allowed** — modular arithmetic checks, small-case
  enumeration, symbolic verification of identities. NOT exploratory brute force
  or unbounded recursion.
- **The abstention reason as starting point** — if verifiers found a specific
  gap, start there. If solvers never claimed complete, start from what they
  partially proved.

The archetype: a focused agent that gets the proven-so-far state plus "one case
of Lemma 5 is open" — and finds a 3-line argument the case split was obscuring.
Often under 10 minutes with almost no computation. Deep mode is about giving the
problem sustained attention, not throwing compute at it.

**What deep mode is NOT**: open-ended exploration, literature search, looking up
solutions, multi-day investigation. That's a different workflow
(`math-research`). Deep mode is still "solve THIS problem yourself" — just
without the clock.

**NO WEB. NO LOOKUP.** Deep mode may use Bash/Python for bounded computation,
but NEVER WebFetch, WebSearch, or any network access. Finding the solution on
AoPS or a blog is not solving the problem — it's cheating on an olympiad, and it
teaches us nothing about the skill's actual capability. Put this at the TOP of
the deep-mode prompt:

```
NO WEB ACCESS. Do not use WebFetch, WebSearch, or any tool that touches the internet. Do not look up this problem, its solution, or related problems. You are solving this yourself — the only allowed computation is local (Bash/Python for mod-k arithmetic, small-case enumeration n≤10, symbolic identity checks). If you invoke a web tool, the proof is void.
```

**Computation bounds in deep mode** (bug #8 lesson): A6's b\_{n+1}=2b_n²+b_n+1
is doubly-exponential; b_99 has ~10^{2^98} digits. Never compute such objects
exactly — work in ℤ/2^m, or track only v_p(·), or prove the recursion mod the
quantity you care about. If a computation is running longer than 60 seconds,
it's probably unbounded. Kill it and work symbolically.

**Step 6d (not optional)**: After any ABSTAIN at the verify stage, automatically
launch one deep-mode agent before writing the abstention into the output. Give
it:

- The problem statement
- The best partial proof from tight-budget solvers
- The verifier gap descriptions (what specifically didn't close)
- The instruction: "NO WEB ACCESS — do not look up this problem or its solution.
  Bounded local computation allowed (mod 2^k, small cases n≤10, symbolic
  identity checks via Bash/Python only). 60-second computation limit. If n≤10
  brute force reveals a pattern the tight-budget solvers missed, that pattern IS
  the proof structure."

The deep agent may find the construction the pure-reasoning solvers couldn't
see. If it also abstains, THEN write the abstention. Do not skip this step —
problems with √n or log n answers are often invisible to pure reasoning because
the optimal structure is the asymmetric one.

**Orchestrator self-restraint**: The orchestrator itself must not web-search the
problem "to help" the deep agent. If you're tempted to Fetch an AoPS thread
"just to check the answer," don't — that contaminates the skill's output and
misrepresents its capability.

### 7. Calibrated abstention

If 3 revise cycles all fail: **stop and admit it.**

```
**Verdict**: no confident solution

**What was tried**: [approaches]
**What WAS proven**: [any lemma or partial result that survived verification]
**Where it breaks**: [the unfixed hole]
```

Do NOT guess. A wrong confident answer is worse than an honest "couldn't solve
it." The metric that matters is CONDITIONAL accuracy — when you say "solved,"
are you right?

### 8. Presentation pass (after correctness is established)

A VERIFIED-CORRECT proof is often not a BEAUTIFUL proof. The order you
discovered it is rarely the best order to present it. Launch a fresh
presentation agent with the verified proof.

Load `references/presentation_prompts.md`. The agent asks:

- What's the simplest way to say this?
- Which lemmas should be inlined? Which deserve to stand alone?
- Is anything OVERKILL? (constructing a double exponential when linear suffices)
- Now that we know the answer, is there a 3-line hindsight proof?

Output: LaTeX-formatted proof. If `pdflatex` is available
(`scripts/check_latex.sh` returns 0), also compile to PDF via
`scripts/compile_pdf.sh`.

---

## Model tier defaults

Read `references/model_tier_defaults.md` for full details. Summary:

| Model  | Solvers | Verify passes          | Abstain after  | Presentation           |
| ------ | ------- | ---------------------- | -------------- | ---------------------- |
| Haiku  | 8       | 3                      | 2 revise fails | skip                   |
| Sonnet | 4       | 5                      | 3 revise fails | yes                    |
| Opus   | 3       | 5 + full pattern sweep | 4 revise fails | 2 drafts, pick cleaner |

Weaker models: more parallel attempts, faster abstention. Stronger models:
deeper verification, more presentation effort.

---

## For numeric-answer problems (AIME-style)

Skip the proof machinery. Run 5-7 solvers with varied approaches, take majority
vote on the numeric answer. If no majority: verify the top 2 candidates by
substitution.

---

## Key references

- `references/verifier_patterns.md` — the 12 adversarial checks
- `references/adversarial_prompts.md` — ready-to-use verifier prompts
- `references/presentation_prompts.md` — beautification prompts + LaTeX template
- `references/model_tier_defaults.md` — per-model configuration

---

## What makes this different from generic verify-and-refine

1. **Dual context isolation**: verifier is blind to (a) the solver's thinking
   trace — which biases toward agreement — and (b) other verifiers' verdicts —
   social proof also biases. Each verifier thinks it's first.
2. **Pattern-specific attacks**: not "is this correct?" but "does this make the
   #40 mistake? the #4 mistake?" Specific beats generic. The 7-category
   refutation taxonomy gives the verifier a checklist.
3. **Asymmetric vote + pigeonhole exit**: 4-to-confirm, 2-to-refute. One flaky
   verifier doesn't kill a correct proof; two dissents does. Stop launching
   verifiers once the outcome is decided — saves ~30% of verification cost on
   clear cases.
4. **Specification-gaming check first**: explicitly asks "is this the intended
   interpretation?" before solving. The #1 failure mode in prior work (50/63
   "correct" answers solved the wrong reading).
5. **Calibrated abstention**: will say "no confident solution" with partial
   results. Optimizes conditional accuracy, not coverage.
6. **Presentation pass**: correctness and elegance are separate steps. The
   presentation agent gets the VERIFIED proof and finds the cleanest way to say
   it.

# Model Tier Defaults

Parameters scale with model capability. Budget is not the constraint — the
constraints are diminishing returns (more voters stop helping past a point) and
the asymmetric noise floor (Haiku verifiers are individually less reliable, so
the right response is width not depth).

## Haiku

Width compensates for per-sample noise. Scaffolding is where the leverage is.

- **Parallel solvers**: 12 (wide fan — each individual solve is weaker, so cast
  a wider net)
- **Vote budget**: 7 verifiers, need 5-confirm / 3-refute (pigeonhole exit: stop
  when outcome decided)
- **Abstain threshold**: 3 consecutive revise cycles fail
- **Pattern sweep**: all 12 patterns — Haiku can follow a checklist, the
  patterns are the scaffold
- **Presentation pass**: yes, 3 drafts, comparator picks cleanest. Haiku's raw
  output is rougher, so this matters MORE not less.
- **Rationale**: The skill's value is highest where the base model is weakest.
  Give Haiku the full harness. The 3-refute threshold (higher than Sonnet's 2)
  accounts for Haiku verifiers being individually noisier — don't let 2 confused
  Haikus kill a correct proof.

## Sonnet

Balanced.

- **Parallel solvers**: 6
- **Vote budget**: 5 verifiers, need 4-confirm / 2-refute
- **Abstain threshold**: 3 consecutive revise cycles fail
- **Pattern sweep**: all 12
- **Presentation pass**: 2 drafts, comparator picks cleaner
- **Rationale**: 4-of-5 tolerates one flake. 2 dissents is signal.

## Opus

Depth. Each sample is strong, so invest in making the adversarial pass harder.

- **Parallel solvers**: 4
- **Vote budget**: 5 general verifiers (4-confirm / 2-refute) PLUS one dedicated
  verifier per pattern in `verifier_patterns.md` (12 targeted attacks). Any
  pattern-specific HOLE FOUND counts toward refute.
- **Abstain threshold**: 5 consecutive revise cycles fail (trust the model's
  ability to eventually fix)
- **Pattern sweep**: all 12, each with its own dedicated agent
- **Presentation pass**: 3 drafts with different instructions ("most elegant,"
  "most elementary," "shortest"), comparator picks the best. Strong models can
  genuinely produce different _styles_ of proof.
- **Rationale**: Opus can execute the deep patterns (#19 base-vs-derived, #22
  mean-first) that need real mathematical judgment. The 12 dedicated pattern
  passes are where the model's capability is best spent — it's the difference
  between "be skeptical" and "check THIS specific thing."

## On the pigeonhole exit

Kept at all tiers — not because of cost, but because once
`inflight >= confirm_needed + refute_needed - 1`, the remaining votes carry no
information regardless of how they land. Launching them anyway is pure latency.

## Identifying the tier

If the orchestrating session doesn't know which model it is, default to Sonnet
configuration. A reasonable heuristic: ask the model to self-identify in its
first response and match against `haiku`/`sonnet`/`opus` in the output.

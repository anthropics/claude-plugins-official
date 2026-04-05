# math-olympiad

Competition math solver with adversarial verification.

## The problem

Self-verification gets fooled. A verifier that sees the reasoning is biased
toward agreement. arXiv:2503.21934 ("Proof or Bluff") showed 85.7% self-verified
IMO success drops to <5% under human grading.

## The approach

- **Context-isolated verification**: verifier sees only the clean proof, never
  the reasoning trace
- **Pattern-armed adversarial checks**: not "is this correct?" but "does this
  accidentally prove RH?" / "extract the general lemma, find a 2×2
  counterexample"
- **Calibrated abstention**: says "no confident solution" rather than bluff
- **Presentation pass**: produces clean LaTeX/PDF after verification passes

## Validation

17/18 IMO+Putnam 2025 problems solved, 0 false positives, 2 novel proofs found.
See the skill's eval data in the
[anthropic monorepo](https://github.com/anthropics/anthropic/tree/staging/sandbox/sandbox/ralph/math_skills/eval_harness).

## Install

```
/plugin install math-olympiad@claude-plugins-official
```

## Use

```
> Solve this IMO problem: [statement]
```

The skill auto-triggers on "IMO", "Putnam", "olympiad", "verify this proof",
etc.

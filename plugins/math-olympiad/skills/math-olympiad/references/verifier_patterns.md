# Verifier Patterns — Olympiad Subset

For a verifier with **no tools, only reasoning**. Each pattern is a mental check
you can run on a candidate proof. These are the specific ways proofs go wrong
that self-verification misses. (Source: 59 patterns from real research sessions;
these 13 need no grep/fetch/compute.)

Run #18 and #19 after any positive finding. Run #40 on any proof that feels too
short.

---

### Pattern 4: Would it prove a famous open problem?

**The check**: Specialize the claimed theorem to the most famous object in its
class (ζ(s), the Ramsey number, the Collatz map). Does the specialization settle
a known open problem?

**What it catches**: A bound "for all Dirichlet series with property P" that,
applied to ζ, would prove Lindelöf — the proof treated arithmetic input as
generic.

**How to run it**: Find the step where the argument uses a generic property.
Ask: does ζ (or the canonical hard instance) actually have this property? The
gap is always where it doesn't.

---

### Pattern 5: Outside the hypothesis class

**The check**: For each example claimed to satisfy a theorem, re-derive the
hypotheses from the definition — don't trust the label.

**What it catches**: "f is entire of order ≤1, so by Thm 3.1…" — but Thm 3.1
needs f analytic in a _full disk_ around 0; a natural boundary on the imaginary
axis blocks it.

**How to run it**: Write out the theorem's hypothesis verbatim. For each claimed
instance, check inclusion from scratch. Watch for near-synonyms ("bounded" vs
"bounded on the line"; "entire" vs "analytic on a domain").

---

### Pattern 6: Divergent sum behind analytic continuation

**The check**: When a divergent-looking sum is "bounded by ζ(s)" or similar,
evaluate the bounding function at the boundary of the claimed range.

**What it catches**: "Σ 1/n ≤ ζ(1)" — but ζ(1) is a pole. The analytic
continuation of a sum is not the sum.

**How to run it**: Mentally substitute the boundary value of the parameter into
the bounding expression. A pole or ∞ there means the original sum diverges,
regardless of what the continued function says elsewhere.

---

### Pattern 10: Same keywords, different theorem

**The check**: When a cited theorem has the right _words_ but the fit feels off
— check pointwise vs averaged, uniform vs a.e., finite vs asymptotic.

**What it catches**: Invoking "Fourier decay ⇒ bound" for a pointwise estimate,
when the cited decay theorem needs curvature and you only have it on average.

**How to run it**: State precisely what the proof _needs_ (pointwise? for all x?
with what uniformity?). State what the cited theorem _gives_. Sometimes the
weaker version is enough and this _closes_ a gap; sometimes the gap is real.

---

### Pattern 17: Test past the first nontrivial block

**The check**: Before accepting a pattern from small cases, identify where the
structure first becomes nontrivial. Confirm the pattern holds _past_ that
threshold.

**What it catches**: "Checked m = 1, 2, 3: all blocks have rank 1." But m ≤ 3
gives only 1×2 blocks — rank 1 is forced. First 2×2 appears at m = 4, and there
the claim fails.

**How to run it**: Ask "what makes the small cases easy?" Find the parameter
value where that degeneracy disappears. The claim must survive at least one case
beyond it.

---

### Pattern 18: Tautological reduction

**The check**: When a reduction chain ends at "estimate X would finish it,"
substitute the chain's own already-proven identities into X.

**What it catches**: "Suffices to show ∫|P|² ≤ C·H." But the chain itself proved
∫|P|² = H + 2Re(OD') _exactly_. So X is just the original conjecture plus a
cosmetic shift — not a reduction.

**How to run it**: Take each identity the chain proved along the way and plug it
into the "final gap." If you recover the starting conjecture (or something at
least as strong), the chain went in a circle.

---

### Pattern 19: Derived obstruction vs base obstruction

**The check**: When the same obstruction kills 3+ independent approaches,
compute the disputed property on the _original_ object — before any reduction.

**What it catches**: "det(Hessian) = 0, ruled surface, decoupling fails" — for
the phase log(2πm−θ). But the _base_ phase is nθ − t·log(n), and _its_ Hessian
has det = −1. The obstruction lived in the proxy.

**How to run it**: Name the object the obstruction is _about_. Is it the thing
you started with, or something a reduction produced? Go back to the start and
check directly.

---

### Pattern 22: Absolute-sum gives O(K); compute the mean first

**The check**: Before accepting that Σₖ Xₖ = O(1) is "too hard because |Xₖ|
summed gives O(K)," compute the mean of Xₖ over the varying parameter.

**What it catches**: Weyl equidistribution gives mean(Xₖ) = 0 _exactly_. So Σ Xₖ
is a fluctuation sum — the target is Var = O(1), and half the conjecture falls
in one line.

**How to run it**: Separate Xₖ into mean + fluctuation. If
orthogonality/equidistribution forces the mean to zero, you were never fighting
K terms of size 1 — you were fighting √K terms (or better). Rewrite the target.

---

### Pattern 23: Formula's scope never stated

**The check**: For any identity used in the proof, ask: was this proved for the
general case, or for a special case that the author silently generalized?

**What it catches**: "κ₄ = 3d − 1" was derived for 2-piece Cantor sets. The
proof applies it to an m-piece set, where the real formula involves additive
energy and can differ by a constant factor.

**How to run it**: Trace the identity to where it was first introduced. What
were the standing assumptions _there_? Check that those assumptions still hold
at the point of use.

---

### Pattern 35: Count quantifiers before diagonalizing

**The check**: Before "diagonalize against class C using property P," ask
whether _certifying_ P is an ∃-statement or a ∀-statement.

**What it catches**: "Find an x not computed by any small circuit" — but
verifying "no small circuit computes x" is a ∀ over circuits. Your diagonalizer
is in Σ₂, not NP. (This is _why_ Kannan gives Σ₂ᴾ ⊄ SIZE, not NP ⊄ SIZE.)

**How to run it**: Write the diagonalization as a formula. Count alternations.
If you need ∀∃ to describe the witness, you've jumped a level in the hierarchy.

---

### Pattern 40: One-line-proof-too-clean

**The check**: Extract the proof's key step as a lemma in _full generality_ —
not specialized to the objects at hand. Try a 2×2 counterexample to the general
lemma.

**What it catches**: "rank depends only on monomial support" — but [[1,1],[1,1]]
has rank 1 and [[1,1],[1,−1]] has rank 2 with the same support. The general
lemma is false; the specific case holds because sgn(π) = f(S)·g(T) factors.
_That's_ the real proof.

**How to run it**: If the general lemma dies but the specific conclusion
survives numerically, there's hidden structure. Find it. The real proof goes
through _that_, not the false lemma.

---

### Pattern 58: Quantifier direction on domain size

**The check**: Before claiming one statement is "strictly stronger" than another
because its domain is smaller — check whether the quantifier is ∀ or ∃.

**What it catches**: "∀ S ∈ D, φ(S)" over a _smaller_ D is _weaker_ (fewer
obligations). "∃ S ∈ D, φ(S)" over smaller D is _stronger_ (fewer candidates).
Backwards strength claims swap these.

**How to run it**: Say the statement out loud with the quantifier explicit.
Shrinking the domain under ∀ drops requirements. Shrinking under ∃ drops
witnesses. Only one direction is "harder."

---

### Pattern 60: Easiest-interpretation trap

**The check**: Before solving, write down 2–3 readings of the problem statement.
Flag whichever one makes the problem trivial.

**What it catches**: 63 "technically correct" solutions; only 13 "meaningfully
correct." The gap: solving the easiest grammatically-valid reading instead of
the intended one. Olympiad problems often _plant_ an easy misreading.

**How to run it**: Ask "under which reading is this a real problem?" If your
interpretation makes it a one-liner and the problem is worth 7 points, you've
probably chosen wrong. Solve the hard reading; note the easy one only as a
remark.

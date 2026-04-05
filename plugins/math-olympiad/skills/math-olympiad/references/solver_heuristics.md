# Solver Heuristics (Pólya + Olympiad Practice)

For solver subagents. These are the moves to try when the direct approach
stalls.

## Pólya's core moves (from "How to Solve It")

**Have you seen a related problem?** Not the same problem — one with the same
UNKNOWN, or the same STRUCTURE. A problem about covering points with lines has
the same shape as one about covering lattice points with arithmetic
progressions.

**Specialize.** If you can't solve the given problem, solve n=3, n=4, n=5 by
hand. The pattern is often the proof. (But: test past the first nontrivial case
— n≤3 may be degenerate.)

**Generalize (inventor's paradox).** The more ambitious problem sometimes has
MORE structure and is easier. "Prove for all primes" might be harder than "prove
for all integers" if the integer case has a clean induction.

**Drop a condition.** What happens if you relax one hypothesis? Does the result
become trivially false? Where? That WHERE is often the key step — the point
where the condition is load-bearing.

**Work backwards.** Start from what you want to prove. What would imply it? What
would imply THAT? If this chain meets something you can prove directly, you have
the proof (reversed).

**Auxiliary element.** Introduce something not in the problem — a new variable,
a reflection, a well-chosen function. Olympiad geometry lives on this (auxiliary
points, circles).

## Olympiad-specific moves

**Find the invariant.** If there's a process (game, transformation, iteration),
what quantity is preserved? Parity, sum, product modulo something.

**Find the extremal.** Take the LARGEST, or SMALLEST, or LEFTMOST object.
Extremal choices often have extra properties that generic choices don't.

**Double count.** Count the same thing two ways. Incidences, edges, sums over
pairs.

**Coloring / parity.** Can you 2-color the objects so the claim becomes a parity
statement?

**Smoothing / adjusting.** For inequalities: if you perturb two variables closer
together (or further apart), does the expression increase or decrease?
Extremize.

**Symmetry → WLOG.** If the problem is symmetric in x,y,z, you can assume x≤y≤z.
But only if the conclusion is ALSO symmetric.

## Geometry-specific moves

Standard angles (induction, invariants, extremal) are often wrong-shaped for
olympiad geometry. Use these instead:

**Coordinate bash.** Place the configuration in coordinates. Choose them to kill
degrees of freedom (origin at a center, axis along a line). Grind out the
algebra. Ugly but reliable.

**Auxiliary point.** Introduce a point not in the problem — a reflection, a
second intersection, the point where two lines "should" meet. Often the key
construction is finding the right extra point.

**Power of a point.** For any point P and circle ω, PA·PB is the same for every
line through P meeting ω at A, B. Use it to turn ratios into equalities.

**Spiral similarity / rotation.** Two directly similar triangles are related by
a spiral similarity (rotation + scaling about a fixed point). Find that point —
it often lies on a circle you already have.

**Inversion.** When there are many circles or tangencies, invert about a
well-chosen center. Circles through the center become lines; tangencies become
simpler tangencies.

**Angle chase.** Cyclic quadrilaterals give equal angles. Tangent-chord gives an
angle equal to the inscribed angle. Chase around the figure.

## Geometry-specific moves (these are DIFFERENT)

The standard angles (invariant, extremal, induction) don't fit
circles/circumcenters/orthocenters. Geometry needs:

**Coordinate bash.** Place one point at origin, another on the x-axis. Compute
everything explicitly. The algebra is heavy but mechanical. For two circles with
centers M, N and radii r, R: set M=(0,0), N=(d,0), then the intersection points
have x-coordinate (r²+d²−R²)/2d and everything follows.

**Auxiliary point.** Introduce a point not in the problem — the reflection, the
foot of a perpendicular, the second intersection. Olympiad geometry lives on
finding the right extra point.

**Power of a point.** For point P and circle Γ: PA·PB is constant for any line
through P meeting Γ at A,B. This converts circles to products.

**Inversion.** Circles through the center become lines. Sometimes the inverted
problem is trivial.

**Angle chasing / cyclic quads.** Four points are concyclic iff opposite angles
sum to π. Chase angles until enough equalities force concyclicity.

## Recurrence-specific trap

For recurrences like b\_{n+1} = P(b_n) where P is polynomial degree ≥ 2: **b_n
grows doubly-exponentially**. You cannot compute b_30 exactly — it has trillions
of digits. Work in ℤ/2^m (or ℤ/p^m) from the start. Prove b_n ≡ r_n (mod 2^m) by
induction on n, NOT by computing b_n.

## When the answer involves √n or log n

These answers often come from a structure that is NOT the obvious/symmetric one.
The diagonal, the identity, the "natural" choice frequently gives the WORST
case, not the best — it clusters the constraint in a way that prevents large
substructures.

**For pure-reasoning solvers**: Before claiming the symmetric choice is optimal,
ask "what if I deliberately break the symmetry?" For grid/covering problems:
what if the gaps are SPREAD OUT instead of clustered? For sequences: what if the
extremal sequence is NOT constant or linear?

**For deep-mode agents**: Brute-force n=3..8 before theorizing. If the formula
that fits is n+c√n instead of cn, the structure has √n-sized blocks.

## The Look Back phase (after you have a proof)

- **Can you check it?** Plug in small cases. Does n=3 give what your formula
  says?
- **Can you prove it differently?** A second proof is a verification. And often
  shorter.
- **Is your bound tight?** If you proved ≤ N and the answer is exactly N, find
  the extremal case. If you can't, your bound might be loose.
- **What did you actually use?** Sometimes you used less than all the hypotheses
  — the real theorem is stronger.

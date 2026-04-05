# Construction Patterns

Methodological patterns for finding optimal constructions. No specific problem
answers.

## Spread vs cluster

For optimization problems over permutations/configurations: the **symmetric
choice (identity, diagonal, regular spacing) is often the worst case, not the
best**. The intuition "symmetric = optimal" fails when the objective rewards
_large substructures_ that symmetry prevents.

**When to suspect this**: The problem asks to maximize the size of something
(tiles, intervals, independent sets) subject to a one-per-row/one-per-column
constraint. The symmetric placement makes the forbidden region a contiguous
band, leaving only thin slivers. Spreading the forbidden positions leaves fat
windows.

**What to try**: Partition into √n groups, assign each group to a residue class
mod √n. Within a group, place in reverse order. This makes any contiguous block
of √n rows/columns have its forbidden positions spread across all residue
classes.

## Moment curve for distinctness

When you need n objects in ℝ^k where "any k are independent" (or similar
genericity), the moment curve `(1, t, t², ..., t^{k-1})` at n distinct parameter
values gives this for free. Vandermonde determinants are nonzero, so any k of
the vectors are linearly independent.

**Rank-1 from vectors**: If you need matrices instead of vectors, rank-1
idempotents `A_i = v_i w_i^T` (projection onto `span(v_i)` along a complementary
hyperplane) turn vector genericity into commutator conditions. `[A_i, A_j] = 0`
iff a specific determinant vanishes.

## When brute-force reveals √n

If brute-forcing n=2..8 gives a sequence that fits `an + b√n + c` better than
`an + b`, the optimal structure has √n-sized blocks. Look for a construction
parameterized by k where k=√n balances two competing costs (e.g., k things each
of size n/k).

## Avoid: storing specific answers here

This file is for construction _techniques_, not solutions. If you find yourself
writing "the answer to Problem X is Y," delete it.

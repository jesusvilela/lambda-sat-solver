# Ladder Rung 2 — the sheaf-obstruction, made executable

**This rung is where the operator's geometric framework and the
classical ladder turn out to be the same object.** The operator's §6–§7
("UNSAT = local sections exist but cannot glue globally; the obstruction
class is the shape of UNSAT") is, precisely, **bounded-width resolution /
k-consistency**: a formula that is locally consistent but globally
unsatisfiable is one whose refutation *requires* width above the local
level (Atserias–Dalmau; Ben-Sasson–Wigderson). The "obstruction level"
has an exact name and an exact value: the **minimum resolution
refutation width**.

## What was built

`backend/complexity/invariants.min_refutation_width(F)` — the smallest
width w at which width-w resolution derives the empty clause, i.e. the
exact level at which local sections fail to glue. Solver-independent,
intrinsic. Validated (in `test_invariants.py`, 4 tests):

| formula | refutation width | why |
|---|---|---|
| x₁ ; ¬x₁ | 1 | unit contradiction |
| x₁ ; ¬x₁∨x₂ ; ¬x₂∨x₃ ; ¬x₃ | 2 | binary chain glues only at width 2 |
| PHP(3→2) | 2 | all clauses width 2; obstruction visible at width 2 |
| (empty clause) | 0 | already refuted |

## Why this is a hardness carrier (a theorem, not a hope)

Ben-Sasson–Wigderson (JACM 2001): resolution **size** ≥
exp(Ω((w − w₀)² / n)), where w is the minimum refutation width and w₀
the initial clause width. So width is not a heuristic correlate of
hardness — it *provably lower-bounds* refutation size, hence DPLL/CDCL
search cost on UNSAT instances. This is exactly the intrinsic,
classical, verifiable carrier the `COMPLEXITYINFERIORLIMIT` report asked
for, and Rung 1 showed the cheap graph invariants could not be.

## The honest limitation (and it is the point)

Exact `min_refutation_width` is **expensive**: the width-w closure has up
to Θ(nʷ) clauses, and it already blows past the guard on PHP(4→3)
(4 pigeons, 3 holes) within 90 s. This is not a bug — it is the
theory made tangible: the obstruction level is the *right* object and it
is *hard to compute*, which is precisely why no cheap scalar read off the
incidence graph can bound complexity (Rung 1), and why the operator's
sheaf-obstruction, while mathematically exact, does not hand you a fast
solver. The geometry names the obstruction; it does not cheapen it.

## Where this leaves the two programs — converged

- **Operator's framing** (sheaf gluing, obstruction geometry, §6–§7,
  §14): correct, and now executable. UNSAT-as-failed-gluing is
  bounded-width resolution; the "obstruction class" is the refutation
  width. This is the genuinely-right core of the geometric program, and
  it survives contact with computation.
- **Classical ladder** (Rung 2): a width/expansion lower bound is the
  established route to resolution-size lower bounds. Same object.
- **What neither gives**: a polynomial algorithm. Both frameworks agree
  (operator's §5, the report's conclusion, BSW's structure) that this
  is a *lower-bound / structure* program, not a P=NP route. That
  agreement is the honest foundation to build the rest on.

## Rung 3 (next, honest)

The real open direction with real theorems under it: **width lower
bounds via boundary expansion on the critically-constrained random
ensemble** (BSW's own application) — show that random 3-SAT just above
threshold requires large refutation width w.h.p. via the expansion of
its clause-variable graph, and connect the measured search-cost peak
(Rung 1) to that width bound. That is a standard, hard, real rung — and
it is the one the operator's obstruction-geometry language and the
resolution-width theory climb together.

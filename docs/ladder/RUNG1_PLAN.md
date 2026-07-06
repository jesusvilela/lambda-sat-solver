# Ladder to a hardness lower bound — Rung 1 plan

The ladder (from the operator's own `COMPLEXITYINFERIORLIMIT` report,
which correctly says ρ★>0 alone gives no lower bound and the carrier
must be intrinsic, classical, verifiable):

1. **Rung 1 (this doc)**: an intrinsic, solver-independent CNF invariant,
   with empirical evidence about whether it governs hardness.
2. Rung 2: a lower bound in a fixed proof model (tree-resolution / DPLL)
   provably tied to that invariant.
3. Rung 3: average-case hardening / worst-to-average.

## Rung 1 question (pinned before running)

Across the random 3-SAT phase transition, empirical hardness (search
cost) has a known sharp peak at α = m/n ≈ 4.26. **Which intrinsic,
solver-independent invariant tracks that peak?** This is the honest
first test of "is there a structural carrier of hardness."

## Invariants under test (all solver-independent)

Cheap / poly-time (graph-structural):
- `mean_var_degree`, `var_degree_entropy` — from the incidence graph.
- `spectral_gap` — algebraic connectivity λ₂ of the normalized variable
  co-occurrence Laplacian (poly-time expansion proxy; Cheeger links it
  to combinatorial expansion, the BSW width driver).

Expensive / exact-for-small-n (solution-space geometry):
- `num_solutions` — exact model count by exhaustive enumeration (n≤22).
- `backbone_fraction` — fraction of variables fixed to one value across
  ALL solutions (frozen variables; the freezing that drives
  phase-transition hardness).
- `num_clusters` — connected components of the solution graph under
  single-bit Hamming adjacency (clustering / shattering).

Hardness metric (the thing to be predicted):
- `dpll_decisions` — median decisions of a plain, robust DPLL
  (unit-prop + branch), a proof-model-faithful search cost independent
  of the VDIS machinery.

## Pre-registered predictions

- **P-cheap**: the cheap graph invariants (degree, spectral gap) do NOT
  track the hardness peak — random 3-SAT instances are all good, similar
  expanders across the ratio, so a graph invariant should be roughly
  flat/monotone in α, not peaked at 4.26. If this holds, cheap structure
  does not explain phase-transition hardness (and this is *why* cheap
  branching signals like degree don't predict per-instance hardness).
- **P-geom**: solution-space geometry DOES track it — backbone_fraction
  and clustering change sharply through the transition; peak hardness
  aligns with the freezing/shattering regime, not with any graph
  statistic. Intrinsic hardness lives in the solution space, which is
  intrinsic but expensive.

A pass for P-geom + fail-to-track for P-cheap is the honest Rung-1
finding: the carrier is real and intrinsic but lives in solution-space
geometry, not cheap graph structure — which tells Rung 2 exactly which
object a lower bound must be about.

## Method

n = 20 (exact enumeration feasible: 2²⁰ ≈ 1e6), k = 3, ratios α ∈
{3.0, 3.6, 4.0, 4.27, 4.6, 5.0, 5.5}, ≥ 15 seeds each. Per instance:
all invariants + DPLL decisions. Report Spearman correlation of each
invariant with hardness, and whether each is peaked at α≈4.27.
Correctness: DPLL SAT/UNSAT cross-checked against the exact enumeration.

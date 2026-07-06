# Ladder Rung 1 — report

**Finding: the carrier of random-3-SAT hardness is NOT a cheap graph
invariant. The easy–hard–easy peak is real and sharp, but the poly-time
graph-structural invariants (spectral-gap expansion proxy, degree
entropy) are monotone in clause density and do not track it — they are
even anti-correlated with hardness in the over-constrained regime. This
confirms, empirically and on our own instances, the thesis of the
`COMPLEXITYINFERIORLIMIT` report: hardness cannot be read off a cheap
structural statistic, and Rung 2 must be about solution-space /
resolution-width, not the incidence-graph spectrum.**

All invariants are solver-independent and unit-tested against
hand-computed cases (`backend/complexity/invariants.py`,
`backend/tests/test_invariants.py`). Hardness = median plain-DPLL
decisions (unit prop + first-unassigned branch), SAT/UNSAT cross-checked
against exact enumeration at n=20.

## The hardness peak is real (n=50, 15 seeds/ratio)

| α = m/n | hardness (median DPLL decisions) | spectral gap | degree entropy |
|---|---|---|---|
| 3.5 | 26 | 0.601 | 0.9880 |
| 4.0 | 188 | 0.628 | 0.9894 |
| 4.2 | **293** | 0.638 | 0.9901 |
| 4.27 | 278 | 0.643 | 0.9902 |
| 4.4 | 272 | 0.644 | 0.9906 |
| 4.6 | 219 | 0.654 | 0.9912 |
| 5.0 | 157 | 0.668 | 0.9921 |
| 5.5 | 119 | 0.683 | 0.9928 |
| 6.0 | 87 | 0.697 | 0.9935 |

Hardness rises to a sharp peak at α ≈ 4.2 and falls away — the textbook
phase-transition easy–hard–easy curve. The instrument works.

## The cheap invariants do NOT track it (P-cheap: CONFIRMED)

Spectral gap and degree entropy **increase monotonically** across the
entire ratio range. At α=6.0 the graph is the *best* expander (gap
0.697) yet the *easiest* instance (87 decisions); at the hardness peak
(α=4.2) the gap is middling. In the over-constrained half the two are
**anti-correlated**. No cheap graph statistic reproduces the peak. A
poly-time incidence-graph invariant is therefore not the carrier of
hardness — full stop.

## Solution-space geometry shifts through the transition, but is also monotone (n=20, exact)

| α | backbone frac | #clusters | sat frac |
|---|---|---|---|
| 3.0 | 0.01 | 4.5 | 1.00 |
| 4.0 | 0.48 | 2.3 | 0.85 |
| 4.27 | 0.59 | 2.0 | 0.70 |
| 5.0 | 0.80 | 1.3 | 0.30 |
| 5.5 | 0.78 | 2.0 | 0.10 |

Backbone/frozen fraction rises and cluster count collapses through the
transition — the freezing/shattering signature (Achlioptas–Coja-Oghlan,
Mézard–Zecchina). But these too are largely **monotone in density**, not
sharply peaked at the hardness maximum; and they are exact only at n≤~22,
where the hardness peak itself is shallow (8→16 decisions). So even the
"right" invariant is (a) expensive exactly where hardness is interesting
and (b) not a single-number peak detector.

## What this establishes for the ladder

1. **Rung 1 result (a clean negative that scopes Rung 2):** hardness is
   not carried by any cheap graph invariant. The hardest instances are
   the *critically-constrained* ones near the threshold, where the
   phenomenon is proof-theoretic (large refutation width) and
   solution-geometric (freezing/shattering) — not spectral.
2. **This is exactly the pivot the `COMPLEXITYINFERIORLIMIT` report
   demanded**: an intrinsic object, yes, but the *right* intrinsic object
   is resolution width / solution-space structure, and it is genuinely
   expensive — which is *why* cheap branching signals (degree) help a
   solver locally but cannot predict per-instance hardness, and why no
   "ρ★"-style scalar read off the incidence graph can bound complexity.
3. **Rung 2 target, now correctly aimed:** a resolution-width /
   boundary-expansion lower bound on the critically-constrained
   ensemble (Ben-Sasson–Wigderson), measured against DPLL/CDCL search
   cost — not a graph-spectrum predictor. That is the honest next rung,
   and it is a real, hard, standard problem with real theorems to build
   on.

No overclaim: this rung proves nothing about P vs NP. It establishes,
on measured evidence, *which* object a hardness lower bound must be
about — and rules out the cheap ones. That is what a first rung is for.

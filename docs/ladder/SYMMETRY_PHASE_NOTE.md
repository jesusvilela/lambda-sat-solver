# What goes on at symmetry and at the phase change — measured

*The probe (`docs/ladder/scripts/symmetry_phase_probe.py`) asked one question: are
symmetry-hardness and phase-transition-hardness the same thing, or two different
things? The measurement is decisive — **they are orthogonal axes** — and it
explains the whole frame program's scope.*

## A. The symmetry axis — CDCL hardness IS the symmetry (pigeonhole)

**A1 — hardness tracks the automorphism order.** As `|Aut| = n!·(n−1)!` grows,
Kissat's time grows exponentially while the counting frame stays flat:

| php | log₂\|Aut\| | counting frame | Kissat |
|---|---|---|---|
| php8 | 27.6 | ~2 ms | 124 ms |
| php10 | 40.3 | ~2 ms | 373 ms |
| php11 | 47.0 | ~3 ms | **2391 ms** |
| php12 | 54.1 | ~3 ms | **TIMEOUT (>8 s)** |

Kissat's time multiplies ~6× per pigeon (373 → 2391 → timeout) as log₂\|Aut\|
climbs ~7 bits per pigeon — CDCL pays the symmetry, re-deriving the same
refutation across every symmetric branch. The frame does not, because it computes
on the **quotient** (the counting bound is the isotropy made into an inequality).

**A2 — breaking the symmetry collapses the hardness.** Adding `k` sound units to
php11 (pinning variables — UNSAT is preserved, the automorphism group shrinks):

| k units | Kissat |
|---|---|
| 0 | 2332 ms |
| 1 | 1492 ms |
| 8 | 521 ms |
| **16** | **4 ms** |

**580× faster once enough symmetry is broken.** This is the knowledge, measured:
on pigeonhole the hardness *is* the symmetry — remove it and CDCL collapses from
2.3 s to 4 ms. Honest nuance: the effect is **non-monotone** — one or two units
barely help (a few even hurt), because partial symmetry breaking leaves most of
the group intact; the collapse comes only once enough generators are broken. (The
color-refinement bracket is a loose upper proxy here — 592 vs the true 47 bits —
so the *Kissat* times, not the bracket, are the load-bearing signal.)

## B. The phase-transition axis — criticality, with ZERO symmetry

Random 3-SAT (n=150) across the ratio α, with Kissat and the exact isotropy:

| α | SAT frac | Kissat median | Kissat **max** | mean log₂\|Aut\| |
|---|---|---|---|---|
| 3.0 | 1.00 | 4 ms | 17 ms | **0.000** |
| 4.0 | 1.00 | 31 ms | 46 ms | **0.000** |
| **4.26** | 0.67 | 40 ms | **114 ms** | **0.000** |
| 4.4 | 0.44 | 57 ms | 97 ms | **0.000** |
| 4.6 | 0.11 | 60 ms | 67 ms | **0.000** |
| 6.0 | 0.00 | 36 ms | 46 ms | **0.000** |

Two classic curves and one decisive null result:

- **The transition** — SAT-fraction falls sharply through α ≈ 4.3 (1.00 → 0.67 →
  0.11 → 0), the known 50% crossing.
- **Easy-hard-easy** — the *hardest* instances (Kissat max) peak right at the
  transition (114 ms at 4.26), then fall off on both tails.
- **Symmetry is identically zero, everywhere.** `mean log₂|Aut| = 0.000` at every
  α, including the hardness peak. Random 3-SAT is **perfectly rigid** — `|Aut| = 1`
  — from the easy-SAT tail through the critical ridge to the easy-UNSAT tail.

So the phase-transition hardness has **nothing to do with symmetry.** The peak at
α ≈ 4.26 is *criticality* — the instance sits on the SAT/UNSAT boundary where
neither a model nor a short refutation is easy to find — and the automorphism
group is trivial the whole way across.

## The synthesis — two orthogonal hardnesses, and where we live

| | symmetry axis (pigeonhole) | criticality axis (random 3-SAT @ 4.26) |
|---|---|---|
| \|Aut\| | astronomically large (`n!·(n−1)!`) | **1** (rigid) |
| source of hardness | symmetry → CDCL re-derives across orbits | criticality → on the SAT/UNSAT knife-edge |
| breaking symmetry | collapses it (2332 → 4 ms) | nothing to break (already rigid) |
| a frame? | **yes** — counting, on the quotient | **no** — no structure to collapse |
| who solves it | our frame (poly) or CDCL+sbp | CDCL, genuinely (no shortcut known) |

The two are **disjoint and measured to be uncorrelated**: pigeonhole is all
symmetry and no criticality; random 3-SAT is all criticality and *exactly zero*
symmetry. This is the deep account of the whole program:

> **Our frames are a symmetry-axis solver.** They win precisely where hardness
> comes from structure/symmetry, by dividing out the quotient — and they are
> silent, correctly, on the criticality axis, where the automorphism group is
> trivial and no quotient exists. That is why the edge-tail sweep found the frames
> firing on 0/6 random-3SAT instances at *every* α: there is nothing there for a
> frame to see. The phase transition is the axis CDCL owns.

And the bridge between the axes is **symmetry breaking**: reducing `|Aut|` moves a
structured instance off the symmetry axis toward CDCL-tractability (A2). The
counting frame is the limit of that move — divide out *all* the symmetry at once,
and the exponential becomes a single inequality.

## Status (Charter labels)

- **Measured** (`symmetry_phase_probe.py`, Kissat 4.0.4 oracle): the PHP
  symmetry-hardness scaling; the 580× collapse under symmetry breaking; the
  easy-hard-easy peak at α ≈ 4.26; and `|Aut| = 1` for random 3-SAT at every α.
- **Honest limits**: n = 150 is modest (the transition sharpens with n); symmetry
  breaking is non-monotone (a known phenomenon — you must break enough, and the
  right, generators); the color bracket is loose on large PHP, so the Kissat
  times carry the A2 conclusion, not the bracket.
- **Known-result grounding, not a new theorem**: that symmetry drives CDCL cost
  (hence symmetry breaking) and that random-3SAT hardness peaks at the transition
  are both established in the literature; what is *ours* is measuring them on one
  bench with an **exact automorphism oracle**, and reading them as the two
  orthogonal axes that place our frame program precisely on the symmetry one.

# VDIS v7 report — Lagrangian multiplier: hypothesis wrong, result better than the hypothesis

**Verdict: the pre-registered symmetry-breaking hypothesis FAILED (Z1
fail, Z3 falsified) — and in failing it uncovered the strongest,
best-validated positive in the entire track. The Lagrangian
dual-descent multiplier λ is not a symmetry-breaker; it is a
general-purpose decision heuristic that beats BOTH EVSIDS and LRB on
aggregate on fresh random 3-SAT and on the hardest mutilated-chessboard
instance.** EMPIRICAL: stage b7, 630 runs, 5 caps (all Random on
mutil_10, irrelevant to the λ comparison); prereg `VDIS7_PREREG.md`
committed before the run.

## Gate outcomes

| Gate | Criterion | Measured | Verdict |
|---|---|---|---|
| Z0 | λ cycles, ≠ EVSIDS | confirmed pre-run | PASS |
| Z1 (primary) | symmetry-break beats EVSIDS on BOTH mutil_8 & mutil_10 | mutil_10 won (−37%), mutil_8 lost | **FAIL** |
| Z2 | λ-only ≥ COMBO on structured aggregate | 28 371 < 37 377 | PASS (incidental) |
| Z3 (falsifier) | λ must NOT help r3sat (no symmetry) | λ-only beats EVSIDS 11/15 on r3sat | **FALSIFIED** |
| Floor | ≥ EVSIDS's Random-beat-count | 19/21 = 19/21 | PASS |

## The falsification is the finding

Z3 was pinned as a falsifier: if λ helps where there is no symmetry, the
symmetry-breaking interpretation is wrong. It does, so it is. λ-only
beats EVSIDS on **11/15 fresh random-3-SAT** instances (n=90, seeds
300–314), broadly — s300 −54%, s306 −55%, s303 −37% — not outlier-driven.
So λ is a *general* decision-quality improvement, not a symmetry device.

## The result that survived — validated against real baselines (post-hoc, same instances/seeds)

LRB was dropped from the v7 grid for compute; run afterward on the
identical instances (deterministic, fair, but not pre-registered — flagged):

| Family | metric | EVSIDS | LRB | **λ-only** |
|---|---|---|---|---|
| random-3sat (15 fresh) | Σ decisions | 8 788 | 8 047 | **7 315** |
| random-3sat | wins by λ-only | 11/15 | 8/15 | — |
| mutil_10 (hard) | decisions | 24 412 | 22 700 | **15 366** |
| mutil_8 (small) | decisions | **1 217** | 1 465 | 1 524 |

λ-only beats **both** standard heuristics on aggregate on the honest
benchmark family (fresh random-3-SAT at scale) and on the hardest
structured instance. This is the first config in seven generations to
beat EVSIDS *and* LRB on aggregate on a fresh, scaled set.

## Mechanism (what λ actually does, corrected)

The load-bearing feature is the **dual descent**: deciding a variable
pays down its multiplier (λ_v ← 0.5·λ_v), so its priority drops and the
search is pushed to *other* high-pressure variables instead of
re-litigating the same neighborhood. This is decision *diversification* /
anti-tunnel-vision — which helps broadly (random and large structured),
exactly the opposite profile of a symmetry-breaker. EVSIDS never lowers
a score for being decided; that primal coupling is the whole difference,
and it is what "consider Lagrange" contributed.

## Division of labor across the two live nudges

- **prime (v6/COMBO)** owns pigeonhole: COMBO php_8 = 4 625 < EVSIDS
  5 099; λ-only does *not* crack php (9 840). Static asymmetric order is
  the right symmetry-break for php.
- **λ (v7)** owns random-3-SAT and large mutilated: the diversifying
  multiplier.
- **Combining them dilutes** (COMBO+λ mediocre everywhere) — they want
  different instances, and a fixed blend serves neither. A router, not a
  blend, is the implied design.

## Caveats — foregrounded, because the hypothesis was wrong once already

1. **One size (n=90), 15 seeds** for the r3sat result; mutil is n=2
   (one win, one loss). The v5 seed-lottery lesson binds: promising, not
   proven. Needs replication across sizes and ≥50 instances before any
   load-bearing claim.
2. **Decisions-to-solve on a Python reference solver**, not wall-clock
   vs Kissat. The claim is "λ dual-descent is a better *decision rule*
   than EVSIDS/LRB on these families at this scale," not "beats SOTA."
3. **Serendipity, not confirmation**: the pre-registered prediction
   (symmetry-breaking) failed. This is an exploratory finding that now
   needs its *own* pre-registration to be trusted — precisely the
   discipline that caught it.

## Disposition

No-rescue closes v7. But unlike the six prior negatives, v7 leaves a
concrete, baseline-validated, scaled positive worth a dedicated
follow-up: pre-register λ dual-descent alone (drop the whole gyrovector
stack — it was never what helped) vs EVSIDS/LRB across sizes n ∈
{50,90,150} × ≥50 seeds each, wall-clock instrumented, with the prime
router for structured families. That is the first VDIS result that has
earned a real replication study rather than another mechanism turn.

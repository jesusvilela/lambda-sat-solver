# VDIS v5 report — C branch + tie-break, fresh instances

**Verdict: X3 PASS — the primary 7/13 bar is cleared for the first
time in the track, on held-out instances: H-MF3 beats EVSIDS on 9/13
(8/9 on fresh random 3-SAT), H-PA on 8/13, both C configs on 7/13. My
own X2 selection-regression prediction was WRONG in the favorable
direction. The floor gate fails at 10/13 — but EVSIDS itself fails it
identically, so it measures the fresh set, not the heuristics.**
EMPIRICAL: stage b13f, 455 runs, 0 capped, seeds 0–4; prereg
`VDIS5_PREREG.md` committed before the benchmark.

## Gate outcomes

| Gate | Pinned criterion | Measured | Verdict |
|---|---|---|---|
| X1 (liveness) | C-PA θ alive | spread 0.334, fires (probed pre-benchmark) | PASS |
| X2 (selection-regression) | prediction: incumbents' fresh-r3sat win-rates regress DOWN from 4/9 | they ROSE: C-plain 6/9, H-PA 7/9, H-MF3 8/9 | **prediction WRONG** — favorably |
| X3 (primary) | best VDIS ≥ 7/13 vs EVSIDS | **H-MF3: 9/13**; H-PA 8/13; C-PA & C-plain 7/13 | **PASS** |
| X4 (transfer) | C-PA ≥ C-plain | wins tied 7/13; total 20 186 < 20 293 | PASS (marginal) |
| Floor | ≥ 11/13 vs Random | 10/13 all configs — and EVSIDS is also 10/13 | FAIL as pinned; see below |

## Results (B13″: php 5–8 unchanged + fresh r3sat seeds 11–13)

| Config | vs EVSIDS | r3sat wins | Σ median decisions |
|---|---|---|---|
| EVSIDS | — | — | 10 441 |
| **H-MF3** | **9/13** | 8/9 | 22 195 |
| H-PA | 8/13 | 7/9 | 22 901 |
| LRB | 8/13 | 7/9 | 24 966 |
| C-PA | 7/13 | 6/9 | 20 186 |
| C-plain | 7/13 | 6/9 | 20 293 |

## Honest interpretation, both directions

1. **The pass is real and pre-registered**: fresh seeds, never used
   anywhere in ~1 900 prior runs, bar pinned in advance, and the
   passing configs (H-MF3, H-PA) were frozen before the fresh set
   existed. On fresh phase-transition random 3-SAT, the VDIS living
   field + anti-ambiguous tie-breaks beat EVSIDS's decision quality
   8 or 9 times out of 13 — e.g. n100_s12: 392 vs 1 243 (−68%);
   n100_s13: 552 vs 1 059 (−48%).
2. **What the pass does NOT say**: EVSIDS still dominates aggregate
   totals 2×  (10 441 vs 22 195), entirely via php (14 494+ vs 5 099
   on php_8_7 alone). And LRB — a stock published heuristic — scores
   8/13 on this fresh set too, so "beats EVSIDS on win-count at the
   phase transition" puts VDIS in LRB's class, not above it: H-MF3's
   9/13 edges LRB's 8/13 by one instance, with a 2 771-lower total.
   The defensible headline is "competitive with, slightly ahead of,
   LRB-class heuristics on random instances; far behind everything on
   structured instances."
3. **X2's failed prediction is the methodological finding**: B13′'s
   r3sat seeds 1–3 were EVSIDS-*lucky*, not VDIS-lucky — four
   generations were judged on a slate that understated every
   VDIS/LRB-class config by 2–4 r3sat wins. The 7/13 bar that failed
   four times on B13′ may simply have been miscalibrated to an
   unlucky draw of nine instances. Seed-to-seed variance in "who wins
   an instance" is larger than any mechanism effect measured in this
   track — which cuts both ways and caps how much any 13-instance
   result, including this pass, should be trusted. A serious verdict
   needs ~50+ instances per family; recorded as the follow-up that
   matters most.
4. **The floor gate is broken, again, the same way**: Random's median
   beats EVSIDS itself on 3/13 fresh instances (php_5_4, n50_s12,
   n75_s13 — all tiny). Two protocols in a row, the Random floor
   measured instance luck rather than heuristic sanity. Any future
   prereg should define the floor relative to EVSIDS's own
   Random-score on the same set (here: match it, 10/13 — all configs
   do).
5. **X4's transfer is real but small**: the tie-break changed 16/65
   C runs (php + big-n100 rows), net −107 total with php_8_7 slightly
   better (14 494) and php_7_6 worse. The C branch's strength stays
   what it was: algebra/curvature, not tie-breaks.

## Track tally after five generations (B13″ is the honest column)

Best-of-track on held-out data: **H-MF3 9/13 / 22 195** and
**C-PA 20 186** (best total). EVSIDS 10 441. The mechanism stack that
survived five generations of falsification attempts: fossil axis
(bit-exact EVSIDS core) + ε-init living field + per-family κ + pair-θ
and precessing-prime tie-breaks at near-ties. Everything else tested
(additive torsion in any form, fixed-frame rotors, Ψ sandwiches,
ortho-only wedges) measurably nulled or hurt.

## Disposition

v5's grid is exhausted (no-rescue). The one follow-up the data itself
demands: scale the instance count (~50/family, fresh seeds) so that
win-counts stop being seed-lottery readings — everything else measured
in this track is smaller than that noise floor. Held-out κ (P4) and
the Laplacian feature remain parked and ready.

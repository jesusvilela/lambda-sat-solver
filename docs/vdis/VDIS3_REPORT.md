# VDIS v3 report — polarity-pair (x/x′) torsion, anti-ambiguous injection

**Verdict: R2 FAIL (best 5/13 vs the 7/13 bar) — the third and, per the
no-rescue rule, final negative on the primary prediction for this line.
But the operator's anti-ambiguous hypothesis is directionally
vindicated *within* v3: pure tie-breaking beats every additive variant
and posts the lowest aggregate decision total in all of Track B1.**
EMPIRICAL throughout: stage b13v3 in `phase3_results.jsonl`, 260 runs,
0 capped, seeds 0–4, prereg `VDIS3_PREREG.md` (committed, with its R1
probe disposition, before the benchmark).

## Gate outcomes

| Gate | Pinned criterion | Measured | Verdict |
|---|---|---|---|
| R1 (liveness) | θ spread > 10⁻², P toggle matters, PA fires | r3sat fully alive; php oscillating (48% of decisions live), PA can't re-decide there — disposition pre-declared in the prereg addendum | PASS with declared asymmetry |
| R2 (primary) | best v3 beats EVSIDS ≥ 7/13 | PA: 5/13; P+PA: 3/13; P@0.3: 4/13; P@0.1: 2/13 | **FAIL** |
| R3 (floor) | ≥ 11/13 vs Random | 11/13, all configs | PASS |
| R4 (anti-ambiguous ≥ best additive) | PA-containing ≥ P@0.3's 4/13 | PA: 5 ≥ 4 ✓; P@0.1+PA: 3 < 4 ✗ | **split** — strict reading FAIL (one PA config below), pure-PA reading PASS |

## Sweep table (median decisions, B13′; v1 winner shown for reference)

| Config | beats EVSIDS | php wins | r3sat wins | Σ median decisions |
|---|---|---|---|---|
| v1 winner (VDIS-H, λχ=0.1, β=0.1) | 6/13 | 1/4 | 5/9 | 24 599 |
| **VDIS3 PA (tie-break only)** | 5/13 | 1/4 | 4/9 | **23 586 — best in Track B1** |
| VDIS3 P, λp=0.3 | 4/13 | 1/4 | 3/9 | 26 043 |
| VDIS3 P@0.1+PA | 3/13 | 1/4 | 2/9 | 25 645 |
| VDIS3 P, λp=0.1 | 2/13 | 1/4 | 1/9 | 25 213 |

## What the numbers say

1. **Anti-ambiguous > smoothing, decisively, within v3.** The pure
   tie-break config (PA — θ consulted *only* inside near-ties, clear
   decisions untouched) beats every additive config on wins (5 vs
   2–4) and total (23 586 vs 25 213–26 043). The additive variants
   reproduce v2's smoothing pathology, worse: λp=0.1 additive is the
   weakest config ever benchmarked in this track (2/13). The
   operator's "on smoothness, perhaps anti ambiguous will help"
   is confirmed as a *relative* statement — injection at ambiguity
   points is the right delivery mechanism for this signal.
2. **But the signal itself doesn't clear the bar.** PA still loses to
   the v1 winner on wins (5 vs 6) and to EVSIDS overall. Notable
   per-instance bests-in-track: r3sat_n50_s1 median 91 (v1: 94,
   EVSIDS: 149) and r3sat_n75_s3 median 94 (v1: 106, EVSIDS: 209 —
   a 55% cut). The n=100 family stays VDIS-friendly (PA wins 2/3).
3. **Attribution gap, stated plainly**: PA differs from the v1 winner
   in TWO ways — rotor machinery removed (β=0) *and* tie-break added —
   because v3 pinned β=0 across its grid. Its 23 586-vs-24 599 total
   improvement over v1 therefore cannot be attributed to the tie-break
   alone without a β=0-plain control (which is exactly Phase 3's
   never-run S3-halted ablation). Running it now would be off-grid
   under v3's no-rescue rule, so it is *not* run; it is the one clean
   follow-up if the operator wants the attribution settled (~6 min).
4. **The php family is untouched by everything** (1/4 for every VDIS
   config in every generation — and that one win is noise-level
   php_5_4). Whatever pigeonhole needs, it is not in the gyrovector
   living field: the θ signal provably collapses exactly there
   (mid-run oscillation, prereg addendum), consistent with PHP's
   symmetric structure giving both polarities identical bump
   histories.

## Track-level tally after three generations

| Generation | Mechanism | Best vs EVSIDS | Best Σ decisions |
|---|---|---|---|
| v1 | fossil + living field + (inert) rotor | 6/13 | 24 599 |
| v2 | prime-anchored live rotor | 5/13 (new configs) | 24 154 |
| v3 | polarity-pair θ, anti-ambiguous | 5/13 | **23 586** |

EVSIDS: 10 163 total, and no VDIS generation has reached 7/13. The
through-line finding: each generation's *sharpening* variant (v2
smoothed and lost wins; v3's tie-break sharpened and recovered totals)
moved aggregate cost down without converting it into per-instance wins
against EVSIDS — the wins stay concentrated where they started, in
large phase-transition random 3-SAT (n=100: 11–43% cuts, all three
generations, every config).

## Disposition

No-rescue closes v3. Open, designed follow-ups for the operator:
(a) the β=0-plain attribution control (one config, settles what PA's
total improvement is made of); (b) the held-out κ test (P4, runner
ready); (c) the parked Laplacian-feature κ policy. The verified
machinery — gyro ops, algebra layer, pair-angle geometry, tie-break
injection — all remains in `backend/vdis/` with 474 tests passing.

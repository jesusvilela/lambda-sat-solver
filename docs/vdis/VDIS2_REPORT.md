# VDIS v2 report — prime-anchored 360° torsion + ortho wedge

**Verdict: the torsion channel was successfully revived (Q1 PASS) and,
now that it is measurably alive, it measurably does not help (Q2 FAIL,
Q4 FAIL). Per the prereg's no-rescue rule this is the final negative
for this line absent a new operator instruction.** All numbers
EMPIRICAL: `phase3_results.jsonl` stages b13/b13v2, seeds 0–4, 390 new
runs, 0 capped, code at commit `6416107` (prereg: `VDIS2_PREREG.md`,
committed before implementation).

## Gate and prediction outcomes

| Gate | Pinned criterion | Measured | Verdict |
|---|---|---|---|
| Q1 (liveness) | τ spread > 10⁻³, λ_τ toggle changes decisions | A: τ spread up to 9×10⁻³, \|Ψ_biv\| 0.20, decisions change on both probes. B: dead (τ spread = 0). AB: alive, marginal on one probe (6×10⁻⁴) | **PASS** (via A/AB) |
| Q2 (primary) | best v2 beats EVSIDS ≥ 7/13 | best 6/13 — and only from B, which is v1 in disguise (below); genuinely-new configs: 4–5/13 | **FAIL** |
| Q3 (floor) | beats Random ≥ 11/13 | 11/13, all six configs | **PASS** |
| Q4 (anchor contribution) | A or AB beats λ_τ-matched B by ≥ 1 instance vs EVSIDS | A: 5 vs B: 6 (both λ_τ); AB: 4–5 vs 6 | **FAIL** |

## Sweep table (median decisions over 5 seeds, B13′)

| Config | beats EVSIDS | beats Random | Σ median decisions |
|---|---|---|---|
| v1 winner (VDIS-H, λχ=0.1) | 6/13 | 11/13 | 24 599 |
| VDIS2-H **B**, λτ=0.1 | 6/13 | 11/13 | 24 599 |
| VDIS2-H B, λτ=0.3 | 6/13 | 11/13 | 24 807 |
| VDIS2-H **A**, λτ=0.1 | 5/13 | 11/13 | 24 610 |
| VDIS2-H A, λτ=0.3 | 5/13 | 11/13 | 24 322 |
| VDIS2-H **AB**, λτ=0.1 | 4/13 | 11/13 | 24 504 |
| VDIS2-H AB, λτ=0.3 | 5/13 | 11/13 | 24 154 |

## The consistency check paid off

The Q1 probe predicted variant B (ortho-only) would be decision-
identical to the v1 winner: ortho revives Ω's magnitude, but Ω enters
decisions only through τ = ⟨RΨR†, Ψ⟩, and Ψ's v1 update still collapses
to identity — and scalars are central, so conjugating an identity Ψ
returns Ψ regardless of R. Measured: **0 differing decision counts in
65 per-seed comparisons.** The pathway analysis is confirmed exactly,
and B's apparent "6/13" is not a v2 result at all — it is v1's.

## What the revival actually established

1. **The mechanism works as designed** (Q1): prime-spread anchor
   phases give Ψ persistent bivector content (‖Ψ_biv‖ ≈ 0.08–0.20
   after solves vs ≤ 2×10⁻⁴ in v1) and literal-differentiated τ. The
   operator's ingredients did revive the channel — this is the part of
   the instruction that succeeded, and it is now reusable machinery
   (`torsion_anchor`, `wedge_ortho` flags; `prime_anchor_bivectors`).
2. **A live torsion signal slightly hurts this benchmark** (Q2/Q4):
   every genuinely-new config scores 4–5/13 against the v1 baseline's
   6/13, with aggregate totals within ±2% of v1's. The phase-alignment
   information the anchors encode (which prime-phased variables have
   been conflicting together) either carries no decision-relevant
   signal on these families, or λ_τ ∈ {0.1, 0.3} injects it at the
   wrong scale — the grid is exhausted, so distinguishing those two is
   out of scope per the no-rescue rule.
3. **Interpretive note, honestly ambiguous**: the two λτ=0.3 anchor
   configs have the *lowest aggregate totals* in the entire Track B1
   history (24 154 / 24 322 vs v1's 24 599) while winning *fewer*
   individual instances — the anchor smooths the profile (fewer
   catastrophes, fewer wins) rather than improving it. Recorded as an
   observation, not a claim.

## Disposition

Q2 failed at the same 7/13 bar P1 failed at, with the channel now
genuinely live — so the negative is more informative than Phase 3's:
it is no longer possible to attribute the torsion channel's
non-contribution to inertness. The pinned no-rescue rule closes this
line. The one measured positive from Track B1 stands unchanged: VDIS-H
beats EVSIDS on all three n=100 phase-transition instances by 11–43%
(v1, reconfirmed by every v2 config also winning those three).

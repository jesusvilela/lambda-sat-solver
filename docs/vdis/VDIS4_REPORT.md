# VDIS v4 report — moving-frame rotor on the v3 PA setup

**Verdict: W2 FAIL (best 5/13 vs 7/13), W4 FAIL on the pinned win-count
(5 = 5, not >). Fourth consecutive miss of the primary bar; no-rescue
closes v4. But this generation settled the attribution question with a
result neither pre-registered pole predicted, and the operator's MF3
(primes precessing in the moving frame) posted the best aggregate
total in Track B1 history.** EMPIRICAL: stage b13v4, 260 runs, 0
capped, seeds 0–4; prereg `VDIS4_PREREG.md` with W1 disposition
committed before the benchmark.

## Gate outcomes

| Gate | Pinned criterion | Measured | Verdict |
|---|---|---|---|
| W1 | frame moves, ρ spread, tie-break fires | ‖F_biv‖ 0.32–0.52; ρ spread 0.082 (r3sat); fires up to 28/solve; php ρ ≡ 0 (pre-declared) | PASS |
| W2 (primary) | best MF ≥ 7/13 vs EVSIDS | MF1/MF2/MF3 all 5/13 | **FAIL** |
| W3 (floor) | ≥ 11/13 vs Random | 11/13 all configs | PASS |
| W4 | best MF > v3-PA's 5/13 | 5 = 5 (though MF3's total beats PA — below) | **FAIL** |

## Sweep table (median decisions, B13′)

| Config | vs EVSIDS | Σ median decisions |
|---|---|---|
| EVSIDS | — | 10 163 |
| v1 winner | 6/13 | 24 599 |
| v3 PA | 5/13 | 23 586 |
| v4 CTRL (β=0 plain) | 4/13 | 25 345 |
| v4 MF1 (θ+ρ tie) | 5/13 | 24 360 |
| v4 MF2 (ρ-only tie) | 5/13 | 25 333 |
| **v4 MF3 (θ+ρ+primes)** | 5/13 | **23 383 — best in track** |

## The CTRL result: both pre-registered readings were wrong

Pinned in advance: CTRL ≈ PA's total ⇒ rotor removal was v3's
improvement; CTRL ≈ v1's ⇒ the tie-break was. Measured: **CTRL =
25 345 — worse than BOTH.** The decomposition that actually holds:

- The pair tie-break is worth **−1 759 total decisions and +1 win**
  (CTRL 25 345/4 → PA 23 586/5; the two configs differ only by the
  tie-break, and differ per-seed in 28/65 runs).
- v1's rotor machinery was worth **−746 and +2 wins over CTRL**
  (25 345 → 24 599) — but NOT as torsion. v1's winner had λ_τ = 0, so
  τ never entered a score; the only rotor pathway into v1's decisions
  was Ψ's ~2×10⁻⁴ bivector drift perturbing ⟨t, Ψ⟩. **v1's rotor was
  functioning as a microscopic score dither, not as geometry** — a
  finding consistent with everything else in this track: tiny
  symmetry-breaking noise (ε-init, Ψ-drift) is worth 1–2 wins on this
  benchmark, and it was never the advertised mechanism doing the work.

## The operator's primes earned their slot

MF3 (= MF1 + prime anchors precessing in the moving frame) vs MF1
(frame alone): **23 383 vs 24 360 total** at equal wins — the identity
component added on top of the frame dynamics, exactly the synthesis
the operator's amendment proposed. MF3 also posts the best-ever VDIS
medians on the two hardest structured instances: php_8_7 = 17 647
(v1: 18 897, PA: 17 929) and php_7_6 = 1 654 — notable precisely
because php's state-dependent signals (θ, state-wedge ρ) are provably
zero there (polarity symmetry ⇒ identical histories); the precessing
prime fingerprint is the only tie-break information php ties ever get,
and it beat both no-information (CTRL) and θ-only (PA) on that family.
Against that: MF3 loses n100_s3 to PA (719 vs 551), so the fingerprint
costs something where the dynamic signal was already good. Net: best
aggregate in track, no new wins — the same "sharpening moves totals,
not win counts" pattern as v2→v3.

## Track tally after four generations

| Generation | Best config | vs EVSIDS | Σ decisions |
|---|---|---|---|
| v1 | H, λχ=0.1 (Ψ-dither rotor) | **6/13** | 24 599 |
| v2 | prime anchors, additive τ | 5/13 | 24 154 |
| v3 | pair-θ, anti-ambiguous | 5/13 | 23 586 |
| v4 | **MF3: θ+ρ+precessing primes** | 5/13 | **23 383** |

EVSIDS: 10 163. Four generations, monotone aggregate improvement
(24 599 → 23 383), and the 7/13 win bar never reached — the aggregate
gap is concentrated where it always was: php_8_7 (17 647 vs 5 099)
and r3sat_n75_s1 (525 vs 293). The n=100 family stays VDIS-friendly
in every generation.

## Disposition

No-rescue closes v4. Standing open items: the held-out κ test (P4,
runner ready), the parked Laplacian κ-policy experiment, and — new
from this generation — the observation that structured-instance ties
respond to *identity-bearing* tie-breaks (MF3 on php) while
random-instance ties respond to *dynamics-bearing* ones (θ on r3sat):
a family-conditional tie-break would be the natural v5 hypothesis if
the operator wants one more turn of the crank.

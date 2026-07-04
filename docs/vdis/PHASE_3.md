# VDIS Track B1 — Phase 3: pre-registered benchmark

**Status: NEGATIVE RESULT. P1 FAIL (6/13), P2 FAIL (11/13). Stop
condition S3 triggered after the debugging pass found no implementation
bug. Per protocol: halt, report negative. The ablation (P3), held-out
κ (P4), and suite-context stages were NOT run — S3 halts Track B1
before them.** (P3's question was nonetheless answered by the sweep
itself; see "The torsion channel is inert" below.)

Everything here follows `PHASE_3_PREREG.md` (commit `011d001`),
committed before any benchmark run. Code under test: commit `6339c6f`.
Raw data: `docs/vdis/scripts/phase3_results.jsonl` (715 runs: 13
instances × 11 configs × seeds 0–4; zero conflict-capped runs; zero
SAT/UNSAT verdict disagreements across heuristics).

## Sweep results (B13′, median decisions over 5 seeds)

| Config | beats EVSIDS | beats Random | Σ median decisions |
|---|---|---|---|
| VDIS-H, λτ=0.0, λχ=0.1 (**winner**) | **6/13** | 11/13 | 24 599 |
| VDIS-H, λτ=0.1, λχ=0.1 | 6/13 | 11/13 | 24 599 |
| VDIS-H, λτ=0.0, λχ=0.0 | 6/13 | 11/13 | 24 634 |
| VDIS-H, λτ=0.1, λχ=0.0 | 6/13 | 11/13 | 24 634 |
| VDIS-C (all four λ combos, identical) | 5/13 | 11/13 | 20 043 |
| LRB | 7/13 | 11/13 | 24 915 |
| EVSIDS | — | 12/13 | 10 163 |
| Random | — | — | 60 237 |

Winner per the pre-registered rule (max wins, then min total):
**VDIS-H, λτ=0, λχ=0.1** — the λτ=0/0.1 pair is decision-identical, so
"the winner" is really "VDIS-H with λχ=0.1, λτ irrelevant".

Per-instance medians, winner vs baselines:

| Instance | EVSIDS | LRB | Random | VDIS-H (winner) | Δ vs EVSIDS |
|---|---|---|---|---|---|
| php_5_4 | 39 | 37 | 32 | 35 | −10% |
| php_6_5 | 181 | 248 | 247 | 191 | +6% |
| php_7_6 | 948 | 2 208 | 2 274 | 1 925 | +103% |
| php_8_7 | 5 099 | 19 176 | 24 253 | 18 897 | +271% |
| r3sat_n50_s1 | 149 | 111 | 222 | 94 | −37% |
| r3sat_n50_s2 | 29 | 26 | 39 | 94 | +224% |
| r3sat_n50_s3 | 11 | 11 | 56 | 25 | +127% |
| r3sat_n75_s1 | 293 | 556 | 2 483 | 525 | +79% |
| r3sat_n75_s2 | 221 | 231 | 1 923 | 368 | +67% |
| r3sat_n75_s3 | 209 | 153 | 380 | 106 | −49% |
| r3sat_n100_s1 | 593 | 486 | 1 821 | 337 | −43% |
| r3sat_n100_s2 | 1 425 | 1 171 | 25 077 | 1 267 | −11% |
| r3sat_n100_s3 | 966 | 501 | 1 430 | 735 | −24% |

## Verdicts (EMPIRICAL)

- **P1: FAIL.** 6/13 < 7/13.
- **P2: FAIL.** 11/13 < 12/13 → **S3**.

## The S3 debugging pass (required before halting on P2)

P2's stated rationale is "failure here = implementation bug, not
physics." The pass looked for the bug and did not find one:

1. **No anomalous runs**: 0 conflict-capped, 0 verdict disagreements
   across 715 runs.
2. **The two P2 losses, per-seed raw data**:
   - `php_5_4`: VDIS [35,35,35,37,39] vs Random [31,32,40,30,40] — a
     39-decision instance where every heuristic lands in a 30–40 band.
     **EVSIDS itself loses this instance to Random** (39 vs median 32),
     which is why EVSIDS's own Random score is exactly 12/13. Noise.
   - `r3sat_n50_s2`: VDIS [47,183,60,126,94] vs EVSIDS deterministic
     29. Genuinely worse, high-variance behavior on a trivially easy
     instance — the ε-init living-field noise perturbs early decisions
     on instances that EVSIDS's clean zero-state solves before any
     signal accumulates. Real behavior, not a defect.
3. **Structural correctness evidence**: the degenerate configuration
   of the same code path reproduces EVSIDS bit-for-bit (S4 gate, still
   green); every Phase 2 SAT answer was model-checked.
4. **Calibration context, not exculpation**: LRB — a real, published
   heuristic (Liang et al. 2016) — also scores 11/13 against Random on
   this set, i.e. the pinned P2 threshold is failable by legitimate
   heuristics because two trivial instances let Random's median win by
   luck. Recorded for the next protocol's design; it does not change
   this one's verdict.

**Conclusion: no implementation bug. The P2 failure stands. S3: halt.**

## The torsion channel is inert (EMPIRICAL + mechanism)

The sweep contained its own λτ ablation: toggling λτ 0 ↔ 0.1 changed
**zero** decision counts anywhere (13 instances × 5 seeds, both
algebras). Direct instrumentation confirms why: after full solves,
τ_ℓ ∈ [1.0, 1.0] with spread ≤ 1.8×10⁻¹⁰ (r3sat_n100_s1), Ψ's
bivector part ≲ 2×10⁻⁴, and on php_7_6 max|Ω| ≈ 0 with Ψ at identity
to 6×10⁻¹⁵. Mechanism, stated precisely: the S3.2 bump moves every
participating literal's tangent *toward* Δ̂_C, so t̂_ℓ ∧ Δ̂_C
self-extinguishes as literals align with the conflict field — the same
state-proportionality motif that produced the Phase 1 absorbing fixed
point and the Phase 2 living-axis stillbirth, in its third form. For
A=C this was PROVED trivially in Phase 2 (commutativity); for A=H it
is now measured. The rotor channel as pinned in S3.4 does nothing on
this benchmark.

## What was not run

Per S3's halt: the β=0 ablation stage (P3 — moot given the above: the
τ pathway is inert and β's only other effect, Ψ drift, is bounded by
|Ψ_bivector| ~ 10⁻⁴), the held-out κ stage (P4), and the quick+medium
suite context stage. The runner supports all three
(`phase3_benchmark.py ablation|p4|suite`) if the spec's author elects
to overrule S3 — that is the operator's call, not this agent's.

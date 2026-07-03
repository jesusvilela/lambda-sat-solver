# VDIS v3 pre-registration — polarity-pair torsion, anti-ambiguous injection

**Operator correction (verbatim): "you misinterpreted primes, which I
meant as in x and x' for prime numbers, serendipitously. Those were
meant on conjunction to Ortho. On smoothness, perhaps anti ambiguous
will help too." Committed before implementation.**

## Corrected interpretation (pinned)

- **"primes" = x and x′** — Boolean complement notation, not prime
  numbers. (The prime-number reading was serendipitous: it revived Ψ
  and is retained as machinery, but it is not what was asked.)
- **"in conjunction to ortho"**: the torsion source is the pair
  (t_x, t_x′) — the angular disagreement between a variable's two
  polarity states — with the ortho treatment making it scale-free:
  θ_v = atan2(‖vec(t̂_{+v}) ∧ vec(t̂_{−v})‖, vec(t̂_{+v})·vec(t̂_{−v}))
  ∈ [0, π], the full angle ("360"), not a magnitude that dies with
  alignment.
- **"anti ambiguous"**: v2 measured that *additive* torsion smooths —
  fewer catastrophes, fewer wins, net −1..−2 instances. The
  anti-ambiguous injection adds the signal **only inside near-ties**,
  where trajectories actually fork (the Phase 1 ULP-tie diagnosis) and
  where EVSIDS has literally no information (its ties break by lowest
  variable index). Clear decisions are left untouched by construction,
  so the smoothing cost cannot recur.

## Why this signal cannot die the previous deaths (to be tested, not assumed)

1. No Ψ, no rotor sandwich — θ_v is read directly from the pair, so
   the Ψ-identity trap (v2's variant-B death) has no pathway.
2. The two polarities of a variable appear in different clauses and
   receive different bump histories, so mutual alignment is not forced
   by the update rule the way literal-vs-Δ̂ alignment was. Residual
   risk, stated in advance: variables whose polarities both track Δ̂
   for long stretches will still converge (θ → 0); the R1 gate
   measures whether enough angular spread survives in practice.

## Pinned v3 mechanics

Per variable v, u± = normalized vector part (algebra H, imaginary
coords) of the slot-sum of t̂_{±v}; θ_v = atan2(‖u₊ × u₋‖, u₊·u₋);
θ_v = 0 where either living state is degenerate (norm ≤ 10⁻¹²).

- **P (additive pair torsion)**: var score += λ_p · (θ_v / π).
- **PA (anti-ambiguous tie-break)**: compute base var scores; the
  near-tie band is {v : score_v ≥ s_max − 10⁻⁶·max(|s_max|, 1)};
  within the band, the decision goes to the variable with the largest
  θ_v (most polarity-contested). Band width pinned at 10⁻⁶ relative.
- Rotor/Ω/Ψ machinery OFF (β=0) in all v3 configs — v2 measured the
  anchor channel net-negative; v3 tests the corrected reading alone.

## Benchmark (unchanged apparatus)

B13′, seeds 0–4, cap 100 000, median decisions over seeds; baselines
(EVSIDS / Random / LRB / v1 winner) reused from `phase3_results.jsonl`.
Configs (algebra H, dim 32, κ per family table, λχ = 0.1):

1. P, λ_p = 0.1
2. P, λ_p = 0.3
3. PA (tie-break only, no additive term)
4. P(λ_p = 0.1) + PA

## Gates

- **R1 (liveness, probe before benchmark)**: θ spread across variables
  > 10⁻² on both probe instances; for P: λ_p toggle changes decisions;
  for PA: the tie-break fires ≥ 1 time per probe solve (counted).
  Fail → halt, report, don't run.
- **R2 (primary)**: best v3 config beats EVSIDS ≥ 7/13 (same bar as
  P1/Q2).
- **R3 (floor)**: ≥ 11/13 vs Random (calibrated floor, per Phase 3).
- **R4 (the operator's hypothesis)**: PA-containing configs ≥ the best
  purely-additive P config on the vs-EVSIDS count — "anti ambiguous
  will help" made falsifiable.
- **No-rescue**: this grid is final for v3.

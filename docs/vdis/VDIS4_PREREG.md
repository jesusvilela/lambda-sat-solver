# VDIS v4 pre-registration — rotor restored in a moving-frame scheme

**Operator instruction (verbatim): "kepp the current setup and restore
rotor in a moving moving frame scheme". Committed before
implementation.**

## Interpretation (pinned)

- **"current setup"**: v3's PA configuration — polarity-pair angle θ_v
  delivered anti-ambiguously (near-tie disambiguation only), H, dim 32,
  λχ = 0.1, κ per family table. Unchanged.
- **"restore rotor"**: β back to 0.1; Ω per literal returns.
- **"moving moving frame"**: Cartan moving frame (repère mobile). A
  global frame rotor F follows the conflict flow, and — the doubled
  "moving" — its update is composed in its own coordinates
  (body-frame/right composition, the natural Lie-group integration):
  every conflict, with d̂ = current conflict direction and p̂ = previous
  one, both re-expressed in the current frame (x_rel = Im(F† x F)),
  F ← normalize(F · exp(wedge(p̂_rel, d̂_rel)/2)).
  Per-literal torsion accumulates **frame-relative**:
  Ω_ℓ ← γΩ_ℓ + β · wedge(û_rel, d̂_rel), û = ℓ's living direction.

  Why this attacks the measured death mode directly: v1/v2 computed
  the wedge in fixed world coordinates, making "aligned with Δ̂" the
  zero of the signal — and the update rule drives everything to align
  with Δ̂. In the moving frame the zero is "co-rotating with the
  conflict flow"; a literal that merely follows the flow reads zero,
  one that rotates against the transported frame accumulates holonomy.
  Alignment no longer kills the signal; only perfect co-rotation does.

- **Torsion readout, kept in the x/x′ conjunction of v3**: the
  per-variable scalar is the polarity DISAGREEMENT of frame-relative
  torsion, ρ_v = ‖Ω_{+v} − Ω_{−v}‖ — no Ψ, no sandwich readout, so
  the v2 identity-collapse pathway does not exist here either.
- **Delivery: anti-ambiguous only** (v3 measured additive injection
  strictly worse in every configuration; that question is closed).
  Tie-break scalar T_v inside the 10⁻⁶ near-tie band:
  - **MF1**: T_v = θ_v/π + ρ_v (pair angle + frame torsion).
  - **MF2**: T_v = ρ_v (frame torsion replaces the pair angle).

## Grid (3 new configs; v1/v3/baseline rows reused from stored results)

1. **CTRL**: β = 0, no pair terms, no tie-break — the plain
   fossil+living+λχ configuration. This is v3's declared attribution
   control (and Phase 3's never-run S3-halted ablation), legitimately
   in-grid here: it decides whether v3-PA's total improvement over v1
   came from the tie-break or from removing the rotor machinery.
   Pre-registered reading: CTRL total ≈ v3-PA's 23 586 ⇒ the rotor
   removal was the improvement; CTRL ≈ v1's 24 599 ⇒ the tie-break was.
2. **MF1** (θ + ρ tie-break, moving-frame rotor, β = 0.1).
3. **MF2** (ρ-only tie-break, moving-frame rotor, β = 0.1).

B13′, seeds 0–4, cap 100 000, median decisions — apparatus unchanged.

## Gates

- **W1 (liveness probe, before benchmark)**: on the r3sat probe —
  frame actually moves (‖F_biv‖ > 10⁻² after solve), ρ spread across
  variables > 10⁻², MF tie-break re-decides ≥ 1 time. php exempted
  from the re-decision criterion per v3's pre-declared family
  asymmetry (θ and any living-state signal collapse there in aligned
  stretches). Fail → halt, report, don't run.
- **W2 (primary)**: best MF config beats EVSIDS on ≥ 7/13.
- **W3 (floor)**: ≥ 11/13 vs Random.
- **W4 (the operator's question)**: best MF config > v3-PA's 5/13 —
  does the restored, moving-frame rotor add wins to the current setup?
- **No-rescue**: grid final for v4.

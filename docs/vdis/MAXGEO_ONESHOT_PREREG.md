# MAX-GEO one-shot — maximal hyperbolic-hypercomplex geometry, pre-registered

**Operator: an explicit indulgence — "perform the hyperbolic spin
swirling in a n-manifold ... moving moving frame, as a one-shot test ...
keep scientific safeguards." Granted as a pre-registered one-shot with a
STRONG-NEGATIVE prior. Committed before the run.**

## The config (poetry decoded to existing machinery, maxed)

MAX-GEO = every geometry mechanism in the codebase, on at once, at full
hyperbolic curvature:
- **hypercomplex**: algebra H (quaternions, m=4).
- **hyperdimensional**: dim=32 (D=8 slots; S3.7 budget dim≤64 respected).
- **hyperbolic (not 2D/Euclidean)**: c=1.0 → κ=−1, a genuinely curved
  Poincaré ball, not the c=0 degenerate.
- **spin / swirling**: β=0.1 rotor channel + `moving_frame=True` (Cartan
  frame, body-frame "moving moving" composition) + `torsion_anchor=True`
  (prime phases precessing in the frame).
- **fiber-bundled / emergent**: the tangent-state × rotor decomposition
  (base × fibre) already is this; nothing new invented.
- decision scalar carries it all: λ_τ=0.1 (torsion), λ_χ=0.1 (χ),
  `tie_break_frame=1.0` + `tie_break_pair` (frame-torsion ρ and pair-θ
  delivered anti-ambiguously).
- "quantum holoportation": no computable contract — honestly dropped,
  not faked.

Verified pre-run: composes, solves correctly (SAT models valid), frame
genuinely moves (|F_biv| 0.58–0.84).

## Strong-negative prior (stated before results, per safeguard)

Eight generations establish: the gyrovector geometry has **never once
moved the decision scalar favorably**; every win cashed out to a
classical non-geometric mechanism (degree branching, Lagrange
diversification, prime symmetry-break). **Predicted: MAX-GEO loses to
degree on every family, and loses to EVSIDS/LRB on random-3sat.** A win
would be genuinely surprising and would reopen the geometry line; the
prior says it won't.

## Safeguards

- Fresh instances (seeds 500+), never used.
- Correctness: every SAT answer model-checked; UNSAT vs expected.
- Real bar: compared to EVSIDS, LRB, and **degree** (the validated
  winner), not just the weakest baseline.
- One-shot: config frozen, no tuning, no-rescue, no second config.
- Decisions-to-solve on the Python reference solver (not wall-clock).

## Instances & configs

- random-3sat n=90 seeds 500–509 (10 fresh); pigeonhole 5–8; mutil_8.
- Configs: EVSIDS, LRB, degree, MAX-GEO. Seeds 0–4, cap 100 000.

## Prediction ledger

- **M1**: MAX-GEO does NOT beat degree on random-3sat aggregate.
- **M2**: MAX-GEO does NOT beat EVSIDS on random-3sat win-count (≥ 6/10).
- **M3**: on pigeonhole, MAX-GEO ≈ prior geometry configs (no php crack;
  the prime precession is present but was marginal in v4).
- Any M-prediction failing = a surprise worth a follow-up; all holding =
  the geometry line closes, indulgence honored with a clean negative.

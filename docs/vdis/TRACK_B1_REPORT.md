# Track B1 final report — VDIS hypercomplex gyrovector decision heuristic

**Verdict: negative result, reported as such per S4's own standard
("a publishable negative result in the IGBundle tradition").** The
pre-registered primary prediction failed; the sanity floor also failed
by one instance, triggering S3 after a debugging pass found no
implementation bug. The machinery is correct — the physics did not
deliver on this benchmark.

## Predictions table

All rows EMPIRICAL, evaluated exactly as pinned in `PHASE_3_PREREG.md`
(commit `011d001`, committed before any run). Code under test:
`6339c6f`. Seeds 0–4 throughout. Raw data:
`docs/vdis/scripts/phase3_results.jsonl` (715 runs, 0 capped, 0
verdict disagreements).

| Prediction | Pinned threshold | Measured | Verdict |
|---|---|---|---|
| P1 (primary): best VDIS beats EVSIDS, decisions-to-solve | ≥ 7/13 | 6/13 (VDIS-H, λχ=0.1) | **FAIL** |
| P2 (sanity floor): winner beats Random | ≥ 12/13 | 11/13 | **FAIL → S3** |
| P3 (rotor ablation degrades P1) | ≥ 1 instance | not run (S3 halt); λτ toggle inside the sweep changed **0** decisions, τ spread ≤ 1.8×10⁻¹⁰ | **moot — channel inert** |
| P4 (per-family κ beats global κ=−1, held out) | ≥ 2/3 families | not run (S3 halt) | **not evaluated** |

## Ablations (what the sweep itself established)

- **λτ (torsion): decision-identical at 0 vs 0.1, both algebras.** For
  A=C this was PROVED in Phase 2 (commutative algebra ⇒ τ ≡ 1). For
  A=H it is measured: Ψ never leaves the identity's neighborhood
  (bivector part ≲ 2×10⁻⁴) because the S3.2 bump aligns every
  literal's tangent with Δ̂_C, extinguishing the wedge that feeds Ω and
  Ψ. Third appearance of the state-proportionality failure motif
  (Phase 1: absorbing fixed point at t=0; Phase 2: living-axis
  stillbirth without ε-init; Phase 3: torsion self-extinction).
- **λχ (clause-length prior): worth −35 total median decisions on H
  (24 599 vs 24 634), nothing on C.** Marginal at best.
- **C vs H**: C had lower total decisions (20 043 vs 24 599) but fewer
  wins vs EVSIDS (5 vs 6) — H is more often better, C less often
  catastrophic.

## Per-family breakdown (B13′, winner vs EVSIDS, median decisions)

| Family | Instances | VDIS wins | Pattern |
|---|---|---|---|
| pigeonhole | 4 | 1 (php_5_4, noise-level) | Degrades with size: +6% (php_6), +103% (php_7), +271% (php_8) |
| random-3sat n=100 | 3 | 3 | −43%, −11%, −24% — consistent wins at the largest size |
| random-3sat n=75 | 3 | 1 | −49% / +79% / +67% — mixed |
| random-3sat n=50 | 3 | 1 | −37% / +224% / +127% — high variance on easy instances |

LRB's profile is qualitatively the same shape (7/13 vs EVSIDS, wins
concentrated on larger random instances, catastrophic on pigeonhole:
19 176 vs EVSIDS's 5 099 on php_8_7) — VDIS-H behaves like a noisy
LRB-class heuristic, not like a broken one.

## What VSIDS's scalar fossil was actually missing

Written only from measured deltas, per §9. On the largest
phase-transition random 3-SAT instances (n=100), the living field
bought 11–43% fewer median decisions than EVSIDS, on all three
instances, robustly across every H-variant λ setting — that, plus a
−37%/−49% at smaller n, is the entire measured upside of hypercomplex
state on this benchmark. Everything else the fossil was "missing" it
did not, in fact, miss: the torsion/rotor channel contributed zero
decisions of difference (τ spread ≤ 1.8×10⁻¹⁰); the χ prior moved 35
total decisions; and on structured instances the extra state was
actively harmful, degrading pigeonhole performance by up to +271% and
easy-instance consistency by up to +224%. The honest headline from
Phase 2's own framing — "hyperbolic radial mass suffices" — turns out
to be generous: on this evidence the radial mass suffices *and* the
rest of the apparatus either cancels itself out by construction
(state-proportional updates self-extinguish — the recurring failure
motif of all three phases) or trades structured-instance performance
for random-instance performance in a way EVSIDS's scalar already
dominates in aggregate (10 163 vs 24 599 total median decisions).

## Stop-condition disposition

S3 (P2 fail after debugging pass) is the operative halt. The debugging
pass (PHASE_3.md) found: 0 capped runs, 0 verdict disagreements,
degenerate config still bit-exact vs EVSIDS, and both P2 losses
explained by per-seed data — one pure noise (EVSIDS itself loses that
instance to Random), one genuine ε-init variance on a trivially easy
instance. Calibration note for any successor protocol: LRB, a real
published heuristic, also fails this P2 threshold on this set (11/13)
— the sanity floor as pinned is failable by legitimate heuristics via
two trivial instances. That observation is recorded for future design;
it does not soften this protocol's verdict.

P3/P4 stages and the suite-context run were not executed (the runner
supports them; overruling S3 is the operator's prerogative, not the
agent's).

## Where this leaves Track B1

- The gyrovector plumbing is validated to an unusually high standard:
  bit-exact EVSIDS reduction (S4 gate), 142 gyro property tests, 19
  algebra tests against an independent Cl(3,0) product table, zero
  numerical failures across every run at c up to 2.
- The pinned S3.1–S3.4 dynamics have a recurring structural defect:
  every state-proportional term (Δ_C from t, the wedge from t̂,
  Ψ from Δ̂-rotors) decays toward inertness; the only component that
  demonstrably works — the fossil axis — is the part that reduces to
  EVSIDS, plus an ε-noise halo whose measured net effect is
  positive only on large phase-transition random instances.
- Any revival should start from the one real signal (the n=100
  random-3-SAT wins) and a reformulated, non-self-extinguishing
  torsion source — as a new pre-registered protocol. The frozen
  κ-table transfer test (P4) and the parked Laplacian-feature
  experiment remain available as designed follow-ups.

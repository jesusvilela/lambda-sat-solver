# VDIS v2 pre-registration — reviving the torsion channel

**Operator instruction (verbatim): "try again using 360 and 360 orto
and primes". Committed before any v2 benchmark run.**

## Interpretation (pinned before implementation)

Track B1's measured failure: the S3.4 wedge t̂_ℓ ∧ Δ̂_C
self-extinguishes because the S3.2 bump aligns every literal's tangent
with the conflict field (τ spread ≤ 1.8×10⁻¹⁰, Ψ at identity — Phase 3
report). The operator's three ingredients are read as the structured
counterpart of the Phase 1 fossil fix — a state-INDEPENDENT torsion
source that cannot self-extinguish:

1. **"360"** — each variable gets a fixed anchor phase on the full
   circle: θ_v = 2π·(p_v mod 360)/360, realized as the bivector
   (cos θ_v, sin θ_v, 0). Negative polarity is antipodal:
   θ_{−v} = θ_v + π.
2. **"primes"** — p_v is the v-th prime. Prime spacing mod 360 spreads
   anchors incommensurately: no arithmetic subfamily of variables
   shares a phase pattern, so anchors never collectively re-align —
   the property random ε-init has statistically, made deterministic
   and reproducible.
3. **"360 orto"** — the state wedge uses the ORTHOGONALIZED tangent:
   û_⊥ = normalize(u − (u·d̂)d̂) where u = vec(t̂), d̂ = vec(Δ̂). The
   wedge magnitude is then ~1 whenever any orthogonal component exists
   at all, removing the alignment-death by construction.

If this reading is wrong, the operator can say so; it is recorded here
precisely so the result can't be quietly re-fitted to a different
reading afterwards.

## Pinned v2 mechanics (deltas to the Phase 2 heuristic; all else frozen)

- **Anchor variant (A)**: on each conflict, every ℓ ∈ C additionally
  receives Ω_ℓ += β·anchor_ℓ — "this literal participated, with its
  own fixed phase," the fossil-axis trick lifted to the rotor channel.
  Ψ's update source becomes the anchor signature of the learned
  clause: r_C = exp(mean_{ℓ∈C}(anchor_ℓ)/2), Ψ ← normalize((1−μ)Ψ +
  μ·r_C). τ_ℓ then measures alignment of ℓ's accumulated rotor with
  the running phase-signature of *which variables have been
  conflicting* — a signal that cannot collapse to identity while
  conflicts occur.
- **Ortho variant (B)**: the state wedge uses û_⊥ as above (v1 Ψ rule
  retained).
- **A+B**: both.
- Algebra **H only**: τ ≡ 1 for C is PROVED (Phase 2), so a torsion
  revival on C is a contradiction in terms.

## Benchmark (identical to Phase 3 where possible)

- B13′, seeds 0–4, cap 100 000, median decisions — unchanged.
- EVSIDS / Random / LRB / VDIS-v1-winner comparators: **reused from
  `phase3_results.jsonl`** (identical instances, seeds, code) — not
  rerun.
- v2 sweep (6 configs): {A, B, A+B} × λ_τ ∈ {0.1, 0.3}; fixed
  λ_χ = 0.1, β = 0.1, dim = 32, κ per family table, other constants as
  Phase 2. λ_τ = 0.3 is included because v1's grid never got to test a
  strong torsion weight on a live channel.

## Gates and success criteria

- **Q1 (liveness gate, before the full run burns compute)**: on two
  probe instances, measured τ spread > 10⁻³ and the λ_τ toggle changes
  at least one decision count. If Q1 fails the design is dead on
  arrival; halt and report without running the benchmark.
- **Q2 (primary, same bar as P1)**: best v2 config beats EVSIDS
  (median decisions) on ≥ 7/13.
- **Q3 (recalibrated sanity floor)**: best v2 config beats Random on
  ≥ 11/13. Recalibration justified by Phase 3 measurement, recorded
  there before this prereg existed: LRB, a real published heuristic,
  scores 11/13 on this set, and EVSIDS itself scores only 12/13
  because Random's median wins php_5_4 by luck. A floor that a real
  heuristic fails is measuring the floor, not the heuristic. 11/13 is
  the highest bar a legitimate non-EVSIDS heuristic has demonstrated.
- **Q4 (the torsion question, v2's reason to exist)**: the best
  A-variant or A+B-variant beats the λ_τ-matched B-only variant on
  ≥ 1 more instance vs EVSIDS — i.e. the anchor channel itself, not
  just orthogonalization, contributes. (v1's P3, now answerable.)
- **No-rescue rule**: this grid is final. If v2 fails Q2, that is the
  second and, absent a new operator instruction, final negative for
  this line.

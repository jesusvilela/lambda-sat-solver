# VDIS Track B1 — Phase 2: Full VDIS (C and H variants, rotor channel, Ψ memory)

**Status: gate PASSED on both criteria.**
Gate (per §5): "Runs whole suite without numerical failure; per-conflict
budget met."

Preceded by the operator's decision closing Phase 1 at float64 exactness
(recorded in `PHASE_1_PATCH.md`).

## What was built

- `backend/vdis/algebra.py` — C (m=2) and H (m=4, ≅ Cl(3,0) even
  subalgebra) operations: products, conjugation, bivector exponentials
  (rotors), sandwiches, wedges. Everything broadcasts over leading axes
  so per-conflict work is vectorized numpy, not Python loops.
- `backend/vdis/vdis_heuristic.py` — full VDIS per §3: D·m-dimensional
  tangent state (array-backed), rotor/torsion channel (§3.4), global
  conflict spinor Ψ, decision scalar (§3.6), χ term, Möbius decay at
  c>0 vectorized (§3.3/§3.7).
- `docs/vdis/scripts/phase2_suite_run.py`, `phase2_budget.py`,
  `phase2_curvature_bandit.py` — the gate runs and the §3.5 offline κ
  sweep, all reproducible.
- Tests: 19 algebra property tests (`test_vdis_algebra.py`) closing the
  §6 rotor requirements deferred from Phase 1, + 16 full-config behavior
  tests (`test_vdis_full.py`). Suite total: 474 passing.

## PROVED (property tests / formal argument in-repo)

- R R† = 1 for R = exp(bivector), all magnitudes tested incl. ~0.
- Rotor action preserves norm and fixes the scalar part.
- `quat_mul` agrees with an **independently implemented** full Cl(3,0)
  blade product table on random even elements (200 samples), under the
  pinned identification i=e₃e₂, j=e₁e₃, k=e₂e₁. This cross-check earned
  its keep immediately: the first draft used the naive "+cross product"
  wedge convention, which is inconsistent with any orientation-uniform
  quaternion↔bivector mapping — the product-table test failed and the
  convention was corrected to −cross (`wedge3` docstring has the
  derivation). A same-formula-tested-against-itself test would have
  passed silently.
- Rotor conjugation is the identity on the commutative algebra C
  (r a r̄ = a·|r|² = a), so **the §3.4 torsion channel carries zero
  information for A=C** — τ_ℓ ≡ 1 identically. It only does anything
  for H. This is a triviality once stated, but it means P3's rotor
  ablation is only meaningful on the H variant, and "C with β>0" and
  "C with β=0" differ only through Ψ's drift, not through τ.
- The degeneracy gate (S4) still passes bit-for-bit on the rewritten,
  array-backed implementation — the Phase 1 code path is preserved
  exactly (elementwise decay by the same γ, identical bump chain,
  identical pick scan) and `test_vdis_degeneracy.py` enforces it.

## The absorbing fixed point, one level up (and its negative control)

Phase 1's failure was: state-proportional forcing from a zero initial
condition stays exactly zero. The identical argument applies verbatim
to Phase 2's living axes (1..dim−1) *and* to the rotor wedge
(t̂_ℓ ∧ Δ̂_C is built from current state): from exact zero, the living
field and the rotor channel would both be stillborn, and "full VDIS"
would be an expensive re-implementation of the fossil axis.

Fix, pinned: axes 1..dim−1 initialize to ε·N(0,1), ε=10⁻³, seeded
(the spec's own state decomposition, u_ℓ ∈ S^{Dm−1}, presumes a
direction exists). Axis 0 initializes to exactly 0.0, so the fossil
dynamic — and the degeneracy gate — are untouched.

EMPIRICAL, both directions tested (`TestLivingFieldActivates`):
- with ε-init, living axes *move from their seeds* once conflicts occur
  (dynamics active, not just frozen noise);
- negative control: with `living_eps=0`, after a full UNSAT solve with
  real conflicts, every living axis is still exactly 0.0 — confirming
  the ε-init is the thing breaking the fixed point, not some other
  Phase 2 change.

## Pinned implementation choices (spec gaps, filled explicitly)

1. **Ω decay**: §3.4 gives no decay for the bivector memory; without
   one |Ω| grows ~β per conflict without bound and the rotor angle
   aliases mod 2π. Pinned: Ω decays by the same γ as t, bounding |Ω| by
   ~β/(1−γ).
2. **Ψ update**: "EMA of Δ̂_C rotors" made concrete as: rotor between
   consecutive conflict directions, r_C = exp((d̂_prev ∧ d̂_curr)/2),
   Ψ ← normalize((1−μ)Ψ + μ·r_C), μ=0.05.
3. **Vector extraction for wedges**: tangent → normalized slot-sum
   algebra element → grade-1 vector (imaginary part for H, (re,im) for
   C) → normalized.
4. **σ = identity**: monotone (so ordering-equivalent to any sigmoid)
   and it cannot round two distinct scores into a new float64 tie the
   way a compressive sigmoid could — directly informed by the Phase 1
   tie-sensitivity diagnosis.
5. **χ_ℓ = 2/(mean length of clauses containing ℓ)** (∈(0,1], 0 if
   absent). The spec's "curvature-compatibility with κ_f" has no
   formula; inventing a κ coupling here would be an unvalidated bridge
   (→ the κ dependence enters only through which κ the §3.5 sweep picks
   per family). HYPOTHESIS: χ as defined carries useful signal at all —
   it is swept via λ_χ in Phase 3 and can be ablated to zero there.

## Gate part 1 — whole suite, no numerical failure: PASS (EMPIRICAL)

`phase2_suite_run.py`, quick (30) + medium (63) suites, full config
(dim=32 ⇒ D=16/A=C and D=8/A=H, κ=−1, β=0.1, λ_τ=λ_χ=0.1, seed=0),
conflict cap 50 000:

| Variant | Instances | Numerical failures | Wrong answers | Capped | Wall time |
|---|---|---|---|---|---|
| VDIS-C | 93 | 0 | 0 | 0 | 89 s |
| VDIS-H | 93 | 0 | 0 | 0 | 101 s |

Correctness cross-check: every SAT answer model-checked against the
formula; every answer compared against the suite's expected label where
one is known. The §6 tripwire (`NumericalInstabilityError`) never fired
at c=1 anywhere in either run. (The script does not aggregate a total
conflict count, so none is quoted here.)

## Gate part 2 — per-conflict budget: PASS (EMPIRICAL, with margin noted)

`phase2_budget.py`, 5 conflict-heavy instances (php_6/php_7, three
random-kSAT at the phase transition). §3.7's sentence is ambiguous, so
both readings were measured:

| Metric | EVSIDS | VDIS-C | VDIS-H |
|---|---|---|---|
| in-solver ms/conflict | 0.141 | 2.250 (**15.9×**) | 2.715 (**19.2×**) |
| heuristic-only µs/conflict | 4.8 | 1783 (369×) | 2213 (459×) |

The gate reading — "per-conflict wall time **in the reference solver**"
— is the in-solver ratio, and both variants are under 20×. Honestly
stated: VDIS-H passes with almost no margin (19.2×), and the
heuristic-only cost is ~400× EVSIDS (dominated by the per-decision
score computation: one (2n+1)×32 matvec plus rotor exp/sandwich per
pick). If Phase 3's larger instances push the in-solver ratio over 20×,
§3.7's prescribed remedy is reducing D — noting now, before Phase 3,
that D is *not* where the time goes (the matvec is, and it scales with
n·dim), so a D reduction will roughly halve the heuristic cost at best.

Context, recorded not interpreted: on these 5 instances the full config
needed ~2.2× more conflicts than EVSIDS (8096/8796 vs 3803). Whether
full VDIS beats EVSIDS on search quality is exactly P1–P4's question
and is deferred to Phase 3's pre-registered protocol — this number is
neither evidence for nor against until the κ table and λ sweep are in
place.

## §3.5 curvature sweep (offline, per Correction 2)

`phase2_curvature_bandit.py`: exhaustive offline sweep, κ ∈ {−0.25,
−0.5, −1, −2} × {C, H} × all quick+medium instances, keyed by suite
category, winner per (algebra, family) by (fewest capped, then fewest
total decisions), frozen into `backend/vdis/kappa_table.py`. No online
adaptation. Note the "bandit" framing degenerates here: at this suite
size every arm is pulled exhaustively, so it is simply a frozen argmin.

Results: see `backend/vdis/kappa_table.py` (generated by the script,
values pasted verbatim from its output; committed separately once the
sweep run finishes — this report's gate sections do not depend on it).

## Deviations / not done in this phase

- No proof logging in refsolver (PARKED per §8), so UNSAT answers are
  cross-checked against expected labels, not DRAT-verified.
- The per-conflict budget was measured on 5 instances, not the whole
  suite (timing the whole suite per-variant would triple gate-run time
  for no additional decision value; the chosen instances are the
  conflict-heaviest families).
- P3's rotor ablation, the λ sweeps, and any claim that the rotor/Ψ/χ
  machinery *helps* are Phase 3 scope. Everything in this phase is
  plumbing-verified, not performance-verified. VDIS-beats-EVSIDS
  remains HYPOTHESIS.

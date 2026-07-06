# VDIS Track B1 — Phase 1: Gyro-op library + degeneracy test

**Status: gyro-op library PASSED. Degeneracy gate (S4) FAILED — diagnosed,
not patched. Per stop condition S2, Track B1 halts here pending a
decision from the spec's author.**

## Gyro-op library (`backend/vdis/gyro_ops.py`)

Closed-form Mobius/Poincare-ball operations (Ganea, Becigneul & Hofmann
2018 formulas), pure numpy, no `geoopt`. Convention: takes curvature
magnitude `c = -kappa >= 0` rather than signed kappa, documented in the
module docstring, specifically to avoid a sign-convention bug.

**142/142 property tests pass** (`test_gyro_ops.py`), across every
combination of dim ∈ {1,2,4,8} (covering D=1 through H at D=2) and
c ∈ {0, 0.25, 0.5, 1, 2}:
- right identity (`x ⊕ 0 = x`)
- left inverse (`(−x) ⊕ x = 0`)
- gyrocommutativity (`x ⊕ y = gyr[x,y](y ⊕ x)`)
- exp/log round trip at arbitrary points and at the origin, to 1e-6
- parallel-transport isometry (`‖PT(v)‖_x = ‖v‖_0` in the Riemannian metric)
- exact Euclidean recovery at c=0, and continuity approaching c=0
- numerical tripwire raises `NumericalInstabilityError` on conformal-factor
  collapse at the ball boundary, rather than returning NaN/Inf

One test-calibration bug on my part (boundary point wasn't extreme enough
to trigger the tripwire) — fixed, not a `gyro_ops.py` bug. Gyration is
implemented via its defining identity (three `mobius_add` calls) rather
than an independently-derived closed form, specifically to make its
correctness depend only on `mobius_add`'s correctness rather than a
second, separately-fallible formula.

**Deferred to Phase 2** (not this phase's scope): the Clifford-algebra
rotor tests listed in §6 (`R R† = 1`, rotor-action norm preservation,
Cl(3,0) product table) — nothing rotor-related exists yet; the rotor
channel is explicitly §3.4/Phase 2 scope.

## Degeneracy test (S4): FAILED

Built `VDISHeuristic` (`backend/vdis/vdis_heuristic.py`) in the pinned
degenerate configuration (A=R, D=1, c=0, beta=0, lambda_tau=lambda_chi=0)
and ran the exact §4 protocol against `EVSIDSHeuristic` on the 30-instance
quick eval suite (exceeds the ">= 20 instances" requirement).

**Result: 22/30 instances agree, 8/30 diverge.** Every divergence is the
same shape: same variable, opposite polarity, at some decision after the
first conflict.

**Root cause, confirmed empirically, not just derived:** the S3.1/S3.2
conflict-bump rule as pinned is

```
Delta_C = sum_{l in C} alpha_l * t_l      (uses literals' CURRENT tangent state)
t_l <- log_0( exp_{V_l}( eta * PT_{0->V_l}(Delta_C) ) )
```

At c=0 this reduces exactly to `t_l <- t_l + eta * mean(t_l' for l' in C)`.
If every literal starts at `t_l = 0` (the natural initial condition — no
other initialization is specified anywhere in the pinned spec), then
`Delta_C = mean(0, 0, ..., 0) = 0` on the *first* conflict, the bump is a
no-op, and every literal touched remains at exactly 0. This is an
**absorbing fixed point**: nothing in the update rule can ever move a
literal off zero, because the forcing term is itself proportional to
the (zero) state. I confirmed this directly rather than trusting the
derivation: ran the solver to completion (1 real conflict occurred) and
checked every literal's tangent state afterward — all exactly `0.0`.

Contrast with EVSIDS: it adds a **fixed** increment (`var_inc`, which
itself grows every conflict) regardless of a variable's current score,
so it discriminates from the very first conflict. VDIS's proportional
update cannot bootstrap the same way from a zero initial condition.

A second, independent gap compounds this: my implementation has no
phase-saving equivalent, so whenever two literals tie (which, given the
above, is always), polarity defaults to positive rather than remembering
assignment history the way EVSIDS's `saved_phase` does. This explains
the specific "same variable, opposite polarity" shape of every mismatch.

**What this is not:** a `gyro_ops.py` bug. The 142 property tests
isolate that module and all pass. The failure is specifically in how
`vdis_heuristic.py` uses S3.1/S3.2's update rule from a zero initial
condition — either the spec intends a nonzero initialization that isn't
written down, or `Delta_C` isn't meant to be computed from literals'
*current* state, or there's a phase-saving mechanism implied but not
specified. I have not guessed at a fix and re-run to force a pass —
per the protocol's own discipline (§5 gate table, and the spirit of
§7's "do not iterate hyperparameters beyond the pre-declared sweep to
rescue P1"), silently patching the update rule to make this test green
would defeat the point of pre-registering it.

## Disposition

Test is marked `xfail(strict=True)` with this diagnosis as its reason —
visible and specific, not deleted, and it will loudly XPASS (demanding
attention) if a corrected update rule is later checked against it.

**Per stop condition S2 ("degeneracy gate unfixable → halt Track B1
entirely"), I am halting here** rather than proceeding to Phase 2. This
is a decision point for the spec's author, not something I should
resolve unilaterally: either (a) the update rule needs a specific,
deliberate correction (e.g., a nonzero initial radial mass, or an
explicit fixed-increment term independent of current state, plus an
explicit phase-saving analogue), in which case Phase 1 should be
re-run against the corrected rule before Phase 2 starts, or (b) this is
accepted as a genuine, informative negative result about the pinned
formulation and Track B1 stops here.

## Test suite

287 (pre-Phase-1) + 142 (`test_gyro_ops.py`) = 429 passing, 1 xfailed
(the degeneracy gate, as above).

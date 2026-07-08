# Pipeline review & traceback — findings and fixes

*A full read of the solve pipeline for errors and omissions before the 2026 SOTA
run. Charter: verify before trust; measure before optimizing; record honest
negatives. Three findings, all resolved; one soundness audit, clean.*

## F1 — omission: the production middleware did not use the frames (FIXED)

`SolverMiddleware._handle_solve` (`backend/middleware.py`) — the actual production
path — ran only a **binary-clause** pre-check, then went straight to Kissat. The
sound parity/counting/coupled frames lived **only** in the benchmark script's own
`middleware_solve`. So "the frame-aware middleware" was a benchmark artifact; the
shipped class threw away two of its three sound frames and the whole coupling.

**Fix**: wired `frame_solve_scouted` into `_handle_solve` as the sound algebraic
pre-check. The production middleware now decides any frame-owned instance (2-SAT,
GF(2), counting, or their coupling) with a certificate and no search — UNSAT by a
channel refutation, SAT only with an independently re-verified model — and falls
through to certified Kissat exactly as before on everything else. Non-destructive:
all integration/middleware tests still pass.

## F2 — performance bug: the fabric read exact |Aut| (FIXED, ~900×)

`fabric()` reads a `gyration` thread = `hyperbolic_depth`, which called
`poincare_radius` → `exact_symmetry_log2` → **Schreier-Sims exact automorphism
counting**. On a highly symmetric instance that is a real search: **php7 took
11.3 s** for a single `fabric()` call, making the fabric descriptor — and the whole
parametric model built on it — unusable at any scale.

**Fix**: added an `exact=False` fast path to `poincare_radius`/`hyperbolic_depth`
(the cheap 1-WL upper bound, which `scout` already uses), and pointed `fabric()` at
it. The placement stays monotone (symmetric → centre, rigid → ∂∞) and the value is
preserved (php7 gyration 0.01 either way). **php7 fabric(): 11 459 ms → 12.5 ms,
~900×.** Measured, values checked.

## F3 — optimization: skip the pre-pass on structureless instances (MEASURED)

The coupled router runs the full frame pre-pass (2–3 XOR extracts + a coupling
loop) even on unstructured random-3SAT, which no frame can decide, before punting
to CDCL.

- **First attempt — the full `scout` as the gate — was measured a NET LOSS**
  (0.28×, i.e. 3.6× *slower*): `scout`'s `symmetry_partition` (1-WL) costs more than
  the pre-pass it saves. Recorded as an honest negative rather than shipped.
- **The light structural gate wins**: one XOR extract + a cheap ALO/AMO scan gates
  the same tunnel at **~3.3× faster** on the pre-pass, and is sound — it punts only
  when there is no XOR structure *and* no pigeonhole-shaped counting structure, so
  nothing the frames or coupling would decide is lost. Differential-tested against
  `frame_solve_coupled`: **0 verdict mismatches, 0 frame-wins lost** across 40
  instances. Shipped as `frame_solve_scouted`.

**Honest scope**: on random-3SAT the middleware's *remaining* overhead vs raw Kissat
is the **DRAT certification** of the UNSAT proof (the value-add), not the frame
pre-pass — which `frame_solve_scouted` has already reduced to ~1 ms. The gate
removes wasted algebraic work; it does not (and should not) remove certification.

## Soundness audit — clean

Read the three frames and the coupling for correctness:

- **implication** (`check_binary_clauses`): SCC refutation, sound.
- **parity** (`gf2_xor_refutation`/`_solve`, `_parity_propagate`): forward
  elimination for UNSAT; a "forced" literal is only emitted from a weight-1 reduced
  GF(2) row (genuinely entailed); SAT models are re-verified against the CNF.
- **counting** (`pigeonhole_counting_refutation`): disjoint ALO ≥ k, each AMO-clique
  component holds ≤ 1 (clique check enforced), so k > m ⟹ UNSAT — sound.
- **coupling** (`frame_solve_coupled`): every exchanged literal is entailed; UNSAT is
  a channel refutation; SAT only on a re-verified completion. Termination: each
  Gaussian reduction strictly raises the lowest set bit; the round loop is monotone
  in `|fixed|`.

No correctness defects found. The verdicts remain certified end-to-end.

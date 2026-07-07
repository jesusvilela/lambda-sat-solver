# Public research claims — proven / measured / speculative

*One page stating exactly what this repository claims, at what confidence, so a
reader never has to guess which parts are theorems, which are benchmarks, and
which are honest lenses. This is the `docs/CHARTER.md` discipline applied to the
public surface: **a name is not a proof.***

## What this is (one sentence)

> A **certified SAT middleware** around Kissat — Kissat is *outside* the trusted
> computing base; SAT is checked by model replay, UNSAT by DRAT/LRAT proof
> tooling — used as a **laboratory for solver-independent SAT hardness**: three
> sound algebraic frames (implication / parity / counting), a coupled router, and
> an executable ladder of intrinsic hardness invariants that must survive tests.

It is **not** a claim to have "solved SAT hardness" or to beat CDCL in general.

## PROVEN (theorem-backed, and the code computes against the theorem)

- **Frame soundness.** Every frame verdict is sound: 2-SAT UNSAT by
  implication-graph SCC (Aspvall–Plass–Tarjan); parity UNSAT by GF(2)
  inconsistency, SAT only with an independently re-verified model; counting UNSAT
  by the pigeonhole magnitude bound. The coupled router only ever emits an
  entailed literal or a channel refutation (Nelson–Oppen combination).
- **Hardness carriers.** `min_refutation_width` computes against Ben-Sasson–
  Wigderson (width lower-bounds resolution size); `nullstellensatz_degree`
  against Clegg–Edmonds–Impagliazzo (PC degree lower-bounds PC size). NS-degree
  and width are **incomparable** (PHP: NS 4 > width 2; Tseitin K4: NS 3 < width 4)
  — a corrected claim, tested both directions.
- **Exact automorphism order.** `|Aut|` by orbit-stabilizer / Schreier–Sims,
  verified against brute force (500+ instances) and the closed form
  `PHP(n→n−1) = n!·(n−1)!` through php6; large groups fall back to a sound bracket.
- **Capture-avoiding β-reduction.** `lambda_sat._subst` alpha-renames to avoid
  capture (`(λx.λy.x) y → λy'. y`), tested — the object-level lambda semantics are
  correct, not naive.
- **Hyperbolic-programming facts.** `e_k` is hyperbolic; `D_1 e_k = (n−k+1)e_{k−1}`
  (the derivative-relaxation tower's infinitesimal generator); `det` recovers
  matrix eigenvalues — all tested against the cited theorems (Gårding, Renegar,
  Brändén).

## MEASURED (benchmarked, reproducible scripts, not proven-in-general)

- **SOTA bench** (`sota_benchmark.py`, Kissat 4.0.4 + CaDiCaL, 40 instances):
  middleware **40/40 · PAR-2 0.06 s · 40/40 certified**, vs Kissat 35/40 (5.36 s)
  and CaDiCaL 36/40 (4.26 s); 26/40 decided by a sound frame with no solver.
- **Symmetry vs phase transition are orthogonal axes**
  (`symmetry_phase_probe.py`): PHP CDCL-time tracks `|Aut|` and **breaking
  symmetry collapses it 2332 ms → 4 ms**; random-3SAT is **rigid (`|Aut|=1`) at
  every α**, hardest at α≈4.26 — criticality, not symmetry.
- **Edge tails** (`edge_tails.py`): 0 soundness violations across the transition,
  the symmetry tail (php13 refuted in 4 ms while Kissat times out from php12), the
  coverage boundary, and the coupling home.
- **In-code optimization**: the frame router is parse-bound; the vectorized
  arity-bucketed extraction is ~1.7–2.8× the pure-Python form, differential-tested
  byte-identical. No metal rewrite is justified at research scale (measured).

## SPECULATIVE (lenses / research substrate — labelled, NOT load-bearing)

Recorded honestly, tied to their status, none claimed to decide SAT:

- The **hypercomplex / hyperbolic / hyperdimensional** geometry as a *lens*
  (octonions, gyrovectors, Cayley–Dickson) — `docs/vdis/` is the generative
  archive, valued by **contribution** (it produced the frames), not equivalence.
- The **synthetic observer** `A†` (Θ/Γ/∇⁻¹/∂∞/R/C/E/J) — built only for the
  SAT-frame task class (`OBSERVER_NOTE.md`); no universal human-replacement claim.
- The **orbifold / hyperbolic mesh** of satisfiability, the **ε>0 dynamic
  remainder**, the **ℝ-side symmetry-adapted SOS/hyperbolic certificate** — open
  directions, not results.

## What we explicitly do NOT claim

- Not P vs NP; not a general SAT algorithm; not "out-engineering CDCL." The frames
  win on **structured** instances (symmetry / parity / counting) and are correctly
  silent on structureless critical instances, where CDCL is irreplaceable.

## Why this matters

Most SAT work treats the solver as the object of study. Here the solver is a
*certified instrument*, and the object of study is **where hardness comes from** —
made executable: every candidate hardness invariant must survive an
input→invariant→action→benchmark contract and a test, and the two proven carriers
(resolution width, Nullstellensatz degree) sit beside a measured account of the
two orthogonal hardness axes (symmetry and criticality). The result is a research
harness where geometric intuition is *forced* to cash out as tested code or be
labelled a lens.

## Trusted computing base (read before trusting a verdict)

Kissat is **not** trusted. A middleware SAT verdict is a model replayed through
`verify_model`; a middleware UNSAT verdict is either a sound frame refutation or a
Kissat proof checked by **drat-trim** (DRAT) / LRAT tooling. **Strict certification
therefore depends on those external proof tools being installed** (the middleware
enforces this at startup for Kissat + DRAT; LRAT is optional). Without them, the
frame verdicts remain sound on their own, but the CDCL-fallback certification
degrades to best-effort — see `README.md` and `backend/proof_checking.py`.

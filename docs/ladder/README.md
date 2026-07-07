# The hardness-lower-bound ladder — index & honest standing

This directory is a research program: find the **intrinsic, solver-independent
object that carries SAT hardness**, climb from cheap-and-wrong to
expensive-and-right, and keep every claim executable. It is *not* a P=NP route,
and every rung says so.

## Where it stands (honest)

- **Two genuine hardness carriers, theorem-backed.** `min_refutation_width`
  (Ben-Sasson–Wigderson: width lower-bounds resolution size) and
  `nullstellensatz_degree` (Clegg–Edmonds–Impagliazzo: PC degree lower-bounds
  PC size). They track but are *distinct*: NS ≥ width on every instance tested,
  and PHP(3→2) separates them (NS 4 vs width 2). Both are exact and
  exponential — the right object is genuinely expensive.
- **A clean, well-measured negative.** No cheap graph-structural scalar
  (`spectral_gap`, degree entropy, `signed_laplacian_frustration`) carries
  random-3-SAT hardness — they are monotone in density, not peaked at the
  transition (Rung 1 / connection-Laplacian addendum).
- **The operator's geometric program, made executable and unified.** The
  sheaf-obstruction *is* bounded resolution width (Rung 2); the zero-divisor =
  rank-deficiency instinct *is* the Nullstellensatz degree
  (RUNG2_ALGEBRAIC — corrected: a carrier for its *own* static system only,
  **incomparable** to resolution width, PHP 4>2 vs Tseitin K4 3<4); the Lie
  telos *is* 𝔤₂ = Der(𝕆) / Moreno's G₂ zero-divisor
  space, real over ℝ (symmetry-adapted SOS) but char-2 obstructed over GF(2)
  (RUNG2_LIE_TELOS); the braid-theta engine / star of closure is the dynamical
  face of the same object — topological QC = BQP, which is *not* believed to
  contain NP (RUNG2_BRAID_THETA). One exceptional object, three faces, each
  real in its own register, none a polynomial SAT algorithm.

## What's proven vs open

- **Proven / measured:** the two size lower bounds (BSW, CEI) as theorems the
  carriers compute against; the Rung-1 negative on our own instances; NS ≥ width
  with PHP separation; the char-2 collapse of the naive symmetry channel.
- **Open / next:** the ℝ-side **G₂-block-diagonalized moment/SOS matrix** on the
  same rank-deficiency operator — the one place the exceptional symmetry is a
  genuine computational lever rather than a name.

## Contracts & evals (the discipline)

Every invariant is pinned to an explicit **input → invariant → action →
benchmark** contract with its theorem-backed part and its honest limit called
out. Contracts cannot silently rot:

- `backend/complexity/contracts.py` — the registry (source of truth).
- `docs/ladder/CONTRACTS.md` — auto-rendered from the registry (a test enforces
  sync).
- `backend/tests/test_ladder_contracts.py` — binds every contract to its
  callable and asserts its contracted claim on small fixtures.

## Rung documents

| doc | content |
|---|---|
| `RUNG1_PLAN.md`, `RUNG1_REPORT.md` | cheap graph invariants do NOT carry hardness (the negative) |
| `RUNG2_REPORT.md` | sheaf-obstruction = min resolution refutation width; connection-Laplacian addendum |
| `RUNG2_ALGEBRAIC_NOTE.md` | zero-divisor = rank-deficiency = Nullstellensatz degree (incomparable to width: PHP 4>2, Tseitin 3<4) |
| `RUNG2_LIE_TELOS_NOTE.md` | 𝔤₂ = Der(𝕆) / G₂ symmetry; real over ℝ, char-2 obstructed over GF(2) |
| `RUNG2_BRAID_THETA_NOTE.md` | braid-theta engine / star of closure = dynamical face; braiding = BQP, not a SAT route |
| `RUNG_SADDLE_NOTE.md` | energy-landscape saddle/barrier structure; ruggedness ≠ hardness, the gate is the separator |
| `HYPERCOMPLEX_DESIGNS_REVIEW.md` | honest review of the operator's computer designs (Berry-braid, symplectic RAM, orbifold, sedenion clock, VDIS channels) + two bridges into the ladder |
| `LEARNINGS.md` | the philosophical arc landed as engineering: each idea tied to its tested artifact; the "Emperor-depth is algebra-relative" corollary → `cross_algebra_depth` (portfolio principle) |
| `FRAME_BENCHMARK_REPORT.md` | the corollary tested on Kissat + CaDiCaL: parity/Tseitin instances are CDCL-exponential but GF(2)-polynomial (~79× PAR-2 via `xor_fraction` routing, soundness 53/53) → `gf2_xor_refutation` fast-path shipped |
| `EDGE_TAILS_REPORT.md` | stress into the tails of the omni distributions (phase-transition α sweep, PHP symmetry tail, parity-coverage boundary, coupling home): **0 soundness violations**; php13 counting-refuted in 4ms while Kissat times out from php12; the honest boundary that the frames never fire on structureless random-3SAT at any α → `docs/ladder/scripts/edge_tails.py` |
| `SOTA_BENCHMARK_REPORT.md` | frame-aware middleware vs raw SOTA CDCL across 5 families: **40/40 solved · PAR-2 0.05s** (Kissat 35/40 · 5.33s, CaDiCaL 36/40 · 4.26s), 40/40 DRAT/model-certified; three sound frames divide the CDCL-hard families |
| `COUNTING_FRAME_NOTE.md` | what survives PHP's collapse against GF(2): the counting/ℤ frame (magnitude, not parity) — PHP as the char-0 dual of Tseitin; `cardinality_check` refutes php12 in 0.44ms |
| `LAMBDA_SAT_NOTE.md` | clashing Lambda ⊗ SAT (Λᴿ): what survived into `lambda_sat.py` (β-reduce → CNF-with-remainder → certified decision) vs what stayed lens; the honest ε=0 scoping |
| `ORBIFOLD_NOTE.md` | satisfiability as a **mesh of orbifolds**: the un-projected verdict (classical bit = `π_truth`) lifted to an orbifold chart = instance + its **isotropy** (CNF automorphisms), bracketed `lower ≤ \|Aut\| ≤ upper` (verified swaps / 1-WL color refinement). Measured payoff: PHP is a high-symmetry orbifold (log₂\|Aut\| → 107 by size), random is rigid → the counting frame is *quotient-computation on the symmetric orbifold* → `backend/orbifold.py`, `satisfiability_signature` |
| `OBSERVER_NOTE.md` | the operator's ideal synthetic observer `A†=(Θ,Γ,∇⁻¹,∂∞,R,C,E,J)` distilled onto tested code: most organs are already the repo's verification architecture; the two hardening organs are built here — **C** the ambiguous critic (polysemy: PHP is 2-frame, Tseitin 1-frame) and **E** the erroneous observer (a mutation-testing vaccine: 4 unsound mock-frames the sound adjudicator kills) → `backend/observer.py` |
| `METAL_ROADMAP.md` | geometry → metal: understanding wants curvature, computation wants flatness (GF(2)); measured (naive numpy rewrite is *slower*); the three optimization passes (algorithm → allocation → tensorize); M4RI / CLMUL·GFNI / GPU-batch roadmap, honestly scoped |
| `HYPERBOLIC_PROGRAMMING_NOTE.md` | hyperbolic *programming* (Gårding–Güler–Renegar–Brändén, LP/SOCP/SDP as special cases) meets the frames: implication ↔ orthant (LP), counting ↔ elementary-symmetric derivative relaxations (Brändén spectrahedral), parity has no real cone (char-2 disanalogy); the ℝ-side SOS/hyperbolic certificate as the open cousin of `nullstellensatz_degree` |

## Reproducible experiments

`docs/ladder/scripts/`: `rung1_transition_sweep.py` (hardness peak + cheap
invariants), `ns_degree_vs_width.py` (algebraic vs resolution obstruction),
`symmetry_channel_ns.py` (the char-2 fork), `saddle_ruggedness_vs_gate.py`
(ruggedness vs the algebraic separator), `fano_braid_associator.py` (the
octonion substrate), `frame_router_scaling.py` (the crystallized
`backend/frame_solver.py` scaled on Tseitin: near-linear refute-first UNSAT,
superlinear full-solve — why the router refutes before it reconstructs),
`hyperbolic_frames.py` (hyperbolic *programming* ↔ the frame ladder: det =
matrix eigenvalues, `e_k` hyperbolic, the derivative-relaxation nesting the
counting frame lives on, and the char-2 disanalogy for parity),
`cosmo_map.py` (tessellate instance-space into clause-ideals, tile each by its
obstruction signature, and draw the atlas — real-cone vs char-2 vs unstructured
bands, the Tseitin↔PHP conjugate-dual edge; `--hunt` follows the *moving frame*
and measures the optim the *rotor* `frame_solve_guided` finds, 1.5–1.75× on the
unstructured/counting bands with identical verdicts; `--couple` measures the
*coupled triple* `frame_solve_coupled` — three frames as three theories exchanging
entailed literals over shared variables (Nelson–Oppen), deciding ~76–82% of the
mixed instances no single frame decides, 0 unsound vs brute force).

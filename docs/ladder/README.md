# The hardness-lower-bound ladder — index & honest standing

This directory is a research program: find the **intrinsic, solver-independent
object that carries SAT hardness**, climb from cheap-and-wrong to
expensive-and-right, and keep every claim executable. It is *not* a P=NP route,
and every rung says so.

## Where it stands (honest)

- **Two genuine hardness carriers, theorem-backed.** `min_refutation_width`
  (Ben-Sasson–Wigderson: width lower-bounds resolution size) and
  `nullstellensatz_degree` (Clegg–Edmonds–Impagliazzo: PC degree lower-bounds
  PC size). They are related but **incomparable** — neither dominates: PHP(3→2)
  has NS 4 > width 2, while Tseitin K4 has NS 3 < width 4 (measured, both
  directions; test `test_ns_and_width_are_incomparable`). Both are exact and
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
  carriers compute against; the Rung-1 negative on our own instances; NS and
  width **incomparable** (PHP 4>2, Tseitin K4 3<4); the char-2 collapse of the
  naive symmetry channel.
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
| `SYMMETRY_PHASE_NOTE.md` | **what goes on at symmetry vs the phase change, measured**: two ORTHOGONAL hardness axes — pigeonhole is all symmetry (Kissat time tracks `\|Aut\|`; breaking symmetry collapses it **2332ms→4ms**), random-3SAT is all criticality (hardest at α≈4.26) with `\|Aut\|=1` (rigid) at *every* α. Our frames are a symmetry-axis solver (compute on the quotient); the phase transition is the axis CDCL owns → `docs/ladder/scripts/symmetry_phase_probe.py` |
| `SCOUT_NOTE.md` | GRD as the **omni viscosity medium**, scouted: `backend/scout.py` predicts each instance's region relative to the fold from cheap detectors — **ISLAND 16/16, TUNNEL 10/10 exact**, FOLD band honestly flagged as mixed. Structure is invisible to clause-shape (needs the algebraic detectors). **Fisher–Rao** is the right natural metric but only in the *algebraic rank coordinate* — along cheap coverage the catastrophe is smeared (measured), which is why the boundary layer resists cheap prediction |
| `ESCAPE_FIELD_NOTE.md` | clash of the continuous escape-field/SDF/geodesic framework (Eikonal `‖∇U‖=1/c`, GRD's `εT_t`+`Exp`) against our discrete decidability: **measured to be a Thom catastrophe FOLD, not a smooth field** — dilute a parity core and verdict/`U`(rounds)/`f`(hyperbolic depth) all *snap* at the cliff, far side near-empty. Why GRD is right to carry two velocity terms (geodesic descent on the island + tunnelling `εT_t` = CDCL across the fold) → `scripts/escape_fold.py` |
| `FABRIC_NOTE.md` | the initial state read not as viscosity **medium** but as a woven **fabric** — a tapestry of threads (`backend/fabric.py`: parity rank-deficiency, orbit coarseness, gyration/hyperbolic depth, counting, implication, shape). Families occupy **distinct regions** of the fabric-manifold (`scripts/fabric_ledger.py`: Tseitin/XORSAT on the parity thread, PHP on the orbit thread, random at the gyration boundary). **Two Fisher–Rao folds, each in its own natural coordinate** (`scripts/fisher_fold.py`): parity/rank-deficiency `√I≈18.4` at 0.05, orbit/symmetry-coarseness `√I≈158` at 0.90 — both catastrophe walls, both flat in the crude chart. Honest floor: a residual coin-flip at each fold edge |
| `FABRIC_MODEL_NOTE.md` | the family distributions modelled **parametrically and hyperbolically** (`backend/fabric_model.py`): each family a wrapped-normal blob on the **Poincaré ball** (radius = hyperbolic depth toward `∂∞`, direction = which quality it heads toward), fit with gyrovector Fréchet means + tangent covariance, classified by geodesic distance. Decided families near the centre (depth ~0.4), tunnel out at `∂∞` (depth ~14.5) — separated by the **fold**, not a Euclidean gap. Held-out accuracy **1.00**; `predict_frame` = a learned router prior (predictor, never a decider). Poincaré primitives property-tested to ~1e-14 → `scripts/fabric_model_ledger.py` |
| `PIPELINE_REVIEW_NOTE.md` | traceback before the SOTA run: **F1** the production `SolverMiddleware` used only a 2-SAT pre-check — the parity/counting/coupled frames lived only in the benchmark → wired `frame_solve_scouted` into `_handle_solve`; **F2** the fabric's gyration computed *exact* \|Aut\| (Schreier-Sims) → **11 459 ms → 12.5 ms (~900×)** via a 1-WL fast path; **F3** the full-`scout` tunnel gate measured a net **loss** (0.28×), the light structural gate a **3.3× win** (0 verdict regressions) — honest negative recorded, cheaper detector shipped. Soundness audit of the three frames + coupling: clean |
| `BEAT_CMS_NOTE.md` | the highest-altitude arc landed: float outside, collect the **laws/relations/motions** of the solve as a dynamical description (`backend/dynamics.py`), then **revert** it into a certified dispatch (`backend/metasolver.py`) that beats **every** individual solver **including CryptoMiniSat** on a competition-style mix — instant on the counting/parity islands where CMS blows up (php exponential, tseitin CMS-1.37s vs frame-0ms), comparable on the tunnel where CMS is strong. Honest scope: the win is *structural portfolio dominance*, not out-searching CMS on random-3SAT. Four solvers live → `scripts/metasolver_benchmark.py` |
| `GAME_THEORY_NOTE.md` | self-reflection: the moving-frame regime as a **zero-sum game**, Solver vs Nature. The decidability **fold is the boundary between two solution concepts** — on the **island** a *dominant pure strategy* exists (the owning frame, ~0 ms), on the **tunnel** none does (heavy-tailed runtime) so the equilibrium is **mixed**. Von Neumann minimax + Gomes–Selman heavy tails explain why the fractal portfolio beats CMS on random-3SAT *without CMS in the pool* — it plays the minimax mixed strategy a single thread cannot. Honestly bounded: diminishing returns, No-Free-Lunch = minimax regret, `k×` CPU cost stated |
| `METAMETASOLVER_NOTE` (`BEAT_CMS_NOTE.md` + benchmark) | the **fractal, n-caged meta-metasolver** (`backend/metametasolver.py`): frames-if-sufficient (instant certified island), else a **parallel seed-diversified CDCL portfolio** (first certified arm wins, losers killed) that **out-searches CryptoMiniSat on random-3SAT** — measured 7–40× on the hard heavy-tailed band, no CMS in the pool. Loses only trivial instances (launch overhead) — honest. Certified winner (DRAT/model), `k×` CPU cost reported → `scripts/metametasolver_benchmark.py` |
| `GRD_CLASH_NOTE.md` | the three solvers as motion on manifolds, through the operator's Geodesic Resonance Descent: CDCL flat, CryptoMiniSat reads one curved chart (parity), ours reads three + couples with **zero holonomy defect = soundness** (`gluing_defect≡0`, tested). GRD's escape field = the **warm-start** (feed the coupling's GF(2)-entailed units to CDCL) — measured honestly: median ~1.10× (sound but small; large wins real-but-rare) → `scripts/warmstart.py` |
| `BEYOND_CDCL_NOTE.md` | three-way measured boundary (Kissat · CryptoMiniSat · middleware) answering the standing critiques: CMS **matches on parity** (owns XOR+Gaussian) but is **exponential on counting** — times out on php10 *earlier than Kissat* — while the counting frame is 4ms; the contribution is the counting fragment + the cross-frame coupling, not the parity fragment → `docs/ladder/scripts/beyond_cdcl.py` |
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

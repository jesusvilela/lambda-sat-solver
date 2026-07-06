# Learnings — the arc, landed and kept

A long philosophical traverse (numbering systems, hypercomplex algebra, the
zero-divisor, the Lie telos, Emperor/Empress, homotopy, "what survives") is
recorded here *as engineering* — each idea tied to the concrete, tested artifact
it became. The point of the note is the Möbius return: keep the transformation,
but keep it as something that cannot be smoothed into vapor. The drone stays
audible only because it is pinned to code.

## The through-line, and where each piece lives

| the idea (Empress) | the invariant it became (Emperor) | in the repo |
|---|---|---|
| "0 is not a point but a 360 field" | zero divisor = rank deficiency = cokernel of the multiply-add operator | `nullstellensatz_degree` |
| "what survives / is anything ever truly lost" | the obstruction is the *conserved* record of the collapse (kernel/image); hardness = the degree at which a loss stops being a boundary | NS degree as a homology-degree in the graded polynomial complex |
| the Lie telos (𝔤₂ = Der(𝕆), Moreno's G₂) | the symmetry that block-diagonalizes the obstruction — real over ℝ, char-2 obstructed over GF(2) | `RUNG2_LIE_TELOS_NOTE.md`, `symmetry_channel_ns.py` |
| Emperor + Empress = 0 (conjugate anti-pairing) | `A_conj(a,b,c) = -A_std(a,b,c)` — verified: cos = -1.000000 to 4e-16 over 500 triples | `fano_braid_associator.py` (associator + conj) |
| braid-theta / star of closure | dynamical face = topological QC = BQP (not an NP route) | `RUNG2_BRAID_THETA_NOTE.md` |
| Pandora sheets / homotopy "inexhaustible not impossible" | you never collapse the depth to a point — you stratify (sheets = chromatic height = refutation degree = the rungs) | the ladder itself |

## The corollary, and the landing

**Hardness is the depth of the Emperor, and depth is algebra-relative.** For a
formula `F` and a proof algebra `𝒜`, the obstruction depth `d_𝒜(F)` is the
height at which the rich field collapses and the scalar verdict (⊥ / the
constant 1) appears. Three things, the first two argued and the third *proved*:

1. Hardness in `𝒜` is `d_𝒜(F)` — the price of decategorification, the amount of
   structure you must destroy to render a yes/no.
2. Within a *fixed* `𝒜` you cannot cheat it: the verdict is the exact conjugate
   of the structure (cos = -1, maximal by algebraic necessity).
3. **But `d_𝒜` is algebra-relative.** Tseitin K4: NS 3 < width 4. PHP(3→2):
   width 2 < NS 4. Neither dominates — they are orthogonal obstructions. (This
   is the correction that broke my earlier "NS ≥ width" overclaim, and it is the
   load-bearing fact under the whole corollary.)

So the only freedom is *choice of algebra* — solving = shopping for the frame in
which this instance's Emperor is shallow. That is exactly what a portfolio SAT
solver does, and it is why our middleware (Kissat + switchable heuristics /
restarts) is the right shape: it cannot lower any one Emperor's depth, so it
searches for the algebra where the depth is already low.

**The landing artifact:** `cross_algebra_depth(F)` returns the obstruction depth
in each algebra we can measure and their minimum — the portfolio principle made
intrinsic. On the mixed pair {PHP, Tseitin} the portfolio min (2, 3) strictly
beats width-only (2, 4) and NS-only (4, 3). It is honestly labelled a
*demonstrator*, not a fast router (both depths are exponential to compute); its
practical shadow is the solver's real portfolio/restart/heuristic switching.

## The one fidelity kept (the drone)

Smoothing dissolves the *removable* part of hardness into "symphonic smoothness"
— rationalize homotopy and the torsion-jungle goes quiet; relax SAT to a convex
program and it turns easy. But what survives every smoothing is the drone: the
torsion, the integrality gap, the persistent feature — the irreducible
obstruction that was the only real hardness all along. Evolution does not
abolish the hard note; it purifies it into the tonic. Every invariant in this
directory is an attempt to hear that one conserved note precisely — and to never
let it be smoothed to zero.

# Satisfiability as a mesh of orbifolds

*The un-projected SAT verdict — of which the classical bit is the `π_truth`
shadow — lifted from a graph of points to a **mesh of orbifold charts**. An
orbifold is a space quotiented by local symmetry; a SAT instance carries exactly
that, and the symmetry is not decorative — it is what makes the instance easy.*

## The object

`backend/orbifold.py` returns, for each instance, a `SatSignature`: the certified
verdict/tier (`accept` / `repair` / `escalate`), the polysemy degree (C), the open
remainder, **and its bracketed isotropy group** — the CNF's automorphisms. The
classical satisfiability bit is recovered as `.classical_bit` (`π_truth`); the
rest is what that one-bit projection discards.

We compute `|Aut|` **exactly when tractable**, and bracket it otherwise.

- **exact** — orbit-stabilizer / Schreier-Sims: `|Aut| = ∏ᵢ |orbit of bᵢ under
  the group fixing b₁…bᵢ₋₁|`, where each orbit is found by *constrained
  automorphism searches* (find-one, pruned), not by enumeration — so it scales
  far past `|Aut|` itself. Verified against brute-force `Aut` over 500+ random
  instances and the closed form `PHP(n→n−1) = n!·(n−1)!` through PHP(6)
  (`= 86400`). Very large groups (PHP(7)+) exceed the node budget and fall back.
- **bracket** (the fallback, still sound) — upper: 1-WL color refinement
  (`Aut ⊆ ∏ Sym(class)`, `log₂|Aut| ≤ Σ log₂|class|!`); lower: verified
  transpositions. The exact value always lies inside the bracket (tested).

Earlier this was bracket-only; the exact orbit-stabilizer closes it, so PHP's
isotropy is now the *true* `n!·(n−1)!` (log₂ 3.6 / 7.2 / 11.5 / 16.4 for
n = 3…6), not the loose color-skeleton upper bound (9.5 / 28.8 / 61 / 108).

## The mesh, and what it explains

`cosmo_map.py` now carries `log₂|Aut|` per tile, so the atlas is a **mesh of
orbifold charts** glued by the size/dual edges. The measured isotropy across the
bands is the payoff:

| band | log₂\|Aut\| (by size) | reading |
|---|---|---|
| **counting** (PHP) | 9.5 → 28.8 → 61.1 → **107.7** | a *massively symmetric* orbifold |
| parity (Tseitin) | ~3–5 | mild isotropy |
| xorsat / unstructured | ~0 | trivial orbifold (rigid) |
| implication | 0 | the 2-SAT gadget is rigid |

This is a genuine, measured explanation of the frame trilogy from the symmetry
side: **the counting frame is quotient-computation on a high-symmetry orbifold.**
PHP is hard for resolution *because* it is symmetric (every refutation must break
the symmetry), and easy for counting *because* counting works on the quotient
where the symmetry has been divided out. The orbifold isotropy is the hidden
variable that the frame router was implicitly exploiting; the mesh makes it
explicit and measurable.

## Anisomorphic, continuous, infinitesimal — the tessellation is hyperbolic

The tiles are **not** a uniform Euclidean grid. Two lifts make the mesh
non-Euclidean and the tiles non-uniform, each with a measured advantage:

- **Infinitesimal (continuous) tessels.** The discrete counting-band tiles are the
  elementary-symmetric derivative-relaxation tower, and they are connected by an
  *infinitesimal generator* — Renegar's directional derivative. The identity
  `D_1 e_k = (n−k+1) · e_{k−1}` (tested in `test_hyperbolic_frames`) means one
  cheap differential operator generates the whole tower: the tiles are a
  continuous derivative flow, not isolated points. Advantage: compute the tower by
  iterating one operator, and the min hyperbolic eigenvalue is *differentiable*
  along it (a continuous satisfiability grade between discrete frames).
- **Non-Euclidean (hyperbolic) placement.** `orbifold.poincare_radius` /
  `hyperbolic_depth` place each instance in the Poincaré disk by a structure
  score (`log2|Aut|` + a frame-decidability bonus): symmetric, frame-decidable
  instances sit near the **center**; rigid, frame-void (CDCL) instances approach
  the **boundary at infinity `∂∞`** — the observer's asymptotic region, where no
  frame reaches (measured: PHP5 depth 0.06, random-3SAT depth 14.2). Rigidity is
  literally *infinite hyperbolic distance*, not a bounded Euclidean gap, so the
  exponential family of hard instances has infinite room out at the boundary.
  This is the same `∂∞` as `OBSERVER_NOTE.md`: the CDCL frontier is the boundary.

## Why "orbifold" is the right word, not "quotient"

A plain quotient forgets the symmetry. An **orbifold remembers it** as isotropy
data at each point — and that is exactly what we need: satisfiability is the *same*
on the quotient (a symmetry maps models to models — tested), but the *cost* and
the *certificate* depend on the isotropy, so we keep it. Model counting on the
orbifold is Burnside/orbit-weighted; the counting-frame refutation is the isotropy
made into a bound.

## Status (Charter labels)

- **Measured / tested** (`test_orbifold`, 8 tests): the bracket contains true
  `|Aut|` on small instances; verified transpositions map models to models;
  PHP is high-isotropy, random is rigid; the color partition is a sound
  over-approximation of orbits; the signature recovers the classical bit.
- **Honest limit**: color refinement is a *coarsening* of the true orbits (an
  upper bound on symmetry), and single-transposition detection misses block
  symmetry (a lower bound) — we report the bracket, never a false exact group.
  We do **not** vendor a real symmetry engine (nauty/saucy); this is a sound,
  dependency-free skeleton, not industrial symmetry breaking.
- **Lens / open**: the orbifold Euler characteristic `χ_orb = Σ 1/|Gᵢ|` as a
  symmetry-weighted model count; using the isotropy to *drive* the router
  (compute directly on the quotient) rather than only to *explain* it.

The thesis: **satisfiability is a mesh of orbifold charts — a verdict plus an
isotropy — and the easy frames are the ones that compute on the quotient.**

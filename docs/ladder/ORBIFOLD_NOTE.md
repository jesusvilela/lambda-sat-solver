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

We do not compute the full automorphism group (graph-isomorphism-hard). We
**bracket** it, soundly, both directions — verified against brute-force Aut on
small instances (`test_orbifold`):

- **upper** — 1-WL color refinement partitions the variables; automorphic
  variables always share a color, so `Aut ⊆ ∏ Sym(class)` and
  `log₂|Aut| ≤ Σ log₂(|class|!)`. The **isotropy skeleton.**
- **lower** — verified single-variable transpositions `v↔w` that map the clause
  *set* to itself are genuine automorphisms; a fully-verified class of size `k`
  generates `Sₖ`, contributing `k!`.

The bracket is honest about its own weakness: PHP's symmetry is *block*
permutation (swap two pigeons = a product of variable-swaps), which single
transpositions miss — so the lower bound is 0 there while the color skeleton
correctly reports huge isotropy.

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

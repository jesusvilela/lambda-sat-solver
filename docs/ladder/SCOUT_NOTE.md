# Scouting the omni viscosity medium — mapping the tunnelings, and Fisher–Rao

*Instead of one solving stream, treat GRD as the omni viscosity medium filling
instance-space and SCOUT it: predict, from cheap detectors, where the decidability
folds (the CDCL tunnelings) arise before falling into them. `backend/scout.py`.*

## The scout map (measured)

`scout(formula)` reads cheap algebraic **detectors** — far cheaper than the
**deciders** they forecast — and predicts the instance's region relative to the
fold:

- **ISLAND** — a sound frame will decide it (full parity coverage, a counting
  signature, or a 2-SAT contradiction);
- **TUNNEL** — no exploitable structure; go straight to certified CDCL;
- **FOLD** — the boundary layer (partial parity), genuinely ambiguous.

Validated on a mixed corpus:

| scout region | prediction | reality |
|---|---|---|
| **ISLAND** | frame decides | **16/16 correct** |
| **TUNNEL** | needs CDCL | **10/10 correct** |
| **FOLD** | ambiguous | 14 instances, **9 decided / 5 escalated** — honestly mixed |

So the confident regions are perfectly predictable from cheap geometry, and the
scout **refuses to guess** exactly where guessing is impossible — the viscosity
boundary layer at the catastrophe.

Two honest sub-findings from the medium:

- **Structure is invisible to clause-shape.** Tseitin (parity island) and random
  3-SAT (tunnel) are *identical* by clause length — both wide clauses. The
  difference lives in the sign patterns (parity groups) and orbits (symmetry), so
  you must run the algebraic detectors to sense the medium; there is no free
  surface shortcut.
- **The payoff addresses the overhead critique.** On confident TUNNEL the router
  can skip the frame deciders (Gaussian, coupling, counting) and go straight to
  CDCL — removing the pre-pass overhead on unstructured instances that the SOTA
  reviewer flagged on random 3-SAT.

## Can Fisher–Rao help? Yes — but only in the natural coordinate

The scout's field is a probability `P(decide | features)`, so the space of these
predictions is a statistical manifold and its natural metric is **Fisher–Rao**
`g = 𝔼[∂log p ∂log p]` — the reparameterization-invariant metric behind GRD's
`natural_gradient`. The hope: the fold is a **metric singularity** — where
`P(decide)` transitions sharply, the Fisher information `I = (P′)²/(P(1−P))`
diverges, so the catastrophe becomes a *wall* in information geometry, invisible to
Euclidean feature-distance.

Measured along the cheap **coverage** coordinate, `√I` does **not** spike cleanly
— because `P(decide | coverage)` stays ≈ 0.9 across coverage 0.6–1.0 (the coupling
is robust; it decides most partially-covered instances). The honest reading:

> **The fold is sharp per instance (`U: 0 → ∞`), but its LOCATION is
> instance-dependent — set by the exact GF(2) rank, not the surface coverage. So
> averaged over instances the transition is smeared, and Fisher–Rao along the
> cheap coordinate washes out.**

This is the deeper point, and it is exactly the hypercomplex/hyperdim/infinitesimal
lesson: **the infinitesimal metric only reveals the fold in the *natural*
(algebraic) coordinate — the rank-deficiency of the GF(2) system — not in the naive
Euclidean feature coordinate.** Fisher–Rao is the right *instrument*; coverage is
the wrong *chart*. It is also precisely why the scout's FOLD band is unpredictable:
the scout's cheap features are not the natural coordinates of the catastrophe, so
no smooth predictor over them can resolve the boundary layer — you must actually
compute the rank (run the coupling).

## Synthesis

- The omni viscosity medium is **scoutable**: confident ISLAND/TUNNEL predictions
  are exact (26/26), and the FOLD band is honestly flagged, not guessed.
- Fisher–Rao is the correct natural metric and *would* geometrize the fold as a
  singularity — **in the algebraic rank coordinate**. In the cheap surface
  coordinate the catastrophe is smeared, which is a measured reason the boundary
  layer resists cheap prediction.
- **Lens, not proven**: that `hyperbolic_depth` / the scout field is a genuine
  Fisher–Rao geodesic system; that the rank coordinate makes `√I` diverge (we
  argue it, we did not compute the rank-parameterized metric). Labelled as the
  next step, not a result.

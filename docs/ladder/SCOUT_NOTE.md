# Scouting the viscosity medium — mapping the tunnelings, and Fisher–Rao

*Instead of one solving stream, treat GRD as the viscosity medium filling
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

## Can Fisher–Rao help? YES — measured, in the natural coordinate

The scout's field is a probability `P(decide | features)`, a statistical manifold
whose natural metric is **Fisher–Rao** `g = 𝔼[∂log p ∂log p]` — the
reparameterization-invariant metric behind GRD's `natural_gradient`. The fold
should be a **metric singularity**: where `P(decide)` transitions sharply, the
Fisher information `I = (P′)²/(P(1−P))` diverges into a *wall*.

*"Can you not measure the sign-patterns and orbits?"* — yes, and doing so is the
whole point. Measured **along coverage** (a crude proxy), `√I` is flat
(`P(decide) ≈ 0.9` everywhere). Measured **along the GF(2) RANK-DEFICIENCY** of the
recovered XOR system — the actual algebraic content of the sign-patterns — the fold
is razor-sharp (`scripts/fisher_fold.py`):

| XOR rank-deficiency | P(decide) | Fisher `√I` |
|---|---|---|
| 0.00 (Gaussian **determines** the variables) | **0.99** — island | 0.0 |
| 0.05 | 0.33 | **≈ 18** ← the spike |
| 0.10 (a free variable remains) | **0.12** — tunnel | 0.0 |

**The catastrophe IS a Fisher–Rao metric singularity — in the natural algebraic
coordinate.** Coverage was the wrong chart; the rank-deficiency of the
sign-patterns is the right one. The mechanism: a consistent partial-parity system
either fully determines its variables (deficiency 0 → the coupling reads off the
answer → decides) or leaves free variables (deficiency > 0 → parity does not pin
the solution → escalate), and the transition is sharp at deficiency ≈ 0.05.

Feeding that coordinate back into the scout **resolves the fold it could not
predict before**: confident coverage rose from **65% → 90%** (ISLAND 32/32, TUNNEL
15/15, both with **zero errors**), and the ambiguous band shrank from 14 to 5
instances — the residual thin layer at deficiency ≈ 0.05 where P(decide) is
genuinely ~0.3 (an irreducible coin-flip, not a measurement gap).

## Synthesis

- The viscosity medium is **scoutable**, and the scout is exact in the
  confident regions (ISLAND/TUNNEL, 0 errors) once it reads the *natural*
  coordinate.
- **Fisher–Rao geometrizes the fold as a metric singularity** — measured (`√I`
  spikes to ~18) in the GF(2) rank-deficiency coordinate, flat in coverage. The
  metric is the right instrument; the sign-patterns (as rank) are the right chart.
- The honest floor: a thin residual FOLD layer remains at deficiency ≈ 0.05 where
  P(decide) ≈ 0.3 — a genuine coin-flip the geometry localizes but cannot remove
  (the last bit needs the actual solve).
- **Lens, not proven**: that this is a full Fisher–Rao *geodesic* system, or that
  `√I` truly *diverges* (we measured a sharp finite spike on finite samples, not a
  proven singularity). Labelled as the next step.

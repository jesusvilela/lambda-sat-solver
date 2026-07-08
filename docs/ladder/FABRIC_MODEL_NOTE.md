# The fabric model — the family distributions, parametric and hyperbolic

*The operator asked to "model the family distributions parametrically over the
fabric… statistically, in n-cosmo / n-manifold distributional ledgers" — and then:
"remember hyperbolic computing, don't do boring euclidean 2d." So the model does not
fit flat Gaussian clouds; it fits **wrapped-normal blobs on the Poincaré ball**, the
curved manifold the fabric already lives in. `backend/fabric_model.py`.*

## Why hyperbolic, not flat

The fabric's `gyration` thread **is** a hyperbolic depth: `hyperbolic_depth =
artanh(r)` (`backend/orbifold.py`). A frame-decided instance sits near the **centre**
of the Poincaré ball; a rigid, frame-void (CDCL) instance runs out toward the
**boundary at infinity ∂∞** — an *infinite* hyperbolic distance, not a bounded
Euclidean one. That boundary is the "holographic screen of hardness." A flat
Gaussian cloud would throw exactly this curvature away; the whole point is that
"decided" and "CDCL" are separated by the fold to ∂∞, not by a Euclidean gap.

## The embedding (each instance → a point in the ball B⁵)

| coordinate | source | meaning |
|---|---|---|
| **radius** `r = tanh(gyration)` | hyperbolic depth | how far toward ∂∞ (→1 = rigid/CDCL) |
| **direction** `u = unit(qualities)` | `[orbit, counting, parity, implication, generic]` | *which* boundary region it heads toward |
| **point** `x = r·u` | | its place on the curved manifold |

The `parity` quality is XOR coverage (the frame's **presence**), added so a
fully-determined parity system — `rank_deficiency ≈ 0`, otherwise indistinguishable
from a structureless instance — points along the parity axis, not the generic one.

Each family is a **wrapped-normal blob**: a Fréchet (Karcher) mean μ computed with
the gyrovector exp/log maps, and a covariance in the Riemannian tangent space at μ.
A new instance is classified by tangent-space Mahalanobis distance — the hyperbolic
geodesic distance to each blob, shaped by that blob's anisotropy. The Poincaré-ball
primitives (Möbius ⊕, exp/log, geodesic) are property-tested to ~1e-14
(`tests/test_fabric_model.py`): `exp∘log` round-trip, `|log|_riemannian == geodesic`,
Möbius left-cancellation.

## The distributional ledger (`scripts/fabric_model_ledger.py`)

| family | frame | **hyp. depth** | placement |
|---|---|---|---|
| parity (xor_chain) | parity | **0.41** | near centre |
| counting (PHP · chessboard) | counting | **0.04** | near centre |
| tunnel (random-3SAT) | none | **14.51** | out at ∂∞ |

Geodesic separation between the blobs: parity↔counting **0.39** (a small *angular*
hop among the decided), parity/counting↔tunnel **≈14.5** (the crossing of the fold to
the boundary). The curvature does the work: the primary axis is depth (decided vs
CDCL), the secondary is direction (parity vs counting).

**Measured separability** — held-out classification accuracy **1.00** on fresh seeds
(the families are cleanly resolved by the hyperbolic fabric). External families
(unseen in training) are placed correctly by the fitted density: Tseitin/XORSAT →
parity, PHP → counting (Mahalanobis 0.70, dead-centre of the counting blob),
random-3SAT → tunnel (0.00, dead-centre), mixed → the parity edge (it is genuinely
strung between, with large Mahalanobis to every blob — honestly out-of-distribution).

## What it is, and is not (Charter)

- **Measured**: the blob depths and geodesic separations; the held-out accuracy; the
  correctness of the gyrovector primitives (property-tested).
- **A predictor, never a decider**: `predict_frame` names the frame to try first
  from the instance's place on the manifold — a learned **router prior**, the cheap
  cousin of `scout`. Soundness lives entirely in the frames it points at; a
  mis-prediction costs a little trial order, never a wrong verdict.
- **Lens, not proven**: that the wrapped-normal is the *true* density of a family
  (it is a fitted approximation), or that the Fréchet mean is unique for every family
  (it is for these near-centre/near-boundary blobs). The model is a fitted density on
  a curved manifold — the parametric completion of the fabric ledger, not a theorem.

# The fabric — the initial state as a tapestry, and its Fisher folds

*From viscosity **medium** (a field to move through) to **fabric** (a woven
tapestry of qualities). `backend/fabric.py` reads an instance's initial state
holistically — not one number, a tapestry of threads — and each thread is a chart
of the cosmo manifold with its own decidability fold, measured to be a Fisher–Rao
metric singularity in its own natural coordinate.*

## The threads (`backend/fabric.py`)

| thread | quality | natural fold coordinate |
|---|---|---|
| **parity (presence)** | *is* it a GF(2) system | XOR **coverage fraction** |
| **parity (fold)** | GF(2) structure of the sign-patterns | XOR **rank-deficiency** (fold ~0.05) |
| **orbit** | symmetry / isotropy | **symmetry coarseness** `1 − orbits/n` (fold ~0.9) |
| **gyration** | position in the hyperbolic mesh | `hyperbolic_depth` (distance to `∂∞`) |
| **counting** | cardinality structure | at-most-one fraction |
| **implication** | 2-SAT structure | binary-clause fraction |
| **shape** | size | clause/variable ratio |

*(The parity **presence** thread — XOR coverage — was added so a fully-determined
parity system, whose rank-deficiency ≈ 0 and is therefore indistinguishable from a
structureless instance on the fold coordinate alone, still reads as parity. It is
what lets the parametric model separate Tseitin/XORSAT from the tunnel; see
`FABRIC_MODEL_NOTE.md`. The gyration thread now uses the cheap 1-WL placement
(`hyperbolic_depth(exact=False)`) — exact |Aut| cost 11 s on PHP, see
`PIPELINE_REVIEW_NOTE.md`.)*

## The distributional ledger (`scripts/fabric_ledger.py`)

Each family is a **distinct region** of the fabric-manifold — the holistic view of
the initial state:

| family | rank_def | orbit | gyration | count | region · frame |
|---|---|---|---|---|---|
| Tseitin | 0.00 | 0.00 | 0.20 | 0.00 | island · parity |
| XORSAT | 0.00 | 0.00 | 0.20 | 0.00 | island · parity |
| PHP | 0.00 | **0.98** | 0.01 | **0.95** | island · counting |
| mixed | 0.23 | 0.00 | **14.16** | 0.00 | tunnel |
| random3 | 0.00 | 0.00 | **14.16** | 0.00 | tunnel |

Parity families live on the parity thread (`rank_def≈0`); PHP lives on the orbit
thread (`orbit≈1`, counting high); the unstructured families sit out at the
gyration boundary (`gyration→14.16`, the depth of `∂∞`); mixed is strung between.

## Fisher–Rao: both threads fold as metric singularities (`scripts/fisher_fold.py`)

Each thread has a decidability fold, and Fisher–Rao geometrizes it — **but only in
that thread's natural coordinate.** Measured `√I`, `I = (P′)²/(P(1−P))`:

| thread | crude coordinate (`√I` peak) | natural coordinate (`√I` peak) |
|---|---|---|
| **parity** | coverage — **2.9** (flat, smeared) | rank-deficiency — **18.4** (spike at 0.05) |
| **orbit** | — | symmetry coarseness — **158** (spike at 0.90) |

`P(decide)` on the parity thread drops 0.99 → 0.12 across rank-deficiency 0 → 0.10;
`P(counting refutes)` on the orbit thread jumps 0.00 → 1.00 across coarseness
0.90 → 1.00. Both are catastrophe folds; both are Fisher walls; both are invisible
in a crude chart and sharp in the natural one. The orbit fold is the sharper of the
two (`√I ≈ 158` vs `18.4`) — counting is more brittle than parity (it needs the
symmetry almost perfectly intact).

## Synthesis (Charter labels)

- **Measured**: the fabric threads; the family regions of the ledger; the two
  Fisher folds and their peaks in the natural coordinates (and their flatness in
  the crude ones).
- **The one honest floor**: a thin residual ambiguity at each fold's edge
  (parity `P≈0.33` at deficiency 0.05) — the geometry *localizes* the catastrophe
  but the last bit needs the actual solve.
- **Lens, not proven**: that the fabric is a genuine Riemannian/Fisher **geodesic**
  system, that `√I` truly *diverges* (finite spikes on finite samples), or that
  gyration is an exact SDF. The tapestry is a measured holistic descriptor and a
  statistical ledger — the next step is to model the family distributions
  parametrically over it (a genuine n-manifold distributional model), not just
  tabulate their regions.

**That next step has landed** (`FABRIC_MODEL_NOTE.md`): `backend/fabric_model.py`
fits each family as a wrapped-normal blob on the **Poincaré ball** — hyperbolic, not
flat — with held-out classification accuracy 1.00 and the decided/tunnel families
separated by the fold to `∂∞` (geodesic ≈14.5) rather than a Euclidean gap.

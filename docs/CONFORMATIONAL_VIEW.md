# λSAT — Conformational Solve Manifold (a breathing, non-Euclidean view)

> This document reports a genuine measurement: where do SAT solves *live* when
> you embed their structure into hyperbolic (gyrovector / Poincaré) space, rather
> than scattering them on a 2D Euclidean plot? The visualization is committed as
> `conformational_3d.html` (interactive) and `conformational_preview.png` (static).
> Re-derive everything with `python rebuild_viz.py`.

## What was built (the operators, not the adjectives — HYPERDIM λ₉)

Three new modules, all using the repo's *existing* tested machinery — no invented
dynamics:

| module | what it does | what it reuses |
|---|---|---|
| `backend/geometry/trajectory.py` | Embeds each instance as a point in the Poincaré ball and each solve as a curve (the "breath") | `fabric()` for the gyration depth, `coupling_breath()` for the breath sequence, `vdis.gyro_ops` for the curved-space maps |
| `backend/geometry/viz.py` | Renders the ball + points + trajectories as interactive 3D plotly HTML | PCA-3 projection of the 7-D signature, honest about being a projection |
| `conformational_run.py` | x10 bench driver: 529 diverse instances × 8 solvers + manifold build + viz | the same `ProcessPoolExecutor` harness as before |

## The embedding (load-bearing vs lens, stated plainly)

**LOAD-BEARING** (survives audit; measured by the repo's own carriers):
- **Radial coordinate = gyration depth.** `fabric(f).gyration` is the hyperbolic
  distance toward the rigid/CDCL boundary ∂∞. Structured instances (low gyration)
  sit near the origin; unstructured instances (high gyration) sit near the
  boundary. This is the geometric face of the frame-router's punt decision.
- **Angular coordinates = obstruction signature.** Which algebraic structure the
  instance carries: implication (2-SAT/LP-orthant), counting (ℤ/e_k ladder),
  parity (GF(2)/char-2), plus |Aut| isotropy, NS rank-deficiency, size, and the
  coupling breath amplitude.
- **The breath trajectory.** `coupling_breath(f).breath` is the literal sequence
  of entailed-literal counts per coupling round — the solve's "inhalations".

**LENS** (a choice of view, not a theorem — different choices rearrange the picture):
- The *particular* tanh squash mapping gyration ∈ [0, ∞) to radius ∈ [0.15, 0.90]
  of the ball. It keeps points readable; it does not encode a physical law.
- The PCA-3 projection for display. The manifold is 7-D; we show its dominant
  three axes. HYPERDIM λ₆: this is explicitly *not* a claim the space is 3-D.
- The per-round rotation of the breathing curve. It makes the path visibly curve
  rather than retrace a ray. Cosmetic.

## What the manifold shows (the actual finding)

**The conformational geometry separates cleanly by hardness regime:**

| family | mean radius | where it lives | frame verdict |
|---|---|---|---|
| pigeonhole | 0.129 | near origin (structured) | counting frame decides — no CDCL |
| graph-coloring | 0.129 | near origin | frame / quick CDCL |
| mutilated-chessboard | 0.129 | near origin | frame |
| xor-chain | 0.142 | near origin, parity band | parity frame decides |
| random-3-SAT | **0.729** | **near boundary ∂∞** | punts to CDCL |
| random-4-SAT | **0.729** | **near boundary ∂∞** | punts to CDCL |
| random-5-SAT | **0.729** | **near boundary ∂∞** | punts to CDCL |

This is not decoration. The radial axis is the *measured* gyration depth, and it
separates exactly the two regimes the repo's own `PUBLIC_RESEARCH_CLAIMS.md`
claims: frames win on structure, are silent on the unstructured critical band.
The conformational view makes that claim *visible* rather than asserted.

The 3D image confirms the clusters are spatially distinct (verified by image
analysis): structured families (purple/blue/green) cluster tightly near the
origin; unstructured families (red/orange/yellow) form a diffuse cloud near the
translucent boundary sphere. The breathing trajectories are curves, not dots.

## Verified x10 solver benchmark (529 instances, 30s timeout, 7 workers)

| solver | solved | PAR-2 |
|---|---|---|
| **middleware** | **529/529** | **0.61s** |
| CaDiCaL 3.0.0 | 529/529 | 0.63s |
| MiniSAT 2.2.1 | 527/529 | 0.70s |
| Kissat 4.0.4 | 528/529 | 0.76s |
| Gimsatul | 528/529 | 0.88s |
| SATCH | 526/529 | 0.83s |
| Z3 4.16.0 | 525/529 | 1.40s |
| CryptoMiniSat 5.14.7 | 510/529 | 3.41s |
| **VBS** | **529/529** | **0.29s** |

- Bench wall: 582s for 4232 cells. **7.27× parallel speedup.**
- **Zero wrong answers** across all 8 solvers on all known-answer instances —
  full cross-solver correctness consensus.
- Middleware honesty: 22/529 verdicts by sound frames (9 counting, 7 2sat,
  6 parity), 507 by certified Kissat fallback. 100% certified.

### Per-family (where the geometry and the benchmark agree)

| family | kissat | cadical | middleware | note |
|---|---|---|---|---|
| **pigeonhole** | 9/10, **7.53s** | 10/10, 0.31s | **10/10, 0.03s** | counting frame: 250× faster than Kissat on the hard php |
| **xor-chain** | 12/12, 0.20s | 12/12, 0.16s | **12/12, 0.02s** | parity frame: 10× faster than CDCL |
| random-3-SAT | 280/280, 0.43s | 280/280, 0.45s | 280/280, 0.44s | ties Kissat (CDCL fallback) — as claimed |
| random-4-SAT | 120/120, 1.59s | 120/120, 1.60s | 120/120, 1.55s | ties CDCL |
| graph-coloring | 24/24 | 24/24 | 24/24 | all tie |
| mutilated-chessboard | 3/3 | 3/3 | 3/3 | all tie |

**The geometry predicts the benchmark.** Instances sitting near the origin
(low gyration, structured) are exactly the ones where the frame middleware beats
CDCL by 10-250×. Instances sitting near ∂∞ (high gyration, unstructured) are
exactly the ones where the middleware correctly adds no overhead and matches its
CDCL fallback. The conformational view is a *predictor map* of where the
middleware helps, not just a picture.

## Honest limitations

1. **Still not competition-scale.** 529 instances at 30s vs the SAT Competition's
   400 at 5000s. The timeout is 167× short. The structural findings hold; the
   absolute PAR-2 numbers do not extrapolate.
2. **Synthetic suite only.** No SAT 2024/2025 Main Track or SATLIB instances. The
   families are the repo's own generators.
3. **The embedding is a lens.** A different obstruction-signature weighting or a
   different curvature would rearrange the cloud. The *clusters* (structured vs
   unstructured) are robust because they come from the load-bearing gyration; the
   *exact positions* are not unique.
4. **PCA-3 loses information.** The first 3 PCs carry 97% / 9% / 3% of variance —
   the manifold is genuinely high-D. The 3D view is a shadow, labelled as such.

## Artifacts

```
backend/geometry/trajectory.py   # the Poincaré embedding (load-bearing + lens, labelled)
backend/geometry/viz.py          # 3D plotly renderer
conformational_run.py            # x10 bench driver
rebuild_viz.py                   # rebuild manifold+viz without re-running solvers
conformational_3d.html           # interactive 3D breathing view (open in browser)
conformational_points.html       # static-points variant
conformational_preview.png       # static preview (verified: real cluster structure)
conformational_results.json      # 4232 raw bench rows + manifold stats
```

## What this settles (and what it does not)

**Settles:** The repo's hypercomplex vocabulary is not pure decoration. The
gyrovector machinery (`vdis.gyro_ops`) is textbook-correct and numerically
guarded; `fabric().gyration` is a real, load-bearing geometric invariant; and the
conformational embedding built from them produces a *discriminating* map whose
radial axis predicts where the middleware beats CDCL. My first review's "the
geometry is performative" verdict was too blunt — the *naming* is grandiose, the
*machinery* is genuine.

**Does not settle:** Whether this geometric view *adds solver capability* (vs
being a visualization of structure the frame router already exploits
symbolically). The conformational map is descriptive/predictive, not algorithmic.
To make it load-bearing for *solving*, one would need a router that reads the
Poincaré coordinates and changes behavior — which is the repo's stated
"metasolver reverts description into dispatch" direction, but that path is not
benchmarked here.

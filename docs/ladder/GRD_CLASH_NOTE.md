# Clashing the solver manifolds — what survives in holonomy

*A theoretical guide (a lens, labelled as such), reading CDCL, CryptoMiniSat and
the frame router as motion on different manifolds, through the operator's
**Geodesic Resonance Descent** (GRD): "move on curves, listen to structure, do not
collapse." GRD is a continuous optimizer and does not decide SAT; it is used here
as the shared skeleton that our discrete decision system turns out to instantiate.*

## The three as motion

| solver | manifold it moves on | what it reads | GRD reading |
|---|---|---|---|
| **CDCL** (Kissat/CaDiCaL) | the flat assignment cube {0,1}ⁿ | only *local* structure (unit propagation, conflict clauses) | flat gradient descent + restarts; "accept if conflict-reducing" |
| **CryptoMiniSat** | cube + **one** curved chart: the GF(2)/parity submanifold | local structure **plus** recovered XORs (Gaussian) | descent + **one** moving-frame correction (the parity frame) |
| **frame router** (ours) | **three** charts — implication / parity / counting — glued | which chart is *flat* here, and their coupled entailments | GRD's full loop: read geometry → move on the flat curve → check coherence → keep or escalate |

CDCL is `x ← x − η∇f` on a flat space: powerful, but it grinds exponentially
through curvature it cannot see (Tseitin parity, pigeonhole counting).
CryptoMiniSat adds exactly one of GRD's `U_t` moving-frame corrections — the
parity chart — and it *works* (it matches us on Tseitin). But it has no counting
chart, so it falls back to flat grinding on PHP and times out earlier than Kissat
(`BEYOND_CDCL_NOTE.md`). Our router reads three charts and moves on whichever is
flat — the moving frame (`frame_solve_guided`) — then couples them.

## What survives the clash: soundness = zero holonomy defect

GRD's energy carries a holonomy term `‖Hol_γ(∇) − I‖²`: transport a state around a
loop; the defect is how much it fails to return to itself. Put a solver's
inference on that footing and the holonomy defect **is unsoundness** — traverse a
cycle of deductions and come back with a *different* truth value. So the invariant
that MUST survive, for any solver worth the name, is **zero holonomy defect =
soundness**, and it is the one thing all three preserve (CDCL by resolution, CMS by
resolution+GF(2), ours by sound frames + certified fallback).

For our frame system this is not a metaphor — it is a *tested theorem*:
`observer.gluing_defect ≡ 0` (sound frames cannot disagree), asserted across
randomized batteries. Any loop through the three frames returns the same truth:
**perfect holonomy on the frame charts.** That is what survives and returns.

## What GRD teaches us to add (the guide for our own algorithm)

Mapping GRD's terms onto tested code shows what we already have and what is next:

| GRD term | our artifact | status |
|---|---|---|
| geodesic move `Exp(V·dt)` | frame-native moves (decide in the flat chart, no gate-Tseitin blow-up) | built |
| moving-frame correction `U_t` | `frame_solve_guided` (rotate to the local cheapest frame) | built |
| coupled coherence `⟨x,Δ_∇x⟩` | `frame_solve_coupled` (Nelson–Oppen entailment exchange) | built |
| holonomy defect `‖Hol−I‖²` | `gluing_defect ≡ 0` (soundness as zero defect) | built, tested |
| dual clock (fast flow / slow certify) | coupling **breathes** fast, then DRAT/model **certifies** slow | built |
| **escape field `εT_t`** (carry structure out of a trap) | **warm-start**: hand the coupling's GF(2)-entailed units to CDCL | **new — measured below** |
| continuous geometry to flow on | the orbifold / hyperbolic mesh (`poincare_radius`, `hyperbolic_depth`) | built (lens) |
| spectral / connection-Laplacian sensors | VDIS `signed_laplacian_frustration` (scoped-out carrier) | lens |

## The escape field, made operational (warm-start)

GRD's `εT_t` says: when a trajectory is trapped, do not restart from nothing —
carry the accumulated moving-frame structure into the escape. Concretely: when the
coupled router escalates (`CDCL_NEEDED`) it has often **entailed** literals by GF(2)
Gaussian elimination — precisely the literals a pure-CDCL solver **cannot derive by
unit propagation** (it has no Gaussian). Appending them as sound units before the
Kissat fallback is that escape field.

Measured (`scripts/warmstart.py`, 16 planted forcing-parity + hard-core
instances), and the result is an **honest half-negative** worth more than a hyped
win: **median speedup ≈ 1.10×**, with a tail — one probe instance where cold Kissat
fell into a 63 ms search warm-started to 3 ms (**21×**), but most instances cold
Kissat already solved in 3–5 ms, where the entailed units are neutral (occasionally
<1× from unit-parse overhead).

Why the escape field is *sound but small here*, stated plainly:
1. **Modern CDCL inprocessing already recovers much of it.** Kissat's probing /
   vivification / equivalent-literal reasoning derives a lot of what GF(2)
   elimination would hand it, so the marginal information is small at these scales.
2. **The narrow-band problem.** Instances hard enough for cold CDCL to *benefit*
   from the entailments are usually instances the frames **fully decide** anyway
   (pure parity → no fallback). The warm-start only bites in the thin band of
   *partial* parity that entails units, does not fully decide, **and** leaves a
   CDCL-hard residual — and that band is thin.

So GRD's escape-field intuition is correct and the mechanism is sound (every
appended unit is entailed — satisfiability preserved), but on this instance
distribution its measured value is modest and high-variance, not the easy win it
looks like a priori. The large wins are real but rare. Honest boundary kept.

## The one-line synthesis

> CDCL moves on a flat space and cannot see curvature; CryptoMiniSat reads one
> curved chart (parity); our router reads three and moves on the flat one, couples
> them with zero holonomy defect (= soundness, tested), and — GRD's escape field —
> carries what it learned into the CDCL fallback rather than collapsing. What
> survives the clash and returns unchanged around every loop is **soundness**;
> what distinguishes the survivors is **how many curvatures each can read before it
> has to grind.**

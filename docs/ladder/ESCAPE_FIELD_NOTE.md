# The escape field is a catastrophe fold — the clash, with GRD

*The operator gave the continuous mathematical backbone of escape-field and
continuous-geometry sensors: the **Eikonal equation** `‖∇U(x)‖ = 1/c(x)` (with
viscosity solutions, Fast Marching, HJB), and the **signed distance function**
`f(x) = sgn·inf‖x−y‖` with `‖∇f‖ = 1`, whose gradient gives geodesic navigation
`ẍ + Γ ẋẋ = 0`. This is exactly the smooth backbone of **GRD**'s escape field
`εT_t` and its geodesic `Exp(V·dt)`. We clash it against our discrete algebraic
decidability — by measuring, not asserting.*

## The two fields, discretely measured

Our system already has honest discrete analogs of both continuous objects:

| continuous framework | our discrete analog | tested artifact |
|---|---|---|
| escape field / Eikonal value `U(x)` (cost-to-boundary) | **coupling rounds** to a verdict | `coupling_breath.rounds` |
| signed distance `f(x)` to the boundary `∂Ω` | **hyperbolic depth** to the decidable region | `orbifold.hyperbolic_depth` |
| geodesic descent `fall down ∇f` | the moving frame + coupling (route to the flat chart) | `frame_solve_guided` / `_coupled` |
| bounded tunnelling `εT_t` (cross a barrier) | the certified **CDCL fallback** | `middleware_solve` |

## The finding: no smooth field — a Thom fold (`scripts/escape_fold.py`)

Dilute a satisfiable parity core with random noise and watch both fields:

| noise | xor coverage | verdict | `U` (rounds) | `f` (depth) | entailed/n |
|---|---|---|---|---|---|
| 0 | 1.00 | SAT | **0** | **0.20** | 0.00 |
| 10 | 0.91 | **CDCL_NEEDED** | **∞** | **14.16** | 0.04 |
| 25 … 320 | 0.81 → 0.25 | CDCL_NEEDED | ∞ | 14.16 | 0.04 |

Between noise 0 and 10 **everything snaps**: `U` jumps `0 → ∞`, `f` jumps from
`0.20` to `14.16` (straight to the boundary at infinity `∂∞`), and the far side is
**near-empty** — the coupling entails ~1 variable out of 26 and never more. Pure
random 3-SAT sits entirely beyond the fold at *every* α.

**So the SAT decidability landscape is a catastrophe FOLD, not a graded
Riemannian field.** The continuous Eikonal `U(x)` is smooth with `‖∇U‖ = 1/c`
everywhere; ours is a step — `0` on the polynomial island, `∞` off it — with no
gradient to descend across the boundary. This *is* the operator's **"shadow
fold"**: the decidability boundary is a discrete catastrophe, and past it lies the
`ε>0` shadow at `∂∞`.

## Why GRD is *right* to carry two velocity terms

This is where GRD pertains most sharply. Its direction field is

```
V_t = −grad_g E  +  U_t  +  J∇H  +  εT_t
      (descent)     (frame)        (tunnelling / escape)
```

A *purely geodesic* optimizer — descend `∇f` only — would be **trapped at the
fold**, exactly as a pure-frame solver is trapped at `CDCL_NEEDED`. GRD anticipates
this by including the **bounded tunnelling `εT_t`** as a separate term: you cannot
geodesically cross a catastrophe fold, so you must *tunnel* across it. Our
architecture is precisely this decomposition:

- on the **island** (decidable), descend the smooth chart — the coupling breathes
  to a fixpoint (GRD's `−grad + U_t`);
- at the **fold**, tunnel — hand off to certified CDCL (GRD's `εT_t`).

GRD's two-part `V_t` is not decoration; it is the *correct* response to a folded
landscape, and it explains two of our own measured results:

- **why the warm-start was a half-negative** (`GRD_CLASH_NOTE.md`): there is no
  smooth escape field to descend into CDCL — the far side of the fold is
  near-empty (entailed/n ≈ 0.04), so the coupling has almost nothing to hand the
  tunnelling step. The escape field carries structure only *up to* the fold.
- **why the frames "win by deciding, not by helping grind"**: the island is where
  we are polynomial; across the fold there is no gradient, only tunnelling, and
  the tunnel (CDCL) is someone else's engine.

## The honest boundary (Charter)

- **Measured**: the fold (verdict/`U`/`f` all snap at ~10 noise clauses); the
  near-empty far side; random-3SAT beyond the fold at every α.
- **Lens, not proven**: that `hyperbolic_depth` is a *viscosity solution* of an
  Eikonal equation, or a true SDF with `‖∇f‖=1`. It is a constructed distance that
  *behaves* like a signed distance to the decidable region (a step there, not a
  smooth ramp) — the analogy is directional, not an equation we solved.
- **The synthesis**: the continuous escape-field/geodesic picture is the smooth
  ideal; the SAT reality is folded; and the operator's "harmoniously coupled
  geometric expansion" is the coupling *widening the island's basin before the
  cliff* (Nelson–Oppen decides some instances no single frame does), while the
  "shadow fold" is the catastrophe boundary itself, past which only tunnelling —
  GRD's `εT_t`, our CDCL — can move.

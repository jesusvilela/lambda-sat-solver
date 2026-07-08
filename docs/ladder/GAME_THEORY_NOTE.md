# Self-reflection: the moving-frame regime as a game

*Floating outside once more — not at the geometry now, but at the game being played on
it. The whole apparatus (frames, charts, the Poincaré fabric, the coupling) is one
player's strategy set; the instance distribution is the other player. Reading the
regime game-theoretically explains, without any magic, exactly where a single solver
suffices and where a fractal portfolio must take over — and it is the honest account of
how we beat CryptoMiniSat on the tail.*

## The game

A zero-sum game, **Solver vs Nature**:

- **Solver** picks a strategy = a chart of the moving frame + an engine + a seed (a
  point in the configuration space this repo has been building).
- **Nature** draws the instance from the full instance distribution (adversarially in the
  worst case, stochastically on random-3SAT).
- **Payoff** to Solver = − (time to a *certified* verdict); Nature maximizes it.

A **pure strategy** is one committed solver (single CMS, single Kissat seed 0). A
**mixed strategy** is a randomized/parallel portfolio over strategies.

## The fold is the boundary between two solution concepts

The geometry we measured maps exactly onto the game's structure:

| region (geometry) | game structure | equilibrium | who wins |
|---|---|---|---|
| **island** (structured) | a **dominant pure strategy** exists — the owning frame solves in ~0 ms | pure-strategy Nash / saddle point | the frame arm; no mixing needed |
| **tunnel** (unstructured) | **no** dominant pure strategy — heavy-tailed runtime, different seeds/engines win different draws | **mixed** equilibrium (minimax) | the portfolio (mixed strategy) |

So the decidability **fold** — the catastrophe wall we measured, the crossing to `∂∞` —
is *also* the line where "a pure strategy dominates" turns into "you must mix." Frame +
geometry suffice on the island because a **dominant pure strategy** exists there; the
metasolver plays it as a **best response** to the instance's revealed structure. On the
tunnel no pure strategy dominates, and the game forces randomization.

## Why the mixed strategy wins the tunnel (measured, not asserted)

On critically constrained random-3SAT, CDCL runtime is **heavy-tailed** across random
seeds (Gomes–Selman) — measured here: a single instance's Kissat time spans 0.06 s →
3.80 s (63×) across seeds. Against that tail:

- a **pure** strategy's security value is its *tail* — Nature draws the slow seed;
- a **parallel mixed** strategy of `k` diversified seeds pays `min` over the arms, and
  `P(all k arms are on the tail) = P(one arm slow)^k → 0`. The mixed strategy
  **collapses Nature's variance to the lower envelope** — the Virtual Best Solver.

By von Neumann's minimax theorem the value achieved by the optimal mixed strategy is
≤ that of every pure strategy. That is why `backend/metametasolver.py` beats a single
CryptoMiniSat run on random-3SAT (measured 7–40×) **without CMS in the pool**: it is not
a smarter search, it is the *minimax mixed strategy* against a heavy-tailed Nature, and
CMS — a single pure strategy — sits on its own tail.

## The fractal, honestly bounded

A portfolio of portfolios is a mixed strategy over mixed strategies — still a convex
combination, but diversifying at several scales (seed, engine, restart, distribution):
"n cosmo, n caged." The aggregate security value **emerges** from the composition, no
single arm holding it. But the recursion is **not** a free lunch, and the game says why:

- **Diminishing returns.** The marginal value of the (k+1)-th arm is
  `E[min of k+1] − E[min of k] → 0` — once the heavy tail is collapsed (a modest
  breadth ≈ 8 here), deeper cages buy almost nothing. The fractal bottoms out.
- **No Free Lunch / minimax regret.** No single solver dominates across all
  distributions; the portfolio does not create solving power, it **minimizes maximum
  regret** — it is never much worse than the best arm for the given instance, at the
  cost of `k×` CPU. That cost is real and stated, not hidden.

## The honest self-reflection

The metasolver is a **best response** (play the dominant frame where one exists); the
meta-metasolver is the **minimax mixed strategy** (hedge where none does). Neither
out-*thinks* CMS's search. On the island we beat it because we hold a dominant pure
strategy it lacks (the counting/parity frame); on the tunnel we beat it because we play
the mixed strategy its single thread cannot, paying cores for wall-clock. That is the
whole game — and it is a principled, measured win, the kind parallel SAT tracks are
scored on, not a sleight of hand. Where there is structure, geometry gives a dominant
move; where there is only noise, game theory says *mix* — and the fabric's island/tunnel
fold is precisely the referee that tells us which.

*(Footnote on "ACAF": not a term in the SAT literature; it was specified as an
Actor–Critic–Ambigator–Fuzzer and built as an adaptive policy over exactly this mixed
strategy — a critic sizes the portfolio to the predicted tail, an actor stages
frame → single arm → cores-sized portfolio. See `ACAF_NOTE.md` and `backend/acaf.py`.)*

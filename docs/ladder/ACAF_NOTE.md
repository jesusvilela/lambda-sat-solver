# ACAF, and lambda logic as a universal game solver

*Your two questions: what is our lambda logic **as a universal game solver**, and how
might it **win the trivial instances** (which the fixed portfolio lost to overhead) or
**best the strongest** Kissat/CMS (which it only tied)? The answer is one idea seen from
two sides, and it is measured, not asserted.*

## Lambda logic as a universal game solver

The game-theory note cast solving as Solver vs Nature. Lambda calculus is the universal
substrate (Church–Turing), so it can host the whole game:

- **Strategies are terms.** A solver is a term `CNF → verdict`; a move is application
  `strategy(instance)`; the payoff is the reduction cost (β-steps / time). Our pipeline
  *is* this — `app(policy, instance)`.
- **The equilibrium is a fixpoint.** The actor–critic solution of a game is a fixpoint:
  the Critic's value obeys the Bellman equation `V = T(V)`, the Actor is greedy w.r.t.
  `V`, and improving the policy iterates to a fixed point. In lambda calculus fixpoints
  are the **Y combinator**, `Y f = f (Y f)` — so the universal game-solver *kernel* is
  the fixpoint combinator, and it already lives in this repo as
  `lambda_sat.fixpoint_sat` (the self-referential Möbius drone, the one sustained tone
  `ε > 0`). Actor–critic is Bellman is Y.
- **Universality, honestly bounded.** Lambda can *express* Kissat's search, CMS, our
  frames, the portfolio, the ACAF policy — but expressing is not executing efficiently:
  running CDCL as β-reductions would be astronomically slow. So lambda logic is the
  universal **policy language** and the zero-overhead **in-process kernel**, not the
  fast executor. The native engines are the hardware the lambda policy dispatches. This
  *is* the actor–critic architecture: a cheap universal policy choosing fast specialized
  executors.

That is the whole answer in one line: **lambda logic is the fixpoint substrate in which
the game and its equilibrium are written; the engines are the moves it plays.**

## ACAF — the adaptive policy (`backend/acaf.py`)

Four organs, each grounded in existing machinery:

| organ | role | realized as |
|---|---|---|
| **Critic** | value estimate: does frame+geometry suffice; how heavy the tail | `dynamics.describe` + a geometric hardness read off the holographic screen ∂∞ (`_cosmological_hardness`) |
| **Actor** | staged policy: frame → single arm → cores-sized portfolio | `frame_solve_scouted` → `_certified_cdcl` → `_parallel_cdcl_portfolio` |
| **Ambigator** | polysemy/region sets how much to diversify | `dynamics` conserved-count / hardness → breadth |
| **Fuzzer** | emit decorrelated engine+seed configs (collapse the tail) | `_fuzzer(breadth)` |

## The critic's hardness — a position on the holographic screen, not a Euclidean ramp

The critic's value estimate was a flat scalar, `min(1, n/260)` — hardness as a straight
Euclidean ramp in the variable count. That threw the geometry away. The fabric already
places every instance on the **Poincaré ball**: a frame-decided instance sits near the
centre, a frame-void (CDCL) instance falls to the **boundary at infinity ∂∞**, an
*infinite* hyperbolic distance out (`orbifold.hyperbolic_depth`, FABRIC_MODEL_NOTE). By
the time the critic is asked for a tunnel hardness the instance has **already fallen to
∂∞** — and there the radial coordinate *degenerates*: measured, `gyration` pins at ~14.16
for **every** tunnel instance, all `n`, all `α`. Rigidity is exhausted; every tunnel
instance is equally structureless.

So hardness cannot live on the radial axis. Holographically it lives on the screen's own
intrinsic coordinates (`backend/acaf._cosmological_hardness`):

- **horizon (scale)** — the assignment cosmos holds `2^n` points; in a curvature −1 space
  volume grows as `e^d`, so `2^n` subtends a comoving horizon `d ~ n ln2`. Mapped back
  *through* the boundary as `tanh(n/N*)`, so the saturation toward 1 is the **geometry's
  own** — there is no artificial `min()` clamp any more.
- **criticality (caustic)** — solutions grow scarce on the phase-transition ridge
  `α_c = 4.26`; a `sech(κ·(α−α_c))` caustic is 1 on the ridge and decays for over- and
  under-constrained cosmoses, which are easy at any scale.
- **screen gate** — `tanh(gyration)` confirms the instance is truly at ∂∞ (frame-void)
  before charging full hardness, honestly discounting any residual near-fold structure.

`hardness = screen · horizon · (½ + ½·caustic)`, in the open interval (0, 1).

The improvement is behavioural, not only aesthetic. `n/260` is **blind to α**: at `n=240`
it hands the same 4-arm swarm to a critical instance and to a trivially over- or
under-constrained one. The screen reads criticality — measured, at `n=240`, α=4.26 gets
the full 4 arms while α=2.5 and α=7.0 (easy tails) step down to 3, returning a core the
old ramp wasted. The measured onset is preserved: `N* = 175` puts the ~220-var heavy-tail
knee at `tanh(220/175) ≈ 0.85`, so the actor's single-vs-portfolio staging is unchanged
where it was already calibrated.

- **Measured**: the gyration pinning at ∂∞ (all n, all α); the (0,1) bounds with no clamp;
  monotonicity in scale on the ridge; the caustic peak on α_c and monotone decay off it;
  the α-blindness of the old ramp vs the α-sensitivity of the screen (arm-count differential).
- **A proxy, never a proof (Charter)**: this is the critic's *expected*-tail-weight
  estimate that sizes the mixed strategy — it is a heuristic value function, not a theorem
  about any single instance's runtime. Soundness is untouched: every verdict stays
  certified regardless of how many arms the screen provisioned.
- **Lens, not proven**: that `n ln2` is the *right* comoving law or `sech` the *true*
  caustic profile (both are fitted, elegant readings of the manifold the fabric measures),
  and that `α_c = 4.26` transfers verbatim off random-3SAT (it is the 3SAT ridge; other
  families have their own, so the caustic is a random-SAT-calibrated prior, not a universal
  constant).

## Winning the trivial tier — the answer is the *certificate*, not the search

The fixed portfolio lost trivial instances to **launch overhead** (9 subprocess spawns on
a 0.01 s instance). ACAF's actor fixes that structurally: trivial instances take the
**single-arm** stage — one process, no swarm. Measured decomposition of what remains on a
trivial UNSAT random-3SAT:

    solve = 54 ms      DRAT-certify = 117 ms      (the proof is 2–3× the solve)

So the residual gap to CryptoMiniSat's 0.01 s is **the certificate**, not the search: CMS
ships an *unchecked* verdict; we ship a *machine-checked* one. This is exactly where
lambda logic wins the trivial tier honestly:

- On **structured** trivial instances (php, tseitin, xorsat) the frames — the lambda/
  algebraic layer — decide **in-process, instantly, and sound *by construction***: the
  certificate is the derivation itself, no external checker. php12: **0.03 s certified**
  vs CMS **30 s timeout**. We win outright.
- On **unstructured** trivial instances the solve is instant and the *proof* is the cost.
  A lambda-style constructive certificate is free; a CDCL DRAT proof must be re-checked.
  So we win trivial exactly where structure lets the certificate come for free, and we
  pay the proof only where the instance forces CDCL. That is a principled position, not a
  deficiency — it is the Charter (verify, don't trust) priced in.

## Besting the strongest engine — size the mixed strategy to the cores

The fixed 9-arm portfolio *oversubscribed* a 4-core box and lost to single Kissat.
Measured, sizing the diversified portfolio **to `nproc`** collapses the heavy tail with
minimal contention and beats the single engine:

| arms on 4 cores | hard-band total (5 instances) |
|---|---|
| k=1 (single Kissat) | 37.0 s |
| k=3 | 34.2 s |
| **k=4 (= nproc)** | **34.0 s — beats single on 5/5** |

ACAF's Ambigator sizes `breadth = round(1 + hardness·(cores−1))`, so a light tail spends
one core and a heavy tail spends all of them — the adaptive mixed strategy the fixed
portfolio lacked. Measured on the hard tunnel: hard-n260 **3.8 s** vs CMS 23 s; hard-n280
**13.5 s** vs CMS 30 s (timeout), at breadth 4.

## What this is, and is not (Charter)

- **Measured**: every stage transition and number above; ACAF verdicts are certified;
  the DRAT-vs-solve decomposition; the nproc-sizing win over single Kissat.
- **The honest claim**: ACAF is *overhead-* and *core-optimal in the certified regime* —
  it wins the structured tier outright (constructive certificate), wins the hard tunnel
  by an adaptively-sized mixed strategy, and on the trivial-unstructured tier its only
  gap to an uncertified solver is the machine-checked proof it insists on.
- **Not claimed**: that ACAF is a trained deep-RL agent (it is an actor-critic-*structured*
  policy with a calibrated critic, not a learned network); that lambda out-*searches*
  CDCL (it does not — it is the policy language and the constructive-certificate kernel);
  that the tail can be abolished (a mixed strategy hedges it; some instances time out on
  every arm). Actor–critic is Bellman is Y — the universal game-solver is the fixpoint,
  and the engines are its moves.

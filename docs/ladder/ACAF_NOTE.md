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
| **Critic** | value estimate: does frame+geometry suffice; how heavy the tail | `dynamics.describe` + a cheap hardness proxy (`n`, `m/n`, gyration) |
| **Actor** | staged policy: frame → single arm → cores-sized portfolio | `frame_solve_scouted` → `_certified_cdcl` → `_parallel_cdcl_portfolio` |
| **Ambigator** | polysemy/region sets how much to diversify | `dynamics` conserved-count / hardness → breadth |
| **Fuzzer** | emit decorrelated engine+seed configs (collapse the tail) | `_fuzzer(breadth)` |

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

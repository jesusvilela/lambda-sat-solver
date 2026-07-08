# Beating every solver, including CryptoMiniSat — the description reverted into a dispatch

*The operator's highest-altitude ask: float outside the model, collect the **laws,
relations and motions** of the solve in lambda logic dynamically, then **revert**
them into operation — using that descriptive power precisely **where frame and
geometry do not suffice**, to beat every solver including CryptoMiniSat. This note is
the measured landing.*

## The three registers of the description (`backend/dynamics.py`)

Floating outside, an instance already has a dynamical signature under the coupled
router, read into three registers before any search:

- **Laws** — the conserved invariants: a GF(2) parity invariant, a ℤ counting bound,
  a 2-SAT implication closure; and whether the verdict is sound-by-construction.
- **Relations** — the couplings: the literals one frame **entails** and hands the
  others (the Nelson–Oppen exchange), and how many cross.
- **Motions** — the trajectory: the breath (entailed-literal count per round), its
  amplitude, whether it resonates to rest, and the instance's place in the hyperbolic
  mesh (gyration/depth toward `∂∞`) and relative to the decidability fold.

`describe(formula).sufficient()` is the pivot: **True** when frame+geometry already
decide it (a certified verdict, no search), **False** when they do not — the exact
place the description must be reverted into a dispatch.

## The revert (`backend/metasolver.py`)

- **Sufficient** (the counting and parity islands) → the certified frame verdict in
  ~0 ms. *This is where the metasolver beats CMS.*
- **Insufficient** (the tunnel) → a DRAT-certified CDCL engine on the original
  formula. Every verdict certified end-to-end (frame-sound | DRAT | model replay);
  CMS is never trusted for a verdict, only raced as a competitor.

## The measured terrain — why the win is structural, not a faster search

Head-to-head on the **tunnel** (random-3SAT), CryptoMiniSat is *competitive-to-faster*
than Kissat and CaDiCaL (it wins most small instances outright). **So the metasolver
does not, and does not claim to, out-CDCL CMS on unstructured instances** — there it
matches the strong engines. CMS also **owns parity**: on `tseitin nv80s1` Kissat and
CaDiCaL both time out (20 s) while CMS solves it in 1.37 s via its Gaussian engine —
and the parity **frame** still beats CMS, 0 ms vs 1.37 s.

The decisive axis is **counting**: CMS carries no counting engine, so pigeonhole is
exponential for it (`php10`/`php12` time out) while the counting frame refutes in
~0 ms. On a competition-style mix that includes counting and parity — as real
benchmarks do — the metasolver is instant where CMS blows up and comparable where CMS
is strong, so it dominates the aggregate.

## Results — four solvers live (`scripts/metasolver_benchmark.py`)

Solved-count / PAR-2 by family (40 instances, 20 s timeout):

| family | n | Kissat | CaDiCaL | CryptoMiniSat | **metasolver** |
|---|---|---|---|---|---|
| random3 | 9 | 9/9 · 0.12 s | 9/9 · 0.13 s | 9/9 · 0.18 s | 9/9 · 0.23 s |
| **tseitin** (parity) | 9 | 5/9 · 18.98 s | 5/9 · 18.83 s | 9/9 · 0.95 s | **9/9 · 0.00 s** |
| xorsat | 12 | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s |
| **php** (counting) | 4 | 3/4 · 10.77 s | 4/4 · 0.12 s | **2/4 · 24.51 s** | **4/4 · 0.00 s** |
| mixed | 6 | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.01 s |
| **TOTAL** | **40** | 35/40 · 5.38 s | 36/40 · 4.28 s | 38/40 · 2.71 s | **40/40 · 0.05 s** |

**CryptoMiniSat is the strongest baseline** — 38/40, PAR-2 2.71 s: its Gaussian
engine owns parity (9/9 tseitin where Kissat and CaDiCaL manage only 5/9), so it beats
both raw CDCL engines. But it carries **no counting engine**, so pigeonhole breaks it
(**php 2/4, PAR-2 24.51 s** — it times out on php10 and php12). The metasolver is
**40/40 at PAR-2 0.05 s — 49.9× better PAR-2 than CMS**, 99.2× than Kissat — with
**26/40 decided by a certified frame, no CDCL**, and **40/40 verdicts certified**.
Even on parity, where CMS is strong, the frame beats it (0.00 s vs 0.95 s); the
metasolver only *matches* CMS on the random-3SAT tail (0.23 s vs 0.18 s — the small
gap is DRAT certification, the value-add).

## What this is, and is not (Charter)

- **Measured**: every number above is a live run of Kissat 4.0.4, CaDiCaL 3.0.0,
  CryptoMiniSat 5.14.7 (pycryptosat) and the metasolver; every metasolver verdict is
  certified.
- **The honest claim**: on a competition-style mix, the description-driven metasolver
  **dominates every individual solver including CMS on solved-count and PAR-2** —
  because it is instant on the counting/parity fragments where they blow up, and
  comparable on the unstructured tail. It is a *portfolio dominance*, the legitimate
  kind competition solvers are built on, driven by an explicit dynamical description.
- **Not claimed**: that the metasolver out-*searches* CMS on random-3SAT (it does
  not — CMS is a strong CDCL there); that lambda descriptive power breaks the tunnel
  (it does not — an unstructured instance has no laws to exploit, `conserved == []`).
  The descriptive power's leverage is real exactly where there is structure to
  describe, and honestly absent where there is none.
- **Open lens**: description-driven engine-selection over {Kissat, CaDiCaL} on the
  tunnel — the engines split wins, but no cheap feature yet predicts the winner
  reliably, so the dispatch defaults to Kissat and the selector stays a hook, not a
  shipped predictor.

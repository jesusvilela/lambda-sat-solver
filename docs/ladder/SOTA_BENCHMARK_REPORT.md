# SOTA stress benchmark — frame-aware middleware vs raw SOTA CDCL

**Question:** subjected to a SAT-competition-style mix, does the frame-aware
middleware (sound algebraic frames → certified CDCL fallback) beat raw SOTA CDCL,
and where does it *not*? Engines: **Kissat 4.0.4** and **CaDiCaL** (both raw),
and the **middleware** = the **scout-gated coupled ("breathing") frame router**
(`frame_solve_scouted`): three sound poly-time frames — implication/2-SAT
(`check_binary_clauses`), parity/GF(2) (`gf2_xor_refutation`/`gf2_xor_solve`),
counting/cardinality (`pigeonhole_counting_refutation`) — run as three theories
that exchange entailed literals to a fixpoint (inhale/propagate → resonate/settle),
fronted by a cheap tunnel gate that skips the algebraic pre-pass on structureless
instances (~3.3× faster there, 0 verdict regressions — `PIPELINE_REVIEW_NOTE.md`),
then a **DRAT- and model-certified Kissat fallback** only when the router escalates.
This same router is now wired into the production `SolverMiddleware` itself, not just
the benchmark (F1, `PIPELINE_REVIEW_NOTE.md`). 40 instances, 5 families, 20 s
timeout. Harness `docs/ladder/scripts/sota_benchmark.py`; raw rows
`sota_benchmark_results.json`.

## Results — solved-count / PAR-2 by family

| family | n | Kissat | CaDiCaL | Middleware |
|---|---|---|---|---|
| random3 (α=4.26) | 9 | 9/9 · 0.12 s | 9/9 · 0.13 s | 9/9 · 0.19 s |
| **tseitin** (parity) | 9 | 5/9 · 18.97 s | 5/9 · 18.83 s | **9/9 · 0.00 s** |
| xorsat | 12 | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s |
| **php** (counting) | 4 | 3/4 · 10.78 s | 4/4 · 0.12 s | **4/4 · 0.00 s** |
| mixed | 6 | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.00 s |
| **TOTAL** | **40** | **35/40 · 5.38 s** | **36/40 · 4.28 s** | **40/40 · 0.04 s** |

The middleware solves **40/40 at PAR-2 0.04 s** — ~134× better PAR-2 than raw
Kissat and ~107× than CaDiCaL — with **26/40 decided by a sound algebraic frame
with no solver at all** (22 parity, 4 counting), and **40/40 verdicts certified**
(fast-path sound by construction, or Kissat-UNSAT verified by drat-trim, or
Kissat-SAT verified by model replay). **Honest scope of the scout gate**: it holds
the totals identical to the coupled router (same verdicts) — its measured win is on
the *pre-pass*, whereas random-3SAT's PAR-2 is bound by the DRAT **certification** of
the UNSAT proof (the value-add), not the pre-pass. The scout gate removes wasted
algebraic work; it does not remove certification.

## How the three frames divide the work

Each family that is hard for CDCL is easy for exactly one frame:

- **tseitin** → the parity frame (`gf2`): 9/9 in <1 ms while both CDCL engines
  time out on 4/9 (~19 s PAR-2). GF(2) linear algebra is polynomial where
  resolution needs exponential width.
- **php** → the counting frame (`counting`): 4/4 in <0.5 ms, including **php12,
  which Kissat times out on**. Its obstruction is a magnitude fact (12 > 11)
  that GF(2) cannot see — the char-0 dual of Tseitin
  (`COUNTING_FRAME_NOTE.md`).
- **random3 / mixed(SAT) / xorsat** → decided by parity where covered, else the
  certified Kissat fallback; on these the middleware ties raw CDCL (the fallback
  is the same engine).

## The honest comparison — CryptoMiniSat already does this in production

The frame router is a *sound re-derivation of an idea that exists in production C
solvers*. **CryptoMiniSat** recovers XOR constraints from CNF and runs Gaussian
elimination on them — exactly the parity frame, built into a general solver.
Measured on this repo's own Tseitin generator (pycryptosat 5.14.7, same CNF, no
hints):

| instance | Kissat 4.0.4 (pure CDCL) | CryptoMiniSat 5.14.7 | our GF(2) router |
|---|---|---|---|
| tseitin nv100 | **TIMEOUT** (>12 s) | UNSAT 1.16 s | UNSAT 1.3 ms |
| tseitin nv150 | **TIMEOUT** | UNSAT 1.23 s | UNSAT 1.8 ms |
| tseitin nv200 | **TIMEOUT** | UNSAT 1.11 s | UNSAT 3.4 ms |

Read this honestly, both directions. The win over **pure-CDCL** (Kissat, CaDiCaL)
is real and decisive — neither has parity reasoning, even in the newest release.
And on **parity**, CryptoMiniSat *already* embodies the same principle, in C, as a
*general* solver: it solves these in ~1 s. Our router is faster on pure parity
(direct Gaussian, no CDCL machinery) but on that fragment it is a **sound
re-derivation of a known production idea**, not a new capability.

**But there is a genuinely different fragment, and it is measured**
(`BEYOND_CDCL_NOTE.md`, `scripts/beyond_cdcl.py`). CryptoMiniSat's XOR+Gaussian is
blind to **counting**: pigeonhole has no XOR structure, so CMS faces the same
exponential resolution wall as pure CDCL and **times out even earlier than Kissat**
(php10: Kissat 403 ms, CMS *timeout*; php12: both timeout) — the XOR preprocessing
becomes pure overhead. The counting frame refutes php12 in **4 ms**. So the
contribution is **not** the parity fragment (CryptoMiniSat owns that) but the
**counting/cardinality fragment plus the cross-frame coupling** (Nelson–Oppen
across implication/parity/counting), which neither Kissat, CaDiCaL, nor
CryptoMiniSat performs. Honest scope: a measured fragment-coverage result on
structured instances, not a general SAT-competition victory.

## Honest scope — still not a new CDCL engine

The middleware does **not** improve CDCL search; it is a set of sound
*frame detectors + decision procedures* in front of one. Its dominance holds
because the benchmark includes the parity and counting categories that real
competitions weight (crypto/Tseitin, cardinality), and on those the right
algebraic frame is polynomial while resolution is exponential. On a pure
random-3-SAT benchmark it would be Kissat + ε (here the ε is the DRAT
certification cost: random3 PAR-2 0.10 → 0.22 s — the honest price of certifying
every fallback rather than trusting it).

Two earlier caveats from the first run are now resolved *by the geometry, not by
luck*:

1. The php12 miss is gone — not by swapping in CaDiCaL as a fallback, but by
   building the **counting frame** the obstruction actually lives in. The gap
   the benchmark exposed pointed straight at the missing third frame.
2. The 18 previously-unverified Kissat fallbacks are gone — **DRAT is back**:
   UNSAT fallbacks are checked by drat-trim, SAT fallbacks by model replay, so
   **every one of the 40 verdicts is certified**, consistent with the repo's
   "Kissat is not in the TCB" guarantee.

## Cross-checks

Every instance decided by two or more strategies agreed (no SAT/UNSAT
disagreement across Kissat, CaDiCaL, and the middleware). Every fast-path verdict
is sound by construction (entailed XORs; the counting bound; 2-SAT SCCs), and
every fallback verdict carries an independent certificate. 40/40 certified.

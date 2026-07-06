# SOTA stress benchmark — frame-aware middleware vs raw SOTA CDCL

**Question:** subjected to a SAT-competition-style mix, does the frame-aware
middleware (sound algebraic frames → certified CDCL fallback) beat raw SOTA CDCL,
and where does it *not*? Engines: **Kissat 4.0.4** and **CaDiCaL** (both raw),
and the **middleware** = three sound poly-time frames —
`check_binary_clauses` (implication/2-SAT), `gf2_xor_solve` (parity/GF(2)),
`pigeonhole_counting_refutation` (counting/cardinality) — then a **DRAT- and
model-certified Kissat fallback**. 40 instances, 5 families, 20 s timeout.
Harness `docs/ladder/scripts/sota_benchmark.py`; raw rows
`sota_benchmark_results.json`.

## Results — solved-count / PAR-2 by family

| family | n | Kissat | CaDiCaL | Middleware |
|---|---|---|---|---|
| random3 (α=4.26) | 9 | 9/9 · 0.10 s | 9/9 · 0.11 s | 9/9 · 0.22 s |
| **tseitin** (parity) | 9 | 5/9 · 18.83 s | 5/9 · 18.75 s | **9/9 · 0.00 s** |
| xorsat | 12 | 12/12 · 0.00 s | 12/12 · 0.00 s | 12/12 · 0.00 s |
| **php** (counting) | 4 | 3/4 · 10.67 s | 4/4 · 0.10 s | **4/4 · 0.00 s** |
| mixed | 6 | 6/6 · 0.00 s | 6/6 · 0.00 s | 6/6 · 0.00 s |
| **TOTAL** | **40** | **35/40 · 5.33 s** | **36/40 · 4.26 s** | **40/40 · 0.05 s** |

The middleware solves **40/40 at PAR-2 0.05 s** — ~100× better PAR-2 than raw
Kissat and ~85× than CaDiCaL — with **26/40 decided by a sound algebraic frame
with no solver at all**, and **40/40 verdicts certified** (fast-path sound by
construction, or Kissat-UNSAT verified by drat-trim, or Kissat-SAT verified by
model replay).

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

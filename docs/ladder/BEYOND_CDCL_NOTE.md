# Beyond CDCL and CryptoMiniSat — the measured boundary

*Three standing critiques of the SOTA benchmark, answered by measuring the exact
boundary rather than asserting it. Harness `docs/ladder/scripts/beyond_cdcl.py`
(Kissat 4.0.4, CryptoMiniSat via pycryptosat 5.14.7, middleware), 10 s timeout.*

## The three-way result

| instance | Kissat | CryptoMiniSat | middleware |
|---|---|---|---|
| **parity** Tseitin nv60 | UNSAT 154 ms | UNSAT 115 ms | UNSAT · parity 13 ms |
| parity Tseitin nv80 | UNSAT 1908 ms | UNSAT 1470 ms | UNSAT · parity 2 ms |
| parity Tseitin nv100 | **TIMEOUT** | UNSAT 1268 ms | UNSAT · parity 2 ms |
| parity XORSAT n60 | UNSAT 3–4 ms | UNSAT 6–7 ms | UNSAT · parity 1 ms |
| **counting** php10 | UNSAT 403 ms | **TIMEOUT** | UNSAT · counting 3 ms |
| counting php11 | UNSAT 2558 ms | **TIMEOUT** | UNSAT · counting 3 ms |
| counting php12 | **TIMEOUT** | **TIMEOUT** | UNSAT · counting 4 ms |

## Critique 3 — "CryptoMiniSat already does XOR recovery + Gaussian"

**True, and now shown.** On the **parity** families CryptoMiniSat matches — it
even solves Tseitin nv100 where raw Kissat times out, because its XOR+Gaussian is
real production machinery. On parity the frames **re-derive what CMS already
ships**; we claim no novelty there.

**But CMS is structurally blind to counting.** Pigeonhole has *no* XOR structure,
so CMS's recovery finds nothing, its CDCL core faces the same exponential
resolution wall as Kissat — and it times out **even earlier** than Kissat (php10:
Kissat 403 ms, CMS timeout), the XOR preprocessing now pure overhead. The counting
frame refutes php12 in 4 ms. So the middleware is **not redundant with CMS**: the
**counting/cardinality fragment** is a genuinely different polynomial island that
even the XOR-aware production solver cannot reach — plus the **cross-frame
coupling** (Nelson–Oppen across implication/parity/counting) that none of Kissat,
CaDiCaL, or CMS performs.

## Critique 1 — "the benchmark is favorable by construction"

The families are the classic **CDCL-hard structured** families (Tseitin, PHP),
not instances cherry-picked *for the middleware*. The sharper evidence is exactly
this three-way table: the *other* XOR-aware SOTA solver falls into the **same
exponential trap** on the counting family. We do not win by choosing easy
instances — we win by covering a fragment (counting) that both a pure-CDCL SOTA
solver and an XOR-aware SOTA solver structurally cannot. On unstructured instances
(random 3-SAT at any α) the frames correctly add nothing but a cheap certified
pre-pass, and the report says so.

## Critique 2 — "not a general CDCL replacement"

Correct, and never claimed otherwise. The frames decide a **polynomial island**
(2-SAT ∪ parity ∪ counting ∪ what their coupling entails); everything else
escalates to certified Kissat. The honest frontier is **cooperation, not
replacement**: the coupled router already *breathes out* sound entailed literals
even on instances it does not fully decide (`coupling_breath`), and feeding those
to CDCL as a warm-start — growing *with* the engine rather than merely gating it —
is the next measured step (an experiment, not yet a claim).

## The honest one-line framing

> On a structured mix (parity + counting), the frame-aware certified middleware
> substantially outperforms **both** a pure-CDCL SOTA solver (Kissat/CaDiCaL) and
> an **XOR-aware** SOTA solver (CryptoMiniSat) — the latter because the counting
> fragment and the cross-frame coupling are outside XOR+Gaussian — while falling
> back to certified CDCL on instances outside the recognized frames. Not a general
> SAT-competition victory; a measured fragment-coverage and certification result.

---
title: "Structured Islands Before CDCL — A Certified SAT Middleware"
---

# Structured Islands Before CDCL

### A certified SAT middleware

*A narrow, reviewable note: here is the executable claim, here is the certification
boundary, here is where CDCL remains sovereign.*

## Abstract

λSAT is a headless SAT middleware that decides *structured* formulas before search and
hands the rest to CDCL. A router tries three sound, engine-independent frames —
implication (2-SAT), parity (GF(2)/XOR), and counting (pigeonhole/cardinality) — and their
cross-frame coupling; a formula that lives in one is decided with a certificate and no
search. Anything else returns `CDCL_NEEDED` and is solved by Kissat. **Every emitted verdict
is independently checked**: SAT by model replay, UNSAT by a sound frame refutation or a
`drat-trim` DRAT proof. The external solver is never a trusted authority. The benchmark
claim is scoped to a small synthetic mix that includes the counting and parity fragments;
it is a statement about *certified frame routing*, not about generally out-searching CDCL.

## 1 · Motivation

SAT solvers are powerful, and getting a formula *solved* is rarely the problem. The problem
addressed here is narrower: some formulas carry structure whose contradiction is decidable
by a short algebraic argument **before** any search, and that argument is its own
certificate. λSAT separates that structured decision from unstructured search, and — the
non-negotiable part — verifies whatever it emits.

## 2 · Architecture

```
formula → router → { implication | parity | counting | coupling } → verdict → observer
                        └───────────── else: CDCL_NEEDED ──────────→ Kissat → observer
```

The router is refute-first (cheap near-linear refutation before any model reconstruction).
The observer is the certification stage: it accepts a verdict only with a checkable
certificate. `strict` mode requires the external tools to be present at startup and turns an
uncertified fallback verdict into an error; `dev`/`research` modes degrade to best-effort.

## 3 · The three frames

Each frame has an **input condition**, a **certificate**, and a **failure mode** (it must
punt, never guess).

- **Implication (2-SAT).** Condition: binary clauses. Certificate: a strongly-connected
  component placing a variable and its negation together (a sound UNSAT), or a satisfying
  assignment. Failure: no binary contradiction → punt.
- **Parity (GF(2)).** Condition: recoverable XOR constraints. Certificate: Gaussian
  elimination reaching `0 = 1` (UNSAT), or a reconstructed, re-verified model. Failure:
  parity does not cover the formula / underdetermined → punt.
- **Counting (ℤ).** Condition: pigeonhole-shaped `k` disjoint at-least-one clauses covered
  by `m < k` at-most-one cliques. Certificate: the magnitude contradiction `k > m`. Failure:
  structure absent → punt.

The **coupling** exchanges entailed literals across frames to a fixpoint (Nelson–Oppen), so
an instance no single frame decides can still be decided soundly; it too only emits UNSAT via
a channel refutation or SAT via a verified model.

## 4 · Certification boundary

| | trusted | not trusted |
|---|---|---|
| components | DIMACS parser · Tseitin transform · model checker · the three frame refutations · the DRAT-checker invocation | Kissat · CaDiCaL · CryptoMiniSat |

- **SAT** → the assignment is replayed against the original clauses.
- **UNSAT via a frame** → sound by construction (no external checker).
- **UNSAT via CDCL** → the DRAT proof is replayed by `drat-trim` (LRAT optional).

A CI lane (`certification-hard`) makes Kissat + `drat-trim` mandatory and fails red unless a
real DRAT UNSAT check and a real model-replay SAT check both execute.

## 5 · Benchmark capsule

Full detail in the [benchmark capsule](benchmark-capsule.md). In one paragraph: on a fixed
synthetic mix (random-3SAT, Tseitin, XORSAT, pigeonhole, mixed; 20 s timeout), the
frame-aware middleware decides the structured families instantly and certified, while raw
CDCL and CryptoMiniSat spend seconds or time out on the parity/counting families. On the
unstructured random-3SAT tail the middleware falls to CDCL and is **comparable**, not
better. The aggregate PAR-2 advantage is therefore a *structural* effect of the mix, not a
faster search.

## 6 · Interpretation

- **Frame-decidable islands** vs the **CDCL tunnel** — a formula either exposes an algebraic
  obstruction (decide + certify) or it does not (search).
- A parallel, seed-diversified **portfolio** helps only on the heavy-tailed tail, and only by
  spending cores for wall-clock; it is a mixed strategy, not a smarter search.
- **No-Free-Lunch holds.** There is no general dominance here, and none is claimed.

## 7 · Limitations

- The benchmark mix is **not** the SAT Competition set.
- Frames fire **only** when structure is exposed; obfuscated structure is missed.
- Random-3SAT is, and remains, **CDCL territory**.
- Strict-mode UNSAT via the fallback still requires external proof tooling (`drat-trim`).

## 8 · Reproduction

```bash
pip install -e ".[dev]"
python -m pytest backend/tests/ -q
python .github/scripts/certification_smoke.py     # forces a real DRAT + model-replay check
```

Pinned versions, per-benchmark commands, and how to read a discrepancy:
[REPRODUCIBILITY.md](https://github.com/jesusvilela/lambda-sat-solver/blob/main/REPRODUCIBILITY.md).

## 9 · Conclusion

λSAT is a claim-discipline artifact as much as a solver: **route when structure is
sufficient, search when it is not, verify either way.** The interesting object is the
certified boundary between the two — not a speed record.

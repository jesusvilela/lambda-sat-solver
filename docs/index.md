---
title: "λSAT — Certified Frame-First SAT Middleware"
description: "Structured regions before CDCL. Certified verdicts after every path."
---

# λSAT

### Certified frame-first SAT middleware

*Structured regions before CDCL. Certified verdicts after every path.*

λSAT is a certified SAT middleware. **It does not try to replace CDCL.** It first checks
whether a formula belongs to one of several structured regions with sound algebraic
certificates — implication, parity, or counting — and falls back to CDCL otherwise. Every
emitted verdict is independently checked.

That is the whole recognizer. The geometry comes later, and only as a map.

---

## 1 · The question

Modern SAT solvers are extremely strong, but a solver's *output* is not by itself an
*explanation*. λSAT asks a smaller, answerable question:

> Can some structured SAT regions be recognized and certified **before** search, while the
> unstructured tail is handed honestly to CDCL?

This deliberately avoids the dangerous claim of "a new solver that beats SOTA."

---

## 2 · Certification — the trusted computing base

This is the part that matters most.

- **SAT** is checked by **model replay** against the original formula.
- **UNSAT** is checked by either a **sound frame refutation** (self-certifying) or an
  **independent DRAT proof replay** (`drat-trim`).
- **Kissat, CaDiCaL, CryptoMiniSat are tools, not trusted authorities.**

The middleware can be wrong only if a *checker or a frame* is wrong — never merely because
an external solver said so. A wrong answer from the engine is **caught, not believed.**

```
formula
  │
  ▼
router ── implication? ─ yes ─▶ 2-SAT frame ─────┐
  │        parity?      ─ yes ─▶ GF(2) frame ─────┤
  │        counting?    ─ yes ─▶ counting frame ──┤ sound by construction
  │                                               │
  └── none of the above ─────▶ CDCL (Kissat) ─────┤ DRAT / model replay
                                                  ▼
                                          certified verdict
```

---

## 3 · The three frames

Each structured region has one sound, engine-independent frame, with an input condition, a
certificate, and an honest failure mode (it *punts* to CDCL rather than guessing).

| frame | structure | certificate |
|---|---|---|
| **implication** | 2-SAT / implication graph | SCC contradiction, or an assignment |
| **parity** | GF(2) / XOR structure | linear-algebra refutation or model |
| **counting** | pigeonhole / cardinality | an arithmetic (magnitude) contradiction |
| **fallback** | general SAT | CDCL + model replay / DRAT |

The contribution is **not** replacing CDCL. It is **deciding structured islands before
CDCL, and certifying every emitted verdict.**

---

## 4 · What the benchmark claims — and doesn't

The benchmark claim is **scoped to the included mix** (a small, fixed, synthetic set:
2-SAT, Tseitin/XOR, pigeonhole, random-3SAT, mixed). It does **not** imply general CDCL
dominance.

| family | why hard for CDCL | λSAT route | result shape |
|---|---|---|---|
| 2-SAT / implication | implication closure | implication frame | instant · certified |
| Tseitin / XOR | parity obstruction | GF(2) frame | instant · certified |
| PHP / counting | cardinality obstruction | counting frame | instant · certified |
| random-3SAT | no exposed frame | CDCL / portfolio | **CDCL remains central** |

Numbers (PAR-2, per-family) live in the [benchmark capsule](benchmark-capsule.md), not on
this page — the headline is the *routing and certification*, not a speed record.

---

## 5 · What it does **not** claim

- It does **not** solve SAT hardness.
- It does **not** dominate CDCL on arbitrary SAT.
- It does **not** claim CryptoMiniSat is weak on XOR (CMS owns parity; the frame merely
  re-derives it with a certificate).
- It does **not** make external solvers trusted.
- The hyperbolic / fabric layer is a **research map**, not part of the minimal certification
  claim.

---

## 6 · Reproduce

```bash
git clone https://github.com/jesusvilela/lambda-sat-solver
cd lambda-sat-solver
pip install -e ".[dev]"
python -m pytest backend/tests/ -q          # the soundness / certification floor
```

The certified strict path (requires Kissat + `drat-trim`):

```bash
python -m backend.cli examples/simple_sat.cnf   --mode strict     # SAT, model-replayed
python -m backend.cli examples/simple_unsat.cnf --mode strict     # UNSAT, checked
```

Full environment, pinned versions, and per-benchmark commands:
[REPRODUCIBILITY.md](https://github.com/jesusvilela/lambda-sat-solver/blob/main/REPRODUCIBILITY.md).

---

## 7 · The research ladder (a map, not a proof)

Only after the engineering is clear: the research layer studies *where SAT hardness lives* —
resolution width, Nullstellensatz degree, parity, counting, symmetry, and heavy-tailed
search. Honestly:

- resolution width and Nullstellensatz degree are **incomparable** (neither dominates);
- cheap graph-structural scalars **failed** to carry random-3SAT hardness;
- the geometry is used as a **routing / modeling lens**, not as proof by metaphor.

Index: [`docs/ladder/`](ladder/). Claim discipline: [`docs/CHARTER.md`](CHARTER.md).

---

## Links

- [Repository](https://github.com/jesusvilela/lambda-sat-solver)
- [Technical note](technical-note.md) · [Benchmark capsule](benchmark-capsule.md)
- [Reproducibility](https://github.com/jesusvilela/lambda-sat-solver/blob/main/REPRODUCIBILITY.md)
  · [Claim ledger](https://github.com/jesusvilela/lambda-sat-solver/blob/main/PUBLIC_RESEARCH_CLAIMS.md)
- [Security policy](https://github.com/jesusvilela/lambda-sat-solver/blob/main/SECURITY.md)
  · [Citation](https://github.com/jesusvilela/lambda-sat-solver/blob/main/CITATION.cff)

*Route when structure is sufficient. Search when it is not. Verify either way.*

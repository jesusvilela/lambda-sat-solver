# Lambda SAT Middleware

[![tests](https://github.com/jesusvilela/lambda-sat-solver/actions/workflows/tests.yml/badge.svg)](https://github.com/jesusvilela/lambda-sat-solver/actions/workflows/tests.yml)

A headless, math-aligned λ-logic middleware for Boolean satisfiability: it
transforms formulas into CNF, solves with **Kissat**, and **independently
certifies** every result — SAT by model replay, UNSAT by DRAT/LRAT proof
checking. On top of the solver sits an honest research program on the
*intrinsic structure of SAT hardness* (`docs/ladder/`).

This repository is deliberately pure: a Python library + CLI + a verifiable
research ladder. There is no web UI. Every claim in the research half is bound
to a test; the discipline that keeps it that way is written down in
[`docs/CHARTER.md`](docs/CHARTER.md) — read it first.

## Two halves

**1. The solver middleware** (`backend/`)
- Typed lambda DSL for composable solve/verify pipelines (`lambda_dsl.py`, `middleware.py`)
- **Lambda ⊗ SAT fusion** (`lambda_sat.py`): a Boolean lambda term is β-reduced,
  projected into CNF carrying a *remainder* (provenance from each clause back to
  its lambda node), and decided with a re-verified witness — the lambda DSL
  situated as an object the solver consumes, not just a pipeline language
- Kissat integration with version-probed heuristic flags (`kissat_wrapper.py`)
- Independent certification: model replay for SAT, DRAT/LRAT for UNSAT (`proof_checking.py`)
- Portfolio solving (`portfolio.py`), rule-based heuristic policy (`policy.py`), structural profiling (`cnf_profile.py`)
- Three sound, engine-independent frames (one per obstruction characteristic):
  implication/2-SAT (`binary_clause_check.py`), parity/GF(2) (`xor_extraction.py`),
  counting/cardinality (`cardinality_check.py`)

**2. The hardness-lower-bound ladder** (`backend/complexity/`, `docs/ladder/`)
- Intrinsic, solver-independent invariants with an enforced contract each
  (`complexity/invariants.py`, `complexity/contracts.py`)
- Two theorem-backed carriers (resolution width; Nullstellensatz degree),
  a clean negative (cheap graph invariants don't carry hardness), and the
  algebra-relative "shallow-frame" corollary — benchmarked on Kissat + CaDiCaL
  (`docs/ladder/FRAME_BENCHMARK_REPORT.md`)

Start at [`docs/ladder/README.md`](docs/ladder/README.md) for the research
index and [`docs/ladder/CONTRACTS.md`](docs/ladder/CONTRACTS.md) for the
per-invariant promises.

## Correctness — the Trusted Computing Base

**Kissat is NOT in the TCB.** Every result is independently verified:

1. CNF parser (DIMACS)
2. Tseitin transformation (formula → equisatisfiable CNF)
3. Model checker (verifies SAT assignments against the original formula)
4. DRAT/LRAT proof checkers (verify UNSAT proofs with an independent tool)

So a wrong answer from the solver is caught, not trusted.

> **Strict certification depends on external proof tools being installed.** The
> three sound frames (implication / parity / counting) are self-certifying with no
> external dependency, but the **CDCL fallback's UNSAT certificate requires
> `drat-trim`** (DRAT; LRAT optional). The middleware enforces the presence of
> Kissat + a DRAT checker at startup in strict mode; without them, frame verdicts
> stay sound but the fallback certification degrades to best-effort. See
> `PUBLIC_RESEARCH_CLAIMS.md` for the full proven / measured / speculative ledger
> and the exact TCB boundary.

## Quick start

```bash
cd backend
pip install -r requirements.txt          # Python 3.11+ (CI-tested on 3.11 & 3.12), numpy
# install Kissat and drat-trim — see BACKEND_README.md

python -m backend.cli examples/simple_sat.cnf --heuristic aggressive
python -m pytest tests/                   # the full suite
```

Docker (backend only):

```bash
docker build -t lambda-sat .
```

## Lambda pipeline example

```python
# λ cnf. solve(cnf, heuristic, budget)
pipeline = abs_('cnf',
    effect('solve', var('cnf'),
        literal({'branching': 'vsids', 'restarts': 'geometric'}),
        literal({'time_limit': 30, 'memory_limit': 256})))
middleware.type_checker.check(pipeline)          # CNF -> Result
result = await middleware.execute_pipeline(pipeline, cnf)   # executed + verified
```

## Project structure

```
lambda-sat-solver/
├── backend/
│   ├── lambda_dsl.py        # typed lambda DSL (pipelines)
│   ├── lambda_sat.py        # Lambda ⊗ SAT fusion (β-reduce → CNF + remainder)
│   ├── cnf_utils.py         # DIMACS parsing + model verification
│   ├── kissat_wrapper.py    # Kissat integration (flag-probed)
│   ├── proof_checking.py    # DRAT/LRAT verification
│   ├── middleware.py        # pipeline kernel
│   ├── portfolio.py         # parallel portfolio solving
│   ├── binary_clause_check.py  # sound 2-SAT UNSAT fast-path (implication frame)
│   ├── xor_extraction.py    # sound GF(2)/XOR fast-path (parity frame)
│   ├── cardinality_check.py    # sound pigeonhole fast-path (counting frame)
│   ├── complexity/          # the intrinsic-invariant ladder + contracts
│   ├── vdis/                # experimental hypercomplex heuristic research
│   ├── eval/                # generators + evaluation
│   └── tests/               # the full test suite
├── docs/
│   ├── CHARTER.md           # stance & claim discipline (read first)
│   └── ladder/              # the hardness research + benchmarks + scripts
├── examples/                # example CNF files
├── Dockerfile               # backend container
└── BACKEND_README.md        # backend detail
```

## References

- **Kissat** — Armin Biere (SAT solver)
- **DRAT/LRAT** — certified UNSAT proof formats
- **Ben-Sasson–Wigderson** (resolution width ↔ size); **Clegg–Edmonds–Impagliazzo** (polynomial calculus) — the ladder's theorem anchors

## License

MIT — see `LICENSE`.

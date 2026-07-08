# Reproducibility

This repository has two separable surfaces:

1. **Certified solving path** — every emitted SAT/UNSAT verdict is independently checked: SAT by model replay, UNSAT by a sound frame refutation or by `drat-trim` over a DRAT proof.
2. **Research benchmark path** — measured comparisons against external engines. These are scope-bound measurements, not claims of general SAT dominance.

## Environment

Recommended baseline:

- Python 3.11 or 3.12
- Kissat available on `PATH`
- `drat-trim` available on `PATH`
- Optional benchmark competitors: CaDiCaL, CryptoMiniSat / `pycryptosat`

The Dockerfile builds a complete headless environment with Python, Kissat, and `drat-trim`.

```bash
docker build -t lambda-sat-solver .
docker run --rm lambda-sat-solver
```

## Local install

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

If using the package metadata:

```bash
pip install -e .[dev,proof,bench]
```

## Certification smoke tests

Run the normal test suite:

```bash
python -m pytest backend/tests/ -q
```

For publication/release claims, also run at least one strict certification path with external proof tools installed:

```bash
python -m backend.cli examples/simple_sat.cnf --mode strict
python -m backend.cli examples/simple_unsat.cnf --mode strict
```

Expected solver-style exit codes are `10` for SAT and `20` for UNSAT.

## Benchmark reproduction discipline

When reporting benchmark numbers, include:

- commit SHA;
- Python version;
- CPU model and core count;
- RAM;
- OS;
- solver versions and exact binary names;
- timeout policy;
- instance list or generator seeds;
- command used;
- raw CSV/JSON output.

The benchmark claims in the repository should be read as **measured on the included benchmark mix** unless explicitly stated otherwise. The intended interpretation is structural portfolio dominance on frame-decidable regions plus certified CDCL fallback, not a claim that the middleware universally out-CDCLs modern solvers.

## Claim register

Before citing or announcing a result, check `PUBLIC_RESEARCH_CLAIMS.md` and `docs/CHARTER.md`:

- **proven** means theorem-backed or sound-by-construction;
- **measured** means benchmarked under stated scope;
- **speculative** means a lens or research direction and is not load-bearing.
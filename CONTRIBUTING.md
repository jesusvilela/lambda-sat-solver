# Contributing

Contributions are welcome, but this repository has a strict claim discipline.

## Core rule

A name is not a proof. New concepts, metaphors, invariants, dispatch policies, or benchmark claims must cash out as one of:

- a theorem-backed or sound-by-construction component;
- a measured result with a reproducible command and scope;
- a clearly labelled speculative lens that is not load-bearing.

## Development setup

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -e .[dev,proof,bench]
python -m pytest backend/tests/ -q
```

For certification-sensitive changes, install Kissat and `drat-trim`, then run strict-mode smoke tests:

```bash
python -m backend.cli examples/simple_sat.cnf --mode strict
python -m backend.cli examples/simple_unsat.cnf --mode strict
```

## What a good PR includes

- A narrow statement of the claim being changed.
- Tests for every new soundness or routing claim.
- Reproducible commands for every benchmark claim.
- Updated docs if public behavior or public claims change.
- A clear label: proven, measured, or speculative.

## What not to do

- Do not claim general SAT dominance from a scoped benchmark.
- Do not let a solver verdict bypass model replay or proof checking on the certified path.
- Do not introduce vocabulary such as sheaf, gyrovector, holonomy, orbifold, or hyperbolic unless it has an explicit input -> invariant -> action -> benchmark contract, or is labelled as a non-load-bearing lens.
- Do not hide failed predictions. Negative results are part of the research record.

## Style

Keep the public surface readable for a skeptical stranger. The poetic layer is allowed, but the first-contact path must make the executable claim clear before the metaphor.
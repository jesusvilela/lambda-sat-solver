# Contributing

Thanks for your interest. This repository has an unusual constitution, and contributions
are judged by it. Read [`docs/CHARTER.md`](docs/CHARTER.md) first — it is the standard
everything here is held to.

## The one rule that matters: a name is not a proof

Every claim must be labelled **proven**, **measured**, or **speculative**, and bound to
something checkable — a theorem, a test, or a reproducible measurement. A pull request that
adds a capability claim without a test or a reproduction is not ready, however elegant.

- **Soundness is non-negotiable.** The frames and the certified paths must never emit a
  wrong `SAT`/`UNSAT`. New frame logic needs a differential test against a trusted oracle
  (brute force on small cases) and must *punt* (`CDCL_NEEDED`) rather than guess.
- **Measure before you optimize.** Performance claims need a before/after measurement in a
  script under `docs/ladder/scripts/`. Honest negatives are welcome and are recorded, not
  hidden.
- **Certification stays intact.** Anything that produces a verdict must keep it checkable:
  SAT by model replay, UNSAT by a sound frame refutation or a DRAT proof.

## Getting set up

```bash
pip install -e ".[dev,bench]"       # editable install + test/bench deps
# external tools for full certification: install Kissat + drat-trim (see BACKEND_README.md)
python -m pytest backend/tests -q   # the full suite must stay green
```

## Before opening a pull request

1. `python -m pytest backend/tests -q` passes locally.
2. New behaviour has a test; new/changed claims are labelled and reproducible.
3. If you touched a benchmark claim, update [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) and
   re-run the named command.
4. Keep the voice honest and scoped — claims are bounded to the mix/axis they were measured
   on, not generalized.

## Style

Match the surrounding code: its naming, comment density, and idiom. New research notes go
under `docs/ladder/` and are linked from its index with a one-line, honest summary.
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

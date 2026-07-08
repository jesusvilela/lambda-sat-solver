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

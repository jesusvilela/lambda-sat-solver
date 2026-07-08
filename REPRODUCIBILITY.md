# Reproducibility

Every benchmark claim in this repository is a **repo-internal measured claim** on a stated
mix, timeout, and environment — not an external competition result. This file gives the
exact command, environment, and expected shape of each so you can regenerate it. Numbers
are **hardware-sensitive** (wall-clock, core count); regenerate on your machine rather than
trusting the absolute seconds.

## Environment (as measured)

| component | version |
|---|---|
| Python | 3.11 / 3.12 (CI matrix) |
| numpy | 2.4.6 |
| Kissat | 4.0.4 |
| CaDiCaL | 3.0.0 |
| CryptoMiniSat (`pycryptosat`) | 5.14.7 |
| drat-trim | (DRAT proof checker) |
| dev container | 4 vCPU (the portfolio/parallel numbers are core-bound — see below) |

```bash
pip install -e ".[dev,bench]"
# external, non-pip: install Kissat + drat-trim (see BACKEND_README.md)
python -m pytest backend/tests -q        # 650 tests; the soundness/certification floor
```

## The measured claims, and how to regenerate each

Each row: the command, the timeout, and what the output should show. Instance lists are
fixed in the harness (deterministic seeds); the JSON outputs are git-ignored so you can
diff your run against the table.

| claim | command | timeout | expected shape |
|---|---|---|---|
| **frame-aware middleware vs raw CDCL** | `python -m docs.ladder.scripts.sota_benchmark` | 20 s | middleware 40/40, PAR-2 ~0.05 s; Kissat 35/40 ~5.4 s; CaDiCaL 36/40 ~4.3 s; 40/40 certified; 26/40 frame-decided |
| **vs CryptoMiniSat (four-way)** | `python -m docs.ladder.scripts.metasolver_benchmark` | 20 s | CMS 38/40, PAR-2 ~2.7 s; metasolver 40/40, PAR-2 ~0.05 s; CMS times out on php10/php12 (counting), metasolver instant there |
| **out-search CMS on random-3SAT** | `python -m docs.ladder.scripts.metametasolver_benchmark` | 30 s | on the n=220–280 hard band, the fractal portfolio beats CMS wall-clock on the majority of instances (PAR-2 ~1.6×); loses trivial instances to launch overhead; CPU cost ≈ breadth× |
| **NS degree vs width incomparable** | `python -m pytest backend/tests/test_ladder_contracts.py -k incomparable -q` | — | PHP (width 2, NS 4); Tseitin K4 (width 4, NS 3) — neither dominates |
| **hard certification actually runs** | `python .github/scripts/certification_smoke.py` | — | "CERTIFICATION LANE PASSED": a CDCL UNSAT DRAT-checked and a CDCL SAT model-replayed |

## How to interpret a discrepancy

- **Solved-count differs.** Almost always a timeout/hardware difference. Solved-count is
  robust; PAR-2 seconds are not — re-read them relative to *your* Kissat baseline, not ours.
- **The portfolio does not beat CMS on your box.** Expected on ≤2 cores: the meta-metasolver
  is a *parallel* mixed strategy; with few cores its arms contend and the wall-clock win
  shrinks or vanishes. It is the `k×`-CPU-for-wall-clock trade, stated in
  [`docs/ladder/GAME_THEORY_NOTE.md`](docs/ladder/GAME_THEORY_NOTE.md). The single-thread
  claims (frames, metasolver on counting/parity) are core-independent.
- **A frame verdict disagrees with a trusted solver.** That would be a **soundness bug** —
  the one class we treat as critical. Please report it (see `SECURITY.md`) with the formula.

## Scope of the claims (read this before quoting a number)

These are measured on a **small, fixed, synthetic competition-style mix** (random-3SAT,
Tseitin, XORSAT, pigeonhole, mixed), not the SAT Competition benchmark set. The honest
one-line reading:

> On a mix that includes the counting and parity fragments, the frame-aware middleware
> dominates raw CDCL and CryptoMiniSat on PAR-2 because it is instant where they blow up
> (counting) and comparable elsewhere; on the unstructured tail a parallel portfolio can
> out-search CMS at a CPU cost. This is a *structural* result on a *specific mix* — not a
> claim of a generally faster SAT solver.

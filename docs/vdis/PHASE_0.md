# VDIS Track B1 — Phase 0: Reference CDCL Solver

**Status:** gate passed. **Tag:** EMPIRICAL (all specific numbers below were run this session).

## What was built

`backend/refsolver/`:
- `solver.py` — `CDCLSolver`: 2-watched-literal unit propagation, 1UIP
  conflict analysis, non-chronological backtracking, Luby restarts
  (`luby_unit=100` default).
- `heuristics.py` — `DecisionHeuristic` protocol plus three
  implementations: `EVSIDSHeuristic` (MiniSat-style exponential VSIDS
  with phase saving), `LRBHeuristic` (Liang et al. 2016, simplified —
  see deviations below), `RandomHeuristic` (sanity floor).

## Deviations from the pinned spec (§2/§5), and why

- `pick()` signature is `pick(self, num_vars, value)` rather than a
  formal `Assignment` object — no `Assignment` class exists yet; the
  plain `List[Optional[bool]]` is equivalent and simpler. Not worth a
  wrapper class for v1.
- All three heuristics select via an **O(n) linear scan** over
  variables, not an indexed priority heap with lazy deletion. The
  stated metric is search quality (decisions/conflicts/propagations),
  not wall-clock, and a heap adds real bug surface (this is exactly the
  kind of subtle-correctness risk the spec elsewhere is careful about)
  without changing what's being measured. Flagging this explicitly
  since it's a deliberate deviation, not an oversight.
- LRB is a simplified version of the real algorithm: participation is
  approximated as "appears in the learned clause" rather than the full
  resolution-trace participation Liang et al. use, and reason-side
  literals aren't separately bumped. It's a real, working
  learning-rate-style heuristic, not a faithful reproduction of the
  paper — good enough as a secondary baseline, not something to cite
  as "this repo implements LRB."

## Correctness verification (gate: 100% agreement with Kissat)

Three separate cross-validation runs, all comparing refsolver's
verdict against either the eval suite's known ground truth or Kissat's
own verdict (SAT models additionally checked via `verify_model`):

1. **Direct Kissat cross-check on the 2-SAT UNSAT gadget** used as a
   regression test: `kissat` on `p cnf 2 4 / 1 2 0 / -1 2 0 / 1 -2 0 /
   -1 -2 0` → `s UNSATISFIABLE`, matching refsolver.
2. **Random 3-SAT sweep**: 60 formulas (n ∈ {10,20,30,50,75}, clause
   ratio ∈ {3.0, 4.267, 6.0} spanning under/at/over the satisfiability
   threshold, 4 seeds each) × 3 heuristics × 2 heuristic-seeds =
   **360/360 agreed** with Kissat, zero mismatches.
3. **`backend/eval.suite.StandardSuites.quick()`** (30 instances across
   random-3sat, pigeonhole, xor-chain, ladder, graph-coloring) × 3
   heuristics = **90/90 agreed**, zero mismatches, including all
   known-ground-truth pigeonhole and xor-chain instances.
4. **`StandardSuites.medium()`** (63 instances, up to 200 vars,
   including mutilated-chessboard and random-4sat) × 3 heuristics =
   **189/189 agreed**, zero mismatches, zero conflict-budget
   exhaustions (every instance solved to completion within 150,000
   conflicts; the hardest, `php_8_7` at 56 vars, took 52s per
   heuristic in pure Python — confirms the solver is correct on harder
   structured instances too, at the expected wall-clock cost).

Total: **639/639 agreement**, 0 mismatches, across three independent
heuristic implementations and six problem families (random-3sat,
random-4sat, pigeonhole, xor-chain, graph-coloring, ladder,
mutilated-chessboard).

## Test suite

`backend/tests/test_refsolver.py`: 40 tests (Luby sequence, SAT/UNSAT
correctness parametrized over all three heuristics, clause-handling
edge cases — tautology dropping, literal deduplication, level-0 unit
propagation — restarts, cross-heuristic answer agreement, stats
instrumentation, conflict-budget enforcement, determinism). All pass.
Combined with the existing suite: 287 total passing.

## Gate

- 100% agreement with Kissat/ground-truth across all four
  cross-validation runs (639/639): **passed**.
- ≥40 new tests: **passed** (exactly 40; 287 total in the repo).

**Gate passed. Proceeding to Phase 1** (gyro-op library + degeneracy
test).

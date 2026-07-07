"""Probe: what governs hardness -- symmetry, or phase-transition criticality?

Two focused experiments with our exact/bracketed isotropy and Kissat as the CDCL
oracle, to bring back measured knowledge (not assertion) about the two regimes.

A. SYMMETRY axis. On pigeonhole (maximally symmetric, CDCL-exponential): does
   CDCL hardness track the automorphism order, and does BREAKING the symmetry
   (adding sound symmetry-breaking units -- UNSAT is preserved, |Aut| drops)
   make Kissat faster? If yes, symmetry *is* the hardness here.

B. PHASE-TRANSITION axis. On random 3-SAT across alpha: the easy-hard-easy Kissat
   curve and the SAT-probability transition -- and, crucially, the isotropy of
   random 3-SAT across the whole sweep. If |Aut| ~ 1 everywhere, then symmetry is
   NOT the phase-transition variable, and the two hardnesses are orthogonal.

Run:  python -m docs.ladder.scripts.symmetry_phase_probe
"""

from __future__ import annotations

import math
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import random_3sat, run_cdcl  # noqa: E402

from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.frame_solver import frame_solve_coupled  # noqa: E402
from backend.orbifold import (  # noqa: E402
    exact_symmetry_log2,
    symmetry_log2_upper,
)


def _kissat_time(formula, timeout=8.0):
    t = time.perf_counter()
    try:
        status, _t, _c = run_cdcl(formula, "kissat", timeout_s=timeout)
    except Exception:
        status = "UNKNOWN"
    return status, (time.perf_counter() - t) * 1000.0


def symmetry_axis():
    print("A. SYMMETRY axis -- pigeonhole, and breaking symmetry with sound units")
    print("   A1. natural scaling (|Aut| = n!*(n-1)!, exact closed form):")
    print(f"      {'php':>5} {'log2|Aut|':>10} {'frame_ms':>9} {'kissat':>14}")
    for n in range(8, 13):
        f = pigeonhole(n)[0]
        log2aut = math.log2(math.factorial(n) * math.factorial(n - 1))
        t = time.perf_counter()
        frame_solve_coupled(f)
        fms = (time.perf_counter() - t) * 1000.0
        ks, kms = _kissat_time(f)
        klabel = f"{ks} {kms:.0f}ms" if ks != "UNKNOWN" else f"TIMEOUT {kms:.0f}ms"
        print(f"      php{n:<2} {log2aut:>10.1f} {fms:>8.2f}m {klabel:>14}")

    print("\n   A2. breaking symmetry on php11 (add k sound units; UNSAT preserved):")
    print(f"      {'k_units':>8} {'log2|Aut|_up':>13} {'kissat':>14}")
    base = pigeonhole(11)[0]
    for k in (0, 1, 2, 4, 8, 16):
        # adding negative units pins variables -> breaks the pigeon/hole symmetry;
        # PHP is UNSAT so extra constraints keep it UNSAT.
        clauses = list(base.clauses) + [[-v] for v in range(1, k + 1)]
        f = CNFFormula(num_vars=base.num_vars, clauses=clauses)
        up = symmetry_log2_upper(f)                # exact is out of budget at n=110
        ks, kms = _kissat_time(f)
        klabel = f"{ks} {kms:.0f}ms" if ks != "UNKNOWN" else f"TIMEOUT {kms:.0f}ms"
        print(f"      {k:>8} {up:>13.1f} {klabel:>14}")


def phase_axis():
    print("\nB. PHASE-TRANSITION axis -- random 3-SAT, n=150, alpha sweep")
    print(f"   {'alpha':>6} {'SAT_frac':>9} {'kissat_med_ms':>14} {'kissat_max_ms':>14} "
          f"{'mean_log2|Aut|':>15}")
    n = 150
    for alpha in (3.0, 3.8, 4.0, 4.2, 4.26, 4.4, 4.6, 5.0, 6.0):
        sats = 0
        times = []
        auts = []
        trials = 9
        for s in range(trials):
            f = random_3sat(n, round(alpha * n), s)
            ks, kms = _kissat_time(f, timeout=8.0)
            times.append(kms)
            if ks == "SAT":
                sats += 1
            ex = exact_symmetry_log2(f, node_budget=60_000)
            auts.append(ex if ex is not None else symmetry_log2_upper(f))
        print(f"   {alpha:>6.2f} {sats/trials:>9.2f} {statistics.median(times):>14.1f} "
              f"{max(times):>14.1f} {statistics.mean(auts):>15.3f}")


if __name__ == "__main__":
    symmetry_axis()
    phase_axis()

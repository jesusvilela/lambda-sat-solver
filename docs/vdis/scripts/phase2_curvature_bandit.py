"""S3.5 curvature learning, exactly as pinned by Correction 2: an
OFFLINE sweep over kappa in {-0.25, -0.5, -1, -2}, keyed by generator
family (the suite's category labels), winner per (algebra, family)
frozen into a lookup table - no online kappa adaptation.

Metric: total decisions-to-solve across the family's instances (quick +
medium suites), full VDIS config (dim=32, beta=0.1, lambdas=0.1).
Deterministic given the instance seeds and heuristic seed=0, so this is
a degenerate "bandit" (every arm can be pulled exhaustively - the
bandit framing in the spec matters only if the sweep were too expensive
to run in full, which at this suite size it is not).

Output: python dict to freeze into backend/vdis/kappa_table.py.
"""

import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.eval.suite import StandardSuites
from backend.refsolver.solver import CDCLSolver
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi

KAPPAS = (-0.25, -0.5, -1.0, -2.0)
MAX_CONFLICTS = 50000


def main():
    instances = (
        StandardSuites.quick().instances + StandardSuites.medium().instances
    )
    # totals[(algebra, family)][kappa] = (total_decisions, capped_count)
    totals = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    t0 = time.perf_counter()
    for algebra in ("C", "H"):
        for kappa in KAPPAS:
            for inst in instances:
                cnf = inst.formula
                h = VDISHeuristic(
                    cnf.num_vars, dim=32, c=-kappa, algebra=algebra,
                    beta=0.1, lambda_tau=0.1, lambda_chi=0.1,
                    chi=compute_chi(cnf.clauses, cnf.num_vars), seed=0,
                )
                solver = CDCLSolver(cnf, h, max_conflicts=MAX_CONFLICTS)
                result, _ = solver.solve()
                cell = totals[(algebra, inst.category)][kappa]
                cell[0] += solver.stats.decisions
                if result.name == "UNKNOWN":
                    cell[1] += 1
            print(
                f"done {algebra} kappa={kappa} ({time.perf_counter()-t0:.0f}s)",
                flush=True,
            )

    print("\nKAPPA_TABLE = {")
    for (algebra, family), by_kappa in sorted(totals.items()):
        rows = sorted(by_kappa.items(), key=lambda kv: (kv[1][1], kv[1][0]))
        winner = rows[0][0]
        detail = ", ".join(
            f"k={k}: {d} dec" + (f" ({c} capped)" if c else "")
            for k, (d, c) in sorted(by_kappa.items())
        )
        print(f"    ({algebra!r}, {family!r}): {winner},   # {detail}")
    print("}")


if __name__ == "__main__":
    main()

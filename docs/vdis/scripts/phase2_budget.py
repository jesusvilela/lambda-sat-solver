"""Phase 2 gate, part 2: S3.7 per-conflict wall-time budget.

Spec text: "If per-conflict wall time in the reference solver exceeds
20x the EVSIDS heuristic's, reduce D before touching the math."

Measured both ways, because the sentence is ambiguous:
  (a) in-solver reading: (total solver wall time / conflicts) for a
      VDIS run vs the same quantity for an EVSIDS run - the heuristic
      embedded in the solver it actually runs in;
  (b) heuristic-only reading: time spent inside heuristic calls
      (on_conflict + decay + pick) per conflict, VDIS vs EVSIDS.
(a) is the reading the gate uses (it is what "per-conflict wall time in
the reference solver" literally denotes); (b) is reported because it is
the honest number for how expensive the gyro machinery itself is.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.eval.generators import pigeonhole, random_ksat
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi


class TimingWrapper:
    def __init__(self, inner):
        self.inner = inner
        self.heuristic_time = 0.0

    def _timed(self, f, *a):
        t0 = time.perf_counter()
        out = f(*a)
        self.heuristic_time += time.perf_counter() - t0
        return out

    def on_conflict(self, learned, lbd, trail):
        return self._timed(self.inner.on_conflict, learned, lbd, trail)

    def on_assign(self, lit):
        self.inner.on_assign(lit)  # untimed: trivial for both

    def on_unassign(self, lit):
        self.inner.on_unassign(lit)

    def pick(self, num_vars, value):
        return self._timed(self.inner.pick, num_vars, value)

    def decay(self):
        return self._timed(self.inner.decay)


def measure(name, make_heuristic, instances):
    total_solver = 0.0
    total_heur = 0.0
    total_conflicts = 0
    for cnf in instances:
        w = TimingWrapper(make_heuristic(cnf))
        solver = CDCLSolver(cnf, w, max_conflicts=50000)
        t0 = time.perf_counter()
        solver.solve()
        total_solver += time.perf_counter() - t0
        total_heur += w.heuristic_time
        total_conflicts += solver.stats.conflicts
    per_conf_solver = total_solver / max(total_conflicts, 1)
    per_conf_heur = total_heur / max(total_conflicts, 1)
    print(
        f"{name:12s} conflicts={total_conflicts:6d} "
        f"solver={1e3*per_conf_solver:8.3f} ms/conf "
        f"heuristic={1e6*per_conf_heur:8.1f} us/conf"
    )
    return per_conf_solver, per_conf_heur


def main():
    instances = [
        pigeonhole(6)[0],                      # UNSAT, conflict-heavy
        pigeonhole(7)[0],
        random_ksat(60, 256, k=3, seed=1)[0],  # phase transition
        random_ksat(80, 341, k=3, seed=2)[0],
        random_ksat(50, 500, k=4, seed=3)[0],
    ]

    ev_solver, ev_heur = measure(
        "EVSIDS", lambda cnf: EVSIDSHeuristic(cnf.num_vars, seed=0), instances
    )

    def make_vdis(algebra):
        def f(cnf):
            return VDISHeuristic(
                cnf.num_vars, dim=32, c=1.0, algebra=algebra,
                beta=0.1, lambda_tau=0.1, lambda_chi=0.1,
                chi=compute_chi(cnf.clauses, cnf.num_vars), seed=0,
            )
        return f

    ok = True
    for algebra in ("C", "H"):
        v_solver, v_heur = measure(f"VDIS-{algebra}", make_vdis(algebra), instances)
        ratio_a = v_solver / ev_solver
        ratio_b = v_heur / ev_heur
        print(
            f"  ratio (a) in-solver per-conflict: {ratio_a:5.2f}x "
            f"(gate: <= 20x) | ratio (b) heuristic-only: {ratio_b:6.1f}x"
        )
        ok = ok and ratio_a <= 20.0
    print("GATE PART 2:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()

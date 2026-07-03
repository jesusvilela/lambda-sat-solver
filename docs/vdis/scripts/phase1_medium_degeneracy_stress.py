import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.eval.suite import StandardSuites
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic
from backend.vdis.vdis_heuristic import VDISHeuristic


class RecordingWrapper:
    def __init__(self, inner):
        self.inner = inner
        self.decisions = []

    def on_conflict(self, learned, lbd, trail):
        self.inner.on_conflict(learned, lbd, trail)

    def on_assign(self, lit):
        self.inner.on_assign(lit)

    def on_unassign(self, lit):
        self.inner.on_unassign(lit)

    def pick(self, num_vars, value):
        lit = self.inner.pick(num_vars, value)
        self.decisions.append(lit)
        return lit

    def decay(self):
        self.inner.decay()


def run(cnf, heuristic, max_conflicts=300000):
    w = RecordingWrapper(heuristic)
    s = CDCLSolver(cnf, w, max_conflicts=max_conflicts)
    r, m = s.solve()
    return r, w.decisions, s.stats


def main():
    suite = StandardSuites.medium()
    print(f"medium suite: {len(suite)} instances")
    mismatches = 0
    for inst in suite.instances:
        cnf = inst.formula
        er, ed, es = run(cnf, EVSIDSHeuristic(cnf.num_vars, seed=0))
        vr, vd, vs = run(
            cnf, VDISHeuristic(cnf.num_vars, dim=1, c=0.0, eta=1.0, decay_gamma=0.95)
        )
        if ed != vd:
            mismatches += 1
            first = next(
                (i for i, (a, b) in enumerate(zip(ed, vd)) if a != b),
                min(len(ed), len(vd)),
            )
            print(
                f"MISMATCH {inst.name}: first_diff={first} "
                f"evsids_decisions={len(ed)} vdis_decisions={len(vd)}"
            )
        else:
            print(f"match {inst.name}: {len(ed)} decisions, {es.conflicts} conflicts")
    print(f"TOTAL mismatches: {mismatches}/{len(suite)}")


if __name__ == "__main__":
    main()

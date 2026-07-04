"""Phase 2 gate, part 1: run full VDIS (C, D=16 and H, D=8; dim=32,
kappa=-1, beta=0.1, lambda_tau=0.1, lambda_chi=0.1) over the quick and
medium suites. Gate criterion: zero numerical failures (the gyro-op
tripwire never fires, no NaN/inf); correctness cross-checked (SAT ->
model check, known-UNSAT -> UNSAT). Decisions/conflicts recorded for
context but NOT part of this gate (search quality is Phase 3's
question, with pre-registered predictions)."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.eval.suite import StandardSuites
from backend.refsolver.solver import CDCLSolver, SolveResult
from backend.vdis.gyro_ops import NumericalInstabilityError
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi

MAX_CONFLICTS = 50000


def check_model(formula, model):
    return all(
        any((lit > 0) == model[abs(lit)] for lit in clause if model[abs(lit)] is not None)
        for clause in formula.clauses
    )


def run_variant(algebra, suites):
    numerical_failures = 0
    wrong_answers = 0
    unknowns = 0
    total = 0
    t0 = time.perf_counter()
    for suite in suites:
        for inst in suite.instances:
            total += 1
            cnf = inst.formula
            chi = compute_chi(cnf.clauses, cnf.num_vars)
            h = VDISHeuristic(
                cnf.num_vars, dim=32, c=1.0, algebra=algebra,
                beta=0.1, lambda_tau=0.1, lambda_chi=0.1, chi=chi, seed=0,
            )
            try:
                solver = CDCLSolver(cnf, h, max_conflicts=MAX_CONFLICTS)
                result, model = solver.solve()
            except NumericalInstabilityError as e:
                numerical_failures += 1
                print(f"  NUMERICAL FAILURE {inst.name}: {e}")
                continue
            if result == SolveResult.SAT:
                if not check_model(cnf, model):
                    wrong_answers += 1
                    print(f"  WRONG MODEL {inst.name}")
                elif inst.expected == "UNSAT":
                    wrong_answers += 1
                    print(f"  SAT on known-UNSAT {inst.name}")
            elif result == SolveResult.UNSAT:
                if inst.expected == "SAT":
                    wrong_answers += 1
                    print(f"  UNSAT on known-SAT {inst.name}")
            else:
                unknowns += 1
                print(f"  conflict-capped (UNKNOWN) {inst.name}: "
                      f"{solver.stats.conflicts} conflicts")
    dt = time.perf_counter() - t0
    print(
        f"[{algebra}] {total} instances in {dt:.1f}s: "
        f"numerical_failures={numerical_failures} wrong={wrong_answers} "
        f"capped={unknowns}"
    )
    return numerical_failures, wrong_answers


def main():
    suites = [StandardSuites.quick(), StandardSuites.medium()]
    for s in suites:
        print(f"suite {s.name}: {len(s)} instances")
    ok = True
    for algebra in ("C", "H"):
        nf, wrong = run_variant(algebra, suites)
        ok = ok and nf == 0 and wrong == 0
    print("GATE PART 1:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()

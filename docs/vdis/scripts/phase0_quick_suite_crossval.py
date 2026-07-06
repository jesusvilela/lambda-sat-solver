import sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.cnf_utils import verify_model
from backend.eval.suite import StandardSuites
from backend.kissat_wrapper import KissatWrapper
from backend.refsolver import CDCLSolver, SolveResult, EVSIDSHeuristic, LRBHeuristic, RandomHeuristic

kw = KissatWrapper("kissat")

HEURISTIC_FACTORIES = {
    "EVSIDS": lambda n, seed: EVSIDSHeuristic(n, seed=seed),
    "LRB": lambda n, seed: LRBHeuristic(n, seed=seed),
    "Random": lambda n, seed: RandomHeuristic(n, seed=seed),
}

suite = StandardSuites.quick()
print(f"Suite: {suite.name}, {len(suite)} instances, categories={suite.categories()}")

total = 0
agree = 0
mismatches = []

for inst in suite.instances:
    cnf = inst.formula
    kissat_out = kw.solve(cnf, produce_proof=False)
    kissat_verdict = kissat_out.result.name

    ground_truth = None
    if inst.expected in ("SAT", "UNSAT"):
        ground_truth = inst.expected
        if kissat_verdict in ("SAT", "UNSAT") and kissat_verdict != ground_truth:
            mismatches.append((inst.name, "KISSAT DISAGREES WITH EXPECTED", kissat_verdict, ground_truth))

    for hname, factory in HEURISTIC_FACTORIES.items():
        for hseed in [0]:
            total += 1
            solver = CDCLSolver(cnf, factory(cnf.num_vars, hseed), max_conflicts=300000)
            res, model = solver.solve()

            ok = True
            detail = ""
            reference = ground_truth or (kissat_verdict if kissat_verdict in ("SAT", "UNSAT") else None)
            if reference is None:
                detail = "no ground truth available (kissat inconclusive too)"
            elif reference == "SAT":
                if res != SolveResult.SAT:
                    ok = False
                    detail = f"expected SAT, refsolver={res}"
                elif not verify_model(cnf, model):
                    ok = False
                    detail = "SAT model failed verify_model"
            elif reference == "UNSAT":
                if res != SolveResult.UNSAT:
                    ok = False
                    detail = f"expected UNSAT, refsolver={res}"

            if ok:
                agree += 1
            else:
                mismatches.append((inst.name, hname, detail))

    print(f"{inst.name:30s} cat={inst.category:12s} expected={inst.expected:8s} kissat={kissat_verdict:8s} vars={cnf.num_vars:4d} clauses={cnf.num_clauses:5d}", flush=True)

print()
print(f"TOTAL={total} AGREE={agree} MISMATCHES={len(mismatches)}")
for m in mismatches:
    print("  MISMATCH:", m)

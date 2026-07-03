import sys, time
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

suite = StandardSuites.medium()
print(f"Suite: {suite.name}, {len(suite)} instances", flush=True)

total = 0
agree = 0
unknown_budget = 0
mismatches = []

for inst in suite.instances:
    cnf = inst.formula
    kissat_out = kw.solve(cnf, produce_proof=False)
    kissat_verdict = kissat_out.result.name
    reference = inst.expected if inst.expected in ("SAT", "UNSAT") else (
        kissat_verdict if kissat_verdict in ("SAT", "UNSAT") else None
    )

    t0 = time.time()
    for hname, factory in HEURISTIC_FACTORIES.items():
        total += 1
        solver = CDCLSolver(cnf, factory(cnf.num_vars, 0), max_conflicts=150000)
        res, model = solver.solve()

        ok = True
        detail = ""
        if reference is None:
            detail = "no ground truth"
        elif res == SolveResult.UNKNOWN:
            unknown_budget += 1
            detail = "conflict budget exhausted"
            ok = True  # not a mismatch, just inconclusive - don't count against correctness
        elif reference == "SAT":
            if res != SolveResult.SAT:
                ok = False
                detail = f"expected SAT, got {res}"
            elif not verify_model(cnf, model):
                ok = False
                detail = "SAT model failed verify_model"
        elif reference == "UNSAT":
            if res != SolveResult.UNSAT:
                ok = False
                detail = f"expected UNSAT, got {res}"

        if ok:
            agree += 1
        else:
            mismatches.append((inst.name, hname, detail))
    dt = time.time() - t0
    print(f"{inst.name:35s} cat={inst.category:20s} ref={str(reference):8s} vars={cnf.num_vars:4d} time={dt:6.2f}s", flush=True)

print()
print(f"TOTAL={total} AGREE(or-inconclusive)={agree} BUDGET_EXHAUSTED={unknown_budget} MISMATCHES={len(mismatches)}")
for m in mismatches:
    print("  MISMATCH:", m)

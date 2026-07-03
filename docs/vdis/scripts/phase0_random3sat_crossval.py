import random
import sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.cnf_utils import CNFFormula, verify_model, write_dimacs
from backend.kissat_wrapper import KissatWrapper
from backend.refsolver import CDCLSolver, SolveResult, EVSIDSHeuristic, LRBHeuristic, RandomHeuristic

kw = KissatWrapper("kissat")

def random_3sat(nvars, ratio, seed):
    rnd = random.Random(seed)
    nclauses = int(nvars * ratio)
    clauses = []
    for _ in range(nclauses):
        vs = rnd.sample(range(1, nvars + 1), 3)
        clause = [v if rnd.random() < 0.5 else -v for v in vs]
        clauses.append(clause)
    return CNFFormula(num_vars=nvars, clauses=clauses)

HEURISTIC_FACTORIES = {
    "EVSIDS": lambda n, seed: EVSIDSHeuristic(n, seed=seed),
    "LRB": lambda n, seed: LRBHeuristic(n, seed=seed),
    "Random": lambda n, seed: RandomHeuristic(n, seed=seed),
}

total = 0
agree = 0
disagree = []

# Sweep small-to-medium random 3-SAT at various ratios (below/at/above threshold)
# plus a few structured cases, across all three heuristics and several seeds.
configs = []
for nvars in [10, 20, 30, 50, 75]:
    for ratio in [3.0, 4.267, 6.0]:
        for seed in range(4):
            configs.append((nvars, ratio, seed))

for nvars, ratio, seed in configs:
    cnf = random_3sat(nvars, ratio, seed)
    kissat_out = kw.solve(cnf, produce_proof=False)
    kissat_verdict = kissat_out.result.name  # SAT / UNSAT / TIMEOUT / ERROR

    for hname, factory in HEURISTIC_FACTORIES.items():
        for hseed in [0, 1]:
            total += 1
            solver = CDCLSolver(cnf, factory(cnf.num_vars, hseed), max_conflicts=200000)
            res, model = solver.solve()

            ok = True
            detail = ""
            if kissat_verdict == "SAT":
                if res != SolveResult.SAT:
                    ok = False
                    detail = f"kissat=SAT but refsolver={res}"
                elif not verify_model(cnf, model):
                    ok = False
                    detail = "refsolver SAT model failed verify_model"
            elif kissat_verdict == "UNSAT":
                if res != SolveResult.UNSAT:
                    ok = False
                    detail = f"kissat=UNSAT but refsolver={res}"
            else:
                detail = f"kissat verdict inconclusive: {kissat_verdict}"

            if ok:
                agree += 1
            else:
                disagree.append((nvars, ratio, seed, hname, hseed, detail))

    print(f"nvars={nvars:3d} ratio={ratio:.3f} seed={seed} kissat={kissat_verdict:10s} checked", flush=True)

print()
print(f"TOTAL={total} AGREE={agree} DISAGREE={len(disagree)}")
for d in disagree:
    print("  MISMATCH:", d)

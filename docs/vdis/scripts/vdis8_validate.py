import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
import numpy as np
from statistics import median
from backend.eval.generators import random_ksat
from backend.refsolver.solver import CDCLSolver
from backend.refsolver.heuristics import EVSIDSHeuristic, LRBHeuristic
from backend.vdis.vdis_heuristic import VDISHeuristic, compute_chi
from backend.vdis.kappa_table import kappa_for
def mk(cnf,tr):
    return VDISHeuristic(cnf.num_vars,dim=32,c=-kappa_for("C","random-3sat"),algebra="C",lambda_chi=0.1,
                         chi=compute_chi(cnf.clauses,cnf.num_vars),combine_nudges=True,nudge_gate=1.0,
                         combine_traders=tr,clauses=cnf.clauses,seed=0)
def run(cnf,h):
    s=CDCLSolver(cnf,h,max_conflicts=100000); r,_=s.solve()
    return s.stats.decisions if r.name!="UNKNOWN" else 100000
for n in (50,90,150):
    m=int(n*4.267); insts=[random_ksat(n,m,k=3,seed=s)[0] for s in range(400,410)]
    med={k:[] for k in ("EVSIDS","LRB","cent","degree")}
    for cnf in insts:
        med["EVSIDS"].append(run(cnf,EVSIDSHeuristic(cnf.num_vars,seed=0)))
        med["LRB"].append(run(cnf,LRBHeuristic(cnf.num_vars,seed=0)))
        med["cent"].append(run(cnf,mk(cnf,("centrality",))))
        med["degree"].append(run(cnf,mk(cnf,("degree",))))
    ev=np.array(med["EVSIDS"]); lr=np.array(med["LRB"])
    for k in ("cent","degree"):
        a=np.array(med[k])
        print(f"n={n} {k}: total={int(a.sum())} vs EV={int(ev.sum())} LRB={int(lr.sum())} | "
              f"beats_EV={int((a<ev).sum())}/10 beats_LRB={int((a<lr).sum())}/10", flush=True)
print("VALIDATE_DONE", flush=True)

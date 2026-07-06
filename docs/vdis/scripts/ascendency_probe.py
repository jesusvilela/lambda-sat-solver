"""Ulanowicz network ascendency as a candidate per-instance structural
feature (contemplation prompted by the operator; see ASCENDENCY.md).

Relative ascendency alpha = A/C = AMI/H of the variable co-occurrence
flow network T_ij = #clauses containing both var i and var j:
  TST = sum T_ij
  A   = sum_ij (T_ij/TST) log( T_ij*TST / (Ti*Tj) )   (= TST*AMI)
  C   = -sum_ij (T_ij/TST) log(T_ij/TST) * ... -> use H = -sum p log p
  alpha = A/C in [0,1]: the degree of ORDER (channelization) of the
  constraint flow, scale-free, no solving required.

Verdict recorded in ASCENDENCY.md: alpha separates families but does
NOT monotonically predict the frozen per-family kappa (random-4sat is
the counterexample), so it is NOT adopted as a kappa-selection rule.
"""
import numpy as np
from collections import defaultdict


def ascendency_alpha(cnf):
    T = defaultdict(float)
    for cl in cnf.clauses:
        vs = list({abs(l) for l in cl})
        for a in range(len(vs)):
            for b in range(len(vs)):
                if a != b:
                    T[(vs[a], vs[b])] += 1.0
    if not T:
        return None
    TST = sum(T.values())
    Ti, Tj = defaultdict(float), defaultdict(float)
    for (i, j), t in T.items():
        Ti[i] += t
        Tj[j] += t
    A = H = 0.0
    for (i, j), t in T.items():
        p = t / TST
        A += p * np.log(t * TST / (Ti[i] * Tj[j]))
        H -= p * np.log(p)
    return A / H if H > 0 else None


if __name__ == "__main__":
    from backend.eval.generators import (
        pigeonhole, random_ksat, graph_coloring, mutilated_chessboard)
    for name, cnf in [
        ("php_8", pigeonhole(8)[0]),
        ("r3sat_n100", random_ksat(100, 426, k=3, seed=1)[0]),
        ("r4sat_n40", random_ksat(40, 397, k=4, seed=0)[0]),
        ("color", graph_coloring(10, 3, 0.5, seed=0)[0]),
        ("mutil_6", mutilated_chessboard(6)[0]),
    ]:
        print(f"{name:14s} alpha={ascendency_alpha(cnf):.4f}")

"""Rung 2 (algebraic): does Nullstellensatz/PC degree over GF(2) track the
resolution refutation width on small UNSAT random 3-SAT?

NS degree is the algebraic sibling of resolution width -- the rank-deficiency
obstruction the operator's zero-divisor insight points at. This measures both
intrinsic obstruction levels on the same instances and reports their rank
correlation. Both are exact and exponential, so n is kept small.

Run: python -m docs.ladder.scripts.ns_degree_vs_width
"""
import collections
import math
import random
import statistics

from backend.cnf_utils import CNFFormula
from backend.complexity.invariants import (
    min_refutation_width as mrw,
    nullstellensatz_degree as nsd,
    solution_stats,
)


def random_3sat(n, m, seed):
    rng = random.Random(seed)
    clauses = []
    for _ in range(m):
        vs = rng.sample(range(1, n + 1), 3)
        clauses.append([v if rng.random() < 0.5 else -v for v in vs])
    return CNFFormula(num_vars=n, clauses=clauses)


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return cov / (sx * sy) if sx and sy else 0.0


def main(n=10, alpha=5.5, target=40, max_seeds=400):
    m = round(alpha * n)
    rows = []
    for seed in range(max_seeds):
        f = random_3sat(n, m, seed)
        s = solution_stats(f, max_vars=n)
        if s.satisfiable:
            continue
        d = nsd(f, dmax=6)
        w = mrw(f, wmax=6, max_closure=400000)
        rows.append((d, w))
        if len(rows) >= target:
            break

    print(f"collected {len(rows)} UNSAT instances at n={n}, alpha={alpha}")
    tab = collections.Counter(rows)
    print("  (NS_degree, width) -> count")
    for k in sorted(tab, key=lambda t: (t[0] or -1, t[1] or -1)):
        print("   ", k, tab[k])

    ds = [d for d, _ in rows if d is not None]
    ws = [w for _, w in rows if w is not None]
    print(f"NS degree: min={min(ds)} max={max(ds)} mean={statistics.mean(ds):.2f}")
    print(f"width    : min={min(ws)} max={max(ws)} mean={statistics.mean(ws):.2f}")

    paired = [(d, w) for d, w in rows if d is not None and w is not None]
    if len(paired) > 2:
        print(f"Spearman(NS, width) = "
              f"{spearman([p[0] for p in paired], [p[1] for p in paired]):.3f}"
              f"  (n={len(paired)})")


if __name__ == "__main__":
    main()

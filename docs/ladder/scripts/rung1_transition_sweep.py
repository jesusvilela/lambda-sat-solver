"""Rung 1 experiment (docs/ladder/RUNG1_PLAN.md): across the random
3-SAT phase transition, which intrinsic invariant tracks hardness?

Hardness = median DPLL decisions (a plain, robust, self-contained DPLL
with unit propagation — proof-model-faithful, independent of the VDIS
machinery). Correctness cross-checked: DPLL SAT/UNSAT vs exact
enumeration (solution_stats).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import random
from statistics import median, mean

import numpy as np

from backend.cnf_utils import CNFFormula
from backend.complexity.invariants import (
    mean_var_degree, var_degree_entropy, spectral_gap, solution_stats,
)


def random_3sat(n, m, seed):
    rng = random.Random(seed)
    clauses = []
    for _ in range(m):
        vs = rng.sample(range(1, n + 1), 3)
        clauses.append([v if rng.random() < 0.5 else -v for v in vs])
    return CNFFormula(num_vars=n, clauses=clauses)


class DPLL:
    """Plain DPLL: unit propagation + first-unassigned branching. Counts
    decisions (branch points). Robust and self-contained."""

    def __init__(self, formula):
        self.n = formula.num_vars
        self.clauses = [list(c) for c in formula.clauses]
        self.decisions = 0

    def _propagate(self, assign):
        changed = True
        while changed:
            changed = False
            for c in self.clauses:
                unassigned = []
                sat = False
                for l in c:
                    v = abs(l)
                    val = assign.get(v)
                    if val is None:
                        unassigned.append(l)
                    elif (l > 0) == val:
                        sat = True
                        break
                if sat:
                    continue
                if not unassigned:
                    return False  # conflict
                if len(unassigned) == 1:
                    l = unassigned[0]
                    assign[abs(l)] = (l > 0)
                    changed = True
        return True

    def solve(self, assign=None):
        if assign is None:
            assign = {}
        assign = dict(assign)
        if not self._propagate(assign):
            return False
        unassigned = [v for v in range(1, self.n + 1) if v not in assign]
        if not unassigned:
            return True
        self.decisions += 1
        v = unassigned[0]
        for val in (True, False):
            a2 = dict(assign)
            a2[v] = val
            if self.solve(a2):
                return True
        return False


def run():
    ratios = [3.0, 3.6, 4.0, 4.27, 4.6, 5.0, 5.5]
    n = 20
    seeds = range(20)
    rows = []
    print(f"n={n}, 3-SAT, {len(list(seeds))} seeds/ratio")
    print(f"{'alpha':>6}{'hard(med dec)':>14}{'spec_gap':>10}{'deg_ent':>9}"
          f"{'backbone':>10}{'clusters':>10}{'sat_frac':>9}")
    for alpha in ratios:
        m = int(round(alpha * n))
        hard, gaps, ents, backs, clus, satc = [], [], [], [], [], []
        for s in seeds:
            f = random_3sat(n, m, seed=1000 + s)
            d = DPLL(f); sat = d.solve()
            ss = solution_stats(f)
            assert sat == ss.satisfiable, f"DPLL/enum disagree a={alpha} s={s}"
            hard.append(d.decisions)
            gaps.append(spectral_gap(f))
            ents.append(var_degree_entropy(f))
            satc.append(1 if ss.satisfiable else 0)
            if ss.satisfiable:
                backs.append(ss.backbone_fraction)
                clus.append(ss.num_clusters)
        row = dict(alpha=alpha, hard=median(hard), gap=mean(gaps), ent=mean(ents),
                   backbone=(mean(backs) if backs else float('nan')),
                   clusters=(mean(clus) if clus else float('nan')),
                   satfrac=mean(satc))
        rows.append((row, hard, gaps, backs))
        print(f"{alpha:>6}{row['hard']:>14.1f}{row['gap']:>10.3f}{row['ent']:>9.3f}"
              f"{row['backbone']:>10.3f}{row['clusters']:>10.1f}{row['satfrac']:>9.2f}")

    # Which invariant peaks at alpha ~ 4.27 (where hardness peaks)?
    peak_alpha = max(rows, key=lambda r: r[0]['hard'])[0]['alpha']
    print(f"\nhardness peaks at alpha = {peak_alpha}")
    # Spearman-ish: correlation of |alpha-peak| with each invariant across ratios
    def corr(xs, ys):
        xr = np.argsort(np.argsort(xs)).astype(float)
        yr = np.argsort(np.argsort(ys)).astype(float)
        xr -= xr.mean(); yr -= yr.mean()
        d = np.sqrt((xr*xr).sum()*(yr*yr).sum())
        return float((xr*yr).sum()/d) if d else 0.0
    hs = [r[0]['hard'] for r in rows]
    print("\nrank-correlation of each invariant with hardness across ratios:")
    for key in ('gap', 'ent', 'backbone', 'clusters', 'satfrac'):
        vals = [r[0][key] for r in rows]
        if any(np.isnan(vals)):
            vals = [v if not np.isnan(v) else 0.0 for v in vals]
        print(f"  {key:10s} corr={corr(hs, vals):+.3f}")


if __name__ == "__main__":
    run()

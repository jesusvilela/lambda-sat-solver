"""Intrinsic, solver-independent structural invariants of a CNF formula,
for the hardness-lower-bound ladder (docs/ladder/RUNG1_PLAN.md).

Every function here takes only the formula and returns a number that is a
property of the formula (or its solution space) — never of a particular
solver's run. Two tiers:

  cheap (poly-time, graph-structural):
    mean_var_degree, var_degree_entropy, spectral_gap
  exact-for-small-n (solution-space geometry, O(2^n)):
    solution_stats -> (num_solutions, backbone_fraction, num_clusters)

Theory anchors (docstrings cite them; the code does not assume them):
  - spectral_gap is a poly-time proxy for combinatorial (boundary)
    expansion via Cheeger; boundary expansion is the driver of resolution
    width lower bounds (Ben-Sasson & Wigderson, JACM 2001), hence
    resolution size — the Rung-2 target.
  - backbone / frozen variables and solution-space clustering are the
    structural phenomena associated with random-k-SAT hardness near the
    satisfiability threshold (Achlioptas-Coja-Oghlan, Mezard-Zecchina).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from ..cnf_utils import CNFFormula


# ---------------------------------------------------------------------------
# Cheap graph-structural invariants
# ---------------------------------------------------------------------------

def _var_cooccurrence(formula: CNFFormula) -> np.ndarray:
    """Weighted adjacency A[i,j] = #clauses containing both var i and j
    (0-indexed n x n, symmetric, zero diagonal)."""
    n = formula.num_vars
    A = np.zeros((n, n))
    for cl in formula.clauses:
        vs = list({abs(l) - 1 for l in cl if 1 <= abs(l) <= n})
        for a in range(len(vs)):
            for b in range(a + 1, len(vs)):
                A[vs[a], vs[b]] += 1.0
                A[vs[b], vs[a]] += 1.0
    return A


def mean_var_degree(formula: CNFFormula) -> float:
    deg = np.zeros(formula.num_vars)
    for cl in formula.clauses:
        for l in cl:
            v = abs(l)
            if 1 <= v <= formula.num_vars:
                deg[v - 1] += 1
    return float(deg.mean()) if formula.num_vars else 0.0


def var_degree_entropy(formula: CNFFormula) -> float:
    """Normalized Shannon entropy of the variable-degree distribution."""
    deg = np.zeros(formula.num_vars)
    for cl in formula.clauses:
        for l in cl:
            v = abs(l)
            if 1 <= v <= formula.num_vars:
                deg[v - 1] += 1
    total = deg.sum()
    if total <= 0 or formula.num_vars < 2:
        return 0.0
    p = deg[deg > 0] / total
    h = -np.sum(p * np.log(p))
    return float(h / math.log(formula.num_vars))


def spectral_gap(formula: CNFFormula) -> float:
    """Algebraic connectivity λ₂ of the normalized Laplacian of the
    variable co-occurrence graph — a poly-time surrogate for boundary
    expansion (Cheeger). Larger ⇒ better expander ⇒ (BSW) larger
    resolution width forced. Returns 0 for a disconnected/empty graph."""
    n = formula.num_vars
    if n < 2:
        return 0.0
    A = _var_cooccurrence(formula)
    d = A.sum(axis=1)
    if np.any(d <= 0):
        return 0.0  # isolated variable ⇒ graph disconnected ⇒ gap 0
    dinv = 1.0 / np.sqrt(d)
    L = np.eye(n) - (dinv[:, None] * A * dinv[None, :])
    ev = np.linalg.eigvalsh((L + L.T) / 2.0)
    ev.sort()
    return float(ev[1])  # smallest nonzero (λ₁ ≈ 0)


# ---------------------------------------------------------------------------
# Exact solution-space geometry (small n only)
# ---------------------------------------------------------------------------

@dataclass
class SolutionStats:
    num_solutions: int
    backbone_fraction: float   # frozen variables / n (defined 0 if UNSAT)
    num_clusters: int          # Hamming-1-connected components of sol set
    satisfiable: bool


def solution_stats(formula: CNFFormula, max_vars: int = 24) -> SolutionStats:
    """Exact solution-space geometry by exhaustive enumeration.

    Enumerates all 2^n assignments (guarded by max_vars), collects the
    satisfying set, then computes:
      - num_solutions
      - backbone_fraction: fraction of variables that take the same value
        in every solution (frozen / backbone variables)
      - num_clusters: connected components of the solution set under
        single-bit-flip (Hamming distance 1) adjacency — the clustering /
        shattering structure.
    """
    n = formula.num_vars
    if n > max_vars:
        raise ValueError(f"solution_stats is exact only for n<=max_vars={max_vars}; got n={n}")
    # Encode clauses as (mask, sign) for fast checking on integer assignments.
    clause_bits = []
    for cl in formula.clauses:
        pos = 0
        neg = 0
        for l in cl:
            v = abs(l) - 1
            if l > 0:
                pos |= (1 << v)
            else:
                neg |= (1 << v)
        clause_bits.append((pos, neg))
    sols = []
    for x in range(1 << n):
        ok = True
        for pos, neg in clause_bits:
            # clause satisfied if some positive lit true or some neg lit false
            if (x & pos) == 0 and (~x & neg) == 0:
                ok = False
                break
        if ok:
            sols.append(x)
    if not sols:
        return SolutionStats(0, 0.0, 0, False)
    arr = np.array(sols, dtype=np.int64)
    # backbone: variables constant across all solutions
    frozen = 0
    for v in range(n):
        bit = (arr >> v) & 1
        if bit.min() == bit.max():
            frozen += 1
    backbone = frozen / n
    # clusters: union-find over Hamming-1 adjacency
    parent = list(range(len(sols)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    index = {s: i for i, s in enumerate(sols)}
    for i, s in enumerate(sols):
        for v in range(n):
            nb = s ^ (1 << v)
            j = index.get(nb)
            if j is not None:
                union(i, j)
    clusters = len({find(i) for i in range(len(sols))})
    return SolutionStats(len(sols), backbone, clusters, True)

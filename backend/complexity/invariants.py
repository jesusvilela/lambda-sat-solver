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


# ---------------------------------------------------------------------------
# Resolution refutation width — the "sheaf obstruction level" made exact
# ---------------------------------------------------------------------------
# For an UNSAT formula, the minimum width w such that width-w resolution
# derives the empty clause is the level at which local (width-<=w)
# consistency fails to glue into global consistency (Atserias-Dalmau
# k-consistency <-> width). By Ben-Sasson-Wigderson, resolution SIZE >=
# exp(Omega((w - w0)^2 / n)), so width is an intrinsic, solver-independent
# hardness carrier. This is the executable form of the sheaf-obstruction
# view of UNSAT.

def _resolve(c1, c2):
    """All non-tautological resolvents of two clauses (frozensets of ints)."""
    out = []
    for lit in c1:
        if -lit in c2:
            r = (c1 - {lit}) | (c2 - {-lit})
            if not any(-x in r for x in r):  # non-tautological
                out.append(frozenset(r))
    return out


def min_refutation_width(formula: CNFFormula, wmax: int = 8,
                         max_closure: int = 200000):
    """Minimum resolution refutation width, or None if not found within
    (wmax, max_closure). Only meaningful for UNSAT formulas; returns 0 if
    the formula already contains the empty clause.

    Exact for small formulas. Guarded by wmax and a closure-size cap so it
    degrades gracefully rather than exploding."""
    axioms = [frozenset(c) for c in formula.clauses]
    if any(len(c) == 0 for c in axioms):
        return 0
    for w in range(1, wmax + 1):
        clauses = {c for c in axioms if len(c) <= w}
        frontier = list(clauses)
        derived_empty = False
        while frontier and len(clauses) < max_closure:
            new = []
            for i, c1 in enumerate(frontier):
                for c2 in clauses:
                    for r in _resolve(c1, c2):
                        if len(r) <= w and r not in clauses:
                            if len(r) == 0:
                                derived_empty = True
                                break
                            new.append(r)
                    if derived_empty:
                        break
                if derived_empty:
                    break
            if derived_empty:
                return w
            fresh = [c for c in new if c not in clauses]
            clauses.update(fresh)
            frontier = fresh
        if derived_empty:
            return w
    return None


# ---------------------------------------------------------------------------
# Connection (signed / Z2 gain) Laplacian frustration - the lateral technique
# ---------------------------------------------------------------------------
# From the connection_laplacian program: build the signed variable graph
# where an edge (i,j) carries the product of the two literals' polarities
# accumulated over the clauses they share. The signed Laplacian
# L = D - A_signed is PSD; its smallest eigenvalue is 0 iff the signed
# graph is BALANCED (frustration-free) and > 0 measures frustration - a
# polarity-aware intrinsic obstruction the unsigned spectral gap misses.

def signed_laplacian_frustration(formula: CNFFormula) -> float:
    """Smallest eigenvalue of the signed (connection) Laplacian of the
    variable graph, normalized by mean degree. 0 ⇒ balanced; larger ⇒
    more frustrated. Polarity-aware, unlike spectral_gap."""
    n = formula.num_vars
    if n < 2:
        return 0.0
    A = np.zeros((n, n))
    for cl in formula.clauses:
        lits = [l for l in cl if 1 <= abs(l) <= n]
        for a in range(len(lits)):
            for b in range(a + 1, len(lits)):
                i, j = abs(lits[a]) - 1, abs(lits[b]) - 1
                if i == j:
                    continue
                s = (1 if lits[a] > 0 else -1) * (1 if lits[b] > 0 else -1)
                A[i, j] += s
                A[j, i] += s
    deg = np.abs(A).sum(axis=1)
    if np.all(deg == 0):
        return 0.0
    L = np.diag(deg) - A          # signed Laplacian, PSD
    ev = np.linalg.eigvalsh((L + L.T) / 2.0)
    lam_min = float(max(0.0, ev[0]))
    mean_deg = deg.mean()
    return lam_min / mean_deg if mean_deg > 0 else 0.0


# ---------------------------------------------------------------------------
# Energy-landscape saddle structure - "hardness as a saddle point"
# ---------------------------------------------------------------------------
# H(x) = number of violated clauses. Solutions are the energy-0 configs.
# The SADDLE connecting two solution basins is the minimum energy E* such
# that the sub-level set {x : H(x) <= E*} connects them (single-bit-flip
# adjacency). E* is the barrier height a local search must climb - the
# instance-level image of the free-energy saddle whose change of character
# is the SAT phase transition (Mezard-Parisi-Zecchina). Exact, small n.

@dataclass
class SaddleStats:
    satisfiable: bool
    num_solution_basins: int   # solution clusters at E=0 (Hamming-1)
    connect_barrier: int       # E* : energy to connect ALL solutions (0 = single basin)
    ground_energy: int         # min H (0 if SAT)


def energy_landscape_saddle(formula: CNFFormula, max_vars: int = 22) -> SaddleStats:
    """Saddle/barrier structure of the violated-clause energy landscape."""
    n = formula.num_vars
    if n > max_vars:
        raise ValueError(f"exact only for n<=max_vars={max_vars}; got n={n}")
    clause_bits = []
    for cl in formula.clauses:
        pos = neg = 0
        for l in cl:
            v = abs(l) - 1
            if l > 0:
                pos |= (1 << v)
            else:
                neg |= (1 << v)
        clause_bits.append((pos, neg))

    def energy(x):
        e = 0
        for pos, neg in clause_bits:
            if (x & pos) == 0 and (~x & neg) == 0:
                e += 1
        return e

    N = 1 << n
    E = np.fromiter((energy(x) for x in range(N)), dtype=np.int32, count=N)
    ground = int(E.min())
    sols = np.flatnonzero(E == 0)
    if sols.size == 0:
        return SaddleStats(False, 0, -1, ground)

    # Flood the landscape in ascending energy order; union Hamming-1
    # neighbours already flooded. Record when all solutions are connected.
    order = np.argsort(E, kind="stable")
    parent = list(range(N))
    added = bytearray(N)
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    sol_set = set(int(s) for s in sols)
    # basins at E=0 (solution clusters)
    for s in sols:
        added[s] = 1
    for s in sols:
        for v in range(n):
            nb = int(s) ^ (1 << v)
            if added[nb]:
                union(int(s), nb)
    num_basins = len({find(int(s)) for s in sols})

    connect_barrier = 0
    if num_basins > 1:
        # continue flooding upward until all solutions share a root
        # reset flood, redo in energy order tracking barrier
        parent2 = list(range(N))
        added2 = bytearray(N)
        def find2(a):
            while parent2[a] != a:
                parent2[a] = parent2[parent2[a]]
                a = parent2[a]
            return a
        def union2(a, b):
            ra, rb = find2(a), find2(b)
            if ra != rb:
                parent2[ra] = rb
        connect_barrier = ground
        for x in order:
            x = int(x)
            added2[x] = 1
            for v in range(n):
                nb = x ^ (1 << v)
                if added2[nb]:
                    union2(x, nb)
            roots = {find2(s) for s in sol_set}
            if len(roots) == 1:
                connect_barrier = int(E[x])
                break
    return SaddleStats(True, num_basins, connect_barrier, 0)

"""Intrinsic, solver-independent structural invariants of a CNF formula,
for the hardness-lower-bound ladder (docs/ladder/RUNG1_PLAN.md).

Every function here takes only the formula and returns a number that is a
property of the formula (or its solution space) — never of a particular
solver's run. Two tiers:

  cheap (poly-time, graph-structural):
    mean_var_degree, var_degree_entropy, spectral_gap
  exact-for-small-n (solution-space geometry, O(2^n)):
    solution_stats -> (num_solutions, backbone_fraction, num_clusters)
  obstruction levels (intrinsic, exact, exponential):
    min_refutation_width  -- resolution/sheaf obstruction (Rung 2)
    nullstellensatz_degree -- algebraic/rank-deficiency obstruction (Rung 2,
                              algebraic face; the zero-divisor lift)

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
# Nullstellensatz / Polynomial-Calculus degree over GF(2)
#   the ALGEBRAIC sibling of min_refutation_width
# ---------------------------------------------------------------------------
# The operator's "zero divisor = rank deficiency = directional collapse"
# insight, made executable. Encode each clause as its violation polynomial
# over GF(2): clause C is violated exactly when every literal is false, so
#     v_C(x) = PROD_{l in C} (1 - l)        (l = x_i or 1 - x_i)
# reduces mod (x_i^2 = x_i) to a multilinear polynomial that is 1 on the
# unique assignment falsifying C and 0 elsewhere. The formula is UNSAT iff
# the constant 1 lies in the ideal generated by {v_C} together with the
# Boolean axioms x_i^2 - x_i -- i.e. iff SUM_C g_C * v_C = 1 for some
# polynomials g_C. The *Nullstellensatz degree* is the least d for which a
# certificate with deg(g_C * v_C) <= d exists. Equivalently: the least d at
# which 1 lies in the GF(2)-linear span of { m * v_C : deg(m*v_C) <= d } --
# a pure rank condition on the degree-d "multiply-and-add" operator M_d.
# The obstruction to a low-degree certificate is exactly a *cokernel* /
# rank deficiency of M_d: 1 is not reachable = the generators collapse into
# a subspace missing the constant. This is the algebraic twin of resolution
# width (Rung 2): NS/PC degree lower-bounds Polynomial-Calculus refutation
# size just as width lower-bounds resolution size, and for many families the
# two obstruction levels coincide up to constants.
#
# Monomials are represented as Python ints (bit i set <=> variable x_i
# present); a polynomial over GF(2) is a set of such monomials (its support),
# with addition = symmetric difference.

def _poly_mul(p, q):
    """Product of two GF(2) multilinear polynomials (sets of monomials).
    x_i^2 = x_i is automatic because monomials are bitmasks and OR is
    idempotent; coefficients live in GF(2) so equal monomials cancel."""
    out = set()
    for a in p:
        for b in q:
            m = a | b
            if m in out:
                out.discard(m)
            else:
                out.add(m)
    return out


def _clause_violation_poly(clause):
    """Multilinear GF(2) polynomial that is 1 exactly on the single
    assignment falsifying `clause` and 0 on every other assignment.
    Literal x_i false => factor x_i; literal ~x_i false => factor (1 + x_i)."""
    poly = {0}  # constant 1
    for l in clause:
        i = abs(l) - 1
        factor = {0, 1 << i} if l > 0 else {1 << i}  # (1 + x_i) or x_i
        poly = _poly_mul(poly, factor)
    return poly


def _deg(m):
    return bin(m).count("1")


def _maxdeg(poly):
    return max((_deg(m) for m in poly), default=0)


def _in_gf2_span(basis, target):
    """Row-reduce `target` against a leading-monomial-keyed `basis`
    (built lazily); return True iff it reduces to 0 (is in the span)."""
    vec = set(target)
    while vec:
        lead = max(vec, key=lambda m: (_deg(m), m))
        row = basis.get(lead)
        if row is None:
            return False
        vec ^= row
    return True


def _reduce_into_basis(basis, vec):
    """Insert `vec` into the GF(2) row-echelon `basis` keyed by leading
    monomial (deg-then-value order), reducing against existing rows first."""
    vec = set(vec)
    while vec:
        lead = max(vec, key=lambda m: (_deg(m), m))
        row = basis.get(lead)
        if row is None:
            basis[lead] = vec
            return
        vec ^= row


def nullstellensatz_degree(formula: CNFFormula, dmax: int = 6,
                           max_vars: int = 22):
    """Nullstellensatz / Polynomial-Calculus refutation degree over GF(2):
    the least degree d at which the constant 1 lies in the GF(2)-linear span
    of { monomial * clause-violation-poly } with product degree <= d.

    Returns the integer degree for an UNSAT formula, or None if the formula
    is satisfiable (no certificate exists at any degree) or none is found
    within `dmax`. Returns 0 if an empty clause is present.

    This is the executable rank-deficiency obstruction: at each d it builds a
    GF(2) row-echelon basis of the degree-d generator space and checks
    whether 1 is reachable; the smallest such d is the NS degree. Exact but
    exponential in the worst case (generator count is O(m * n^d)), so it is
    guarded by `dmax` and `max_vars` -- the algebraic sibling of
    min_refutation_width, and equally the intrinsic obstruction level rather
    than a cheap proxy.

    Theory: an UNSAT CNF has 1 in the ideal <v_C, x_i^2-x_i>; the least
    certificate degree is the NS degree, which lower-bounds Polynomial
    Calculus refutation size (Clegg-Edmonds-Impagliazzo; Buss et al.), the
    algebraic analogue of Ben-Sasson-Wigderson width lower bounds.
    """
    n = formula.num_vars
    if n > max_vars:
        raise ValueError(
            f"nullstellensatz_degree exact only for n <= {max_vars}; got {n}")
    if any(len(c) == 0 for c in formula.clauses):
        return 0
    if not formula.clauses:
        return None  # empty formula is trivially SAT

    violation_polys = [_clause_violation_poly(c) for c in formula.clauses]
    # monomials grouped by degree, so we can extend the generator set as d grows
    monos_by_deg: List[List[int]] = [[] for _ in range(dmax + 1)]
    for m in range(1 << n):
        d = _deg(m)
        if d <= dmax:
            monos_by_deg[d].append(m)

    for d in range(0, dmax + 1):
        basis: dict = {}
        for vc in violation_polys:
            for md in range(0, d + 1):
                for m in monos_by_deg[md]:
                    g = _poly_mul({m}, vc)
                    if _maxdeg(g) <= d:
                        _reduce_into_basis(basis, g)
        if _in_gf2_span(basis, {0}):
            return d
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
class CrossAlgebraDepth:
    resolution_width: Optional[int]      # obstruction depth in resolution
    nullstellensatz_degree: Optional[int]  # obstruction depth in GF(2) NS
    best: Optional[int]                  # min over the algebras we can measure


def cross_algebra_depth(formula: CNFFormula, wmax: int = 8,
                        dmax: int = 6, max_vars: int = 22,
                        max_closure: int = 200000) -> CrossAlgebraDepth:
    """The 'shallow-Emperor' depth: the obstruction level of an UNSAT formula
    in EACH proof algebra we can measure (resolution width, GF(2)
    Nullstellensatz degree), and the minimum over them.

    This is the portfolio principle made intrinsic. We proved these two depths
    are INCOMPARABLE (PHP: width 2 < NS 4; Tseitin K4: NS 3 < width 4), so
    neither algebra dominates and `best = min(...)` is strictly better than
    either alone on a mixed workload -- exactly why a portfolio SAT solver
    (which runs several engines and takes the winner) beats any single engine.

    Honest label: this is a DEMONSTRATOR, not a fast router. Both depths are
    exponential to compute, so you would never call this to *route* a solver;
    it exists to make the cross-algebra structure explicit and testable. The
    practical shadow of the same principle is the solver's real portfolio /
    restart / heuristic switching -- searching for the frame in which this
    instance's obstruction is shallowest.
    """
    w = min_refutation_width(formula, wmax=wmax, max_closure=max_closure)
    d = nullstellensatz_degree(formula, dmax=dmax, max_vars=max_vars)
    present = [x for x in (w, d) if x is not None]
    best = min(present) if present else None
    return CrossAlgebraDepth(w, d, best)


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

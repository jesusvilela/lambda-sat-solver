"""orbifold -- satisfiability as a mesh of orbifold charts (symmetry quotients).

The un-projected satisfiability signature (the object of which the classical
SAT/UNSAT bit is the pi_truth shadow) gains its natural extra structure here: an
instance is not a bare point but an ORBIFOLD chart -- an instance together with
its local symmetry (isotropy) group, the CNF's automorphisms. Satisfiability is
the same on the quotient as on the cover (a symmetry maps models to models), but
the quotient is exponentially smaller -- which is exactly why the counting frame
works on PHP (interchangeable pigeons ARE the isotropy).

We do not compute the full automorphism group (graph-isomorphism-hard). We
BRACKET it, soundly, both directions:

  * upper bound -- 1-WL color refinement partitions the variables so that
    automorphic variables always share a color; hence Aut subset of the class-wise
    symmetric group, so |Aut| <= prod |class|!. This is the isotropy SKELETON.
  * lower bound -- verified single-variable transpositions: a swap v<->w that maps
    the clause SET to itself is a genuine automorphism (checked by application).
    Within a fully-verified color class of size k these generate S_k, so
    |Aut| >= prod k! over such classes.

The mesh: the cosmo-map tiles, each now carrying its symmetry skeleton, glued by
the same restriction/dual edges -- a mesh of orbifold charts, not a graph of
points.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .cnf_utils import CNFFormula
from .observer import adjudicate, frame_ambiguity


def _log2_factorial(k: int) -> float:
    return math.lgamma(k + 1) / math.log(2.0) if k > 1 else 0.0


# --------------------------------------------------------------------------
# Color refinement (1-WL): the isotropy skeleton (sound upper bound on Aut)
# --------------------------------------------------------------------------
def symmetry_partition(formula: CNFFormula) -> List[List[int]]:
    """1-WL color refinement of the variables (sign- and clause-length-aware).
    Automorphic variables always share a color, so the returned classes are a
    sound OVER-approximation of the orbits: variables in different classes are
    provably in different orbits."""
    n = formula.num_vars
    if n == 0:
        return []
    # dedup to the clause SET: automorphisms act on the set, and duplicate/raw
    # clauses would spuriously refine (separate) genuinely-symmetric variables.
    seen: set = set()
    clauses = []
    for c in formula.clauses:
        fc = frozenset(c)
        if fc not in seen:
            seen.add(fc)
            clauses.append(sorted(fc, key=abs))
    occ: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for ci, c in enumerate(clauses):
        for lit in c:
            occ[abs(lit)].append((1 if lit > 0 else -1, ci))

    def normalize(colmap: Dict[int, object]) -> Dict[int, int]:
        order = {c: i for i, c in enumerate(sorted(set(colmap.values()),
                                                   key=repr))}
        return {k: order[v] for k, v in colmap.items()}

    var_color = normalize({
        v: tuple(sorted((s, len(clauses[ci])) for s, ci in occ[v]))
        for v in range(1, n + 1)})
    prev = len(set(var_color.values()))
    for _ in range(n + 2):
        clause_color = {
            ci: tuple(sorted((1 if lit > 0 else -1, var_color[abs(lit)])
                             for lit in c))
            for ci, c in enumerate(clauses)}
        var_color = normalize({
            v: (var_color[v],
                tuple(sorted((s, clause_color[ci]) for s, ci in occ[v])))
            for v in range(1, n + 1)})
        ncol = len(set(var_color.values()))
        if ncol == prev:
            break
        prev = ncol

    classes: Dict[int, List[int]] = defaultdict(list)
    for v in range(1, n + 1):
        classes[var_color[v]].append(v)
    return sorted((sorted(g) for g in classes.values()),
                  key=lambda g: (len(g), g))


def symmetry_log2_upper(formula: CNFFormula) -> float:
    """log2 of the isotropy-skeleton order: sum log2(|class|!) over color classes
    -- a sound UPPER bound on log2|Aut| (Aut preserves colors)."""
    return sum(_log2_factorial(len(g)) for g in symmetry_partition(formula))


# --------------------------------------------------------------------------
# Verified transpositions: a sound LOWER bound on Aut
# --------------------------------------------------------------------------
def _transposition_is_automorphism(clause_set, v: int, w: int) -> bool:
    """Does swapping variables v and w map the clause SET to itself?"""
    def swap(lit: int) -> int:
        a = abs(lit)
        if a == v:
            return w if lit > 0 else -w
        if a == w:
            return v if lit > 0 else -v
        return lit
    return {frozenset(swap(l) for l in c) for c in clause_set} == clause_set


def verified_symmetry(formula: CNFFormula) -> Tuple[List[List[int]], float]:
    """Union variables joined by a VERIFIED transposition (a real automorphism),
    searching only within color classes (cheap and complete for single swaps).
    Returns (classes, log2 lower bound on |Aut|). A class all of whose members
    verify against a common base is fully symmetric -> contributes |class|!."""
    clause_set = [frozenset(c) for c in formula.clauses]
    clause_set = set(clause_set)
    lower_classes: List[List[int]] = []
    log2_lb = 0.0
    for group in symmetry_partition(formula):
        if len(group) == 1:
            lower_classes.append(group)
            continue
        base = group[0]
        verified = [base]
        for other in group[1:]:
            if _transposition_is_automorphism(clause_set, base, other):
                verified.append(other)
        lower_classes.append(sorted(verified))
        log2_lb += _log2_factorial(len(verified))
        for other in group[1:]:
            if other not in verified:
                lower_classes.append([other])
    return lower_classes, log2_lb


# --------------------------------------------------------------------------
# EXACT isotropy: refinement-pruned automorphism enumeration
# --------------------------------------------------------------------------
def _var_order(n: int, clauses, cand) -> List[int]:
    """Order variables so clauses close early (max pruning): BFS over the
    clause-adjacency graph, seeded at the most-constrained variable."""
    adj: Dict[int, set] = {v: set() for v in range(1, n + 1)}
    for c in clauses:
        vs = [abs(l) for l in c]
        for a in vs:
            adj[a].update(vs)
    seen: set = set()
    order: List[int] = []
    for seed in sorted(range(1, n + 1), key=lambda v: (len(cand[v]), v)):
        if seed in seen:
            continue
        stack = [seed]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            order.append(v)
            for w in sorted(adj[v] - seen, key=lambda u: (len(cand[u]), u)):
                stack.append(w)
    return order


class _Over(Exception):
    pass


def _exists_automorphism(clause_set, cand, cls_of, order_vars, forced,
                         budget, nodes) -> bool:
    """Is there a sign-preserving automorphism fixing the clause set that extends
    the partial map `forced` (var -> image)? A single pruned backtracking SEARCH
    (find one), not an enumeration -- this is what makes the order computation
    scale past |Aut|."""
    assign = dict(forced)
    used = set(assign.values())

    def closes_ok(v: int) -> bool:
        for c in cls_of[v]:
            if all(abs(l) in assign for l in c):
                img = frozenset(assign[abs(l)] if l > 0 else -assign[abs(l)]
                                for l in c)
                if img not in clause_set:
                    return False
        return True

    for v in list(assign):                     # forced part must be consistent
        if not closes_ok(v):
            return False
    remaining = [v for v in order_vars if v not in assign]

    def bt(i: int) -> bool:
        nodes[0] += 1
        if nodes[0] > budget:
            raise _Over()
        if i == len(remaining):
            return True
        v = remaining[i]
        for w in cand[v]:
            if w in used:
                continue
            assign[v] = w
            used.add(w)
            if closes_ok(v) and bt(i + 1):
                return True
            del assign[v]
            used.discard(w)
        return False

    return bt(0)


def automorphism_group_order(formula: CNFFormula,
                             node_budget: int = 80_000):
    """EXACT |Aut| by orbit-stabilizer (Schreier-Sims): |Aut| = product over a
    base b1,b2,... of |orbit of bi under the group fixing b1..b_{i-1}|, where each
    orbit is found by constrained automorphism SEARCHES (not enumeration), so it
    scales far past |Aut|. Returns (order, True), or (None, False) if the node
    budget is exceeded. Verified against brute force and the PHP closed form
    n!*(n-1)! in test_orbifold."""
    n = formula.num_vars
    if n == 0:
        return 1, True
    clause_set = frozenset(frozenset(c) for c in formula.clauses)
    cand = {v: list(cls) for cls in symmetry_partition(formula) for v in cls}
    clauses = [list(c) for c in clause_set]           # deduped
    cls_of: Dict[int, List[List[int]]] = {v: [] for v in range(1, n + 1)}
    for c in clauses:
        for lit in c:
            cls_of[abs(lit)].append(c)
    order_vars = _var_order(n, clauses, cand)
    nodes = [0]
    total = 1
    forced: Dict[int, int] = {}                # pointwise-stabilized base points
    fixed_images = set()
    try:
        for b in order_vars:
            orbit = 1                          # b -> b (identity in the stabilizer)
            for target in cand[b]:
                if target == b or target in fixed_images:
                    continue
                probe = dict(forced)
                probe[b] = target
                if _exists_automorphism(clause_set, cand, cls_of, order_vars,
                                        probe, node_budget, nodes):
                    orbit += 1
            total *= orbit
            forced[b] = b                      # fix b pointwise for later levels
            fixed_images.add(b)
        return total, True
    except _Over:
        return None, False


def exact_symmetry_log2(formula: CNFFormula,
                        node_budget: int = 80_000) -> Optional[float]:
    """Exact log2|Aut| when tractable within budget, else None (use the bracket)."""
    order, ok = automorphism_group_order(formula, node_budget)
    return math.log2(order) if ok and order else (0.0 if ok else None)


# --------------------------------------------------------------------------
# The orbifold satisfiability signature (the un-projected verdict)
# --------------------------------------------------------------------------
@dataclass
class SatSignature:
    """The un-projected satisfiability verdict: the classical bit is `status`
    (pi_truth), and everything else is what that projection discards."""
    status: str                       # 'SAT' | 'UNSAT' | 'CDCL_NEEDED'  (the bit)
    action: str                       # accept | repair | escalate  (the tier)
    resolved_by: str
    certified: bool
    polysemy_degree: int              # C: how many single frames also decide it
    remainder_open: bool              # escalate -> an explicit open remainder
    symmetry_classes: List[List[int]]      # the isotropy skeleton (upper)
    symmetry_log2_upper: float             # log2 |Aut| upper bound
    symmetry_log2_lower: float             # log2 |Aut| verified lower bound
    symmetry_log2_exact: Optional[float]   # EXACT log2 |Aut| when tractable

    @property
    def classical_bit(self) -> str:
        """pi_truth: the one-bit shadow this whole object extends."""
        return self.status


def poincare_radius(formula: CNFFormula, node_budget: int = 80_000) -> float:
    """Non-Euclidean placement: the Poincare-disk radius of an instance. A
    STRUCTURE score = log2|Aut| (exact or bracketed) + a bonus if a frame decides
    it; radius = 1/(1+score) in (0,1]. Highly symmetric / frame-decidable
    instances sit near the center; RIGID, frame-void (CDCL) instances approach
    the boundary at infinity d_infinity -- the observer's asymptotic region, where
    no frame reaches. The tessellation is thus anisomorphic and hyperbolic: the
    exponential family of hard instances has infinite room out at the boundary."""
    sym = exact_symmetry_log2(formula, node_budget)
    if sym is None:
        sym = symmetry_log2_upper(formula)
    decided = adjudicate(formula).status != "CDCL_NEEDED"
    score = sym + (4.0 if decided else 0.0)
    return 1.0 / (1.0 + score)


def hyperbolic_depth(formula: CNFFormula, node_budget: int = 80_000) -> float:
    """artanh(radius): hyperbolic distance from the center. Diverges as an
    instance approaches the rigid/frame-void boundary d_infinity -- so rigidity is
    literally an infinite hyperbolic distance, not a bounded Euclidean one."""
    r = min(poincare_radius(formula, node_budget), 1.0 - 1e-12)
    return math.atanh(r)


def satisfiability_signature(formula: CNFFormula) -> SatSignature:
    """Return the orbifold chart of `formula`: its certified verdict/tier, its
    polysemy (C), its open remainder, and its bracketed isotropy group. The
    classical satisfiability bit is recovered as `.classical_bit`."""
    v = adjudicate(formula)
    upper_classes = symmetry_partition(formula)
    _, log2_lb = verified_symmetry(formula)
    return SatSignature(
        status=v.status,
        action=v.action,
        resolved_by=v.resolved_by,
        certified=v.certified,
        polysemy_degree=frame_ambiguity(formula).degree,
        remainder_open=(v.status == "CDCL_NEEDED"),
        symmetry_classes=upper_classes,
        symmetry_log2_upper=sum(_log2_factorial(len(g)) for g in upper_classes),
        symmetry_log2_lower=log2_lb,
        symmetry_log2_exact=exact_symmetry_log2(formula),
    )

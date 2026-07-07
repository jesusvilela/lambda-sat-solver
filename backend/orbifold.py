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
    clauses = [list(c) for c in formula.clauses]
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

    @property
    def classical_bit(self) -> str:
        """pi_truth: the one-bit shadow this whole object extends."""
        return self.status


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
    )

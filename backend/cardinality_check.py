"""Counting / cardinality frame — a sound UNSAT fast-path for the pigeonhole
structure, the third sibling of `binary_clause_check` (implication frame) and
`xor_extraction` (GF(2)/parity frame).

Why this frame exists: the pigeonhole principle survives both other frames.
It carries no parity (`xor_fraction = 0`, so GF(2) is blind) and its 2-SAT
subset is consistent (the implication frame is blind). Its obstruction is a
*magnitude* fact — n pigeons cannot fit in n-1 holes — and GF(2) cannot count
(1+1=0 destroys magnitude). PHP is the characteristic-0 dual of Tseitin: Tseitin
collapses under GF(2) linear algebra, PHP collapses under integer counting
(cutting planes / pseudo-Boolean), where it has polynomial-size refutations while
resolution needs 2^Ω(n) (Haken 1985).

This module recovers the pigeonhole structure and refutes it by the counting
argument, soundly:

  * ALO ("at least one"): each all-positive clause forces >= 1 of its variables
    true. If the ALO clauses are variable-disjoint, at least `k` variables are
    true, where `k` = number of ALO clauses (the pigeons).
  * AMO ("at most one"): negative binary clauses (-a v -b) mean a, b are not
    both true. A set of variables that are pairwise excluded (a clique in the
    exclusion graph) can hold at most one true (a hole).
  * If every ALO variable lies in one of `m` disjoint AMO cliques, at most `m`
    variables are true. So `k > m`  =>  UNSAT.

Scope: this refutes the clean pigeonhole pattern (and its relatives). Anything
else returns `refuted = False` and falls through to CDCL — it is a sound partial
certificate, not a decision procedure.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

from .cnf_utils import CNFFormula


@dataclass
class CardinalityRefutation:
    refuted: bool          # True => formula is UNSAT (sound counting certificate)
    pigeons: int           # k : variable-disjoint at-least-one clauses
    holes: int             # m : disjoint at-most-one cliques covering their vars


def pigeonhole_counting_refutation(formula: CNFFormula) -> CardinalityRefutation:
    """Sound UNSAT via the counting argument if the pigeonhole structure is
    present (k disjoint ALO clauses whose variables are covered by m < k
    disjoint AMO cliques); otherwise `refuted = False`."""
    # ALO = all-positive clauses (each forces >= 1 true)
    alo: List[Set[int]] = [set(c) for c in formula.clauses
                           if c and all(l > 0 for l in c)]
    if len(alo) < 2:
        return CardinalityRefutation(False, len(alo), 0)

    # ALO clauses must be variable-disjoint for the >= k bound to be sound
    alo_vars: Set[int] = set()
    for s in alo:
        if alo_vars & s:
            return CardinalityRefutation(False, len(alo), 0)  # overlap
        alo_vars |= s
    k = len(alo)

    # exclusion graph from negative binary clauses (-a v -b), restricted to
    # ALO variables
    excl: Dict[int, Set[int]] = defaultdict(set)
    for c in formula.clauses:
        if len(c) == 2 and c[0] < 0 and c[1] < 0:
            a, b = -c[0], -c[1]
            if a in alo_vars and b in alo_vars and a != b:
                excl[a].add(b)
                excl[b].add(a)

    # connected components of the exclusion graph over ALO variables
    unvisited = set(alo_vars)
    m = 0
    while unvisited:
        root = next(iter(unvisited))
        stack, comp = [root], set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            unvisited.discard(u)
            for w in excl[u]:
                if w not in comp:
                    stack.append(w)
        # each component must be a clique to hold at most one true (else the
        # <= 1 capacity is not justified and we must not claim a refutation)
        for a in comp:
            if not (comp - {a}) <= excl[a]:
                return CardinalityRefutation(False, k, 0)  # non-clique group
        m += 1

    return CardinalityRefutation(k > m, k, m)

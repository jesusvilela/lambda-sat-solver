"""
Binary-clause consistency check (2-SAT / implication-graph analysis).

Correction to an earlier plan: the connection Laplacian kernel-dimension
theorem (jesusvilela/connection_laplacian_lean, L8_Recognition.lean:
finrank ker(signedLaplacianMobius) = numBalancedComponents) is about
signed/gain graphs - equality/inequality (XOR) constraints between node
pairs - via union-find-with-parity / bipartiteness. That is a real but
narrower structure than general 2-literal OR-clauses, and doesn't apply
to them directly; conflating the two would have shipped a feature that
looked grounded but wasn't. The correct, general tool for "is this
formula's binary-clause subset consistent" is the classical 2-SAT
algorithm (Aspvall, Plass, Tarjan, 1979): build the implication graph
over literals and find strongly connected components. That's what this
module implements - no signed-graph machinery needed, and it correctly
covers XOR-encoded clause pairs too as a special case, since those are
just particular binary clauses.

A binary clause (a OR b) is equivalent to two implications:
  not(a) -> b   and   not(b) -> a
Build a directed graph over 2n nodes (one per literal), add both edges
for every binary clause, and find strongly connected components (SCCs)
via Kosaraju's algorithm. If a variable and its negation land in the
same SCC, the formula forces that variable to be both true and false:
proof of UNSAT from the binary clauses alone, independent of Kissat,
independent of DRAT/proof-checker availability.

Scope: this only inspects 2-literal clauses. A formula can be
consistent on its binary clauses but still UNSAT overall (the
contradiction may only emerge from longer clauses) - in that case this
reports "consistent" and simply doesn't apply. It is a sound partial
certificate for UNSAT, not a full decision procedure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .cnf_utils import CNFFormula


@dataclass
class BinaryClauseCheckResult:
    """Result of checking a formula's binary-clause subset for consistency."""

    consistent: bool
    num_binary_clauses: int
    #: 1-indexed variable forced to be both true and false; set iff not consistent
    conflicting_variable: Optional[int] = None


def _literal_node(lit: int) -> int:
    """Map a DIMACS literal to a 0-indexed node: var v true -> 2*(v-1), false -> 2*(v-1)+1."""
    v = abs(lit)
    return 2 * (v - 1) + (0 if lit > 0 else 1)


def _negate_node(node: int) -> int:
    """The node for the opposite polarity of the same variable."""
    return node ^ 1


def _kosaraju_scc(graph: List[List[int]], num_nodes: int) -> List[int]:
    """Iterative Kosaraju's algorithm (avoids Python recursion-depth limits)."""
    visited = [False] * num_nodes
    finish_order: List[int] = []

    for start in range(num_nodes):
        if visited[start]:
            continue
        visited[start] = True
        stack = [(start, iter(graph[start]))]
        while stack:
            node, it = stack[-1]
            advanced = False
            for succ in it:
                if not visited[succ]:
                    visited[succ] = True
                    stack.append((succ, iter(graph[succ])))
                    advanced = True
                    break
            if not advanced:
                finish_order.append(node)
                stack.pop()

    transpose: List[List[int]] = [[] for _ in range(num_nodes)]
    for u in range(num_nodes):
        for v in graph[u]:
            transpose[v].append(u)

    scc_id = [-1] * num_nodes
    current = 0
    for node in reversed(finish_order):
        if scc_id[node] != -1:
            continue
        scc_id[node] = current
        stack = [node]
        while stack:
            u = stack.pop()
            for v in transpose[u]:
                if scc_id[v] == -1:
                    scc_id[v] = current
                    stack.append(v)
        current += 1

    return scc_id


def check_binary_clauses(formula: CNFFormula) -> BinaryClauseCheckResult:
    """Check whether the formula's 2-literal clauses are jointly consistent.

    Args:
        formula: CNF formula (only its binary clauses are inspected)

    Returns:
        BinaryClauseCheckResult; `consistent=False` is a sound proof that
        the whole formula is UNSAT (a necessary sub-constraint already
        fails), independent of Kissat or proof checking.
    """
    binary_clauses = [c for c in formula.clauses if len(c) == 2]
    num_nodes = 2 * formula.num_vars

    graph: List[List[int]] = [[] for _ in range(num_nodes)]
    for clause in binary_clauses:
        a, b = clause
        na = _negate_node(_literal_node(a))
        nb = _negate_node(_literal_node(b))
        graph[na].append(_literal_node(b))
        graph[nb].append(_literal_node(a))

    scc_id = _kosaraju_scc(graph, num_nodes)

    for v in range(1, formula.num_vars + 1):
        if scc_id[_literal_node(v)] == scc_id[_literal_node(-v)]:
            return BinaryClauseCheckResult(
                consistent=False,
                num_binary_clauses=len(binary_clauses),
                conflicting_variable=v,
            )

    return BinaryClauseCheckResult(
        consistent=True,
        num_binary_clauses=len(binary_clauses),
    )

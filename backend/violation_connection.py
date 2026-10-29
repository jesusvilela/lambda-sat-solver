"""Finite signed clause-variable connection, independent of assignment sampling.

This is a *diagnostic* on the signed bipartite incidence graph, not a
SAT/UNSAT certificate, a connection-Laplacian theorem, or a Kakeya estimate.
Literal duplication is normalized; tautological clauses have no edges.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from random import Random

from .cnf_utils import CNFFormula


@dataclass(frozen=True)
class SignedConnection:
    edges: int
    components: int
    cycle_rank: int
    globally_balanced: bool
    four_cycles: int
    negative_four_cycles: int
    negative_square_fraction: float
    square_density: float
    tautological_clauses: int
    balanced_components: int


def _rows(formula: CNFFormula) -> list[dict[int, int]]:
    """Each row: variable index (0-based) -> signed literal (+1/-1)."""
    if not isinstance(formula.num_vars, int) or isinstance(formula.num_vars, bool) or formula.num_vars < 0:
        raise ValueError('invalid declared variable count')
    result = []
    for clause in formula.clauses:
        signs: dict[int, int] = {}
        tautology = False
        for lit in clause:
            if (not isinstance(lit, int) or isinstance(lit, bool) or
                    lit == 0 or abs(lit) > formula.num_vars):
                raise ValueError('invalid literal')
            var, sign = abs(lit) - 1, (1 if lit > 0 else -1)
            if var in signs and signs[var] != sign:
                tautology = True
            signs[var] = sign
        result.append({} if tautology else signs)
    return result


def signed_connection(formula: CNFFormula, *, max_wedges: int = 250000) -> SignedConnection:
    """Exact BFS Z2 switching obstruction and all signed four-cycles.

    A negative cycle obstructs a factorization s(c,v)=g(c)g(v) for all
    incidences. This factorization is NOT equivalent to satisfiability.
    Cost O(n+m+L+sum_v degree(v)^2), bounded by max_wedges.
    """
    if max_wedges < 0:
        raise ValueError('negative wedge budget')
    rows = _rows(formula)
    n, m = formula.num_vars, len(rows)
    by_var: list[list[tuple[int,int]]] = [[] for _ in range(n)]
    adj: list[list[tuple[int,int]]] = [[] for _ in range(n+m)]
    edge_count = 0
    for ci, row in enumerate(rows):
        for v, s in row.items():
            by_var[v].append((ci, s))
            adj[ci].append((m+v, s))
            adj[m+v].append((ci, s))
            edge_count += 1
    components = 0
    balanced = True
    balanced_components = 0
    spins = [0] * (n + m)
    for root in range(n + m):
        if spins[root]:
            continue
        components += 1
        spins[root] = 1
        stack = [root]
        component_balanced = True
        while stack:
            node = stack.pop()
            for neighbor, sign in adj[node]:
                expected = spins[node] * sign
                if spins[neighbor] == 0:
                    spins[neighbor] = expected
                    stack.append(neighbor)
                elif spins[neighbor] != expected:
                    balanced = False
                    component_balanced = False
        balanced_components += int(component_balanced)
    wedges = sum(len(v)*(len(v)-1)//2 for v in by_var)
    if wedges > max_wedges:
        raise ValueError('signed square wedge budget exceeded')
    # Clause-pair shared-variable wedge signs: a positive/negative pair
    # creates a negative C4, regardless of variable or clause gauge flips.
    wedge_signs: dict[tuple[int,int], list[int]] = defaultdict(lambda:[0,0])
    for entries in by_var:
        for (c1,s1),(c2,s2) in combinations(entries,2):
            counts = wedge_signs[(c1,c2)]
            counts[0 if s1*s2 > 0 else 1] += 1
    four = sum((pos+neg)*(pos+neg-1)//2 for pos,neg in wedge_signs.values())
    neg_four = sum(pos*neg for pos,neg in wedge_signs.values())
    possible = (m*(m-1)//2) * (n*(n-1)//2)
    taut_count = 0
    for original in formula.clauses:
        literals = set(original)
        taut_count += int(any(-lit in literals for lit in literals))
    return SignedConnection(edge_count, components,
                            edge_count - (m+n) + components,
                            balanced, four, neg_four,
                            neg_four / four if four else 0.0,
                            four / possible if possible else 0.0,
                            taut_count, balanced_components)


def connection_features(sig: SignedConnection) -> tuple[float, ...]:
    """Five finite structural features; low-dimensional baseline augmentation."""
    return (sig.cycle_rank/max(sig.edges,1),
            float(not sig.globally_balanced),
            sig.negative_square_fraction,
            sig.square_density,
            sig.four_cycles/max(sig.edges,1))


def margin_matched_sign_null(formula: CNFFormula, *, seed: int,
                             target_swaps: int = 32) -> tuple[CNFFormula, int]:
    """Swap checkerboards; preserve clause support and BOTH sign margins.

    A 2x2 swap flips [[+,-],[-,+]] -> [[-,+],[+,-]] on edges of a
    clause-variable square. Row and column positive counts remain fixed.
    Unlike variable gauge flips this null need NOT preserve the SAT solution
    set. It tests signed-incidence structure alone. Zero swaps = null failure.
    """
    if not 0 <= target_swaps <= 1024:
        raise ValueError('invalid swap budget')
    # Restrict the null to simple clauses. Otherwise duplicate literals
    # or tautologies would change the syntax or meaning on serialization.
    for clause in formula.clauses:
        if len({abs(lit) for lit in clause}) != len(clause):
            raise ValueError('margin null requires distinct variables per clause')
    rows = _rows(formula)
    m = len(rows)
    rng = Random(seed)
    done = 0
    for _ in range(target_swaps*80):
        if done >= target_swaps or m < 2:
            break
        c1,c2 = rng.sample(range(m),2)
        one, two = rows[c1], rows[c2]
        plus = [v for v,s in one.items() if s == 1 and two.get(v) == -1]
        minus = [v for v,s in one.items() if s == -1 and two.get(v) == 1]
        if not plus or not minus:
            continue
        u,v = rng.choice(plus), rng.choice(minus)
        for c in (c1,c2):
            rows[c][u] *= -1
            rows[c][v] *= -1
        done += 1
    # Preserve *clause and literal order* of the original as much as possible.
    output = []
    for old, signs in zip(formula.clauses, rows):
        output.append([signs[abs(lit)-1]*abs(lit) for lit in old])
    return CNFFormula(formula.num_vars,output),done

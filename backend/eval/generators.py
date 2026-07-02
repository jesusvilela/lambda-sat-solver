"""
CNF formula generators for standard SAT benchmark families.

Each generator returns a CNFFormula and the expected result (SAT/UNSAT/UNKNOWN)
so correctness of solver output can be checked automatically.

Families covered:
  - Random k-SAT (phase transition)
  - Pigeonhole principle PHP(n, n-1) — always UNSAT
  - Graph k-coloring — sat/unsat depends on graph
  - XOR chain — always SAT or UNSAT by construction
  - Mutilated chessboard — always UNSAT
  - Ladder encoding (ordering constraints) — always SAT
"""

import random
from typing import List, Optional, Tuple

from ..cnf_utils import CNFFormula


# ---------------------------------------------------------------------------
# Random k-SAT
# ---------------------------------------------------------------------------

def random_ksat(
    num_vars: int,
    num_clauses: int,
    k: int = 3,
    seed: Optional[int] = None,
) -> Tuple[CNFFormula, str]:
    """
    Generate a random k-SAT instance.

    At the well-known phase transition ratio (≈4.267 for 3-SAT) instances are
    hardest. Below the ratio instances are almost always SAT; above almost
    always UNSAT.

    Args:
        num_vars: Number of Boolean variables.
        num_clauses: Number of clauses to generate.
        k: Clause width (default 3).
        seed: Random seed for reproducibility.

    Returns:
        (formula, expected) where expected is 'UNKNOWN' for generated instances
        (the phase-transition region), 'SAT' for under-constrained, or 'UNSAT'
        for over-constrained (heuristic labels only — not guaranteed correct).
    """
    rng = random.Random(seed)
    clauses = []
    for _ in range(num_clauses):
        vars_in_clause = rng.sample(range(1, num_vars + 1), min(k, num_vars))
        clause = [v if rng.random() < 0.5 else -v for v in vars_in_clause]
        clauses.append(clause)

    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[
            f"random {k}-SAT n={num_vars} m={num_clauses} seed={seed}",
            f"ratio={num_clauses/num_vars:.3f}",
        ],
    )

    # Phase-transition heuristic labels
    ratio = num_clauses / num_vars
    phase_transition = {3: 4.267, 4: 9.93, 5: 20.8}
    pt = phase_transition.get(k, 4.267)
    if ratio < pt * 0.7:
        expected = "SAT"
    elif ratio > pt * 1.5:
        expected = "UNSAT"
    else:
        expected = "UNKNOWN"

    return formula, expected


# ---------------------------------------------------------------------------
# Pigeonhole principle PHP(n, n-1)
# ---------------------------------------------------------------------------

def pigeonhole(n: int) -> Tuple[CNFFormula, str]:
    """
    Generate the pigeonhole principle formula PHP(n, n-1).

    Encodes: n pigeons, n-1 holes.
    - Every pigeon must be in at least one hole.
    - At most one pigeon per hole.

    This is always UNSAT and exponentially hard for resolution-based solvers.

    Variable encoding: x(p, h) = pigeon p is in hole h.
    Variable index: (p-1)*(n-1) + h  (1-indexed, p in 1..n, h in 1..n-1)

    Args:
        n: Number of pigeons (n-1 holes).

    Returns:
        (formula, 'UNSAT')
    """
    holes = n - 1
    clauses: List[List[int]] = []

    def var(pigeon: int, hole: int) -> int:
        return (pigeon - 1) * holes + hole

    # Each pigeon in at least one hole
    for p in range(1, n + 1):
        clauses.append([var(p, h) for h in range(1, holes + 1)])

    # At most one pigeon per hole (at-most-one encoding)
    for h in range(1, holes + 1):
        for p1 in range(1, n + 1):
            for p2 in range(p1 + 1, n + 1):
                clauses.append([-var(p1, h), -var(p2, h)])

    num_vars = n * holes
    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[f"Pigeonhole principle PHP({n},{holes})"],
    )
    return formula, "UNSAT"


# ---------------------------------------------------------------------------
# Graph k-coloring
# ---------------------------------------------------------------------------

def graph_coloring(
    num_vertices: int,
    num_colors: int,
    edge_probability: float = 0.5,
    seed: Optional[int] = None,
) -> Tuple[CNFFormula, str]:
    """
    Generate a random graph k-coloring instance.

    Variable encoding: x(v, c) = vertex v has color c.
    Var index: (v-1)*k + c  (1-indexed).

    Clauses:
    - At least one color per vertex.
    - At most one color per vertex (pairwise).
    - Conflicting colors on edges.

    Args:
        num_vertices: Number of vertices in the graph.
        num_colors: Number of colors.
        edge_probability: Edge inclusion probability (Erdős–Rényi G(n,p)).
        seed: Random seed.

    Returns:
        (formula, expected)  where expected is 'UNKNOWN'.
    """
    rng = random.Random(seed)
    k = num_colors

    # Generate random edges (undirected)
    edges = []
    for u in range(1, num_vertices + 1):
        for v in range(u + 1, num_vertices + 1):
            if rng.random() < edge_probability:
                edges.append((u, v))

    def var(vertex: int, color: int) -> int:
        return (vertex - 1) * k + color

    clauses: List[List[int]] = []

    # At least one color per vertex
    for v in range(1, num_vertices + 1):
        clauses.append([var(v, c) for c in range(1, k + 1)])

    # At most one color per vertex (pairwise exclusion)
    for v in range(1, num_vertices + 1):
        for c1 in range(1, k + 1):
            for c2 in range(c1 + 1, k + 1):
                clauses.append([-var(v, c1), -var(v, c2)])

    # Adjacent vertices cannot share the same color
    for u, v in edges:
        for c in range(1, k + 1):
            clauses.append([-var(u, c), -var(v, c)])

    num_vars = num_vertices * k
    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[
            f"Graph {k}-coloring n={num_vertices} edges={len(edges)} p={edge_probability}",
            f"seed={seed}",
        ],
    )
    return formula, "UNKNOWN"


# ---------------------------------------------------------------------------
# XOR chain
# ---------------------------------------------------------------------------

def xor_chain(
    num_vars: int,
    expected_sat: bool = True,
    seed: Optional[int] = None,
) -> Tuple[CNFFormula, str]:
    """
    Generate an XOR-chain formula.

    Constructs a chain of XOR constraints:
        x1 XOR x2 = b1
        x2 XOR x3 = b2
        ...
        x_{n-1} XOR x_n = b_{n-1}

    with a final constraint  x1 XOR x_n = b_final chosen to make the
    formula SAT or UNSAT.

    XOR encoded into CNF as two-literal clauses (the standard 2-clause encoding
    for a XOR b = c adds 4 clauses, but for binary XOR directly we use
    (a ∨ b) ∧ (¬a ∨ ¬b) for XOR=1 and (a ∨ ¬b) ∧ (¬a ∨ b) for XOR=0).

    Args:
        num_vars: Number of variables in the chain.
        expected_sat: Whether the constructed instance should be SAT.
        seed: Random seed.

    Returns:
        (formula, 'SAT' | 'UNSAT')
    """
    if num_vars < 2:
        raise ValueError("num_vars must be at least 2")

    rng = random.Random(seed)
    clauses: List[List[int]] = []

    # Random XOR values for each adjacent pair
    xor_values = [rng.randint(0, 1) for _ in range(num_vars - 1)]

    # Encode each XOR constraint into CNF
    # x_i XOR x_{i+1} = b
    # b=1: (x_i ∨ x_{i+1}) ∧ (¬x_i ∨ ¬x_{i+1})
    # b=0: (¬x_i ∨ x_{i+1}) ∧ (x_i ∨ ¬x_{i+1})
    for i in range(num_vars - 1):
        a = i + 1
        b = i + 2
        if xor_values[i] == 1:
            clauses.append([a, b])
            clauses.append([-a, -b])
        else:
            clauses.append([-a, b])
            clauses.append([a, -b])

    # Determine the implied value of x1 XOR x_n from the chain
    chain_xor = 0
    for v in xor_values:
        chain_xor ^= v  # XOR is associative; chain gives x1 XOR x_n = chain_xor

    # Add a final XOR constraint on x1 and x_n
    # If expected_sat=True, use the consistent final value
    # If expected_sat=False, use the contradictory final value
    final_value = chain_xor if expected_sat else (1 - chain_xor)
    a = 1
    b = num_vars
    if final_value == 1:
        clauses.append([a, b])
        clauses.append([-a, -b])
    else:
        clauses.append([-a, b])
        clauses.append([a, -b])

    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[
            f"XOR chain n={num_vars} expected={'SAT' if expected_sat else 'UNSAT'}",
            f"seed={seed}",
        ],
    )
    return formula, "SAT" if expected_sat else "UNSAT"


# ---------------------------------------------------------------------------
# Mutilated chessboard
# ---------------------------------------------------------------------------

def mutilated_chessboard(n: int = 4) -> Tuple[CNFFormula, str]:
    """
    Generate the mutilated chessboard problem for an n×n board.

    Two opposite corners (top-left and bottom-right) are removed, leaving
    n²-2 squares. Asks: can the remaining squares be tiled with dominoes
    (1×2 or 2×1 tiles)?

    The answer is always NO (UNSAT) because the two removed corners have the
    same color in checkerboard coloring, so the remaining board has an unequal
    number of black and white squares.

    Variable encoding:
    - h(r, c) = horizontal domino covering (r,c) and (r,c+1) → var(r,c,'h')
    - v(r, c) = vertical domino covering (r,c) and (r+1,c) → var(r,c,'v')

    Variables are numbered 1..N in row-major order.

    Args:
        n: Board dimension (n×n). Default: 4.

    Returns:
        (formula, 'UNSAT')
    """
    removed = {(0, 0), (n - 1, n - 1)}

    def is_valid(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < n and (r, c) not in removed

    # Assign variable indices
    h_vars: dict = {}  # horizontal domino starting at (r, c)
    v_vars: dict = {}  # vertical domino starting at (r, c)
    idx = 1
    for r in range(n):
        for c in range(n):
            if is_valid(r, c) and is_valid(r, c + 1):
                h_vars[(r, c)] = idx
                idx += 1
            if is_valid(r, c) and is_valid(r + 1, c):
                v_vars[(r, c)] = idx
                idx += 1

    clauses: List[List[int]] = []

    # Every valid square must be covered by exactly one domino
    for r in range(n):
        for c in range(n):
            if not is_valid(r, c):
                continue
            # Collect all dominoes that cover (r, c)
            covering = []
            if (r, c - 1) in h_vars:
                covering.append(h_vars[(r, c - 1)])   # horizontal from left
            if (r, c) in h_vars:
                covering.append(h_vars[(r, c)])         # horizontal from this cell
            if (r - 1, c) in v_vars:
                covering.append(v_vars[(r - 1, c)])    # vertical from above
            if (r, c) in v_vars:
                covering.append(v_vars[(r, c)])          # vertical from this cell

            if not covering:
                # This square cannot be covered — formula is trivially UNSAT
                clauses.append([])  # empty clause
                continue

            # At least one domino covers this square
            clauses.append(covering)

            # At most one domino covers this square (pairwise)
            for i in range(len(covering)):
                for j in range(i + 1, len(covering)):
                    clauses.append([-covering[i], -covering[j]])

    num_vars = idx - 1
    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[f"Mutilated chessboard {n}x{n}"],
    )
    return formula, "UNSAT"


# ---------------------------------------------------------------------------
# Ladder encoding (ordering / totality constraints)
# ---------------------------------------------------------------------------

def ladder_encoding(
    num_vars: int,
    seed: Optional[int] = None,
) -> Tuple[CNFFormula, str]:
    """
    Generate a satisfiable formula using a ladder (totality) encoding.

    The ladder encoding for a variable x ∈ {0..n-1} uses n Boolean variables
    y_0, ..., y_{n-1} with y_i = (x ≥ i), enforcing totality:
        y_0 = True
        y_n = False (conceptual)
        y_i → y_{i-1}  for all i

    Here we generate a random target value t, encode it as a unit
    clause on y_t and ¬y_{t+1}, and add the ladder clauses.

    The resulting formula is always SAT.

    Args:
        num_vars: Number of Boolean variables in the ladder.
        seed: Random seed for target selection.

    Returns:
        (formula, 'SAT')
    """
    rng = random.Random(seed)
    clauses: List[List[int]] = []

    # Ladder implication chain: y_i → y_{i-1}  (if i > 0)
    # Encoded as ¬y_i ∨ y_{i-1}
    for i in range(1, num_vars):
        clauses.append([-(i + 1), i])

    # Fix y_1 = True (the first variable is always true)
    clauses.append([1])

    # Fix a random "break point": y_t = True, y_{t+1} = False
    t = rng.randint(1, num_vars - 1)
    clauses.append([t])
    clauses.append([-(t + 1)])

    formula = CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=[f"Ladder encoding n={num_vars} target={t} seed={seed}"],
    )
    return formula, "SAT"

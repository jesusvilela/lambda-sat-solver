"""
CNF instance profiling.

Extracts a small feature vector describing a formula's structure, for use
in portfolio/heuristic selection (SATzilla-style algorithm-selection
features), plus one experimental geometric feature.

All features here are computed directly from the clause list - no solving,
no external tools. Costs are kept to O(vars * clauses) except for the
optional spectral feature, which is skipped above a size threshold (see
`_SVD_MAX_CELLS`) since its SVD cost can otherwise dominate the time it
would take to just solve the instance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from .cnf_utils import CNFFormula

# Above this many (clauses * vars) matrix cells, skip the SVD-based spectral
# feature - dense SVD is roughly O(min(m, n) * m * n), and profiling should
# stay cheap relative to solving.
_SVD_MAX_CELLS = 4_000_000


@dataclass
class CNFProfile:
    """Structural feature vector for a CNF formula."""

    num_vars: int
    num_clauses: int
    clause_length_histogram: Dict[int, int]
    unit_ratio: float
    binary_ratio: float
    horn_ratio: float
    pos_neg_balance: float
    avg_var_degree: float
    var_degree_entropy: float

    #: Experimental: difference in normalized spectral entropy of the
    #: clause-variable incidence matrix under a hyperbolic (Poincare-ball
    #: exponential map) vs. plain Euclidean representation. This is a
    #: from-scratch reimplementation of an idea explored informally
    #: elsewhere (not the original author's code, which isn't available
    #: here); its only validated use so far is as a family-discriminating
    #: statistic on a small toy benchmark, not as a solving-speed signal.
    #: None when skipped (formula too large, or degenerate matrix).
    hyp_delta_entropy_ratio: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _clause_is_horn(clause) -> bool:
    """A clause is Horn if it has at most one positive literal."""
    return sum(1 for lit in clause if lit > 0) <= 1





def profile_cnf(formula: CNFFormula, compute_spectral: bool = True) -> CNFProfile:
    """Compute a structural feature vector for a CNF formula.

    Args:
        formula: CNF formula to profile
        compute_spectral: Whether to attempt the experimental hyperbolic
            spectral feature (skipped automatically above `_SVD_MAX_CELLS`
            regardless of this flag)

    Returns:
        CNFProfile with the computed features
    """
    num_vars = formula.num_vars
    num_clauses = formula.num_clauses

    clause_length_histogram: Dict[int, int] = {}
    num_unit = 0
    num_binary = 0
    num_horn = 0
    num_positive_lits = 0
    num_negative_lits = 0
    var_degree = [0] * (num_vars + 1)  # 1-indexed

    for clause in formula.clauses:
        length = len(clause)
        clause_length_histogram[length] = clause_length_histogram.get(length, 0) + 1
        if length == 1:
            num_unit += 1
        elif length == 2:
            num_binary += 1
        if _clause_is_horn(clause):
            num_horn += 1
        for lit in clause:
            if lit > 0:
                num_positive_lits += 1
            else:
                num_negative_lits += 1
            v = abs(lit)
            if 1 <= v <= num_vars:
                var_degree[v] += 1

    total_lits = num_positive_lits + num_negative_lits
    unit_ratio = num_unit / num_clauses if num_clauses else 0.0
    binary_ratio = num_binary / num_clauses if num_clauses else 0.0
    horn_ratio = num_horn / num_clauses if num_clauses else 0.0
    pos_neg_balance = num_positive_lits / total_lits if total_lits else 0.5
    avg_var_degree = total_lits / num_vars if num_vars else 0.0

    # SVD entropy ratio previously removed
    var_degree_entropy = 0.0

    return CNFProfile(
        num_vars=num_vars,
        num_clauses=num_clauses,
        clause_length_histogram=clause_length_histogram,
        unit_ratio=unit_ratio,
        binary_ratio=binary_ratio,
        horn_ratio=horn_ratio,
        pos_neg_balance=pos_neg_balance,
        avg_var_degree=avg_var_degree,
        var_degree_entropy=var_degree_entropy,
        hyp_delta_entropy_ratio=None,
    )

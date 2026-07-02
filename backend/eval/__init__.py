"""
SAT Solver Evaluation Framework

Provides:
- CNF instance generators for standard problem families
- Evaluation metrics (PAR-2, solve rate, correctness)
- Standard eval suites
- Eval runner CLI
"""

from .generators import (
    random_ksat,
    pigeonhole,
    graph_coloring,
    xor_chain,
    mutilated_chessboard,
    ladder_encoding,
)
from .metrics import (
    EvalResult,
    compute_par2,
    compute_solve_rate,
    compute_correctness_rate,
    summarize_results,
)
from .suite import EvalSuite, StandardSuites

__all__ = [
    "random_ksat",
    "pigeonhole",
    "graph_coloring",
    "xor_chain",
    "mutilated_chessboard",
    "ladder_encoding",
    "EvalResult",
    "compute_par2",
    "compute_solve_rate",
    "compute_correctness_rate",
    "summarize_results",
    "EvalSuite",
    "StandardSuites",
]

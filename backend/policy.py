"""
Rule-based heuristic/budget selection from a CNF profile.

Deliberately simple (explicit if/else rules, not learned) so its behavior
is auditable and its effect on solve time can be validated against plain
Kissat before any more sophisticated (learned) policy replaces it.
"""

from __future__ import annotations

from .cnf_utils import CNFFormula
from .kissat_wrapper import Budget, Heuristic

CONSERVATIVE = Heuristic(
    branching='vsids', restarts='geometric', phase='saved', vivify=False
)
AGGRESSIVE = Heuristic(
    branching='lrb', restarts='luby', phase='false', vivify=True
)


def choose_heuristic(formula: CNFFormula) -> Heuristic:
    """
    Hyperdimensional Geometric Routing (Geodesic Resonance Descent).
    Uses the C++ Flavor Analyzer to classify the topology into discrete
    Riemannian structures instead of squashing into 3D Euclidean scalars.
    """
    try:
        from .cython import tribridge
        res = tribridge.route_instance_topology(formula.clauses, formula.num_vars)
        struct_class = res["class"]
        
        # AGGRESSIVE for highly structured, dense manifolds (Z2xZ2, A4)
        if struct_class in ("PURE_GF2", "PARTIAL_XOR_SADDLE"):
            return AGGRESSIVE
            
        # CONSERVATIVE for UNSTRUCTURED heavy-tailed geometry
        return CONSERVATIVE
        
    except ImportError:
        # Fallback if Cython not compiled (should not happen in Canary)
        return CONSERVATIVE


def choose_budget(
    formula: CNFFormula,
    time_limit: int = 60,
    memory_limit: int = 2048,
) -> Budget:
    """Pick a resource budget for a formula."""
    del formula
    return Budget(time_limit=time_limit, memory_limit=memory_limit)

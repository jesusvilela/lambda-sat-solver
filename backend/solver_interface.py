"""
Solver Interface for R188 Level-Crossing Instrument

Wraps SAT solver infrastructure (pysat) into a uniform
SolverInterface protocol that the R188 sweep can call.

Depth-limited search is approximated via conflict budget limiting.
"""

import random
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from pysat.solvers import Glucose4, Cadical153

from .cnf_utils import CNFFormula


@dataclass
class SolverStatus:
    result: str  # SAT, UNSAT, TIMEOUT, ERROR
    model: Optional[Dict[int, bool]] = None
    stats: Optional[Dict] = None
    error_message: Optional[str] = None


# Conflict budget per depth unit (empirically tuned for Kissat/pysat)
CONFLICTS_PER_DEPTH = 5000


class SolverInterface:
    """SAT Solver Interface with depth-limited probing."""

    def __init__(
        self,
        formula: CNFFormula,
        seed: int = 0,
        depth_limit: int = 0,
        time_limit: int = 30,
    ):
        self.formula = formula
        self.seed = seed
        self.depth_limit = depth_limit
        self.time_limit = time_limit

        # Compute conflict budget from depth limit
        self.conflict_budget = (
            self.depth_limit * CONFLICTS_PER_DEPTH
            if depth_limit > 0
            else None
        )

        self.solution: Optional[Dict[int, bool]] = None
        self.status: Optional[SolverStatus] = None

    def run(self) -> Tuple[str, Optional[Dict[int, bool]]]:
        """Run the solver. Returns (status, solution)."""
        start_time = time.time()

        # Shuffle clauses for different seed
        rng = random.Random(self.seed)
        clauses = [list(c) for c in self.formula.clauses]
        rng.shuffle(clauses)

        # Select solver with appropriate settings
        solver = Glucose4()

        try:
            # Add clauses to solver
            for clause in clauses:
                solver.add_clause(clause)

            # Solve with conflict budget limit
            if self.conflict_budget:
                solver.conf_budget(self.conflict_budget)

            result = solver.solve()
            elapsed = time.time() - start_time

            if result:
                model = solver.get_model()
                self.solution = {abs(v): v > 0 for v in model if v != 0}
                stats = {
                    'time': elapsed,
                    'clauses': solver.nof_clauses(),
                    'vars': solver.nof_vars(),
                }
                self.status = SolverStatus(result='SAT', model=self.solution, stats=stats)
                return 'SAT', self.solution
            else:
                stats = {
                    'time': elapsed,
                    'clauses': solver.nof_clauses(),
                    'vars': solver.nof_vars(),
                }
                self.status = SolverStatus(result='UNSAT', model=None, stats=stats)
                return 'UNSAT', None

        except Exception as e:
            elapsed = time.time() - start_time
            self.status = SolverStatus(
                result='ERROR',
                error_message=str(e),
                stats={'time': elapsed},
            )
            return 'ERROR', None
        finally:
            solver.delete()


def generate_random_3sat(n: int, alpha: float, seed: Optional[int] = None) -> CNFFormula:
    """Generate a random 3-SAT instance with m = α·n clauses."""
    rng = random.Random(seed)
    m = max(int(alpha * n), 1)

    clauses = []
    for _ in range(m):
        vars_in_clause = rng.sample(range(1, n + 1), min(3, n))
        clause = [v if rng.random() < 0.5 else -v for v in vars_in_clause]
        clauses.append(clause)

    return CNFFormula(
        num_vars=n,
        clauses=clauses,
        comments=[
            f"random 3-SAT n={n} m={m} alpha={alpha:.3f} seed={seed}",
            f"ratio={m/n:.3f}",
        ],
    )


def measure_certified_backbone(formula: CNFFormula, model: Dict[int, bool]) -> int:
    """Count backbone-certified clauses (all literals satisfied)."""
    if model is None:
        return 0
    count = 0
    for clause in formula.clauses:
        certified = True
        for lit in clause:
            var = abs(lit)
            if var in model:
                if (lit > 0 and not model[var]) or (lit < 0 and model[var]):
                    certified = False
                    break
        if certified:
            count += 1
    return count


def verify_model(formula: CNFFormula, model: Dict[int, bool]) -> bool:
    """Verify that a model satisfies the CNF formula."""
    for clause in formula.clauses:
        clause_satisfied = False
        for literal in clause:
            var = abs(literal)
            value = model.get(var)
            if value is None:
                continue
            literal_value = value if literal > 0 else not value
            if literal_value:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True

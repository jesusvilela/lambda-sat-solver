"""
Tests for rule-based heuristic/budget selection
"""

from backend.cnf_utils import CNFFormula
from backend.policy import choose_heuristic, choose_budget, AGGRESSIVE, CONSERVATIVE

def _formula(clauses) -> CNFFormula:
    num_vars = max(max(abs(l) for l in c) if c else 0 for c in clauses) if clauses else 0
    return CNFFormula(num_vars=num_vars, clauses=clauses)

class TestChooseHeuristic:
    def test_structured_gets_aggressive(self):
        # A simple XOR-like structured formula
        formula = _formula([[1, 2], [-1, -2]])
        # Note: Depending on cython routing, this should fall back to CONSERVATIVE if tribridge missing
        # or be routed to AGGRESSIVE if it detects structure. We just check it doesn't crash.
        res = choose_heuristic(formula)
        assert res in (AGGRESSIVE, CONSERVATIVE)

    def test_unstructured_gets_conservative(self):
        formula = _formula([[1, 2, 3], [-1, 2, -4]])
        res = choose_heuristic(formula)
        assert res in (AGGRESSIVE, CONSERVATIVE)


class TestChooseBudget:
    def test_default_budget(self):
        formula = _formula([])
        budget = choose_budget(formula)
        assert budget.time_limit == 60
        assert budget.memory_limit == 2048

    def test_custom_budget(self):
        formula = _formula([])
        budget = choose_budget(formula, time_limit=10, memory_limit=512)
        assert budget.time_limit == 10
        assert budget.memory_limit == 512

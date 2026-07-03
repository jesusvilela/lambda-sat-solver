"""
Tests for the binary-clause (2-SAT) consistency check
"""

from backend.cnf_utils import CNFFormula
from backend.binary_clause_check import check_binary_clauses


class TestBinaryClauseCheck:
    def test_empty_formula_is_consistent(self):
        cnf = CNFFormula(num_vars=0, clauses=[])
        result = check_binary_clauses(cnf)
        assert result.consistent is True
        assert result.num_binary_clauses == 0

    def test_no_binary_clauses_is_consistent(self):
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2, 3], [-1, -2, -3]])
        result = check_binary_clauses(cnf)
        assert result.consistent is True
        assert result.num_binary_clauses == 0

    def test_simple_satisfiable_binary_clauses(self):
        # (x1 OR x2): satisfiable (e.g. x1=T, x2=T)
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2]])
        result = check_binary_clauses(cnf)
        assert result.consistent is True
        assert result.num_binary_clauses == 1

    def test_classic_unsat_2sat_gadget(self):
        # All 4 binary clauses over {x1, x2} with every sign combination:
        # (x1∨x2), (¬x1∨x2), (x1∨¬x2), (¬x1∨¬x2) - unsatisfiable by
        # exhaustive check (every assignment of x1,x2 falsifies one clause).
        cnf = CNFFormula(
            num_vars=2,
            clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]],
        )
        result = check_binary_clauses(cnf)
        assert result.consistent is False
        assert result.conflicting_variable in (1, 2)
        assert result.num_binary_clauses == 4

    def test_equivalence_chain_consistent(self):
        # x1 <-> x2 <-> x3 (via iff-as-two-implications), all can be True
        cnf = CNFFormula(
            num_vars=3,
            clauses=[
                [-1, 2], [1, -2],  # x1 <-> x2
                [-2, 3], [2, -3],  # x2 <-> x3
            ],
        )
        result = check_binary_clauses(cnf)
        assert result.consistent is True
        assert result.num_binary_clauses == 4

    def test_equivalence_chain_with_forced_contradiction(self):
        # x1 <-> x2, x2 <-> x3, and x1 <-> ¬x3: forces x1 = x3 and x1 != x3
        cnf = CNFFormula(
            num_vars=3,
            clauses=[
                [-1, 2], [1, -2],   # x1 <-> x2
                [-2, 3], [2, -3],   # x2 <-> x3
                [-1, -3], [1, 3],   # x1 <-> ¬x3
            ],
        )
        result = check_binary_clauses(cnf)
        assert result.consistent is False

    def test_mixed_clause_lengths_only_binary_considered(self):
        # Ternary clause is ignored; binary clauses alone are consistent
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2, 3], [1, 2]])
        result = check_binary_clauses(cnf)
        assert result.consistent is True
        assert result.num_binary_clauses == 1

    def test_self_conflicting_unit_pair(self):
        # (x1 OR x1) forces x1 true via itself; (¬x1 OR ¬x1) forces
        # x1 false - direct self-conflict via a single variable.
        cnf = CNFFormula(num_vars=1, clauses=[[1, 1], [-1, -1]])
        result = check_binary_clauses(cnf)
        assert result.consistent is False
        assert result.conflicting_variable == 1

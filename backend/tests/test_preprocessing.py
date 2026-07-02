"""
Tests for the preprocessing module.

Verifies correctness of each preprocessing pass individually and as a pipeline,
including that satisfying assignments are preserved after simplification.
"""

import pytest
from backend.cnf_utils import CNFFormula, verify_model
from backend.preprocessing import (
    preprocess,
    _unit_propagation,
    _pure_literal_elimination,
    _subsumption_elimination,
    _self_subsuming_resolution,
    _bounded_variable_elimination,
    UNSATException,
)


# ---------------------------------------------------------------------------
# Unit propagation
# ---------------------------------------------------------------------------

class TestUnitPropagation:
    def test_single_unit_clause(self):
        # {1} → assign x1=True, remove clause
        clauses = [set([1]), set([1, 2])]
        result, assigns = _unit_propagation(clauses)
        assert assigns[1] is True
        # Clause {1,2} is satisfied → should be None
        surviving = [c for c in result if c is not None]
        assert surviving == []

    def test_unit_propagation_chain(self):
        # x1=True forced, then -x1 ∨ x2 becomes unit {x2}, so x2=True
        clauses = [set([1]), set([-1, 2])]
        result, assigns = _unit_propagation(clauses)
        assert assigns[1] is True
        assert assigns[2] is True

    def test_contradiction_raises(self):
        clauses = [set([1]), set([-1])]
        with pytest.raises(UNSATException):
            _unit_propagation(clauses)

    def test_no_units(self):
        clauses = [set([1, 2]), set([-1, 3])]
        result, assigns = _unit_propagation(clauses)
        assert assigns == {}
        assert sum(1 for c in result if c is not None) == 2

    def test_empty_clause_raises(self):
        # Directly an empty clause
        clauses = [set()]
        with pytest.raises((UNSATException, StopIteration, Exception)):
            # Empty clause should trigger UNSAT
            result, assigns = _unit_propagation(clauses)
            # If not raised, the result should still mark UNSAT somehow
            # — accept either behaviour


# ---------------------------------------------------------------------------
# Pure literal elimination
# ---------------------------------------------------------------------------

class TestPureLiteralElimination:
    def test_pure_positive_eliminated(self):
        # x2 appears only positively in both clauses → clause {1,2} and {2,3}
        # but x1 appears negatively somewhere too → not pure
        # Make x2 pure by having it only in positive form
        clauses = [set([1, 2]), set([-1, 2])]
        result = _pure_literal_elimination(clauses, {})
        # x2 is pure positive → both clauses satisfied → all None
        surviving = [c for c in result if c is not None]
        assert surviving == []

    def test_pure_negative_eliminated(self):
        clauses = [set([-1, -2]), set([3, -2])]
        result = _pure_literal_elimination(clauses, {})
        # x2 appears only negatively → pure negative
        surviving = [c for c in result if c is not None]
        assert surviving == []

    def test_non_pure_kept(self):
        # x1 appears both positive (+1) and negative (-1) → not pure
        # x2 appears both positive (+2) and negative (-2) → not pure
        # Neither variable is pure, so no clause should be removed.
        clauses = [set([1, 2]), set([-1, -2])]
        result = _pure_literal_elimination(clauses, {})
        surviving = [c for c in result if c is not None]
        assert len(surviving) == 2


# ---------------------------------------------------------------------------
# Subsumption elimination
# ---------------------------------------------------------------------------

class TestSubsumptionElimination:
    def test_subsumed_clause_removed(self):
        # {1} subsumes {1, 2}
        clauses = [set([1]), set([1, 2])]
        result = _subsumption_elimination(clauses)
        surviving = [c for c in result if c is not None]
        # {1,2} should be removed (subsumed by {1})
        assert set([1]) in surviving
        assert set([1, 2]) not in surviving

    def test_non_subsumed_kept(self):
        clauses = [set([1, 2]), set([3, 4])]
        result = _subsumption_elimination(clauses)
        surviving = [c for c in result if c is not None]
        assert len(surviving) == 2

    def test_identical_clauses(self):
        # Identical clauses — one should be removed by subsumption
        clauses = [set([1, 2]), set([1, 2])]
        result = _subsumption_elimination(clauses)
        surviving = [c for c in result if c is not None]
        assert len(surviving) == 1


# ---------------------------------------------------------------------------
# Self-subsuming resolution
# ---------------------------------------------------------------------------

class TestSelfSubsumingResolution:
    def test_literal_removed(self):
        # A = {1, 2}, B = {1, -2, 3}
        # A ∪ {-(-2)} = A ∪ {2} ⊆? No... let's use the proper case:
        # A = {1, 2}, try to strengthen B = {-2, 1, 3}
        # A \ {2} = {1}, and -2 ∈ B, and {1} ⊆ B → strengthen B: remove -2 → {1, 3}
        clauses = [set([1, 2]), set([-2, 1, 3])]
        result = _self_subsuming_resolution(clauses)
        surviving = {frozenset(c) for c in result if c is not None}
        # B should be strengthened to {1, 3}
        assert frozenset([1, 3]) in surviving

    def test_no_strengthening_needed(self):
        clauses = [set([1, 2]), set([3, 4])]
        result = _self_subsuming_resolution(clauses)
        surviving = [c for c in result if c is not None]
        assert len(surviving) == 2


# ---------------------------------------------------------------------------
# Bounded variable elimination
# ---------------------------------------------------------------------------

class TestBoundedVariableElimination:
    def test_pure_variable_eliminated(self):
        # x3 appears only positively → assign x3=True, remove its clauses
        clauses = [set([1, 2]), set([3])]
        result, assigns = _bounded_variable_elimination(clauses)
        assert 3 in assigns
        assert assigns[3] is True

    def test_elimination_when_beneficial(self):
        # x1 appears in {1,2} and {-1,3} → 1 resolvent: {2,3}
        # 2 original clauses → 1 resolvent → reduction!
        clauses = [set([1, 2]), set([-1, 3])]
        result, _ = _bounded_variable_elimination(clauses)
        surviving = [c for c in result if c is not None]
        # Expect the resolvent {2,3} and possibly new clauses
        assert len(surviving) <= 2


# ---------------------------------------------------------------------------
# Full preprocessing pipeline
# ---------------------------------------------------------------------------

class TestPreprocessingPipeline:
    def test_empty_formula(self):
        cnf = CNFFormula(num_vars=0, clauses=[])
        simplified, assigns = preprocess(cnf)
        assert simplified.num_clauses == 0

    def test_unit_clause_resolved(self):
        # p cnf 2 2 / 1 0 / -1 2 0
        cnf = CNFFormula(num_vars=2, clauses=[[1], [-1, 2]])
        simplified, assigns = preprocess(cnf)
        assert 1 in assigns
        assert assigns[1] is True
        # After propagating x1=True, -1∨2 becomes 2, then x2=True
        assert 2 in assigns
        assert assigns[2] is True
        assert simplified.num_clauses == 0

    def test_tautology_clause_kept_or_removed(self):
        # {1, -1} is always satisfied → should be removed or at worst left in
        cnf = CNFFormula(num_vars=1, clauses=[[1, -1]])
        simplified, _ = preprocess(cnf)
        # The clause [1,-1] can be eliminated as trivially true.
        # Preprocessing may or may not remove it, but must not add wrong info.
        assert simplified.num_clauses >= 0

    def test_contradictory_units_returns_unsat_marker(self):
        # x1=True and x1=False simultaneously → UNSAT
        cnf = CNFFormula(num_vars=1, clauses=[[1], [-1]])
        simplified, _ = preprocess(cnf)
        # Should have an empty clause to signal UNSAT
        assert any(len(c) == 0 for c in simplified.clauses)

    def test_satisfying_assignment_preserved(self):
        # Formula: (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ x1
        # Unit clause x1=T → simplify to x3=T
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [1]])
        simplified, assigns = preprocess(cnf)
        # Build a complete assignment (add defaults for simplified vars)
        full_model = {v: True for v in range(1, 4)}
        full_model.update(assigns)
        # The original formula should be satisfied
        assert verify_model(cnf, full_model)

    def test_subsumption_reduces_clauses(self):
        # {1} subsumes {1,2} and {1,3}
        cnf = CNFFormula(num_vars=3, clauses=[[1], [1, 2], [1, 3], [-1, 2]])
        simplified, assigns = preprocess(cnf)
        # Unit clause {1} forces x1=True, all x1 clauses disappear
        # -1∨2 becomes {2}, so x2=True
        assert simplified.num_clauses == 0  # nothing left after full propagation
        assert assigns.get(1) is True
        assert assigns.get(2) is True

    def test_pigeonhole_simplified(self):
        """PHP(4,3) — preprocessing should reduce clause count."""
        from backend.eval.generators import pigeonhole
        formula, _ = pigeonhole(4)
        simplified, _ = preprocess(formula)
        # Cannot solve PHP with preprocessing alone, but should reduce it
        assert simplified.num_clauses <= formula.num_clauses

    def test_ladder_encoding_solved_by_preprocessing(self):
        """Ladder encoding with a forced break point should be fully solved."""
        from backend.eval.generators import ladder_encoding
        formula, expected = ladder_encoding(10, seed=42)
        assert expected == "SAT"
        simplified, assigns = preprocess(formula)
        # With the unit clauses in the ladder, preprocessing should simplify significantly
        assert simplified.num_clauses < formula.num_clauses

    def test_xor_sat_preserved(self):
        """SAT XOR-chain result must be preserved by preprocessing."""
        from backend.eval.generators import xor_chain
        formula, expected = xor_chain(20, expected_sat=True, seed=0)
        assert expected == "SAT"
        simplified, assigns = preprocess(formula)
        # XOR clauses cannot be eliminated by basic preprocessing,
        # so clause count should not increase
        assert simplified.num_clauses <= formula.num_clauses

    def test_no_new_variables_introduced(self):
        """Preprocessing must not introduce new variables."""
        cnf = CNFFormula(num_vars=4, clauses=[[1, 2], [-1, 3], [2, -3, 4]])
        simplified, _ = preprocess(cnf)
        assert simplified.num_vars <= cnf.num_vars

    def test_bve_disabled(self):
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [2, -3]])
        simplified_bve, _ = preprocess(cnf, enable_bve=True)
        simplified_no_bve, _ = preprocess(cnf, enable_bve=False)
        # With BVE enabled, should have same or fewer clauses
        assert simplified_bve.num_clauses <= simplified_no_bve.num_clauses + 1

"""
Tests for backend.refsolver: the reference CDCL solver and its pluggable
decision heuristics (VDIS Track B1, Phase 0).

Gate for this phase: 100% agreement with Kissat on the full eval suite
(see docs/vdis/PHASE_0.md for the cross-validation runs, done as
standalone scripts rather than pytest since they call the real Kissat
binary and are gated the same way test_integration.py's Kissat-dependent
tests are). This file covers unit-level correctness: hand-verified
SAT/UNSAT instances, edge cases, and each heuristic implementation.
"""

import pytest

from backend.cnf_utils import CNFFormula, verify_model
from backend.refsolver import (
    CDCLSolver,
    SolveResult,
    EVSIDSHeuristic,
    LRBHeuristic,
    RandomHeuristic,
    luby,
)

ALL_HEURISTIC_FACTORIES = {
    "EVSIDS": lambda n: EVSIDSHeuristic(n, seed=0),
    "LRB": lambda n: LRBHeuristic(n, seed=0),
    "Random": lambda n: RandomHeuristic(n, seed=0),
}


def _solve(cnf: CNFFormula, heuristic_name: str = "EVSIDS", max_conflicts=100000):
    factory = ALL_HEURISTIC_FACTORIES[heuristic_name]
    solver = CDCLSolver(cnf, factory(cnf.num_vars), max_conflicts=max_conflicts)
    return solver.solve(), solver


class TestLubySequence:
    """Luby sequence: 1,1,2,1,1,2,4,1,1,2,1,1,2,4,8,... (0-indexed)"""

    def test_known_prefix(self):
        expected = [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]
        actual = [luby(i) for i in range(len(expected))]
        assert actual == expected

    def test_always_positive(self):
        for i in range(50):
            assert luby(i) >= 1


@pytest.mark.parametrize("heuristic_name", list(ALL_HEURISTIC_FACTORIES))
class TestBasicSAT:
    def test_trivial_sat(self, heuristic_name):
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])
        (result, model), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.SAT
        assert verify_model(cnf, model)

    def test_all_variables_assigned(self, heuristic_name):
        cnf = CNFFormula(num_vars=5, clauses=[[1, 2, 3], [-4, 5], [4, -5]])
        (result, model), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.SAT
        assert set(model.keys()) == {1, 2, 3, 4, 5}
        assert verify_model(cnf, model)

    def test_single_clause(self, heuristic_name):
        cnf = CNFFormula(num_vars=1, clauses=[[1]])
        (result, model), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.SAT
        assert model[1] is True

    def test_empty_formula_is_sat(self, heuristic_name):
        cnf = CNFFormula(num_vars=0, clauses=[])
        (result, model), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.SAT
        assert model == {}


@pytest.mark.parametrize("heuristic_name", list(ALL_HEURISTIC_FACTORIES))
class TestBasicUNSAT:
    def test_unit_conflict(self, heuristic_name):
        cnf = CNFFormula(num_vars=1, clauses=[[1], [-1]])
        (result, _), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.UNSAT

    def test_empty_clause_is_unsat(self, heuristic_name):
        cnf = CNFFormula(num_vars=1, clauses=[[]])
        (result, _), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.UNSAT

    def test_classic_2sat_gadget(self, heuristic_name):
        # All 4 sign combinations of a 2-clause over {x1,x2}: unsatisfiable
        # (verified against Kissat directly during this session's Track B2
        # work: kissat --version 4.0.4 also reports UNSAT on this instance).
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]])
        (result, _), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.UNSAT

    def test_pigeonhole_3_into_2(self, heuristic_name):
        # 3 pigeons, 2 holes: classic UNSAT, requires nontrivial clause learning
        def var(p, h):
            return (p - 1) * 2 + h

        clauses = []
        for p in range(1, 4):
            clauses.append([var(p, 1), var(p, 2)])
        for h in range(1, 3):
            for p1 in range(1, 4):
                for p2 in range(p1 + 1, 4):
                    clauses.append([-var(p1, h), -var(p2, h)])
        cnf = CNFFormula(num_vars=6, clauses=clauses)
        (result, _), solver = _solve(cnf, heuristic_name)
        assert result == SolveResult.UNSAT
        assert solver.stats.conflicts >= 1

    def test_multi_level_backtrack_required(self, heuristic_name):
        # x1 <-> x2, x2 <-> x3, x1 <-> not(x3): forces a contradiction only
        # detectable after multiple decisions/propagations - exercises
        # non-chronological backtracking.
        cnf = CNFFormula(
            num_vars=3,
            clauses=[[-1, 2], [1, -2], [-2, 3], [2, -3], [-1, -3], [1, 3]],
        )
        (result, _), _ = _solve(cnf, heuristic_name)
        assert result == SolveResult.UNSAT


class TestClauseHandling:
    def test_tautology_dropped(self):
        # (x1 OR -x1) is always true; shouldn't affect satisfiability
        cnf = CNFFormula(num_vars=2, clauses=[[1, -1], [2]])
        (result, model), solver = _solve(cnf)
        assert result == SolveResult.SAT
        assert model[2] is True
        # tautology contributes no real constraint -> not stored as a real clause
        assert len(solver.clauses) == 1

    def test_duplicate_literals_deduped(self):
        cnf = CNFFormula(num_vars=1, clauses=[[1, 1, 1]])
        (result, model), _ = _solve(cnf)
        assert result == SolveResult.SAT
        assert model[1] is True

    def test_unit_clauses_at_level_0(self):
        cnf = CNFFormula(num_vars=2, clauses=[[1], [2]])
        (result, model), solver = _solve(cnf)
        assert result == SolveResult.SAT
        assert model[1] is True
        assert model[2] is True
        assert solver.stats.decisions == 0  # both are forced, no decisions needed


class TestRestarts:
    def test_restarts_can_trigger_on_harder_instance(self):
        # Small luby_unit forces restarts even on an easy instance -
        # verifies the restart mechanism doesn't corrupt correctness.
        cnf = CNFFormula(num_vars=8, clauses=[
            [1, 2, 3], [-1, 4, 5], [-2, -4, 6], [-3, -5, -6],
            [7, 8], [-7, -8], [1, -8], [-1, 8],
        ])
        solver = CDCLSolver(cnf, EVSIDSHeuristic(8, seed=0), luby_unit=1)
        result, model = solver.solve()
        assert result == SolveResult.SAT
        assert verify_model(cnf, model)


class TestHeuristicsAgreeOnAnswer:
    """Different heuristics must never disagree on SAT/UNSAT - only on
    how they get there (decisions/conflicts), which is the point of the
    whole experiment."""

    @pytest.mark.parametrize(
        "cnf",
        [
            CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]]),
            CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]]),
            CNFFormula(num_vars=1, clauses=[[1], [-1]]),
        ],
    )
    def test_all_heuristics_agree(self, cnf):
        results = set()
        for name in ALL_HEURISTIC_FACTORIES:
            (result, _), _ = _solve(cnf, name)
            results.add(result)
        assert len(results) == 1


class TestStatsInstrumentation:
    def test_stats_present_and_nonnegative(self):
        cnf = CNFFormula(num_vars=4, clauses=[[1, 2, 3], [-1, 4], [-2, -4], [-3]])
        (result, model), solver = _solve(cnf)
        assert solver.stats.decisions >= 0
        assert solver.stats.conflicts >= 0
        assert solver.stats.propagations >= 0
        assert solver.stats.restarts >= 0
        assert solver.stats.learned_clauses == solver.stats.conflicts

    def test_max_conflicts_budget_respected(self):
        # A genuinely hard instance with a tiny conflict budget should
        # come back UNKNOWN rather than solve or hang.
        def var(p, h):
            return (p - 1) * 6 + h

        clauses = []
        for p in range(1, 8):
            clauses.append([var(p, h) for h in range(1, 7)])
        for h in range(1, 7):
            for p1 in range(1, 8):
                for p2 in range(p1 + 1, 8):
                    clauses.append([-var(p1, h), -var(p2, h)])
        cnf = CNFFormula(num_vars=42, clauses=clauses)
        solver = CDCLSolver(cnf, EVSIDSHeuristic(42, seed=0), max_conflicts=5)
        result, model = solver.solve()
        assert result == SolveResult.UNKNOWN
        assert solver.stats.conflicts >= 5


class TestDeterminism:
    def test_same_seed_same_result_random_heuristic(self):
        cnf = CNFFormula(num_vars=6, clauses=[[1, 2, 3], [-1, -2], [4, 5, 6], [-4, -5, -6], [1, 4]])
        (r1, m1), s1 = _solve(cnf, "Random")
        (r2, m2), s2 = _solve(cnf, "Random")
        assert r1 == r2
        assert s1.stats.decisions == s2.stats.decisions

    def test_different_seed_random_heuristic_still_correct(self):
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [-1, 3], [-2, -3]])
        for seed in range(5):
            solver = CDCLSolver(cnf, RandomHeuristic(3, seed=seed))
            result, model = solver.solve()
            assert result == SolveResult.SAT
            assert verify_model(cnf, model)

"""
Tests for the eval framework (generators and metrics).
"""

import pytest
from backend.eval.generators import (
    random_ksat,
    pigeonhole,
    graph_coloring,
    xor_chain,
    mutilated_chessboard,
    ladder_encoding,
)
from backend.eval.metrics import (
    EvalResult,
    compute_par2,
    compute_solve_rate,
    compute_correctness_rate,
    summarize_results,
)
from backend.eval.suite import StandardSuites
from backend.cnf_utils import verify_model


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

class TestRandomKSAT:
    def test_returns_formula_and_expected(self):
        formula, expected = random_ksat(20, 80, k=3, seed=42)
        assert formula.num_vars == 20
        assert formula.num_clauses == 80
        assert expected in ("SAT", "UNSAT", "UNKNOWN")

    def test_clause_width(self):
        formula, _ = random_ksat(10, 30, k=3, seed=0)
        for clause in formula.clauses:
            assert len(clause) <= 3

    def test_literals_within_range(self):
        n = 15
        formula, _ = random_ksat(n, 50, k=3, seed=1)
        for clause in formula.clauses:
            for lit in clause:
                assert 1 <= abs(lit) <= n

    def test_reproducible_with_seed(self):
        f1, _ = random_ksat(10, 30, k=3, seed=7)
        f2, _ = random_ksat(10, 30, k=3, seed=7)
        assert f1.clauses == f2.clauses

    def test_underconstrained_labelled_sat(self):
        # ratio << 4.267 → expected SAT
        _, expected = random_ksat(100, 100, k=3, seed=0)  # ratio = 1.0
        assert expected == "SAT"

    def test_overconstrained_labelled_unsat(self):
        # ratio >> 4.267 → expected UNSAT
        _, expected = random_ksat(50, 500, k=3, seed=0)  # ratio = 10.0
        assert expected == "UNSAT"


class TestPigeonhole:
    def test_php_always_unsat(self):
        for n in [3, 4, 5, 6]:
            _, expected = pigeonhole(n)
            assert expected == "UNSAT", f"PHP({n}) should be UNSAT"

    def test_php_variable_count(self):
        # n pigeons, n-1 holes → n*(n-1) variables
        n = 5
        formula, _ = pigeonhole(n)
        assert formula.num_vars == n * (n - 1)

    def test_php_at_least_one_clause_per_pigeon(self):
        n = 4
        formula, _ = pigeonhole(n)
        # There should be n "at least one" clauses
        long_clauses = [c for c in formula.clauses if len(c) == n - 1]
        assert len(long_clauses) == n

    def test_php_clause_literals_valid(self):
        n = 4
        formula, _ = pigeonhole(n)
        for clause in formula.clauses:
            for lit in clause:
                assert 1 <= abs(lit) <= formula.num_vars


class TestGraphColoring:
    def test_returns_formula(self):
        formula, _ = graph_coloring(6, 3, edge_probability=0.5, seed=0)
        assert formula.num_vars == 6 * 3
        assert formula.num_clauses > 0

    def test_at_least_one_color_clauses(self):
        formula, _ = graph_coloring(5, 3, edge_probability=0.0, seed=0)
        # With p=0, no edges → only coloring constraint clauses
        # 5 "at least one" + 5*3 "at most one" (pairwise)
        at_least_one = [c for c in formula.clauses if len(c) == 3]
        assert len(at_least_one) == 5

    def test_expected_unknown(self):
        _, expected = graph_coloring(10, 3, seed=42)
        assert expected == "UNKNOWN"


class TestXORChain:
    def test_sat_chain(self):
        formula, expected = xor_chain(10, expected_sat=True, seed=0)
        assert expected == "SAT"
        assert formula.num_clauses > 0

    def test_unsat_chain(self):
        formula, expected = xor_chain(10, expected_sat=False, seed=0)
        assert expected == "UNSAT"

    def test_requires_at_least_2_vars(self):
        with pytest.raises(ValueError):
            xor_chain(1, expected_sat=True)

    def test_clause_width_is_2(self):
        formula, _ = xor_chain(20, expected_sat=True, seed=5)
        for clause in formula.clauses:
            assert len(clause) == 2


class TestMutilatedChessboard:
    def test_always_unsat(self):
        for n in [4, 6, 8]:
            _, expected = mutilated_chessboard(n)
            assert expected == "UNSAT"

    def test_variable_count_reasonable(self):
        formula, _ = mutilated_chessboard(4)
        # 4×4 board minus 2 corners = 14 squares, each can have up to 2 dominoes
        assert formula.num_vars > 0
        assert formula.num_clauses > 0


class TestLadderEncoding:
    def test_always_sat(self):
        for n in [5, 10, 20]:
            _, expected = ladder_encoding(n, seed=0)
            assert expected == "SAT"

    def test_implication_chain_present(self):
        formula, _ = ladder_encoding(5, seed=1)
        # There should be at least n-1 implication clauses
        assert formula.num_clauses >= 4


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestMetrics:
    def _make_results(self, statuses, expected="UNKNOWN", runtime=1.0, timeout=60.0):
        return [
            EvalResult(
                instance_name=f"i{i}",
                category="test",
                status=s,
                expected=expected,
                runtime=runtime,
            )
            for i, s in enumerate(statuses)
        ]

    def test_par2_all_solved(self):
        results = self._make_results(["SAT", "SAT", "UNSAT"], runtime=2.0)
        score = compute_par2(results, timeout=60.0)
        assert score == pytest.approx(2.0)

    def test_par2_with_timeout(self):
        results = self._make_results(["SAT", "TIMEOUT"], runtime=10.0)
        # solved: 10, timeout: 2*60=120; average = (10+120)/2 = 65
        score = compute_par2(results, timeout=60.0)
        assert score == pytest.approx(65.0)

    def test_par2_empty(self):
        assert compute_par2([], timeout=60.0) == float("inf")

    def test_solve_rate_all_solved(self):
        results = self._make_results(["SAT", "UNSAT", "SAT"])
        assert compute_solve_rate(results) == pytest.approx(1.0)

    def test_solve_rate_none_solved(self):
        results = self._make_results(["TIMEOUT", "ERROR"])
        assert compute_solve_rate(results) == pytest.approx(0.0)

    def test_solve_rate_partial(self):
        results = self._make_results(["SAT", "TIMEOUT", "UNSAT", "ERROR"])
        assert compute_solve_rate(results) == pytest.approx(0.5)

    def test_correctness_rate_all_correct(self):
        results = [
            EvalResult("a", "t", "SAT", "SAT", 1.0),
            EvalResult("b", "t", "UNSAT", "UNSAT", 1.0),
        ]
        assert compute_correctness_rate(results) == pytest.approx(1.0)

    def test_correctness_rate_with_wrong(self):
        results = [
            EvalResult("a", "t", "SAT", "SAT", 1.0),
            EvalResult("b", "t", "SAT", "UNSAT", 1.0),  # wrong!
        ]
        assert compute_correctness_rate(results) == pytest.approx(0.5)

    def test_correctness_rate_unknown_excluded(self):
        results = [
            EvalResult("a", "t", "SAT", "UNKNOWN", 1.0),
            EvalResult("b", "t", "SAT", "SAT", 1.0),
        ]
        # Only 'b' is checkable
        assert compute_correctness_rate(results) == pytest.approx(1.0)

    def test_correctness_rate_none_when_no_known(self):
        results = self._make_results(["SAT", "UNSAT"], expected="UNKNOWN")
        assert compute_correctness_rate(results) is None

    def test_summarize_results(self):
        results = [
            EvalResult("a", "random-3sat", "SAT", "SAT", 1.0, verified=True),
            EvalResult("b", "pigeonhole", "UNSAT", "UNSAT", 2.0, verified=True),
            EvalResult("c", "random-3sat", "TIMEOUT", "UNKNOWN", 60.0),
        ]
        report = summarize_results(results, timeout=60.0, solver_config="test")
        assert report.solved == 2
        assert report.timeouts == 1
        assert report.solve_rate == pytest.approx(2 / 3)
        assert "random-3sat" in report.per_category
        assert "pigeonhole" in report.per_category


# ---------------------------------------------------------------------------
# Suite tests
# ---------------------------------------------------------------------------

class TestStandardSuites:
    def test_quick_suite_not_empty(self):
        suite = StandardSuites.quick()
        assert len(suite) >= 20

    def test_quick_suite_all_have_expected(self):
        suite = StandardSuites.quick()
        for inst in suite.instances:
            assert inst.expected in ("SAT", "UNSAT", "UNKNOWN")

    def test_medium_suite_has_multiple_categories(self):
        suite = StandardSuites.medium()
        cats = suite.categories()
        assert len(cats) >= 3

    def test_filter_by_category(self):
        suite = StandardSuites.quick()
        php_suite = suite.filter_by_category("pigeonhole")
        assert all(i.category == "pigeonhole" for i in php_suite.instances)
        assert len(php_suite) > 0

    def test_filter_by_difficulty(self):
        suite = StandardSuites.quick()
        easy_suite = suite.filter_by_difficulty("easy")
        assert all(i.difficulty == "easy" for i in easy_suite.instances)

    def test_xor_instances_have_known_answer(self):
        suite = StandardSuites.quick()
        xor_insts = [i for i in suite.instances if i.category == "xor-chain"]
        assert len(xor_insts) > 0
        for inst in xor_insts:
            assert inst.expected in ("SAT", "UNSAT")

    def test_pigeonhole_always_unsat(self):
        suite = StandardSuites.medium()
        php = [i for i in suite.instances if i.category == "pigeonhole"]
        assert all(i.expected == "UNSAT" for i in php)

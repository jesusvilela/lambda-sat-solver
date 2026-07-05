"""Tests for intrinsic structural invariants (ladder Rung 1)."""

from backend.cnf_utils import CNFFormula
from backend.complexity.invariants import (
    solution_stats, spectral_gap, mean_var_degree, var_degree_entropy,
)


class TestSolutionStats:
    def test_disjunction(self):
        s = solution_stats(CNFFormula(num_vars=2, clauses=[[1, 2]]))
        assert s.num_solutions == 3 and s.backbone_fraction == 0.0
        assert s.num_clusters == 1 and s.satisfiable

    def test_conjunction_full_backbone(self):
        s = solution_stats(CNFFormula(num_vars=2, clauses=[[1], [2]]))
        assert s.num_solutions == 1 and s.backbone_fraction == 1.0

    def test_xor_two_clusters(self):
        # solutions 01 and 10 are Hamming distance 2 -> 2 clusters
        s = solution_stats(CNFFormula(num_vars=2, clauses=[[1, 2], [-1, -2]]))
        assert s.num_solutions == 2 and s.num_clusters == 2
        assert s.backbone_fraction == 0.0

    def test_unsat(self):
        s = solution_stats(CNFFormula(num_vars=1, clauses=[[1], [-1]]))
        assert not s.satisfiable and s.num_solutions == 0

    def test_guard_large_n(self):
        import pytest
        with pytest.raises(ValueError):
            solution_stats(CNFFormula(num_vars=30, clauses=[[1]]), max_vars=24)


class TestGraphInvariants:
    def test_mean_degree(self):
        # 2 clauses of width 3 over 3 vars: each var appears twice
        f = CNFFormula(num_vars=3, clauses=[[1, 2, 3], [-1, -2, -3]])
        assert mean_var_degree(f) == 2.0

    def test_spectral_gap_range(self):
        f = CNFFormula(num_vars=4, clauses=[[1, 2, 3], [2, 3, 4], [1, 4, -2]])
        g = spectral_gap(f)
        assert 0.0 <= g <= 2.0

    def test_spectral_gap_disconnected_is_zero(self):
        # variable 3 isolated -> disconnected -> gap 0
        f = CNFFormula(num_vars=3, clauses=[[1, 2]])
        assert spectral_gap(f) == 0.0

    def test_entropy_uniform_high(self):
        f = CNFFormula(num_vars=4, clauses=[[1, 2], [3, 4], [1, 3], [2, 4]])
        assert 0.0 <= var_degree_entropy(f) <= 1.0


class TestRefutationWidth:
    def test_unit_contradiction_width_1(self):
        from backend.complexity.invariants import min_refutation_width
        f = CNFFormula(num_vars=1, clauses=[[1], [-1]])
        assert min_refutation_width(f) == 1

    def test_implication_chain_width_2(self):
        from backend.complexity.invariants import min_refutation_width
        f = CNFFormula(num_vars=3, clauses=[[1], [-1, 2], [-2, 3], [-3]])
        assert min_refutation_width(f) == 2

    def test_php_3_2_width_2(self):
        # PHP(3 pigeons -> 2 holes): all clauses width 2, refutable at width 2
        from backend.eval.generators import pigeonhole
        from backend.complexity.invariants import min_refutation_width
        cnf, _ = pigeonhole(3)
        assert min_refutation_width(cnf, wmax=4) == 2

    def test_empty_clause_width_0(self):
        from backend.complexity.invariants import min_refutation_width
        f = CNFFormula(num_vars=2, clauses=[[]])
        assert min_refutation_width(f) == 0


class TestSignedLaplacian:
    def test_balanced_is_zero(self):
        from backend.complexity.invariants import signed_laplacian_frustration
        f = CNFFormula(num_vars=3, clauses=[[1, 2], [2, 3]])  # path: always balanced
        assert signed_laplacian_frustration(f) < 1e-9

    def test_frustrated_triangle_positive(self):
        from backend.complexity.invariants import signed_laplacian_frustration
        f = CNFFormula(num_vars=3, clauses=[[1, 2], [2, 3], [1, -3]])
        assert signed_laplacian_frustration(f) > 0.0


class TestEnergyLandscapeSaddle:
    def test_connected_basin_zero_barrier(self):
        from backend.complexity.invariants import energy_landscape_saddle
        s = energy_landscape_saddle(CNFFormula(num_vars=2, clauses=[[1, 2]]))
        assert s.satisfiable and s.num_solution_basins == 1 and s.connect_barrier == 0

    def test_xor_two_basins_barrier_one(self):
        from backend.complexity.invariants import energy_landscape_saddle
        s = energy_landscape_saddle(CNFFormula(num_vars=2, clauses=[[1, 2], [-1, -2]]))
        assert s.num_solution_basins == 2 and s.connect_barrier == 1

    def test_unsat_reports_ground(self):
        from backend.complexity.invariants import energy_landscape_saddle
        s = energy_landscape_saddle(CNFFormula(num_vars=1, clauses=[[1], [-1]]))
        assert not s.satisfiable and s.ground_energy == 1

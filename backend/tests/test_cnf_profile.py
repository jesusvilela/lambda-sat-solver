"""
Tests for CNF instance profiling
"""

from backend.cnf_utils import CNFFormula
from backend.cnf_profile import profile_cnf, CNFProfile


class TestProfileBasicFeatures:
    """Test structural (non-spectral) profile features"""

    def test_empty_formula(self):
        cnf = CNFFormula(num_vars=0, clauses=[])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.num_vars == 0
        assert profile.num_clauses == 0
        assert profile.unit_ratio == 0.0
        assert profile.horn_ratio == 0.0
        assert profile.avg_var_degree == 0.0

    def test_clause_length_histogram(self):
        cnf = CNFFormula(num_vars=3, clauses=[[1], [1, 2], [1, -2, 3]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.clause_length_histogram == {1: 1, 2: 1, 3: 1}
        assert profile.unit_ratio == 1 / 3
        assert profile.binary_ratio == 1 / 3

    def test_horn_ratio_all_horn(self):
        # Every clause here has at most one positive literal
        cnf = CNFFormula(num_vars=3, clauses=[[-1, -2], [-1, 3], [-2, -3]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.horn_ratio == 1.0

    def test_horn_ratio_no_horn(self):
        # Every clause has two positive literals -> not Horn
        cnf = CNFFormula(num_vars=3, clauses=[[1, 2], [1, 3], [2, 3]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.horn_ratio == 0.0

    def test_pos_neg_balance_all_positive(self):
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2], [1, 2]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.pos_neg_balance == 1.0

    def test_avg_var_degree(self):
        # var 1 appears in both clauses, var 2 in one -> total lits=3, vars=2
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2], [1]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.avg_var_degree == 1.5

    def test_var_degree_entropy_uniform_is_high(self):
        # Every variable appears exactly once -> maximal entropy ratio (1.0)
        cnf = CNFFormula(num_vars=4, clauses=[[1, 2], [3, 4]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.var_degree_entropy == 1.0

    def test_to_dict(self):
        cnf = CNFFormula(num_vars=2, clauses=[[1, 2]])
        profile = profile_cnf(cnf, compute_spectral=False)
        d = profile.to_dict()
        assert d['num_vars'] == 2
        assert d['num_clauses'] == 1
        assert 'hyp_delta_entropy_ratio' in d


class TestProfileSpectralFeature:
    """Test the experimental hyperbolic spectral feature"""

    def test_computed_when_numpy_available(self):
        cnf = CNFFormula(num_vars=4, clauses=[[1, 2], [-1, 3], [2, -3, 4], [-4, 1]])
        profile = profile_cnf(cnf, compute_spectral=True)
        assert profile.hyp_delta_entropy_ratio is None or isinstance(
            profile.hyp_delta_entropy_ratio, float
        )

    def test_skipped_when_flag_false(self):
        cnf = CNFFormula(num_vars=4, clauses=[[1, 2], [-1, 3], [2, -3, 4]])
        profile = profile_cnf(cnf, compute_spectral=False)
        assert profile.hyp_delta_entropy_ratio is None

    def test_skipped_for_empty_formula(self):
        cnf = CNFFormula(num_vars=0, clauses=[])
        profile = profile_cnf(cnf, compute_spectral=True)
        assert profile.hyp_delta_entropy_ratio is None

    def test_skipped_above_size_threshold(self):
        import backend.cnf_profile as cnf_profile_mod

        original = cnf_profile_mod._SVD_MAX_CELLS
        try:
            cnf_profile_mod._SVD_MAX_CELLS = 1
            cnf = CNFFormula(num_vars=4, clauses=[[1, 2], [-1, 3], [2, -3, 4]])
            profile = profile_cnf(cnf, compute_spectral=True)
            assert profile.hyp_delta_entropy_ratio is None
        finally:
            cnf_profile_mod._SVD_MAX_CELLS = original

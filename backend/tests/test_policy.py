"""
Tests for rule-based heuristic/budget selection
"""

from backend.cnf_profile import CNFProfile
from backend.policy import choose_heuristic, choose_budget, AGGRESSIVE


def _profile(**overrides) -> CNFProfile:
    defaults = dict(
        num_vars=500,
        num_clauses=1000,
        clause_length_histogram={3: 1000},
        unit_ratio=0.0,
        binary_ratio=0.0,
        horn_ratio=0.3,
        pos_neg_balance=0.5,
        avg_var_degree=6.0,
        var_degree_entropy=0.9,
        hyp_delta_entropy_ratio=None,
    )
    defaults.update(overrides)
    return CNFProfile(**defaults)


class TestChooseHeuristic:
    """AGGRESSIVE won or tied on 10/13 of this repo's benchmark instances
    (including all 4 high-Horn-ratio pigeonhole instances, where an earlier
    version of this policy incorrectly routed to CONSERVATIVE). No feature
    has yet shown predictive value for when CONSERVATIVE should win, so the
    policy currently returns AGGRESSIVE regardless of profile."""

    def test_horn_dominated_still_gets_aggressive(self):
        profile = _profile(horn_ratio=0.95)
        assert choose_heuristic(profile) == AGGRESSIVE

    def test_small_formula_still_gets_aggressive(self):
        profile = _profile(num_vars=50, horn_ratio=0.3)
        assert choose_heuristic(profile) == AGGRESSIVE

    def test_large_non_horn_gets_aggressive(self):
        profile = _profile(num_vars=1000, horn_ratio=0.3)
        assert choose_heuristic(profile) == AGGRESSIVE


class TestChooseBudget:
    def test_default_budget(self):
        profile = _profile()
        budget = choose_budget(profile)
        assert budget.time_limit == 60
        assert budget.memory_limit == 2048

    def test_custom_budget(self):
        profile = _profile()
        budget = choose_budget(profile, time_limit=10, memory_limit=512)
        assert budget.time_limit == 10
        assert budget.memory_limit == 512

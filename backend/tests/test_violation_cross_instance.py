"""Test oracle separation, held-out-family folds and deterministic controls."""
import math
import pytest
from backend.cnf_utils import CNFFormula
from backend.violation_cross_instance import (
    FAMILIES, PREDICTORS, _dpll_search_nodes, _xor_clauses,
    cross_instance_benchmark, generate_formula, record_formula,
    sampled_signatures, structural_features)
from backend.violation_geometry import violation_masks


def test_sample_is_bounded_and_does_not_enumerate_all_assignments():
    f = CNFFormula(4, [[1], [-2], [1, -3]])
    sample = sampled_signatures(f, budget=7, seed=42)
    full = violation_masks(f)
    assert len(sample) == 7 and all(v in full for v in sample)
    assert sample == sampled_signatures(f, budget=7, seed=42)
    with pytest.raises(ValueError):
        sampled_signatures(f, budget=16, seed=42)
    with pytest.raises(ValueError):
        sampled_signatures(f, budget=0, seed=42)


def test_dpll_baselines_count_nodes_not_sat_verdicts():
    assert _dpll_search_nodes(CNFFormula(3, [])) == 1
    assert _dpll_search_nodes(CNFFormula(1, [[1], [-1]])) == 1
    assert _dpll_search_nodes(CNFFormula(1, [[1]])) == 1
    assert _dpll_search_nodes(CNFFormula(2, [[1, 2]])) > 1


def test_all_generators_fit_budget_and_valid_semantics():
    for family in FAMILIES:
        for seed in range(5):
            f = generate_formula(family, seed)
            assert 1 <= f.num_vars <= 12
            assert 0 < len(f.clauses) <= 128
            assert all(1 <= abs(x) <= f.num_vars for c in f.clauses for x in c)
            assert generate_formula(family, seed) == f
            assert len(structural_features(f)) == 9
            r = record_formula(f, family, seed, budget=24, candidate_budget=96)
            assert len(r.features) == 29
            assert r.dpll_nodes >= 1
            assert math.isfinite(r.target_log2_nodes)
            assert r.measured_feature_ns >= r.structural_ns


def test_tseitin_charge_parity_sets_sat_status():
    for seed in range(6):
        f = generate_formula("tseitin", seed)
        masks = violation_masks(f, max_vars=12)
        assert (any(v == 0 for v in masks)) == (seed % 2 == 0)


def test_xor_convention():
    f = CNFFormula(3, _xor_clauses((1, 2, 3), 1))
    masks = violation_masks(f)
    assert [i for i, v in enumerate(masks) if v == 0] == [1, 2, 4, 7]


def test_cross_instance_folds_and_null_comparator():
    r = cross_instance_benchmark(seed_count=2, sample_budget=24,
                                 rows=4, candidate_budget=96)
    assert r.instances == 2 * len(FAMILIES)
    assert {f.heldout_family for f in r.folds} == set(FAMILIES)
    assert set(r.overall_mae_log2) == set(PREDICTORS)
    assert all(math.isfinite(v) and v >= 0 for v in r.overall_mae_log2.values())
    assert all(f.instances == 2 for f in r.folds)
    assert r.seed_count == 2
    assert r.median_dpll_ms >= 0 and r.median_centered_ms >= 0


def test_no_formula_labels_are_used_in_feature_extraction(monkeypatch):
    # Predictor work happens BEFORE and separately from the reference DPLL call.
    from backend import violation_cross_instance as mod
    f = generate_formula("random-3SAT", 0)
    def no_oracle(_):
        raise RuntimeError("target requested")
    monkeypatch.setattr(mod, "_dpll_search_nodes", no_oracle)
    with pytest.raises(RuntimeError, match="target requested"):
        mod.record_formula(f, "random-3SAT", 0, budget=24, candidate_budget=96)


def test_canary_low_degree_variance_is_not_a_symmetry_proof():
    # Every variable has degree 3 and each clause has length 3.
    # The canary's flavor threshold would call this Z2_x_Z2, but it has
    # no complete XOR sign-pattern group at all.
    f = CNFFormula(4, [[1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4]])
    features = structural_features(f)
    assert features[6] == 0.0  # degree coefficient of variation
    assert features[8] == 0.0  # fraction of complete XOR clause patterns

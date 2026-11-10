"""Orbit target is separately sampled; structural features precede oracle calls."""
from math import isfinite
from random import Random

import pytest

from backend.violation_cross_instance import generate_formula, _dpll_search_nodes, _shuffle_vars
from backend.violation_connection import signed_connection, connection_features
from backend.violation_orbit import (
    orbit_effort, orbit_holdout_benchmark, measure_orbit_record, PREDICTORS)


def test_same_cnf_changed_dpll_cost_by_signed_renaming():
    f=generate_formula('random-3SAT',0)
    original=_dpll_search_nodes(f)
    image=[_dpll_search_nodes(_shuffle_vars(f,Random(1000+j))) for j in range(40)]
    assert original == 7
    assert min(image) == 7
    assert max(image) == 21
    assert len(set(image)) > 1
    assert all(signed_connection(f)==signed_connection(_shuffle_vars(f,Random(j)))
               for j in range(10))


def test_relabeling_orbit_is_finite_and_repeatable():
    f=generate_formula('random-3SAT',0)
    a=orbit_effort(f,seed=9,repeats=6)
    assert a==orbit_effort(f,seed=9,repeats=6)
    assert a[1]>=0 and 1<=a[2]<=6
    assert a[3]>=1
    with pytest.raises(ValueError): orbit_effort(f,seed=9,repeats=1)


def test_feature_production_precedes_reference_oracle(monkeypatch):
    from backend import violation_orbit as mod
    f=generate_formula('random-3SAT',0)
    expected = (mod.structural_features(f) +
                connection_features(signed_connection(f)))
    def stop_oracle(_):
        assert expected[:9]==mod.structural_features(f)
        raise RuntimeError('target called')
    monkeypatch.setattr(mod,'_dpll_search_nodes',stop_oracle)
    with pytest.raises(RuntimeError,match='target called'):
        mod.measure_orbit_record(f,'random-3SAT',0,repeats=2,null_swaps=0)


def test_small_cross_family_holdout_runs_with_matched_controls():
    report=orbit_holdout_benchmark(seed_count=2,repeats=3,null_swaps=4)
    assert report.formulas==12
    assert len(report.folds)==6
    assert set(report.overall_raw_mae)==set(PREDICTORS)
    assert set(report.overall_orbit_mae)==set(PREDICTORS)
    assert all(isfinite(x) and x>=0 for x in report.overall_orbit_mae.values())
    assert 0 <= report.fraction_nulls_with_switches <= 1
    assert report.median_feature_ms>=0
    assert report.median_reference_ms>=0


def test_orbit_features_are_baseline_compatible():
    f=generate_formula('random-3XOR',2)
    r=measure_orbit_record(f,'random-3XOR',2,repeats=3,null_swaps=4)
    assert len(r.features)==19
    assert r.raw_log_nodes>=1.0
    assert 0 <= r.successful_null_switches <= 4

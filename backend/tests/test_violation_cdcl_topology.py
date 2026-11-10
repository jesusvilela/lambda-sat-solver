"""Topology-holdout contracts, with external PySAT test only when installed."""
from collections import Counter
from itertools import combinations
from random import Random

import numpy as np
import pytest

from backend.cnf_utils import CNFFormula
from backend.violation_connection import signed_connection
from backend.violation_cross_instance import _shuffle_vars
from backend.violation_cdcl_topology import (
    BASE, SIGN, NULL, PREDICTORS, FAMILIES, cubic_graph, generate_formula,
    support_degree_sign_null, extract_features, cdcl_call,
    canonical_labeled_digest, topology_benchmark)


def _sign_margins(f):
    return (tuple((len(c),sum(v>0 for v in c)) for c in f.clauses),
            Counter((abs(v), v>0) for c in f.clauses for v in c))


def _is_model(f, state):
    return all(any(bool(state & (1 << (abs(v)-1))) == (v>0)
                   for v in c) for c in f.clauses)


@pytest.mark.parametrize("vertices", [8, 16, 32, 48])
def test_cubic_nontrivial_topologies(vertices):
    for topology in ("prism", "rewired"):
        edges = cubic_graph(vertices, topology, seed=33)
        assert edges == cubic_graph(vertices, topology, seed=33)
        assert len(edges) == vertices*3//2
        degrees=Counter(v for a,b in edges for v in (a,b))
        assert set(degrees.values()) == {3}
        assert len(edges) == len(set(edges))
    assert cubic_graph(vertices, "prism", 33) != cubic_graph(vertices, "rewired", 33)


def test_graph_isomorphism_checks_of_rewired_seeded_graphs():
    nx = pytest.importorskip("networkx")
    graphs=[]
    for seed in range(4):
        G=nx.Graph()
        G.add_edges_from(cubic_graph(32, "rewired", seed))
        graphs.append(G)
    assert all(not nx.is_isomorphic(a,b) for a,b in combinations(graphs,2))
    prism=nx.Graph()
    prism.add_edges_from(cubic_graph(32,"prism",0))
    assert all(not nx.is_isomorphic(prism,g) for g in graphs)


def test_generators_have_unique_signed_clauses_and_fixed_budget():
    hashes=set()
    for family in FAMILIES:
        for n in (48, 72):
            for seed in (0,1,2):
                f=generate_formula(family,n,seed)
                assert f.num_vars==n
                assert all(len(c)==3 and len({abs(v) for v in c})==3
                           for c in f.clauses)
                assert all(1<=abs(v)<=n for c in f.clauses for v in c)
                assert len({tuple(sorted(c)) for c in f.clauses})==len(f.clauses)
                if family.startswith("tseitin"):
                    assert len(f.clauses)==4*(2*n//3)
                else:
                    assert len(f.clauses)==round(4.26*n)
                h=canonical_labeled_digest(f)
                assert h not in hashes
                hashes.add(h)


def test_tseitin_charge_parity_in_small_explicit_truth_table():
    # Recheck generator truth without using the CDCL instrument.
    for family in ("tseitin-prism","tseitin-rewired"):
        for seed in range(4):
            f=generate_formula(family,12,seed)
            satisfiable=any(_is_model(f,x) for x in range(1<<f.num_vars))
            assert satisfiable == (seed%2==0)


def test_degree_sign_null_preserves_2d_incidence_margins():
    for family in FAMILIES:
        f=generate_formula(family,48,5)
        randomised,count=support_degree_sign_null(f,seed=77,swaps=80)
        assert count>0, family
        assert _sign_margins(f)==_sign_margins(randomised)
        assert canonical_labeled_digest(f)!=canonical_labeled_digest(randomised)
        assert support_degree_sign_null(f,seed=77,swaps=80)==(randomised,count)


def test_signed_connection_and_structural_features_are_gauge_invariant():
    for family in FAMILIES:
        f=generate_formula(family,48,3)
        features,null_count,base_ns,extra_ns=extract_features(f,null_seed=11,swaps=32)
        assert len(features)==len(BASE)+len(SIGN)+len(NULL)
        assert 0<=features[len(BASE)+2]<=1
        assert null_count>0 and base_ns>=0 and extra_ns>=0
        original=signed_connection(f)
        assert original==signed_connection(_shuffle_vars(f,Random(39)))


class FakeCDCL:
    def __init__(self, answer, clauses, model=None):
        self.answer=answer
        self.clauses=clauses
        self.model=model
        self.budget=None
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def conf_budget(self,b): self.budget=b
    def solve_limited(self):
        assert self.budget is not None
        return self.answer
    def accum_stats(self):
        return {"conflicts": min(17,self.budget),
                "decisions": 23, "propagations": 109}
    def get_model(self): return self.model


def fake_factory(answer,model=None):
    return lambda **kw: FakeCDCL(answer,kw["bootstrap_with"],model=model)


def test_external_observation_truths_and_censoring_are_distinct():
    f=CNFFormula(2,[[1],[2]])
    sat=cdcl_call(f,budget=20,solver_factory=fake_factory(True,[1,2]))
    assert sat.status=="SAT" and sat.valid_sat_model is True
    bad=fake_factory(True,[-1,-2])
    with pytest.raises(AssertionError,match="replay"):
        cdcl_call(f,budget=20,solver_factory=bad)
    unsat=cdcl_call(f,budget=10,solver_factory=fake_factory(False))
    unknown=cdcl_call(f,budget=10,solver_factory=fake_factory(None))
    assert unsat.status=="UNSAT" and unsat.valid_sat_model is None
    assert unknown.status=="UNKNOWN" and unknown.valid_sat_model is None


def test_external_pysat_glucose4_smoke_if_installed():
    pytest.importorskip("pysat.solvers")
    sat=cdcl_call(CNFFormula(2,[[1],[2]]),budget=100)
    unsat=cdcl_call(CNFFormula(1,[[1],[-1]]),budget=100)
    assert sat.status=="SAT" and sat.valid_sat_model
    assert unsat.status=="UNSAT"
    assert sat.conflicts>=0 and unsat.conflicts>=0


def test_fake_oracle_family_and_size_holdouts_do_not_require_verdicts():
    # Fake UNSAT stats are test data only; never publish them as measured SAT results.
    report=topology_benchmark(seeds=2,sizes=(12,15),orbits=2,
                   budget=50,swaps=8,solver_factory=fake_factory(False))
    assert report.total_formulas==24
    assert report.unique_labeled_formulas==24
    assert len(report.family_holdouts)==len(FAMILIES)
    assert report.size_holdout is not None
    assert report.size_holdout.count==12
    assert set(report.aggregate_family_mae)==set(PREDICTORS)
    assert report.censored_call_fraction==0
    assert all(np.isfinite(v) and v>=0 for v in report.aggregate_family_mae.values())


def test_invalid_instrument_budgets():
    with pytest.raises(ValueError): cubic_graph(7,"rewired",1)
    with pytest.raises(ValueError): generate_formula("uniform3",47,2)
    with pytest.raises(ValueError): support_degree_sign_null(CNFFormula(1,[[1,-1]]),seed=1)
    with pytest.raises(ValueError): cdcl_call(CNFFormula(1,[[1]]),budget=0,solver_factory=fake_factory(None))

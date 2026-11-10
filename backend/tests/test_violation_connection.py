"""Validate signed square transport and matched-null invariants."""
from collections import Counter
from itertools import combinations
from random import Random

import pytest

from backend.cnf_utils import CNFFormula
from backend.violation_connection import (
    signed_connection, connection_features, margin_matched_sign_null)
from backend.violation_cross_instance import _shuffle_vars


def test_negative_and_positive_single_square():
    positive = signed_connection(CNFFormula(2,[[1,2],[1,2]]))
    negative = signed_connection(CNFFormula(2,[[1,2],[1,-2]]))
    assert (positive.four_cycles,positive.negative_four_cycles) == (1,0)
    assert (negative.four_cycles,negative.negative_four_cycles) == (1,1)
    assert positive.globally_balanced
    assert not negative.globally_balanced
    assert positive.cycle_rank == negative.cycle_rank == 1


def test_negative_six_cycle_without_squares():
    # Three binary clauses sharing variables in a simple 6-cycle.
    result = signed_connection(CNFFormula(3,[[1,2],[2,3],[3,-1]]))
    assert result.four_cycles == 0
    assert not result.globally_balanced
    assert result.cycle_rank == 1


def test_sign_switch_relabel_and_clause_shuffle_gauge():
    f = CNFFormula(4,[[1,2,-3],[1,-2,4],[-1,-3,4],[2,3,-4]])
    orig = signed_connection(f)
    for seed in range(15):
        image = _shuffle_vars(f,Random(seed))
        new = signed_connection(image)
        assert orig == new
    assert len(connection_features(orig)) == 5


def test_tautological_clauses_are_not_obstructions():
    f = CNFFormula(2,[[1,-1,2],[1,2]])
    r = signed_connection(f)
    assert r.tautological_clauses == 1
    assert r.four_cycles == 0
    assert r.globally_balanced


def _margins(f):
    return (tuple(Counter(abs(lit) for lit in c) for c in f.clauses),
            tuple(sum(lit>0 for lit in c) for c in f.clauses),
            tuple(sum(lit>0 for c in f.clauses for lit in c if abs(lit)==v)
                  for v in range(1,f.num_vars+1)))


def test_checkerboard_null_preserves_both_sign_margins():
    f=CNFFormula(3,[[1,-2,3],[-1,2,-3],[1,-2,-3],[-1,2,3]])
    p=_margins(f)
    out,done = margin_matched_sign_null(f,seed=4,target_swaps=20)
    assert done > 0
    assert _margins(out) == p
    assert signed_connection(out).edges == signed_connection(f).edges
    assert margin_matched_sign_null(f,seed=4,target_swaps=20) == (out,done)


def test_null_noop_and_bounds():
    f=CNFFormula(2,[[1],[2]])
    same,done = margin_matched_sign_null(f,seed=1,target_swaps=10)
    assert done == 0 and same==f
    with pytest.raises(ValueError):
        margin_matched_sign_null(CNFFormula(1,[[1,-1]]),seed=1)
    with pytest.raises(ValueError):
        signed_connection(CNFFormula(1,[[2]]))
    with pytest.raises(ValueError):
        signed_connection(CNFFormula(2,[[1,2],[1,-2]]),max_wedges=0)


def test_signed_square_count_against_literal_four_cycle_enumeration():
    rng=Random(20261029)
    for _ in range(120):
        n,m=rng.randint(1,5),rng.randint(1,6)
        clauses=[]
        for _ in range(m):
            vs=rng.sample(range(1,n+1),rng.randint(0,n))
            clauses.append([v*rng.choice((-1,1)) for v in vs])
        f=CNFFormula(n,clauses)
        s=signed_connection(f)
        total=negative=0
        for c1,c2 in combinations(f.clauses,2):
            one={abs(l):1 if l>0 else -1 for l in c1}
            two={abs(l):1 if l>0 else -1 for l in c2}
            for v,w in combinations(one.keys()&two.keys(),2):
                total+=1
                negative+=int(one[v]*one[w]*two[v]*two[w]==-1)
        assert (s.four_cycles,s.negative_four_cycles)==(total,negative)


def test_balanced_connection_has_no_semantic_sat_implication():
    # UNSAT conjunction of unit clauses: acyclic and thus balanced.
    unsat=signed_connection(CNFFormula(1,[[1],[-1]]))
    assert unsat.globally_balanced
    # SAT CNF with an unbalanced square: set x=True.
    sat=signed_connection(CNFFormula(2,[[1,2],[1,-2]]))
    assert not sat.globally_balanced

"""Finite ETH x Kakeya probe invariants (no SAT verdicts)."""
import math
import random
import pytest
from backend.cnf_utils import CNFFormula
from backend.violation_geometry import (
    audit_hash, greedy_violation_rows, incidence_overlap, matched_random_rows,
    parity_accepts, run_bridge_experiment, violation_masks)


def direct_satisfies(formula, assignment):
    return all(any(bool(assignment & (1 << (abs(lit)-1))) == (lit > 0)
                   for lit in clause) for clause in formula.clauses)


def test_violation_masks_match_direct_cnf_semantics():
    for formula in [CNFFormula(0, []), CNFFormula(0, [[]]),
                    CNFFormula(2, []), CNFFormula(2, [[1,2],[-1,-2]]),
                    CNFFormula(3, [[1,-2], [2,3], [-1], [1,-1], []])]:
        masks = violation_masks(formula)
        assert len(masks) == 2**formula.num_vars
        assert [v == 0 for v in masks] == [
            direct_satisfies(formula, x) for x in range(2**formula.num_vars)]


def test_parity_relaxation_never_eliminates_a_real_model():
    rng = random.Random(20261029)
    for _ in range(70):
        n, m = rng.randrange(1,6), rng.randrange(1,12)
        clauses = [[rng.choice((-1,1))*rng.randint(1,n)
                    for _ in range(rng.randint(0,4))] for _ in range(m)]
        f = CNFFormula(n, clauses)
        masks = violation_masks(f)
        rows = tuple(rng.randint(1,(1<<m)-1) for _ in range(4))
        a = audit_hash(masks, rows, m)
        assert a.models == sum(direct_satisfies(f,x) for x in range(1<<n))
        assert a.survivors >= a.models
        assert all(all(parity_accepts(v,r) for r in rows) for v in masks if v==0)


def test_relaxation_is_not_a_sat_certificate():
    masks = violation_masks(CNFFormula(1, [[1],[-1]]))
    weak = audit_hash(masks, [1], 2)
    assert (weak.models,weak.spurious) == (0,1)
    assert not weak.equivalent_on_enumerated_domain
    strong = audit_hash(masks, [3], 2)
    assert (strong.models,strong.spurious)==(0,0)


def test_greedy_searches_clause_violation_space():
    masks = violation_masks(CNFFormula(1, [[1],[-1]]))
    rows = greedy_violation_rows(masks,2,max_rows=1,max_weight=2)
    assert rows==(3,)
    assert audit_hash(masks, rows, 2).spurious==0


def test_holdout_and_controls_accounted():
    f=CNFFormula(3, [[1,2],[-1,3],[-2,-3],[1,-3]])
    r=run_bridge_experiment(f,max_rows=2)
    assert r.states==8
    assert r.training_states+r.heldout_states==8
    assert r.models==sum(v==0 for v in violation_masks(f))
    assert r.training_spurious+r.heldout_spurious==r.exact_audit.spurious
    assert len(r.controls)==4
    assert len(r.singleton_baseline_rows)<=len(r.chosen_rows)
    for c in r.controls:
        assert sorted(row.bit_count() for row in c.rows)==sorted(row.bit_count() for row in r.chosen_rows)


def test_incidence_has_known_spectra():
    masks=violation_masks(CNFFormula(1, [[1],[-1]]))
    identical=incidence_overlap(masks,(1,1),2)
    assert identical.active_rows==2
    assert math.isclose(identical.top_gram_eigenvalue,2)
    assert math.isclose(identical.mean_pairwise_cosine,1)
    assert identical.maximum_multiplicity==2
    disjoint=incidence_overlap(masks,(1,2),2)
    assert math.isclose(disjoint.top_gram_eigenvalue,1)
    assert math.isclose(disjoint.mean_pairwise_cosine,0)
    assert disjoint.maximum_multiplicity==1
    empty=incidence_overlap(violation_masks(CNFFormula(2,[])),(),0)
    assert empty.top_gram_eigenvalue==0


def test_spurious_nonincreasing_with_more_rows():
    f=CNFFormula(4,[[1,-2],[-1,2],[3,4],[-3,-4],[1,3]])
    masks=violation_masks(f)
    counts=[audit_hash(masks,greedy_violation_rows(masks,5,max_rows=k),5).spurious for k in range(5)]
    assert counts==sorted(counts,reverse=True)


def test_declared_unused_variables_remain_counted():
    f=CNFFormula(3,[[1]])
    assert sum(v==0 for v in violation_masks(f))==4
    assert run_bridge_experiment(f).models==4


def test_matched_null_deterministic():
    rows=(0b11,0b111,0b101)
    r=matched_random_rows(rows,8,77)
    assert r==matched_random_rows(rows,8,77)
    assert [v.bit_count() for v in r]==[v.bit_count() for v in rows]


def test_resource_limits_and_invalid_inputs():
    with pytest.raises(ValueError): violation_masks(CNFFormula(13,[]),max_vars=12)
    with pytest.raises(ValueError): violation_masks(CNFFormula(1,[[0]]))
    with pytest.raises(ValueError): violation_masks(CNFFormula(1,[[2]]))
    with pytest.raises(ValueError): greedy_violation_rows((1,),3,candidate_budget=2)
    with pytest.raises(ValueError): audit_hash((1,),(8,),3)
    with pytest.raises(ValueError): incidence_overlap((8,),(1,),3)

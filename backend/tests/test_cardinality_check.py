"""Tests for the counting/cardinality frame (pigeonhole counting refutation)."""

from backend.cardinality_check import pigeonhole_counting_refutation
from backend.cnf_utils import CNFFormula
from backend.eval.generators import pigeonhole


class TestPigeonholeCounting:
    def test_php_family_refuted(self):
        # PHP(n -> n-1) refutes soundly with k=n pigeons, m=n-1 holes
        for n in range(3, 8):
            cnf, _ = pigeonhole(n)
            r = pigeonhole_counting_refutation(cnf)
            assert r.refuted and r.pigeons == n and r.holes == n - 1

    def test_satisfiable_pigeonhole_not_refuted(self):
        # 2 pigeons, 2 holes -> k=m -> not a contradiction
        # ALO: (x11 v x12), (x21 v x22); AMO holes: (-x11 v -x21),(-x12 v -x22)
        f = CNFFormula(num_vars=4, clauses=[[1, 2], [3, 4], [-1, -3], [-2, -4]])
        r = pigeonhole_counting_refutation(f)
        assert not r.refuted and r.pigeons == 2 and r.holes == 2

    def test_no_alo_structure_not_refuted(self):
        f = CNFFormula(num_vars=3, clauses=[[-1, -2], [-2, -3]])  # no ALO clauses
        assert not pigeonhole_counting_refutation(f).refuted

    def test_overlapping_alo_not_refuted(self):
        # ALO clauses sharing a variable are not variable-disjoint -> inapplicable
        f = CNFFormula(num_vars=3, clauses=[[1, 2], [2, 3], [-1, -3]])
        assert not pigeonhole_counting_refutation(f).refuted

    def test_non_clique_group_not_refuted(self):
        # exclusion path a-b-c (a,c NOT excluded) is not an at-most-one group,
        # so the <=1 bound is unjustified -> must not claim refutation
        f = CNFFormula(num_vars=6,
                       clauses=[[1, 2], [3, 4], [5, 6],      # 3 ALO (pigeons)
                                [-1, -3], [-3, -5]])          # path, not a clique
        assert not pigeonhole_counting_refutation(f).refuted

"""Tests for XOR/parity recovery (the GF(2) frame detector)."""

from itertools import combinations, product

from backend.cnf_utils import CNFFormula
from backend.eval.generators import pigeonhole
from backend.xor_extraction import extract_xors


def _tseitin_k4():
    edges = list(combinations(range(4), 2))
    ev = {e: i + 1 for i, e in enumerate(edges)}
    charge = {0: 1, 1: 0, 2: 0, 3: 0}
    clauses = []
    for v in range(4):
        inc = [ev[e] for e in edges if v in e]
        for bits in product([0, 1], repeat=len(inc)):
            if sum(bits) % 2 != charge[v]:
                clauses.append([(l if b else -l) for l, b in zip(inc, bits)])
    return CNFFormula(num_vars=6, clauses=clauses)


class TestXORExtraction:
    def test_single_xor_recovered_with_rhs(self):
        # x1 ^ x2 ^ x3 = 1  encoded as the 4 clauses with an even # of negatives
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        r = extract_xors(f)
        assert len(r.xors) == 1
        assert r.xors[0].variables == (1, 2, 3)
        assert r.xors[0].rhs == 1
        assert r.xor_clause_fraction == 1.0

    def test_rhs_zero_variant(self):
        # x1 ^ x2 = 0  -> clauses (x1 v -x2), (-x1 v x2)  (odd # negatives, c=1)
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]])
        r = extract_xors(f)
        assert len(r.xors) == 1 and r.xors[0].rhs == 0

    def test_incomplete_group_not_recovered(self):
        # only 3 of the 4 clauses of a 3-XOR -> not a complete parity group
        f = CNFFormula(num_vars=3, clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3]])
        assert extract_xors(f).xors == []

    def test_tseitin_is_all_parity(self):
        # Tseitin = pure parity: GF(2) is the shallow frame, fraction 1.0
        r = extract_xors(_tseitin_k4())
        assert len(r.xors) == 4
        assert r.xor_clause_fraction == 1.0

    def test_php_has_no_xor_structure(self):
        # PHP is counting, not parity: resolution is the shallow frame, 0.0
        php, _ = pigeonhole(3)
        r = extract_xors(php)
        assert r.xors == [] and r.xor_clause_fraction == 0.0

    def test_max_arity_caps_recovery(self):
        # a 3-XOR is not recovered when max_arity is 2
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        assert extract_xors(f, max_arity=2).xors == []

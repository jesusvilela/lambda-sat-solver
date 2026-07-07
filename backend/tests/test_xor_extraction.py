"""Tests for XOR/parity recovery (the GF(2) frame detector)."""

import random
from itertools import combinations, product

from backend.cnf_utils import CNFFormula
from backend.eval.generators import pigeonhole
from backend.xor_extraction import (
    _bucket_python,
    _bucket_vectorized,
    extract_xors,
)


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


class TestVectorizedMatchesReference:
    """The numpy fast path must agree with the pure-Python reference exactly --
    extraction is soundness-critical (a spurious XOR is an unsound refutation),
    so the vectorized path never widens the trusted base."""

    def _bucketize(self, formula, max_arity=6):
        from collections import defaultdict
        b = defaultdict(list)
        for c in formula.clauses:
            k = len(c)
            if 2 <= k <= max_arity:
                b[k].append(c)
        return b

    def _agree(self, formula):
        bits = max(1, int(formula.num_vars).bit_length())
        for k, rows in self._bucketize(formula).items():
            ref = set(_bucket_python(rows, k))
            if bits * k <= 62:
                vec = set(_bucket_vectorized(rows, k, bits))
                assert vec == ref, f"bucket k={k}: vectorized != reference"

    def test_agree_on_structured_families(self):
        self._agree(_tseitin_k4())
        for n in range(3, 7):
            self._agree(pigeonhole(n)[0])

    def test_agree_on_random_battery(self):
        rng = random.Random(1234)
        for _ in range(60):
            n = rng.randint(4, 40)
            m = rng.randint(1, 120)
            clauses = []
            for _ in range(m):
                k = rng.randint(1, 7)                 # includes arity > max & dups
                clauses.append([rng.choice([-1, 1]) * rng.randint(1, n)
                                for _ in range(k)])
            self._agree(CNFFormula(num_vars=n, clauses=clauses))

    def test_wide_bucket_falls_back_to_python(self):
        # arity*bits over 62 must NOT take the int64 vectorized path; extract_xors
        # still returns correctly (via the pure-Python reference).
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        r = extract_xors(f)
        assert len(r.xors) == 1 and r.xors[0].rhs == 1


class TestGF2Refutation:
    def test_tseitin_refuted_fast(self):
        from backend.xor_extraction import gf2_xor_refutation
        r = gf2_xor_refutation(_tseitin_k4())
        assert r.refuted is True and r.decides_fully is True

    def test_satisfiable_xor_not_refuted(self):
        from backend.xor_extraction import gf2_xor_refutation
        # x1 ^ x2 = 0  is satisfiable -> not refuted, but fully decided (all parity)
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]])
        r = gf2_xor_refutation(f)
        assert r.refuted is False and r.decides_fully is True

    def test_no_xor_structure_inconclusive(self):
        from backend.xor_extraction import gf2_xor_refutation
        php, _ = pigeonhole(3)
        r = gf2_xor_refutation(php)
        assert r.refuted is False and r.decides_fully is False

    def test_soundness_agrees_with_inconsistent_system(self):
        from backend.xor_extraction import gf2_xor_refutation
        # x1^x2=0 AND x1^x2=1  -> inconsistent -> refuted
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2], [1, 2], [-1, -2]])
        assert gf2_xor_refutation(f).refuted is True


class TestGF2Solve:
    def test_sat_xor_returns_verified_model(self):
        from backend.xor_extraction import gf2_xor_solve
        from backend.cnf_utils import verify_model
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]])  # x1^x2=0, SAT
        r = gf2_xor_solve(f)
        assert r.status == 'SAT' and r.model is not None
        assert verify_model(f, r.model)          # independently verified

    def test_unsat_tseitin(self):
        from backend.xor_extraction import gf2_xor_solve
        r = gf2_xor_solve(_tseitin_k4())
        assert r.status == 'UNSAT' and r.model is None

    def test_inconclusive_when_not_fully_covered(self):
        from backend.xor_extraction import gf2_xor_solve
        # x1^x2=0 (2 clauses) + a non-parity unit [3] -> XORs don't cover it
        f = CNFFormula(num_vars=3, clauses=[[1, -2], [-1, 2], [3]])
        r = gf2_xor_solve(f)
        assert r.status == 'INCONCLUSIVE' and r.decides_fully is False

    def test_never_claims_unverified_sat(self):
        # every SAT verdict this returns must satisfy the formula
        from backend.xor_extraction import gf2_xor_solve
        from backend.cnf_utils import verify_model
        # x1^x2^x3 = 1 (SAT), full parity
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        r = gf2_xor_solve(f)
        assert r.status == 'SAT' and verify_model(f, r.model)

"""Tests for the orbifold layer (backend/orbifold.py): satisfiability as a chart
carrying a bracketed isotropy (symmetry) group.

Soundness of the bracket lower <= |Aut| <= upper is checked against brute-force
automorphism counting; the signature must recover the classical bit as pi_truth.
"""

import itertools
import math

from backend.cnf_utils import CNFFormula, verify_model
from backend.eval.generators import pigeonhole
from backend.orbifold import (
    _transposition_is_automorphism,
    satisfiability_signature,
    symmetry_log2_upper,
    symmetry_partition,
    verified_symmetry,
)


def _true_aut_log2(f: CNFFormula) -> float:
    """Brute-force log2|Aut| over variable permutations (sign-preserving)."""
    n = f.num_vars
    cs = {frozenset(c) for c in f.clauses}
    cnt = 0
    for perm in itertools.permutations(range(1, n + 1)):
        m = {i + 1: perm[i] for i in range(n)}
        if {frozenset((m[abs(l)] if l > 0 else -m[abs(l)]) for l in c)
                for c in cs} == cs:
            cnt += 1
    return math.log2(cnt)


class TestSymmetryBracket:
    def test_bracket_contains_true_aut(self):
        cases = [
            pigeonhole(3)[0],
            CNFFormula(3, [[1, 2], [2, 3], [1, 3]]),                 # triangle
            CNFFormula(3, [[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]]),
            CNFFormula(4, [[1, 2], [3, 4]]),                          # two indep
        ]
        for f in cases:
            lo = verified_symmetry(f)[1]
            up = symmetry_log2_upper(f)
            true = _true_aut_log2(f)
            assert lo - 1e-9 <= true <= up + 1e-9

    def test_verified_transpositions_are_real_automorphisms(self):
        # a genuine single-variable symmetry: x1, x2 interchangeable
        f = CNFFormula(3, [[1, 2], [-1, -2], [1, 3], [2, 3]])
        cs = {frozenset(c) for c in f.clauses}
        assert _transposition_is_automorphism(cs, 1, 2)
        # and it maps models to models
        for b in itertools.product([False, True], repeat=3):
            a = {1: b[0], 2: b[1], 3: b[2]}
            swapped = {1: b[1], 2: b[0], 3: b[2]}
            assert verify_model(f, a) == verify_model(f, swapped)

    def test_no_false_symmetry_on_asymmetric_formula(self):
        # x1 appears differently from x2 -> not interchangeable
        f = CNFFormula(2, [[1], [1, 2]])
        cs = {frozenset(c) for c in f.clauses}
        assert not _transposition_is_automorphism(cs, 1, 2)


class TestOrbifoldCharts:
    def test_pigeonhole_is_high_symmetry(self):
        # PHP variables collapse into very few color classes -> large isotropy
        part = symmetry_partition(pigeonhole(5)[0])
        assert len(part) <= 3                      # 20 vars, few orbits
        assert symmetry_log2_upper(pigeonhole(5)[0]) > 20.0

    def test_random_is_trivial_symmetry(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                               / "docs/ladder/scripts"))
        from frame_benchmark import random_3sat
        f = random_3sat(30, 128, 3)
        # almost all variables individualized -> near-trivial isotropy
        assert len(symmetry_partition(f)) >= 25
        assert symmetry_log2_upper(f) < 3.0

    def test_partition_is_sound_over_approximation(self):
        # verified-interchangeable variables must land in the SAME color class
        f = CNFFormula(3, [[1, 2], [-1, -2], [1, 3], [2, 3]])
        colour_of = {}
        for i, cls in enumerate(symmetry_partition(f)):
            for v in cls:
                colour_of[v] = i
        assert colour_of[1] == colour_of[2]        # 1,2 are automorphic


class TestSignature:
    def test_recovers_classical_bit(self):
        for f, bit in [(pigeonhole(4)[0], "UNSAT"),
                       (CNFFormula(2, [[1, 2]]), None)]:
            sig = satisfiability_signature(f)
            assert sig.classical_bit == sig.status
            if bit is not None:
                assert sig.status == bit

    def test_signature_brackets_symmetry(self):
        sig = satisfiability_signature(pigeonhole(4)[0])
        assert sig.symmetry_log2_lower <= sig.symmetry_log2_upper
        assert sig.action in ("accept", "repair", "escalate")

"""Tests for the crystallized frame router (backend/frame_solver.py).

The router is the session's distilled result: one call that decides a formula in
the shallowest sound frame that collapses it, or reports CDCL_NEEDED. These tests
pin the contract -- each frame resolves the family it owns, every verdict is
certified, and a structureless instance honestly falls through.
"""

from itertools import combinations, product

from backend.cnf_utils import CNFFormula, verify_model
from backend.eval.generators import pigeonhole
from backend.frame_solver import frame_solve


def _tseitin_k4():
    """Tseitin on K4 with one odd vertex -> UNSAT; pure parity (GF(2) frame)."""
    edges = list(combinations(range(4), 2))
    ev = {e: i + 1 for i, e in enumerate(edges)}
    charge = {0: 1, 1: 0, 2: 0, 3: 0}  # total charge odd
    clauses = []
    for v in range(4):
        inc = [ev[e] for e in edges if v in e]
        for bits in product([0, 1], repeat=len(inc)):
            if sum(bits) % 2 != charge[v]:
                clauses.append([(l if b else -l) for l, b in zip(inc, bits)])
    return CNFFormula(num_vars=6, clauses=clauses)


class TestFrameRouting:
    def test_tseitin_resolves_in_parity_frame(self):
        r = frame_solve(_tseitin_k4())
        assert r.status == 'UNSAT'
        assert r.resolved_by == 'parity'
        assert r.certified is True
        assert r.model is None

    def test_pigeonhole_resolves_in_counting_frame(self):
        # PHP is counting-shallow / GF(2)-blind: it must land in 'counting',
        # not 'parity' (the parity frame has no XOR structure to bite on).
        php, _ = pigeonhole(4)
        r = frame_solve(php)
        assert r.status == 'UNSAT'
        assert r.resolved_by == 'counting'
        assert r.certified is True

    def test_binary_contradiction_resolves_in_2sat_frame(self):
        # (x1) and (-x1) as binary/unit clauses: the implication frame refutes
        f = CNFFormula(num_vars=2, clauses=[[1, 2], [-1, 2], [1, -2], [-1, -2]])
        r = frame_solve(f)
        assert r.status == 'UNSAT'
        assert r.resolved_by == '2sat'
        assert r.certified is True

    def test_satisfiable_parity_returns_verified_model(self):
        # x1 ^ x2 ^ x3 = 1 (full parity, SAT): decided in 'parity' with a model
        # that is INDEPENDENTLY re-checked against the original CNF.
        f = CNFFormula(num_vars=3,
                       clauses=[[1, 2, 3], [1, -2, -3], [-1, 2, -3], [-1, -2, 3]])
        r = frame_solve(f)
        assert r.status == 'SAT'
        assert r.resolved_by == 'parity'
        assert r.certified is True
        assert r.model is not None
        assert verify_model(f, r.model)          # the certificate is real

    def test_structureless_formula_falls_through_to_cdcl(self):
        # a small satisfiable 3-SAT with no parity/counting/2-SAT collapse:
        # the router must NOT invent a verdict -- it reports CDCL_NEEDED,
        # uncertified, and leaves the decision to the engine.
        f = CNFFormula(num_vars=4,
                       clauses=[[1, 2, 3], [-1, 2, 4], [1, -3, 4], [2, 3, -4]])
        r = frame_solve(f)
        assert r.status == 'CDCL_NEEDED'
        assert r.resolved_by == 'none'
        assert r.certified is False
        assert r.model is None


class TestFrameSoundness:
    def test_every_certified_unsat_is_genuinely_unsatisfiable(self):
        # differential soundness: no certified UNSAT verdict may have a model.
        # Brute-force the small instances the frames claim to refute.
        instances = [
            _tseitin_k4(),
            pigeonhole(3)[0],
            pigeonhole(4)[0],
        ]
        for f in instances:
            r = frame_solve(f)
            assert r.status == 'UNSAT' and r.certified
            # exhaustively confirm unsatisfiability
            assert not _has_model(f)

    def test_every_certified_sat_model_verifies(self):
        # any SAT the router returns must satisfy the original formula
        f = CNFFormula(num_vars=2, clauses=[[1, -2], [-1, 2]])  # x1^x2=0, SAT
        r = frame_solve(f)
        assert r.status == 'SAT' and r.certified
        assert verify_model(f, r.model)


def _has_model(f: CNFFormula) -> bool:
    """Brute-force satisfiability check for small formulas (test oracle)."""
    n = f.num_vars
    for bits in product([False, True], repeat=n):
        assign = {i + 1: bits[i] for i in range(n)}
        if verify_model(f, assign):
            return True
    return False

"""Tests for the descriptive dispatch stack: cms_wrapper, dynamics, metasolver.

The metasolver reverts the dynamical description into a certified dispatch. These
tests pin: the CMS baseline is correct and honest; the description separates
"frame+geometry suffice" from "does not suffice"; and the metasolver's every verdict
is certified and agrees with ground truth -- including the counting fragment where
CMS is exponential (the axis on which the metasolver beats it).
"""

import sys
from itertools import combinations, product
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_3sat, random_xorsat, tseitin  # noqa: E402

from backend.cms_wrapper import cms_solve  # noqa: E402
from backend.cnf_utils import CNFFormula, verify_model  # noqa: E402
from backend.dynamics import describe  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.metasolver import metasolve  # noqa: E402
from backend.tests.test_kissat_wrapper import requires_kissat  # noqa: E402

try:
    import pycryptosat
    cms_available = True
except ImportError:
    cms_available = False

requires_cms = pytest.mark.skipif(
    not cms_available,
    reason="pycryptosat module not installed"
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
                clauses.append([(-1 if b else 1) * inc[i] for i, b in enumerate(bits)])
    return CNFFormula(num_vars=len(edges), clauses=clauses)


@requires_cms
class TestCMSBaseline:
    def test_trivial_sat_and_unsat(self):
        sat = cms_solve(CNFFormula(2, [[1, 2], [-1]]))
        assert sat.status == "SAT" and sat.verified
        uns = cms_solve(CNFFormula(1, [[1], [-1]]))
        assert uns.status == "UNSAT"

    def test_sat_model_is_verified(self):
        f = random_3sat(30, 100, 7)
        r = cms_solve(f)
        if r.status == "SAT":
            assert r.verified and verify_model(f, r.model)

    def test_cms_is_exponential_on_counting(self):
        # the honest hard case: CMS blows up on php where the counting frame is
        # instant. php10 within a short budget must NOT be solved by CMS.
        r = cms_solve(pigeonhole(10)[0], timeout_s=3)
        assert r.status == "TIMEOUT"


class TestDynamicsDescription:
    def test_frame_geometry_suffice_on_structured(self):
        assert describe(_tseitin_k4()).sufficient()
        assert describe(pigeonhole(7)[0]).sufficient()

    def test_does_not_suffice_on_tunnel(self):
        d = describe(random_3sat(80, round(4.26 * 80), 0))
        assert not d.sufficient()
        assert d.region == "tunnel"
        assert d.conserved == []            # no algebraic invariant to exploit

    def test_conserved_invariants_named(self):
        assert "parity" in describe(_tseitin_k4()).conserved
        assert "counting" in describe(pigeonhole(7)[0]).conserved


class TestMetasolver:
    @pytest.mark.parametrize("gen,expect_frame", [
        (lambda: _tseitin_k4(), "parity"),
        (lambda: pigeonhole(7)[0], "counting"),
        (lambda: random_xorsat(20, 20, 1), "parity"),
    ])
    def test_structured_decided_by_certified_frame(self, gen, expect_frame):
        r = metasolve(gen())
        assert r.status == "UNSAT"
        assert r.strategy == expect_frame
        assert r.certified

    def test_counting_beats_cms_instantly(self):
        # php12: CMS times out; the metasolver refutes by the counting frame in ms
        r = metasolve(pigeonhole(12)[0], timeout_s=10)
        assert r.status == "UNSAT" and r.strategy == "counting" and r.certified
        assert r.seconds < 1.0

    @requires_kissat
    def test_tunnel_falls_to_certified_cdcl(self):
        r = metasolve(random_3sat(120, round(4.26 * 120), 0))
        assert r.status in ("SAT", "UNSAT")
        assert r.strategy in ("kissat", "cadical")
        assert r.certified                  # DRAT (UNSAT) or model replay (SAT)

    @requires_kissat
    def test_sat_verdicts_carry_verified_models(self):
        r = metasolve(random_3sat(40, 120, 3))
        if r.status == "SAT" and r.model is not None:
            assert verify_model(random_3sat(40, 120, 3), r.model)

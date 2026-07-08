"""Tests for the fractal, n-caged meta-metasolver (backend/metametasolver.py).

The cage must: decide structured islands instantly via the certified frame arm; on the
tunnel, race a seed-diversified CDCL portfolio and return a CERTIFIED verdict that
matches ground truth; never leak losing processes; and never trust an unchecked arm.
"""

import sys
from itertools import combinations, product
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_3sat, random_xorsat  # noqa: E402

from backend.cnf_utils import CNFFormula, verify_model  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.metametasolver import (  # noqa: E402
    default_arms, metametasolve,
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


class TestFrameArm:
    def test_structured_islands_decided_instantly_by_one_arm(self):
        for f, frame in [(_tseitin_k4(), "parity"), (pigeonhole(7)[0], "counting"),
                         (random_xorsat(20, 20, 1), "parity")]:
            r = metametasolve(f, breadth=4, timeout_s=15)
            assert r.status == "UNSAT" and r.certified
            assert r.winner == frame and r.arms == 1        # no portfolio needed


class TestTunnelPortfolio:
    def test_tunnel_decided_by_certified_cdcl_arm(self):
        f = random_3sat(120, round(4.26 * 120), 0)
        r = metametasolve(f, breadth=4, timeout_s=25)
        assert r.status in ("SAT", "UNSAT")
        assert r.certified                                  # DRAT or model-verified
        assert r.winner.startswith(("kissat", "cadical"))
        assert r.arms >= 4                                  # the portfolio actually raced

    def test_sat_winner_carries_a_verified_model(self):
        f = random_3sat(90, 300, 5)
        r = metametasolve(f, breadth=4, timeout_s=25)
        if r.status == "SAT":
            assert r.model is not None and verify_model(f, r.model)

    def test_portfolio_agrees_with_ground_truth(self):
        # cross-check the portfolio verdict against a single certified solve
        from backend.metasolver import metasolve
        f = random_3sat(100, round(4.26 * 100), 2)
        mm = metametasolve(f, breadth=4, timeout_s=25)
        m = metasolve(f, timeout_s=25)
        if mm.status in ("SAT", "UNSAT") and m.status in ("SAT", "UNSAT"):
            assert mm.status == m.status


class TestPortfolioShape:
    def test_default_arms_diversify_without_cms(self):
        arms = default_arms(6)
        engines = {e for e, _ in arms}
        seeds = {s for e, s in arms if e == "kissat"}
        assert "kissat" in engines and "cadical" in engines
        assert "cryptominisat" not in engines and "cms" not in engines
        assert len(seeds) == 6                              # six diversified seeds

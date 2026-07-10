"""Tests for ACAF (backend/acaf.py) -- the adaptive actor-critic-ambigator-fuzzer.

Pin the policy: structured islands go to the in-process frame (instant, certified, no
swarm); the easy tunnel goes to a SINGLE arm (no launch swarm); the hard tunnel escalates
to a cores-sized diversified portfolio. Every verdict certified and agreeing with truth.
"""

import sys
from itertools import combinations, product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_3sat, random_xorsat  # noqa: E402

from backend.acaf import _critic, _fuzzer, acaf_solve  # noqa: E402
from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402
from backend.tests.test_kissat_wrapper import requires_kissat  # noqa: E402


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


class TestCritic:
    def test_frames_suffice_on_structure(self):
        suffice, hardness, _amb = _critic(_tseitin_k4())
        assert suffice and hardness == 0.0
        assert _critic(pigeonhole(7)[0])[0]

    def test_tunnel_hardness_is_high_for_unstructured(self):
        s_small, h_small, _ = _critic(random_3sat(120, round(4.26 * 120), 0))
        assert not s_small
        assert h_small == 1.0  # Unstructured is assigned max hardness


class TestFuzzer:
    def test_diversifies_engines_and_seeds(self):
        arms = _fuzzer(4)
        assert ("cadical", 0) in arms               # engine diversity
        assert len([a for a in arms if a[0] == "kissat"]) == 3
        assert _fuzzer(1) == [("kissat", 0)]        # degenerate: one arm


class TestActorStages:
    def test_structured_goes_to_frame_stage(self):
        for f, frame in [(_tseitin_k4(), "parity"), (pigeonhole(7)[0], "counting"),
                         (random_xorsat(20, 20, 1), "parity")]:
            r = acaf_solve(f, timeout_s=15)
            assert r.status == "UNSAT" and r.certified
            assert r.stage == "frame" and r.winner == frame and r.breadth == 0

    @requires_kissat
    def test_easy_tunnel_uses_a_single_arm_not_a_swarm(self):
        r = acaf_solve(random_3sat(140, round(4.26 * 140), 0), timeout_s=20)
        assert r.status in ("SAT", "UNSAT") and r.certified
        assert r.stage == "single" and r.breadth == 1        # no swarm overhead

    @requires_kissat
    def test_hard_tunnel_escalates_to_cores_sized_portfolio(self):
        import os
        r = acaf_solve(random_3sat(280, round(4.26 * 280), 0), timeout_s=30)
        assert r.status in ("SAT", "UNSAT") and r.certified
        assert r.stage == "portfolio"
        assert 2 <= r.breadth <= max(2, os.cpu_count() or 1)  # sized to the cores

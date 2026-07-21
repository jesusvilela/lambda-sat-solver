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

from backend.acaf import (  # noqa: E402
    _ALPHA_C, _cosmological_hardness, _critic, _fuzzer, acaf_solve,
)
from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.eval.generators import pigeonhole  # noqa: E402


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

    def test_tunnel_hardness_grows_with_size(self):
        s_small, h_small, _ = _critic(random_3sat(120, round(4.26 * 120), 0))
        s_big, h_big, _ = _critic(random_3sat(300, round(4.26 * 300), 0))
        assert not s_small and not s_big
        assert h_big > h_small                      # bigger instance -> heavier tail


class TestCosmologicalHardness:
    """The hardness lives on the holographic screen of hardness (∂∞) -- a geometric
    position (comoving scale x criticality), NOT a Euclidean var-count ramp. Pin the
    properties that make it novel, elegant, and honestly bounded (Charter)."""

    def test_strictly_bounded_open_unit_interval(self):
        # geometry's own saturation (tanh through the boundary), never a min() clamp:
        # even an astronomically large cosmos stays strictly inside the screen (0, 1).
        for n in (10, 100, 500, 5_000, 5_000_000):
            h = _cosmological_hardness(n, round(_ALPHA_C * n), 14.16)
            assert 0.0 < h < 1.0
        assert _cosmological_hardness(5_000_000, round(_ALPHA_C * 5_000_000), 14.16) < 1.0

    def test_horizon_monotone_in_scale_on_the_ridge(self):
        # on the critical ridge, hardness rises monotonically with the comoving horizon (n).
        ns = [40, 80, 120, 160, 200, 240, 280, 320, 400, 600]
        hs = [_cosmological_hardness(n, round(_ALPHA_C * n), 14.16) for n in ns]
        assert all(b > a for a, b in zip(hs, hs[1:]))

    def test_criticality_caustic_peaks_on_the_phase_transition_ridge(self):
        # at fixed scale, the ridge alpha_c=4.26 is hardest; over- and under-constrained
        # cosmoses (a caustic, sech-shaped) are easier -- something n/260 could never see.
        n = 220
        on_ridge = _cosmological_hardness(n, round(_ALPHA_C * n), 14.16)
        under = _cosmological_hardness(n, round(2.5 * n), 14.16)   # under-constrained
        over = _cosmological_hardness(n, round(7.0 * n), 14.16)    # over-constrained
        assert on_ridge > under and on_ridge > over

    def test_caustic_decays_monotonically_off_the_ridge(self):
        n = 220
        below = [_cosmological_hardness(n, round(a * n), 14.16)
                 for a in (4.26, 3.5, 3.0, 2.5, 2.0)]
        above = [_cosmological_hardness(n, round(a * n), 14.16)
                 for a in (4.26, 5.0, 6.0, 7.0, 8.0)]
        assert all(b < a for a, b in zip(below, below[1:]))   # monotone below the ridge
        assert all(b < a for a, b in zip(above, above[1:]))   # monotone above the ridge

    def test_screen_gate_discounts_residual_near_fold_structure(self):
        # a genuine tunnel instance is pinned at ∂∞ (gyration ~14): full screen weight.
        # residual structure (small gyration, still near the fold) is HONESTLY discounted --
        # the boundary gate confirms we are truly frame-void before charging full hardness.
        n, m = 280, round(_ALPHA_C * 280)
        deep = _cosmological_hardness(n, m, 14.16)
        shallow = _cosmological_hardness(n, m, 1.0)
        assert shallow < deep
        assert _cosmological_hardness(n, m, 0.5) < shallow    # deeper discount nearer centre

    def test_matches_measured_heavy_tail_onset(self):
        # the constant N* is fixed to the MEASURED onset: the ~220-var heavy-tail knee
        # lands at the screen's horizon knee (~0.85), so the actor's staging is preserved.
        knee = _cosmological_hardness(220, round(_ALPHA_C * 220), 14.16)
        assert 0.82 <= knee <= 0.88


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

    def test_easy_tunnel_uses_a_single_arm_not_a_swarm(self):
        r = acaf_solve(random_3sat(140, round(4.26 * 140), 0), timeout_s=20)
        assert r.status in ("SAT", "UNSAT") and r.certified
        assert r.stage == "single" and r.breadth == 1        # no swarm overhead

    def test_hard_tunnel_escalates_to_cores_sized_portfolio(self):
        import os
        r = acaf_solve(random_3sat(280, round(4.26 * 280), 0), timeout_s=30)
        assert r.status in ("SAT", "UNSAT") and r.certified
        assert r.stage == "portfolio"
        assert 2 <= r.breadth <= max(2, os.cpu_count() or 1)  # sized to the cores

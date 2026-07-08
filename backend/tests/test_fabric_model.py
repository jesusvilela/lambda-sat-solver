"""Tests for backend/fabric_model.py -- the hyperbolic parametric fabric model.

Two layers:
  1. the Poincare-ball (gyrovector) primitives are mathematically correct
     (exp∘log round-trip, |log|_riemannian == geodesic distance, Frechet mean);
  2. the fitted model places the families where the geometry says they belong
     (decided near the centre, CDCL out at ∂∞) and classifies held-out instances.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_xorsat, tseitin  # noqa: E402

from backend.eval.generators import (  # noqa: E402
    pigeonhole, random_ksat, xor_chain,
)
from backend.fabric import fabric  # noqa: E402
from backend.fabric_model import (  # noqa: E402
    exp_map, fit_default_model, frechet_mean, geodesic, log_map, mobius_add,
    poincare_embed, predict_frame,
)


def _conformal(x):
    return 2.0 / (1 - float(x @ x))


class TestPoincarePrimitives:
    """The gyrovector maps must be exact on interior points (they carry the model)."""

    def _pts(self, seed, scale=0.25, d=5, n=400):
        rng = np.random.default_rng(seed)
        out = []
        while len(out) < n:
            x = rng.normal(size=d) * scale
            if np.linalg.norm(x) < 0.9:          # stay strictly interior
                out.append(x)
        return out

    def test_geodesic_from_origin(self):
        # d(0, y) == 2 artanh(|y|)
        for y in self._pts(1):
            ref = 2 * math.atanh(np.linalg.norm(y))
            assert abs(geodesic(np.zeros_like(y), y) - ref) < 1e-9

    def test_geodesic_symmetric_and_zero(self):
        pts = self._pts(2)
        for x, y in zip(pts, pts[1:]):
            assert abs(geodesic(x, y) - geodesic(y, x)) < 1e-9
            assert geodesic(x, x) < 1e-9

    def test_exp_log_roundtrip(self):
        # exp_x(log_x(y)) == y  (inverse maps) to machine precision on interior pts
        pts = self._pts(3)
        worst = max(np.linalg.norm(exp_map(x, log_map(x, y)) - y)
                    for x, y in zip(pts, pts[1:]))
        assert worst < 1e-9, worst

    def test_log_norm_is_geodesic(self):
        # the RIEMANNIAN tangent norm lambda_x*|log_x(y)| equals geodesic(x, y)
        pts = self._pts(4)
        worst = max(abs(_conformal(x) * np.linalg.norm(log_map(x, y))
                        - geodesic(x, y))
                    for x, y in zip(pts, pts[1:]))
        assert worst < 1e-8, worst

    def test_mobius_left_cancellation(self):
        # x (+) ((-x) (+) y) == y  on interior points
        pts = self._pts(5)
        worst = max(np.linalg.norm(mobius_add(x, mobius_add(-x, y)) - y)
                    for x, y in zip(pts, pts[1:]))
        assert worst < 1e-9, worst

    def test_frechet_mean_of_identical_points(self):
        p = poincare_embed(fabric(pigeonhole(6)[0]))
        mu = frechet_mean([p, p, p])
        assert np.linalg.norm(mu - p) < 1e-9


class TestEmbeddingGeometry:
    def test_decided_near_centre_cdcl_at_boundary(self):
        # a frame-decided instance sits near the centre; a rigid random one runs
        # out toward the boundary at infinity (a much larger hyperbolic depth)
        php = poincare_embed(fabric(pigeonhole(7)[0]))
        rnd = poincare_embed(fabric(random_ksat(70, round(4.26 * 70), seed=1)[0]))
        c = np.zeros_like(php)
        assert geodesic(c, php) < 1.0
        assert geodesic(c, rnd) > 5.0


class TestFabricModel:
    def test_blob_depths_match_the_manifold(self):
        m = fit_default_model()
        depth = {g.name: g.depth() for g in m.families}
        # decided families near the centre, tunnel out at the boundary
        assert depth["parity"] < 2.0 and depth["counting"] < 2.0
        assert depth["tunnel"] > 5.0

    def test_geodesic_separation_orders_the_fold(self):
        m = fit_default_model()
        sep = m.geodesic_separation()
        # decided<->decided is a small angular hop; decided<->tunnel crosses the fold
        assert sep[("parity", "counting")] < 3.0
        assert sep[("parity", "tunnel")] > 5.0
        assert sep[("counting", "tunnel")] > 5.0

    @pytest.mark.parametrize("gen,expect", [
        (lambda: tseitin(20, 1), "parity"),
        (lambda: random_xorsat(30, 30, 1), "parity"),
        (lambda: pigeonhole(8)[0], "counting"),
        (lambda: random_ksat(70, 300, seed=1)[0], "none"),
    ])
    def test_predict_frame_on_external_families(self, gen, expect):
        assert predict_frame(gen()) == expect

    def test_held_out_accuracy(self):
        m = fit_default_model()
        truth = {
            "parity": lambda s: xor_chain(22, expected_sat=(s % 2 == 0), seed=s)[0],
            "counting": lambda s: pigeonhole(7)[0],
            "tunnel": lambda s: random_ksat(60, round(4.26 * 60), seed=s)[0],
        }
        tot = cor = 0
        for fam, g in truth.items():
            for s in range(300, 308):
                cor += (m.classify(fabric(g(s))) == fam)
                tot += 1
        assert cor / tot >= 0.85            # measured ~0.98; floor well below it

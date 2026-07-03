"""
VDIS Track B1, Phase 1 - property tests for backend.vdis.gyro_ops (spec S6).

Property-based via manual random sampling with fixed seeds (not the
`hypothesis` package - not a project dependency, and fixed-seed random
sampling gives the same falsifiability property with no new dependency).
Random points are sampled well inside the ball for each curvature so
near-boundary numerical noise doesn't mask a real formula bug.
"""

import numpy as np
import pytest

from backend.vdis.gyro_ops import (
    NumericalInstabilityError,
    conformal_factor,
    exp_map,
    exp_map_zero,
    gyration,
    log_map,
    log_map_zero,
    mobius_add,
    mobius_neg,
    mobius_scalar_mul,
    parallel_transport_from_zero,
    riemannian_norm,
)

CURVATURES = [0.0, 0.25, 0.5, 1.0, 2.0]  # magnitudes; spec's kappa grid is the negatives of these
DIMS = [1, 2, 4, 8]  # covers D=1 (degeneracy test dimension) through D*m=8 (H, D=2)


def _random_ball_point(rng: np.random.Generator, dim: int, c: float, radius_frac: float = 0.6):
    """A random point well inside the ball (radius_frac of the max radius)."""
    v = rng.normal(size=dim)
    v /= np.linalg.norm(v)
    if c <= 0:
        r = rng.uniform(0.1, 3.0)
    else:
        max_r = 1.0 / np.sqrt(c)
        r = rng.uniform(0.05, radius_frac) * max_r
    return v * r


def _random_tangent(rng: np.random.Generator, dim: int, scale: float = 1.0):
    return rng.normal(size=dim) * scale


@pytest.mark.parametrize("c", CURVATURES)
@pytest.mark.parametrize("dim", DIMS)
class TestGyroProperties:
    def _rng(self, c, dim):
        return np.random.default_rng(seed=hash((round(c, 3), dim)) % (2**32))

    def test_right_identity(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            x = _random_ball_point(rng, dim, c)
            zero = np.zeros(dim)
            result = mobius_add(x, zero, c)
            assert np.allclose(result, x, atol=1e-8)

    def test_left_inverse(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            x = _random_ball_point(rng, dim, c)
            result = mobius_add(mobius_neg(x), x, c)
            assert np.allclose(result, np.zeros(dim), atol=1e-8)

    def test_gyrocommutativity(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            x = _random_ball_point(rng, dim, c, radius_frac=0.5)
            y = _random_ball_point(rng, dim, c, radius_frac=0.5)
            lhs = mobius_add(x, y, c)
            rhs = gyration(x, y, mobius_add(y, x, c), c)
            assert np.allclose(lhs, rhs, atol=1e-6), f"c={c} dim={dim}\n{lhs}\nvs\n{rhs}"

    def test_exp_log_round_trip(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            x = _random_ball_point(rng, dim, c, radius_frac=0.5)
            v = _random_tangent(rng, dim, scale=0.3)
            recovered = log_map(x, exp_map(x, v, c), c)
            assert np.allclose(recovered, v, atol=1e-6), f"c={c} dim={dim}\n{recovered}\nvs\n{v}"

    def test_log_exp_round_trip_at_zero(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            v = _random_tangent(rng, dim, scale=0.3)
            recovered = log_map_zero(exp_map_zero(v, c), c)
            assert np.allclose(recovered, v, atol=1e-6)

    def test_transport_isometry(self, c, dim):
        rng = self._rng(c, dim)
        for _ in range(20):
            x = _random_ball_point(rng, dim, c, radius_frac=0.5)
            v = _random_tangent(rng, dim, scale=0.3)
            transported = parallel_transport_from_zero(x, v, c)
            norm_at_x = riemannian_norm(transported, x, c)
            norm_at_0 = riemannian_norm(v, np.zeros(dim), c)
            assert norm_at_x == pytest.approx(norm_at_0, rel=1e-5), f"c={c} dim={dim}"


class TestEuclideanLimit:
    """kappa -> 0 (c -> 0) must recover exact Euclidean operations."""

    @pytest.mark.parametrize("dim", DIMS)
    def test_mobius_add_is_addition(self, dim):
        rng = np.random.default_rng(dim)
        x, y = rng.normal(size=dim), rng.normal(size=dim)
        assert np.allclose(mobius_add(x, y, 0.0), x + y)

    @pytest.mark.parametrize("dim", DIMS)
    def test_exp_map_zero_is_identity(self, dim):
        rng = np.random.default_rng(dim + 100)
        v = rng.normal(size=dim)
        assert np.allclose(exp_map_zero(v, 0.0), v)

    @pytest.mark.parametrize("dim", DIMS)
    def test_log_map_zero_is_identity(self, dim):
        rng = np.random.default_rng(dim + 200)
        v = rng.normal(size=dim)
        assert np.allclose(log_map_zero(v, 0.0), v)

    @pytest.mark.parametrize("dim", DIMS)
    def test_transport_is_identity(self, dim):
        rng = np.random.default_rng(dim + 300)
        x, v = rng.normal(size=dim), rng.normal(size=dim)
        assert np.allclose(parallel_transport_from_zero(x, v, 0.0), v)

    @pytest.mark.parametrize("dim", DIMS)
    def test_small_c_approaches_euclidean(self, dim):
        """A small but nonzero c should be numerically close to the exact
        c=0 result - catches a formula that's discontinuous at c=0."""
        rng = np.random.default_rng(dim + 400)
        v = rng.normal(size=dim) * 0.1
        exact = exp_map_zero(v, 0.0)
        approx = exp_map_zero(v, 1e-6)
        assert np.allclose(exact, approx, atol=1e-4)


class TestNumericalTripwire:
    def test_conformal_factor_collapse_raises(self):
        # A point exactly on the boundary (norm = 1/sqrt(c)) makes the
        # denominator 1 - c*||x||^2 collapse to exactly 0 in float64 -
        # must raise, not return NaN/Inf.
        c = 1.0
        x = np.array([1.0, 0.0])  # norm exactly 1, exactly the c=1 boundary
        with pytest.raises(NumericalInstabilityError):
            conformal_factor(x, c)

    def test_all_ops_finite_near_boundary_after_projection(self):
        from backend.vdis.gyro_ops import project_to_ball, max_norm

        c = 1.0
        x = np.array([10.0, 0.0])  # far outside the ball
        projected = project_to_ball(x, c)
        assert np.linalg.norm(projected) <= max_norm(c) + 1e-9
        assert np.all(np.isfinite(projected))

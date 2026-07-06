"""
VDIS Track B1, Phase 1 — closed-form Mobius gyrovector operations on the
Poincare ball (Ungar's gyrovector spaces; formulas as used in Ganea,
Becigneul & Hofmann, "Hyperbolic Neural Networks", NeurIPS 2018).
Reimplemented directly in numpy - no geoopt dependency (spec ruling).

Convention note: the pinned spec (docs/vdis/ agent instructions, S3)
writes the curvature as kappa < 0. This module instead takes a curvature
MAGNITUDE `c = -kappa >= 0` throughout (c=0 is the Euclidean limit,
c>0 gives the standard Ganea et al. formulas over a ball of radius
1/sqrt(c)), because that is the convention the closed-form formulas
below are stated in, and mixing sign conventions inside the
implementation is exactly the kind of thing that produces a silent,
hard-to-catch bug. All properties in S6 are property-tested against
this convention (test_gyro_ops.py) rather than assumed correct from
the derivation.

Points and tangent vectors are plain numpy float64 arrays of shape (n,)
for a real n-dimensional representation (n = D * m, D = per-literal
dimension, m = dim_R(algebra) - the algebra structure itself is not
used by these operations, which only need the ambient real inner
product; the algebra determines n and, in Phase 2, the extra
rotor/bivector operations on top of this).
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-5
_NUM_EPS = 1e-15


class NumericalInstabilityError(RuntimeError):
    """Raised when an operation would produce NaN/Inf - the S6 tripwire.
    Callers should treat this as a hard stop, not something to catch and
    continue past silently."""


def _check_finite(x: np.ndarray, where: str) -> np.ndarray:
    if not np.all(np.isfinite(x)):
        raise NumericalInstabilityError(f"non-finite value produced in {where}: {x}")
    return x


def max_norm(c: float) -> float:
    """Ball radius for curvature magnitude c (unbounded for c=0)."""
    if c <= 0:
        return float("inf")
    return 1.0 / np.sqrt(c) - _EPS


def project_to_ball(x: np.ndarray, c: float) -> np.ndarray:
    """Clamp a point to stay strictly inside the ball (S6 numerics requirement)."""
    if c <= 0:
        return x
    r = max_norm(c)
    norm = np.linalg.norm(x)
    if norm > r:
        return x * (r / norm)
    return x


def conformal_factor(x: np.ndarray, c: float) -> float:
    """lambda_x^c = 2 / (1 - c * ||x||^2)."""
    if c <= 0:
        return 2.0
    denom = 1.0 - c * float(np.dot(x, x))
    if denom <= _NUM_EPS:
        raise NumericalInstabilityError(f"conformal factor denominator collapsed: {denom}")
    return 2.0 / denom


def mobius_add(x: np.ndarray, y: np.ndarray, c: float) -> np.ndarray:
    """x (+)_c y - Mobius addition. Exact Euclidean x+y at c=0."""
    if c <= 0:
        return _check_finite(x + y, "mobius_add(c=0)")
    xy = float(np.dot(x, y))
    xx = float(np.dot(x, x))
    yy = float(np.dot(y, y))
    num = (1.0 + 2.0 * c * xy + c * yy) * x + (1.0 - c * xx) * y
    denom = 1.0 + 2.0 * c * xy + (c ** 2) * xx * yy
    if abs(denom) < _NUM_EPS:
        raise NumericalInstabilityError(f"mobius_add denominator collapsed: {denom}")
    return _check_finite(num / denom, "mobius_add")


def mobius_neg(x: np.ndarray) -> np.ndarray:
    """(-)x - the gyrogroup inverse; x (+)_c (-x) = 0 for any c."""
    return -x


def mobius_scalar_mul(r: float, x: np.ndarray, c: float) -> np.ndarray:
    """r (x)_c x - Mobius scalar multiplication. Exact r*x at c=0.

    This is the S3.3 "decay" operation: t <- gamma (x)_c t.
    """
    if c <= 0:
        return _check_finite(r * x, "mobius_scalar_mul(c=0)")
    norm = np.linalg.norm(x)
    if norm < _NUM_EPS:
        return np.zeros_like(x)
    sqrt_c = np.sqrt(c)
    scaled = np.tanh(r * np.arctanh(np.clip(sqrt_c * norm, -1 + _NUM_EPS, 1 - _NUM_EPS))) / sqrt_c
    return _check_finite(scaled * x / norm, "mobius_scalar_mul")


def gyration(x: np.ndarray, y: np.ndarray, v: np.ndarray, c: float) -> np.ndarray:
    """gyr[x, y]v, computed via its defining identity
        x (+)_c (y (+)_c v) = (x (+)_c y) (+)_c gyr[x,y]v
    i.e. gyr[x,y]v = (-)(x (+)_c y) (+)_c (x (+)_c (y (+)_c v)).

    Three Mobius additions rather than the single-shot closed form: slower,
    but its correctness reduces directly to mobius_add's correctness
    instead of requiring an independently-verified closed-form expression -
    deliberate choice given how easy this class of formula is to mistype.
    """
    if c <= 0:
        return _check_finite(v.copy(), "gyration(c=0)")
    lhs_inner = mobius_add(x, mobius_add(y, v, c), c)
    xy = mobius_add(x, y, c)
    return mobius_add(mobius_neg(xy), lhs_inner, c)


def exp_map(x: np.ndarray, v: np.ndarray, c: float) -> np.ndarray:
    """exp_x^c(v): Riemannian exponential map at x. Exact x+v at c=0."""
    if c <= 0:
        return _check_finite(x + v, "exp_map(c=0)")
    norm_v = np.linalg.norm(v)
    if norm_v < _NUM_EPS:
        return x.copy()
    lam_x = conformal_factor(x, c)
    sqrt_c = np.sqrt(c)
    second = np.tanh(sqrt_c * lam_x * norm_v / 2.0) * v / (sqrt_c * norm_v)
    return project_to_ball(_check_finite(mobius_add(x, second, c), "exp_map"), c)


def log_map(x: np.ndarray, y: np.ndarray, c: float) -> np.ndarray:
    """log_x^c(y): Riemannian logarithmic map at x (inverse of exp_map(x, ., c)).
    Exact y-x at c=0."""
    if c <= 0:
        return _check_finite(y - x, "log_map(c=0)")
    diff = mobius_add(mobius_neg(x), y, c)
    norm_diff = np.linalg.norm(diff)
    if norm_diff < _NUM_EPS:
        return np.zeros_like(x)
    lam_x = conformal_factor(x, c)
    sqrt_c = np.sqrt(c)
    coeff = (2.0 / (sqrt_c * lam_x)) * np.arctanh(np.clip(sqrt_c * norm_diff, -1 + _NUM_EPS, 1 - _NUM_EPS))
    return _check_finite(coeff * diff / norm_diff, "log_map")


def exp_map_zero(v: np.ndarray, c: float) -> np.ndarray:
    """exp_0^c(v), specialised (x=0 identically, not just numerically)."""
    if c <= 0:
        return _check_finite(v.copy(), "exp_map_zero(c=0)")
    norm_v = np.linalg.norm(v)
    if norm_v < _NUM_EPS:
        return np.zeros_like(v)
    sqrt_c = np.sqrt(c)
    scale = np.tanh(sqrt_c * norm_v) / (sqrt_c * norm_v)
    return project_to_ball(_check_finite(scale * v, "exp_map_zero"), c)


def log_map_zero(y: np.ndarray, c: float) -> np.ndarray:
    """log_0^c(y), specialised."""
    if c <= 0:
        return _check_finite(y.copy(), "log_map_zero(c=0)")
    norm_y = np.linalg.norm(y)
    if norm_y < _NUM_EPS:
        return np.zeros_like(y)
    sqrt_c = np.sqrt(c)
    scale = np.arctanh(np.clip(sqrt_c * norm_y, -1 + _NUM_EPS, 1 - _NUM_EPS)) / sqrt_c
    return _check_finite(scale * y / norm_y, "log_map_zero")


def parallel_transport_from_zero(x: np.ndarray, v: np.ndarray, c: float) -> np.ndarray:
    """PT_{0 -> x}^c(v) = (lambda_0^c / lambda_x^c) * gyr[x, 0]v.

    gyr[x, 0] = identity is a standard gyrogroup identity (gyration
    against the group identity element is trivial), so this reduces to
    a pure scaling by (2 / lambda_x^c) = (1 - c*||x||^2). Implemented via
    the general formula (not the reduced one) so a bug in the gyr[x,0]=id
    assumption would still be caught by the transport-isometry property
    test rather than silently assumed away.
    """
    if c <= 0:
        return _check_finite(v.copy(), "parallel_transport(c=0)")
    lam_0 = conformal_factor(np.zeros_like(x), c)
    lam_x = conformal_factor(x, c)
    gyr = gyration(x, np.zeros_like(x), v, c)
    return _check_finite((lam_0 / lam_x) * gyr, "parallel_transport")


def riemannian_norm(v: np.ndarray, x: np.ndarray, c: float) -> float:
    """||v||_x = lambda_x^c * ||v||_Euclidean (the Poincare-ball metric)."""
    return conformal_factor(x, c) * float(np.linalg.norm(v))

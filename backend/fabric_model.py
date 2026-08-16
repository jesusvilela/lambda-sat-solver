"""fabric_model -- the family distributions modelled parametrically on the fabric,
in the HYPERBOLIC geometry the fabric already lives in (not a flat Gaussian cloud).

The fabric's `gyration` thread IS a hyperbolic depth: `hyperbolic_depth = artanh(r)`
(backend/orbifold.py), so an instance already has a Poincare-ball radius -- decided/
symmetric instances sit near the CENTER, rigid/frame-void (CDCL) instances run out
toward the boundary at infinity ∂∞ (the "holographic screen of hardness"), an
INFINITE hyperbolic distance away, not a bounded Euclidean one. Modelling the
families as flat Euclidean Gaussians would throw exactly this curvature away.

So each instance is embedded as a POINT in the Poincare ball B^d:

    radius     r = tanh(gyration)            (its hyperbolic depth; ->1 at ∂∞)
    direction  u = unit(quality threads)     (WHICH boundary it heads toward:
               [orbit, counting, rank-deficiency, implication, generic])
    point      x = r * u

and each family is a wrapped-normal blob on the ball: a Frechet (Karcher) mean μ
computed with the gyrovector exp/log maps, and a covariance in the tangent space at
μ measured in the Riemannian (geodesic) metric. A new instance is classified by its
tangent-space Mahalanobis distance -- the hyperbolic geodesic distance to each blob,
shaped by that blob's anisotropy. The radial axis (depth toward ∂∞) is the primary
separator of "a frame decides it" from "CDCL territory"; the angular axes separate
parity from counting among the decided. This is the "n cosmo / n manifold
distributional ledger" as a fitted density on a curved manifold.

Charter: the model is a PREDICTOR, never a decider. It says "try parity first"; it
never says UNSAT. Soundness lives in the frames it points at; a mis-prediction costs
a little trial order, never a wrong verdict. Deterministic: `fit_default_model()`
trains on a fixed generator set with fixed seeds.

The Poincare-ball primitives below are property-tested in tests/test_fabric_model.py
(exp∘log round-trip, |log|_riem == geodesic distance) to ~1e-14 on interior points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Dict, List, Sequence, Tuple

import numpy as np

from .cnf_utils import CNFFormula
from .fabric import Fabric, fabric

_EPS = 1e-12
_RMAX = 1.0 - 1e-6            # keep every embedded point strictly inside the ball

# The quality threads that set an instance's DIRECTION in the ball (which region of
# ∂∞ it heads toward). `_GENERIC` is a constant baseline axis so a structureless
# instance (all qualities ~0) points along a dedicated "tunnel/generic" direction
# instead of being undefined; structured instances tilt off it toward their quality.
QUALITY_THREADS: Tuple[str, ...] = (
    "orbit_coarseness", "counting_signal", "parity_signal", "implication_signal",
)
_GENERIC = 0.15


# --------------------------------------------------------------------------
# Poincare-ball (gyrovector) primitives, curvature -1. Verified in tests.
# --------------------------------------------------------------------------
def _project(x: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(x))
    return x * (_RMAX / n) if n >= _RMAX else x


def mobius_add(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Gyrovector (Mobius) addition on the ball -- the curved analogue of +."""
    xy = float(x @ y); xx = float(x @ x); yy = float(y @ y)
    num = (1 + 2 * xy + yy) * x + (1 - xx) * y
    den = 1 + 2 * xy + xx * yy
    return num / (den if abs(den) > _EPS else _EPS)


def geodesic(x: np.ndarray, y: np.ndarray) -> float:
    """Hyperbolic geodesic distance -- diverges as either point approaches ∂∞."""
    diff = x - y
    arg = 1 + 2 * float(diff @ diff) / max((1 - float(x @ x)) * (1 - float(y @y)),
                                           _EPS)
    return float(np.arccosh(max(arg, 1.0)))


def log_map(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Tangent vector at x pointing to y (Euclidean representative; its Riemannian
    norm λ_x·|·| equals geodesic(x, y))."""
    a = mobius_add(-x, y)
    na = float(np.linalg.norm(a))
    if na < _EPS:
        return np.zeros_like(x)
    return (1 - float(x @ x)) * math.atanh(min(na, 1 - _EPS)) * a / na


def exp_map(x: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Move from x along tangent v to a new ball point (inverse of log_map)."""
    nv = float(np.linalg.norm(v))
    if nv < _EPS:
        return x
    lam = 2.0 / max(1 - float(x @ x), _EPS)
    return _project(mobius_add(x, math.tanh(lam * nv / 2) * v / nv))


def _conformal(x: np.ndarray) -> float:
    return 2.0 / max(1 - float(x @ x), _EPS)


def frechet_mean(points: Sequence[np.ndarray], iters: int = 64,
                 tol: float = 1e-10) -> np.ndarray:
    """The Karcher mean on the ball: the point minimizing summed squared geodesic
    distance, found by Riemannian gradient descent with the gyrovector maps."""
    mu = _project(np.mean(points, axis=0))          # Euclidean init inside the ball
    for _ in range(iters):
        g = np.mean([log_map(mu, p) for p in points], axis=0)
        mu = exp_map(mu, g)
        if float(np.linalg.norm(g)) < tol:
            break
    return mu


# --------------------------------------------------------------------------
# Embedding a fabric into the ball
# --------------------------------------------------------------------------
def poincare_embed(fb: Fabric) -> np.ndarray:
    """Place an instance in the Poincare ball B^5: radius = its hyperbolic depth
    (tanh(gyration), ->1 at the rigid boundary ∂∞), direction = the unit vector of
    its quality threads (with a generic baseline axis)."""
    r = min(math.tanh(fb.gyration), _RMAX)
    q = np.array([getattr(fb, t) for t in QUALITY_THREADS] + [_GENERIC], dtype=float)
    n = float(np.linalg.norm(q))
    u = q / n if n > _EPS else np.eye(len(q))[-1]
    return r * u


# --------------------------------------------------------------------------
# A family as a wrapped-normal blob on the ball
# --------------------------------------------------------------------------
@dataclass
class HyperbolicFamily:
    name: str
    frame: str                 # the frame this region routes to
    mean: np.ndarray           # Frechet mean on the ball
    cov_inv: np.ndarray        # inverse tangent covariance (the blob's metric)
    logdet: float
    log_prior: float
    n: int

    def _tangent(self, x: np.ndarray) -> np.ndarray:
        """Scaled tangent coordinate of x at the mean: |·| = geodesic(mean, x)."""
        return _conformal(self.mean) * log_map(self.mean, x)

    def log_density(self, x: np.ndarray) -> float:
        t = self._tangent(x)
        maha = float(t @ self.cov_inv @ t)
        return -0.5 * (maha + self.logdet) + self.log_prior

    def mahalanobis(self, x: np.ndarray) -> float:
        t = self._tangent(x)
        return math.sqrt(max(float(t @ self.cov_inv @ t), 0.0))

    def depth(self) -> float:
        """Hyperbolic depth of the blob's centre (distance from the ball centre)."""
        return geodesic(np.zeros_like(self.mean), self.mean)


@dataclass
class FabricModel:
    """A fitted density over the hyperbolic fabric-manifold: one blob per family."""
    families: List[HyperbolicFamily]
    dim: int = field(default=len(QUALITY_THREADS) + 1)

    def embed(self, fb: Fabric) -> np.ndarray:
        return poincare_embed(fb)

    def log_likelihoods(self, fb: Fabric) -> Dict[str, float]:
        x = self.embed(fb)
        return {g.name: g.log_density(x) for g in self.families}

    def classify(self, fb: Fabric) -> str:
        ll = self.log_likelihoods(fb)
        return max(ll, key=ll.get)

    def predict_frame(self, fb: Fabric) -> str:
        name = self.classify(fb)
        return next(g.frame for g in self.families if g.name == name)

    def mahalanobis(self, fb: Fabric) -> Dict[str, float]:
        x = self.embed(fb)
        return {g.name: g.mahalanobis(x) for g in self.families}

    def geodesic_separation(self) -> Dict[Tuple[str, str], float]:
        """Pure hyperbolic geodesic distance between family centres -- how far apart
        the blobs sit on the curved manifold (a measured property, no covariance)."""
        out: Dict[Tuple[str, str], float] = {}
        for i, a in enumerate(self.families):
            for b in self.families[i + 1:]:
                out[(a.name, b.name)] = geodesic(a.mean, b.mean)
        return out


def fit(samples: Dict[str, Tuple[str, Sequence[Fabric]]],
        shrinkage: float = 0.35, ridge: float = 1e-3) -> FabricModel:
    """Fit one wrapped-normal blob per family. Covariances are computed in the
    tangent space at each family's Frechet mean (in the Riemannian metric), shrunk
    toward their diagonal and ridged -- several quality threads are near-constant
    within a family (e.g. rank-deficiency ~0 for a determined parity system), so a
    raw tangent covariance from few samples would be singular. Shrinkage keeps every
    blob a proper, invertible metric without inventing covariance the data lacks."""
    dim = len(QUALITY_THREADS) + 1
    total = sum(len(fbs) for _, (_f, fbs) in samples.items())
    fams: List[HyperbolicFamily] = []
    for name, (frame, fbs) in samples.items():
        pts = [poincare_embed(fb) for fb in fbs]
        mu = frechet_mean(pts) if len(pts) > 1 else _project(pts[0])
        lam = _conformal(mu)
        T = np.array([lam * log_map(mu, p) for p in pts])   # scaled tangents
        S = np.cov(T.T) if len(T) > 1 else np.eye(dim)
        S = np.atleast_2d(S)
        S = (1 - shrinkage) * S + shrinkage * np.diag(np.diag(S)) + ridge * np.eye(dim)
        cov_inv = np.linalg.inv(S)
        _sign, logdet = np.linalg.slogdet(S)
        fams.append(HyperbolicFamily(
            name=name, frame=frame, mean=mu, cov_inv=cov_inv,
            logdet=float(logdet), log_prior=math.log(len(fbs) / total), n=len(fbs)))
    return FabricModel(fams, dim)


# --------------------------------------------------------------------------
# A deterministic default training set, drawn entirely from backend.eval
# generators (no dependency on the docs/ladder scripts).
# --------------------------------------------------------------------------
def _default_generators() -> Dict[str, Tuple[str, Callable[[int], CNFFormula]]]:
    from .eval.generators import (
        mutilated_chessboard, pigeonhole, random_ksat, xor_chain,
    )
    return {
        "parity": ("parity", lambda s: xor_chain(18 + (s % 6) * 2,
                                                  expected_sat=(s % 2 == 0),
                                                  seed=s)[0]),
        "counting": ("counting", lambda s: (pigeonhole(6 + s % 4)[0] if s % 2 == 0
                                             else mutilated_chessboard(4 + s % 3)[0])),
        "tunnel": ("none", lambda s: random_ksat(60 + 10 * (s % 4),
                                                  round(4.26 * (60 + 10 * (s % 4))),
                                                  k=3, seed=s)[0]),
    }


def default_samples(trials: int = 10) -> Dict[str, Tuple[str, List[Fabric]]]:
    gens = _default_generators()
    return {name: (frame, [fabric(gen(s)) for s in range(trials)])
            for name, (frame, gen) in gens.items()}


@lru_cache(maxsize=1)
def fit_default_model() -> FabricModel:
    """The reproducible default model: parity / counting / tunnel blobs on the ball,
    fit from a fixed generator set with fixed seeds. Cached -- fit once per process."""
    return fit(default_samples())


def predict_frame(formula: CNFFormula) -> str:
    """Cheap hyperbolic-fabric prediction of the solving frame -- a router PRIOR from
    the instance's place on the manifold, not a verdict."""
    return fit_default_model().predict_frame(fabric(formula))

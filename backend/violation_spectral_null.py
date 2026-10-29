"""Centered finite parity incidence and signed-triangle diagnostics.

Not Kakeya geometry, not a SAT hardness invariant, and never a verdict.
Drop constant-on-sample check rows before computing Pearson correlations.
This removes the trivial shared ~1/2 acceptance background of random checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

import numpy as np

from .violation_geometry import _check_rows, parity_accepts


@dataclass(frozen=True)
class CenteredOverlap:
    sampled_nonmodels: int
    variable_checks: int
    largest_eigenvalue_per_check: float
    mean_absolute_correlation: float
    signed_triangle_frustration: float
    triangle_mass: float


def _correlations(bit_vectors: Sequence[Sequence[int]]) -> np.ndarray:
    """Pearson matrix of rows; constant rows must be removed by caller.

    Gauge action b_i -> 1-b_i flips c_ij for every j!=i, so the sign
    of c_ij*c_jk*c_ki is invariant under all independent row flips.
    """
    b = np.asarray(bit_vectors, dtype=np.float64)
    if b.ndim != 2 or b.shape[1] < 1:
        raise ValueError("expected a rectangular matrix with at least one column")
    means = b.mean(axis=1, keepdims=True)
    std = b.std(axis=1, keepdims=True)
    if np.any(std < 1e-12):
        raise ValueError("constant observation rows cannot be centered")
    x = (b - means) / std
    cov = (x @ x.T) / b.shape[1]
    return np.clip((cov + cov.T) / 2.0, -1.0, 1.0)


def _triangle_stats(corr: np.ndarray, *, threshold: float = 0.10) -> tuple[float, float]:
    """Weighted negative signed triangles / all substantial triangle mass.

    This is a *signed cycle statistic*, not the minimum frustrated-edge
    deletion number and not automatically a CNF contradiction certificate.
    """
    k = len(corr)
    negative = 0.0
    total = 0.0
    for i, j, k3 in combinations(range(k), 3):
        a, b, c = float(corr[i, j]), float(corr[j, k3]), float(corr[k3, i])
        if min(abs(a), abs(b), abs(c)) < threshold:
            continue
        product = a * b * c
        total += abs(product)
        if product < 0:
            negative += abs(product)
    return (negative / total if total else 0.0, total)


def centered_incidence(masks: Sequence[int], rows: Sequence[int],
                       clause_count: int, *, threshold: float = 0.10) -> CenteredOverlap:
    """Standardized row covariance on finite NON-model sampled signatures.

    For N nonmodels, b_{ix} = 1 if row i accepts signature x, and
    C_ij = E[(b_i-p_i)(b_j-p_j)]/sqrt(p_i(1-p_i)p_j(1-p_j)).
    Constant rows are excluded; |rows|<=64, N<=4096.
    """
    _check_rows(rows, clause_count)
    if len(rows) > 64 or len(masks) > 4096:
        raise ValueError("bounded experimental incidence budget exceeded")
    if not 0 <= threshold < 1:
        raise ValueError("threshold must lie in [0,1)")
    if any(not isinstance(v, int) or v < 0 or v >= (1 << clause_count)
           for v in masks):
        raise ValueError("invalid violation masks")
    nonmodels = [v for v in masks if v]
    n = len(nonmodels)
    observations = []
    for row in rows:
        bits = [int(parity_accepts(v, row)) for v in nonmodels]
        if 0 < sum(bits) < n:
            observations.append(bits)
    k = len(observations)
    if k == 0:
        return CenteredOverlap(n, 0, 0.0, 0.0, 0.0, 0.0)
    corr = _correlations(observations)
    top = float(np.linalg.eigvalsh(corr)[-1]) / k
    pairs = [abs(float(corr[i, j])) for i in range(k) for j in range(i+1, k)]
    f, mass = _triangle_stats(corr, threshold=threshold)
    return CenteredOverlap(n, k, top, sum(pairs) / len(pairs) if pairs else 0.0, f, mass)

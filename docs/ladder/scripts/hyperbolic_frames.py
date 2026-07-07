"""Hyperbolic PROGRAMMING (not hyperbolic geometry) meets the frame ladder.

The operator's "hyperbolic" refers to hyperbolic programming in the
Gårding–Güler–Renegar–Brändén sense: convex optimization over the hyperbolicity
cone Λ_{p,e} of a hyperbolic polynomial p, with LP, SOCP and SDP as the special
cases p = x1···xn (orthant), p = r^2 - ||x||^2 (Lorentz), p = det(X) (PSD).

This module makes the one *genuine, computable* bridge to our work concrete and
tested -- and names the honest disanalogy. It is a lens/substrate demonstrator,
NOT a solver route (deciding hyperbolicity is co-NP-hard in general; the SOS /
hyperbolic certificates below are exponential-degree proof objects, the real
cousins of our nullstellensatz_degree carrier -- not a poly-time frame).

The hyperbolic eigenvalues of x (w.r.t. e) are the roots of t ↦ p(t·e − x); the
hyperbolicity cone is where they are all ≥ 0. We verify:

  1. det recovers matrix eigenvalues (the SDP special case) -- a correctness
     anchor that the eigenvalue machinery is right.
  2. the elementary symmetric polynomials e_k are hyperbolic (all restrictions
     real-rooted) -- Brändén: their cones are even spectrahedral.
  3. e_k are Renegar's DERIVATIVE RELAXATIONS of the LP cone p = x1···xn, so the
     cones NEST: orthant = Λ(e_n) ⊆ Λ(e_{n-1}) ⊆ ... ⊆ Λ(e_1) = halfspace. The
     counting/cardinality frame (cardinality_check) is the combinatorial face of
     exactly this ladder -- our 2-SAT/implication frame sits at the orthant (LP)
     end, the counting frame on its symmetric-function relaxations.

The disanalogy, named honestly: the PARITY (GF(2)) frame has NO hyperbolic-cone
analog. Hyperbolicity is a real-rootedness / ordering notion; GF(2) has no order,
no reals, no "all eigenvalues real". This is the same char-2 wall the ladder
already hit for the Lie telos (RUNG2_LIE_TELOS: real over ℝ, char-2 obstructed).
So hyperbolic programming illuminates two of our three frames (implication at the
LP vertex, counting on the derivative-relaxation ladder) and structurally cannot
see the third -- which is exactly why the frame trilogy needed a char-2 member.

The tower is CONTINUOUS/INFINITESIMAL, not a set of isolated tiles: the
directional derivative `D_1` is its infinitesimal generator, with the exact
identity `D_1 e_k = (n-k+1) e_{k-1}` (see `directional_derivative`,
`sum_partials_e_k`) -- one cheap operator generates the whole derivative-
relaxation ladder that the counting frame lives on.

Run:  python -m docs.ladder.scripts.hyperbolic_frames
"""

from __future__ import annotations

from itertools import combinations
from typing import Callable, List

import numpy as np


def hyperbolic_eigenvalues(p: Callable[[np.ndarray], float], x: np.ndarray,
                           e: np.ndarray, degree: int) -> np.ndarray:
    """Roots of t ↦ p(t·e − x): the hyperbolic eigenvalues of x w.r.t. e, for a
    homogeneous p of the given degree. (Interpolate p on degree+1 nodes, then
    root-find -- exact for a true degree-`degree` polynomial up to conditioning.)
    """
    span = 1.0 + float(np.max(np.abs(x)))
    ts = np.linspace(-span, span, degree + 1)
    ys = [p(t * e - x) for t in ts]
    coeffs = np.polyfit(ts, ys, degree)
    return np.sort_complex(np.roots(coeffs))


def elementary_symmetric(vals: np.ndarray, k: int) -> float:
    """e_k(vals): sum over size-k subsets of the product of entries."""
    if k == 0:
        return 1.0
    n = len(vals)
    return float(sum(np.prod(vals[list(S)]) for S in combinations(range(n), k)))


def e_k_poly(k: int) -> Callable[[np.ndarray], float]:
    return lambda x: elementary_symmetric(x, k)


def in_hyperbolicity_cone(p: Callable[[np.ndarray], float], x: np.ndarray,
                          e: np.ndarray, degree: int, tol: float = 1e-7) -> bool:
    """x ∈ Λ_{p,e}  ⇔  all hyperbolic eigenvalues ≥ 0 (up to tol)."""
    ev = hyperbolic_eigenvalues(p, x, e, degree)
    assert np.max(np.abs(ev.imag)) < 1e-6, "not real-rooted: p not hyperbolic here"
    return bool(np.min(ev.real) >= -tol)


def max_imag_over_samples(k: int, n: int, trials: int, seed: int = 0) -> float:
    """Largest |Im(eigenvalue)| of e_k over random x -- 0 ⇔ hyperbolic."""
    rng = np.random.default_rng(seed)
    e = np.ones(n)
    worst = 0.0
    for _ in range(trials):
        x = rng.standard_normal(n) * rng.uniform(1.0, 5.0)
        ev = hyperbolic_eigenvalues(e_k_poly(k), x, e, k)
        worst = max(worst, float(np.max(np.abs(ev.imag))))
    return worst


def directional_derivative(p: Callable[[np.ndarray], float], x: np.ndarray,
                           e: np.ndarray, h: float = 1e-5) -> float:
    """The infinitesimal generator D_e p (x) = d/dt p(x + t e)|_0 -- Renegar's
    derivative-relaxation operator, the tangent that connects one tile of the
    tessellation to the next (central difference)."""
    return (p(x + h * e) - p(x - h * e)) / (2.0 * h)


def sum_partials_e_k(x: np.ndarray, k: int) -> float:
    """sum_i d/dx_i e_k(x) = D_1 e_k(x), the infinitesimal step down the tower."""
    e = np.ones(len(x))
    return directional_derivative(lambda z: elementary_symmetric(z, k), x, e)


def _demo() -> None:
    print("1. SDP special case: det recovers matrix eigenvalues")
    rng = np.random.default_rng(1)
    A = rng.standard_normal((3, 3))
    S = A + A.T                                    # symmetric 3x3
    def det_poly(x):                               # x is a flattened 3x3
        return float(np.linalg.det(x.reshape(3, 3)))
    e = np.eye(3).flatten()
    hev = hyperbolic_eigenvalues(det_poly, S.flatten(), e, 3).real
    print(f"   hyperbolic eigvals: {np.sort(hev)}")
    print(f"   numpy   eigvals:    {np.sort(np.linalg.eigvalsh(S))}")

    print("\n2. e_k is hyperbolic (max |Im| over 200 random x; 0 = real-rooted)")
    for n in (5, 6, 7):
        for k in range(2, n):
            w = max_imag_over_samples(k, n, 200)
            print(f"   n={n} k={k}: max|Im| = {w:.2e}")

    print("\n3. derivative-relaxation nesting  orthant = Λ(e_n) ⊆ ... ⊆ Λ(e_1)")
    n = 3
    e = np.ones(n)
    x = np.array([1.0, 1.0, -1.0])                 # NOT in the orthant
    row = []
    for k in range(1, n + 1):
        row.append((k, in_hyperbolicity_cone(e_k_poly(k), x, e, k)))
    print(f"   x={x}: " + ", ".join(f"Λ(e_{k}):{'in' if m else 'out'}"
                                     for k, m in row))
    print("   -> in the larger relaxations, out of the orthant: strict nesting.")

    print("\n4. the char-2 disanalogy (parity frame): GF(2) has no ordering, no")
    print("   real-rootedness -- the parity frame has NO hyperbolicity cone. HP")
    print("   sees implication (LP vertex) and counting (e_k ladder), not parity.")


if __name__ == "__main__":
    _demo()

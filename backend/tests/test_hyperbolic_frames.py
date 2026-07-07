"""Tests for the hyperbolic-programming demonstrator (docs/ladder/scripts).

Pins the three computable claims that ground the HP<->frame-ladder bridge: the
SDP special case (det = matrix eigenvalues), the hyperbolicity of the elementary
symmetric polynomials, and the derivative-relaxation nesting the counting frame
lives on. This is a lens/substrate demonstrator, not a solver path.
"""

import numpy as np

from docs.ladder.scripts.hyperbolic_frames import (
    e_k_poly,
    elementary_symmetric,
    hyperbolic_eigenvalues,
    in_hyperbolicity_cone,
    max_imag_over_samples,
    sum_partials_e_k,
)


class TestHyperbolicFrames:
    def test_det_recovers_matrix_eigenvalues(self):
        # SDP special case p = det(X): hyperbolic eigenvalues of a symmetric X
        # w.r.t. e = I are exactly the matrix eigenvalues.
        rng = np.random.default_rng(1)
        A = rng.standard_normal((3, 3))
        S = A + A.T
        hev = np.sort(hyperbolic_eigenvalues(
            lambda x: float(np.linalg.det(x.reshape(3, 3))),
            S.flatten(), np.eye(3).flatten(), 3).real)
        assert np.allclose(hev, np.sort(np.linalg.eigvalsh(S)), atol=1e-6)

    def test_elementary_symmetric_are_hyperbolic(self):
        # every restriction of e_k is real-rooted -> e_k hyperbolic w.r.t. 1
        for n in (5, 6, 7):
            for k in range(2, n):
                assert max_imag_over_samples(k, n, 100) < 1e-6

    def test_derivative_relaxation_nesting_is_strict(self):
        # orthant = Λ(e_n) ⊆ ... ⊆ Λ(e_1): a point in the e_1 halfspace but not
        # the orthant witnesses strict nesting (the counting frame's ladder).
        n = 3
        e = np.ones(n)
        x = np.array([1.0, 1.0, -1.0])            # sum 1 >= 0, but has a negative
        assert in_hyperbolicity_cone(e_k_poly(1), x, e, 1)        # halfspace: in
        assert not in_hyperbolicity_cone(e_k_poly(n), x, e, n)    # orthant: out

    def test_infinitesimal_generator_of_the_tower(self):
        # D_1 e_k = (n-k+1) e_{k-1}: the derivative operator is the infinitesimal
        # generator connecting one tile of the tessellation to the next.
        rng = np.random.default_rng(0)
        for n in (4, 5, 6):
            for k in range(1, n):
                for _ in range(20):
                    x = rng.standard_normal(n) * rng.uniform(1, 4)
                    lhs = sum_partials_e_k(x, k)
                    rhs = (n - k + 1) * elementary_symmetric(x, k - 1)
                    assert abs(lhs - rhs) <= 1e-4 * (abs(rhs) + 1.0)

    def test_orthant_point_in_every_relaxation(self):
        # a strictly-positive point is in the orthant, hence in all relaxations
        n = 4
        e = np.ones(n)
        x = np.array([2.0, 1.0, 3.0, 0.5])
        for k in range(1, n + 1):
            assert in_hyperbolicity_cone(e_k_poly(k), x, e, k)

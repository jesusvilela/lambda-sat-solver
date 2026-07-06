"""
VDIS Track B1, Phase 2 - S6 rotor/algebra property tests, deferred from
Phase 1 ("Rotor: R R^dagger = 1; rotor action preserves norm; Cl(3,0)
product table against known identities").

The Cl(3,0) reference multiplication below is implemented INDEPENDENTLY
of backend.vdis.algebra (blade-index representation with sign tracking),
so agreement between quat_mul and the Clifford product on even elements
is a genuine cross-check, not the same formula tested against itself.
"""

import numpy as np
import pytest

from backend.vdis.algebra import (
    cplx_conj,
    cplx_exp_bivector,
    cplx_mul,
    cplx_normalize,
    identity_rotor,
    quat_conj,
    quat_exp_bivector,
    quat_mul,
    quat_normalize,
    quat_sandwich,
    rotor_exp,
    rotor_normalize,
    rotor_sandwich,
    vector_part,
    wedge,
    wedge2,
    wedge3,
)

RNG = np.random.default_rng(20260703)


# ---------------------------------------------------------------------------
# Independent Cl(3,0) implementation (blades as bitmasks, e1=1, e2=2, e3=4)
# ---------------------------------------------------------------------------

def _blade_mul(a_mask: int, b_mask: int):
    """Multiply basis blades; returns (sign, result_mask). Metric +++."""
    sign = 1
    # Move each generator of b left through the remaining generators of a.
    for gen in (1, 2, 4):  # e1, e2, e3 in order
        if not (b_mask & gen):
            continue
        # count generators in a strictly above `gen` (must be swapped past)
        higher = a_mask & ~(2 * gen - 1)
        sign *= (-1) ** bin(higher).count("1")
        if a_mask & gen:
            a_mask &= ~gen  # e_i e_i = +1
        else:
            a_mask |= gen
    return sign, a_mask


def cl30_mul(a: dict, b: dict) -> dict:
    """Full Cl(3,0) product of multivectors given as {blade_mask: coeff}."""
    out = {}
    for ma, ca in a.items():
        for mb, cb in b.items():
            s, m = _blade_mul(ma, mb)
            out[m] = out.get(m, 0.0) + s * ca * cb
    return out


# Quaternion basis -> even Cl(3,0) blades, per the mapping pinned in
# algebra.py: 1 <-> 1, i <-> e3e2, j <-> e1e3, k <-> e2e1. Blades are
# stored here in canonical ascending order, so i = e3e2 = -e2e3 lands on
# mask 6 with sign -1, j = e1e3 on mask 5 with sign +1, and k = e2e1 =
# -e1e2 on mask 3 with sign -1.
def _quat_to_cl(q: np.ndarray) -> dict:
    w, x, y, z = q
    return {0: w, 6: -x, 5: y, 3: -z}


def _cl_to_quat(m: dict) -> np.ndarray:
    return np.array(
        [m.get(0, 0.0), -m.get(6, 0.0), m.get(5, 0.0), -m.get(3, 0.0)]
    )


class TestCl30ProductTable:
    def test_blade_squares(self):
        # e1^2 = e2^2 = e3^2 = +1; (e1e2)^2 = (e1e3)^2 = (e2e3)^2 = -1
        for mask in (1, 2, 4):
            s, m = _blade_mul(mask, mask)
            assert (s, m) == (1, 0)
        for mask in (3, 5, 6):
            s, m = _blade_mul(mask, mask)
            assert (s, m) == (-1, 0)

    def test_pseudoscalar(self):
        # (e1e2e3)^2 = -1 in Cl(3,0)
        s, m = _blade_mul(7, 7)
        assert (s, m) == (-1, 0)

    def test_known_bivector_identities(self):
        # (e1e2)(e2e3) = e1e3 ; (e2e3)(e1e2) = e3e1... check both orders
        s, m = _blade_mul(3, 6)
        assert (s, m) == (1, 5)      # e1e2 e2e3 = e1e3
        s, m = _blade_mul(6, 3)
        assert (s, m) == (-1, 5)     # e2e3 e1e2 = -e1e3

    def test_quaternion_relations_through_cl30(self):
        i = np.array([0.0, 1.0, 0.0, 0.0])
        j = np.array([0.0, 0.0, 1.0, 0.0])
        k = np.array([0.0, 0.0, 0.0, 1.0])
        one = np.array([1.0, 0.0, 0.0, 0.0])
        # i j = k, j k = i, k i = j, i^2 = j^2 = k^2 = -1, all THROUGH the
        # independent Clifford table:
        for a, b, expect in [(i, j, k), (j, k, i), (k, i, j)]:
            got = _cl_to_quat(cl30_mul(_quat_to_cl(a), _quat_to_cl(b)))
            np.testing.assert_allclose(got, expect, atol=1e-14)
        for u in (i, j, k):
            got = _cl_to_quat(cl30_mul(_quat_to_cl(u), _quat_to_cl(u)))
            np.testing.assert_allclose(got, -one, atol=1e-14)

    def test_quat_mul_matches_cl30_on_random_even_elements(self):
        for _ in range(200):
            a = RNG.standard_normal(4)
            b = RNG.standard_normal(4)
            via_quat = quat_mul(a, b)
            via_cl = _cl_to_quat(cl30_mul(_quat_to_cl(a), _quat_to_cl(b)))
            np.testing.assert_allclose(via_quat, via_cl, atol=1e-12)

    def test_wedge3_matches_cl30_vector_wedge(self):
        # u ^ v of grade-1 vectors, coefficients read in the quaternion
        # (i, j, k) = (e3e2, e1e3, e2e1) basis, must equal wedge3
        # (which is -cross(u, v) under this mapping).
        for _ in range(100):
            u = RNG.standard_normal(3)
            v = RNG.standard_normal(3)
            uv = cl30_mul(
                {1: u[0], 2: u[1], 4: u[2]}, {1: v[0], 2: v[1], 4: v[2]}
            )
            # grade-2 part sits on blade masks 6 (e2e3), 5 (e1e3),
            # 3 (e1e2); convert canonical-blade coeffs to (i, j, k)
            got = np.array([-uv.get(6, 0.0), uv.get(5, 0.0), -uv.get(3, 0.0)])
            np.testing.assert_allclose(got, wedge3(u, v), atol=1e-12)


class TestRotorProperties:
    def test_rotor_unit_norm(self):
        # R R^dagger = 1 for R = exp(bivector), all magnitudes incl. ~0
        for scale in (0.0, 1e-12, 0.1, 1.0, 10.0):
            for _ in range(50):
                omega = scale * RNG.standard_normal(3)
                r = quat_exp_bivector(omega)
                rr = quat_mul(r, quat_conj(r))
                np.testing.assert_allclose(rr, [1.0, 0.0, 0.0, 0.0], atol=1e-12)

    def test_rotor_action_preserves_norm(self):
        for _ in range(100):
            r = quat_exp_bivector(RNG.standard_normal(3))
            a = RNG.standard_normal(4)
            out = quat_sandwich(r, a)
            assert np.linalg.norm(out) == pytest.approx(np.linalg.norm(a), abs=1e-10)

    def test_rotor_action_fixes_scalar_part(self):
        for _ in range(100):
            r = quat_exp_bivector(RNG.standard_normal(3))
            a = RNG.standard_normal(4)
            out = quat_sandwich(r, a)
            assert out[0] == pytest.approx(a[0], abs=1e-10)

    def test_exp_zero_is_identity(self):
        np.testing.assert_allclose(
            quat_exp_bivector(np.zeros(3)), [1.0, 0.0, 0.0, 0.0], atol=1e-15
        )
        np.testing.assert_allclose(
            cplx_exp_bivector(np.zeros(1)), [1.0, 0.0], atol=1e-15
        )

    def test_broadcasting(self):
        omegas = RNG.standard_normal((7, 3))
        rotors = quat_exp_bivector(omegas)
        assert rotors.shape == (7, 4)
        np.testing.assert_allclose(np.linalg.norm(rotors, axis=-1), 1.0, atol=1e-12)
        psi = quat_exp_bivector(RNG.standard_normal(3))
        out = quat_sandwich(rotors, psi)
        assert out.shape == (7, 4)
        for row, r in zip(out, rotors):
            np.testing.assert_allclose(row, quat_sandwich(r, psi), atol=1e-14)


class TestComplexAlgebra:
    def test_mul_against_python_complex(self):
        for _ in range(100):
            a = RNG.standard_normal(2)
            b = RNG.standard_normal(2)
            got = cplx_mul(a, b)
            expect = complex(*a) * complex(*b)
            np.testing.assert_allclose(got, [expect.real, expect.imag], atol=1e-12)

    def test_rotor_sandwich_is_trivial_for_C(self):
        # PROVED (commutativity): r a conj(r) = a |r|^2 = a for unit r.
        for _ in range(50):
            r = cplx_exp_bivector(RNG.standard_normal(1))
            a = RNG.standard_normal(2)
            np.testing.assert_allclose(rotor_sandwich(r, a, "C"), a, atol=1e-12)

    def test_wedge2_antisymmetric(self):
        for _ in range(50):
            u = RNG.standard_normal(2)
            v = RNG.standard_normal(2)
            assert wedge2(u, v)[0] == pytest.approx(-wedge2(v, u)[0], abs=1e-14)
            assert wedge2(u, u)[0] == pytest.approx(0.0, abs=1e-14)


class TestDispatch:
    def test_identity_rotor(self):
        np.testing.assert_array_equal(identity_rotor("H"), [1.0, 0.0, 0.0, 0.0])
        np.testing.assert_array_equal(identity_rotor("C"), [1.0, 0.0])

    def test_normalize_degenerate_returns_identity(self):
        np.testing.assert_array_equal(quat_normalize(np.zeros(4)), [1.0, 0, 0, 0])
        np.testing.assert_array_equal(cplx_normalize(np.zeros(2)), [1.0, 0])

    def test_vector_part_shapes(self):
        assert vector_part(np.zeros(4), "H").shape == (3,)
        assert vector_part(np.zeros(2), "C").shape == (2,)

    def test_rotor_exp_norms(self):
        for alg, bdim in (("H", 3), ("C", 1)):
            r = rotor_exp(RNG.standard_normal(bdim), alg)
            assert np.linalg.norm(r) == pytest.approx(1.0, abs=1e-12)
            n = rotor_normalize(3.0 * r, alg)
            np.testing.assert_allclose(n, r, atol=1e-12)

    def test_unknown_algebra_raises(self):
        with pytest.raises(ValueError):
            wedge(np.zeros(3), np.zeros(3), "O")  # octonions are PARKED

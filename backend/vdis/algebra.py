"""
VDIS Track B1, Phase 2 - hypercomplex algebra operations for the rotor /
torsion channel (S3.4) and the Clifford decision scalar (S3.6).

v1 algebras per the pinned spec (Correction 1 - octonions excluded):
  - 'R'  m=1: trivial algebra, degenerate/Phase-1 configuration only.
  - 'C'  m=2: complex numbers as np.array([re, im]); isomorphic to the
    even subalgebra of Cl(2,0) via  a + b*i  <->  a + b*e12.
  - 'H'  m=4: quaternions as np.array([w, x, y, z]); isomorphic to the
    even subalgebra of Cl(3,0) via the standard (reversed-bivector)
    identification
        i <-> e3 e2,   j <-> e1 e3,   k <-> e2 e1
    which satisfies i*j = k, j*k = i, k*i = j. Under this mapping the
    wedge u ^ v of two grade-1 vectors has (i, j, k) coordinates equal
    to MINUS the cross product - see wedge3. Both facts are verified in
    test_vdis_algebra.py against an independently implemented full
    Cl(3,0) product table, per S6's "Cl(3,0) product table against
    known identities" requirement (an earlier draft used the naive
    +cross convention and the product-table cross-check caught the
    inconsistency).

Every function broadcasts over leading axes: inputs of shape (..., m)
give outputs of shape (..., m), so per-literal state arrays can be
processed in one call (needed for the S3.7 per-conflict budget - a
Python loop over 2n literals per conflict would dominate wall time).

A PROVED triviality worth stating up front (see PHASE_2.md): for A = C
the algebra is commutative, so the rotor sandwich R psi R^dagger = psi
identically and the torsion scalar tau is constant. The S3.4 channel
only carries information for the noncommutative algebra H.
"""

from __future__ import annotations

import numpy as np

_NUM_EPS = 1e-15


# ---------------------------------------------------------------------------
# Quaternions (A = 'H', m = 4) - even subalgebra of Cl(3,0)
# ---------------------------------------------------------------------------

def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product a * b, broadcasting over leading axes."""
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        axis=-1,
    )


def quat_conj(a: np.ndarray) -> np.ndarray:
    """Quaternion conjugate (= Clifford reversion on the even subalgebra)."""
    out = a.copy()
    out[..., 1:] = -out[..., 1:]
    return out


def quat_exp_bivector(omega: np.ndarray) -> np.ndarray:
    """exp(omega) for a bivector omega given by 3 coords (..., 3) in the
    basis (i, j, k) = (e3e2, e1e3, e2e1). Returns a unit quaternion
    (rotor): cos|omega| + sin|omega| * omega_hat. exp(0) = 1."""
    theta = np.linalg.norm(omega, axis=-1, keepdims=True)
    w = np.cos(theta)
    # sinc form is stable at theta -> 0: sin(t)/t -> 1
    with np.errstate(invalid="ignore", divide="ignore"):
        s = np.where(theta > _NUM_EPS, np.sin(theta) / np.where(theta > 0, theta, 1.0), 1.0)
    return np.concatenate([w, s * omega], axis=-1)


def quat_normalize(a: np.ndarray) -> np.ndarray:
    """a / |a|; identity rotor where |a| ~ 0 (degenerate EMA guard)."""
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    out = np.where(n > _NUM_EPS, a / np.where(n > 0, n, 1.0), 0.0)
    if out.ndim == 1 and np.linalg.norm(out) <= _NUM_EPS:
        out = out.copy()
        out[0] = 1.0
    return out


def quat_sandwich(r: np.ndarray, a: np.ndarray) -> np.ndarray:
    """r * a * conj(r), broadcasting; for unit r this is the rotor action
    (a rotation of a's imaginary part, identity on its scalar part)."""
    return quat_mul(quat_mul(r, a), quat_conj(r))


# ---------------------------------------------------------------------------
# Complex numbers (A = 'C', m = 2) - even subalgebra of Cl(2,0)
# ---------------------------------------------------------------------------

def cplx_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(a0 + a1 i)(b0 + b1 i), broadcasting over leading axes."""
    ar, ai = a[..., 0], a[..., 1]
    br, bi = b[..., 0], b[..., 1]
    return np.stack([ar * br - ai * bi, ar * bi + ai * br], axis=-1)


def cplx_conj(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    out[..., 1] = -out[..., 1]
    return out


def cplx_exp_bivector(omega: np.ndarray) -> np.ndarray:
    """exp(omega * e12) for scalar bivector coord omega of shape (..., 1):
    the unit complex number (cos omega, sin omega)."""
    return np.concatenate([np.cos(omega), np.sin(omega)], axis=-1)


def cplx_normalize(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    out = np.where(n > _NUM_EPS, a / np.where(n > 0, n, 1.0), 0.0)
    if out.ndim == 1 and np.linalg.norm(out) <= _NUM_EPS:
        out = out.copy()
        out[0] = 1.0
    return out


# ---------------------------------------------------------------------------
# Wedge products (vector, vector) -> bivector coords
# ---------------------------------------------------------------------------

def wedge3(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """u ^ v for u, v in R^3, returned as 3 bivector coords in the
    quaternion basis (i, j, k) = (e3e2, e1e3, e2e1). Expanding
    u ^ v = c1 e2e3 + c2 e3e1 + c3 e1e2 with c = cross(u, v), and
    e2e3 = -i, e3e1 = -j, e1e2 = -k under the pinned mapping, the
    (i, j, k) coordinates are MINUS the cross product - verified
    against the independent Cl(3,0) table in tests, not asserted."""
    return -np.cross(u, v)


def wedge2(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """u ^ v for u, v in R^2: the single e12 coord, shape (..., 1)."""
    return (u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0])[..., None]


# ---------------------------------------------------------------------------
# Uniform per-algebra dispatch used by the heuristic
# ---------------------------------------------------------------------------

#: algebra name -> (m = dim_R(A), bivector coord count)
ALGEBRAS = {"R": (1, 0), "C": (2, 1), "H": (4, 3)}


def algebra_dims(algebra: str) -> tuple:
    if algebra not in ALGEBRAS:
        raise ValueError(f"unknown algebra {algebra!r}; v1 supports {sorted(ALGEBRAS)}")
    return ALGEBRAS[algebra]


def rotor_exp(omega: np.ndarray, algebra: str) -> np.ndarray:
    if algebra == "H":
        return quat_exp_bivector(omega)
    if algebra == "C":
        return cplx_exp_bivector(omega)
    raise ValueError(f"no rotor structure for algebra {algebra!r}")


def rotor_sandwich(r: np.ndarray, a: np.ndarray, algebra: str) -> np.ndarray:
    if algebra == "H":
        return quat_sandwich(r, a)
    if algebra == "C":
        # Commutative: r a conj(r) = a |r|^2 = a for unit r. Computed
        # literally anyway so the C path exercises the same code shape.
        return cplx_mul(cplx_mul(r, a), cplx_conj(r))
    raise ValueError(f"no rotor structure for algebra {algebra!r}")


def rotor_normalize(a: np.ndarray, algebra: str) -> np.ndarray:
    if algebra == "H":
        return quat_normalize(a)
    if algebra == "C":
        return cplx_normalize(a)
    raise ValueError(f"no rotor structure for algebra {algebra!r}")


def vector_part(element_sum: np.ndarray, algebra: str) -> np.ndarray:
    """Map an algebra element (slot-sum of a literal's tangent state) to
    the grade-1 vector its wedge products are taken in.

    Pinned implementation choice (documented in PHASE_2.md): for H the
    vector is the imaginary part (x, y, z) - the standard pure-quaternion
    <-> R^3 identification; for C it is (re, im) as a vector in the R^2
    that Cl(2,0) is built on."""
    if algebra == "H":
        return element_sum[..., 1:]
    if algebra == "C":
        return element_sum
    raise ValueError(f"no vector structure for algebra {algebra!r}")


def wedge(u: np.ndarray, v: np.ndarray, algebra: str) -> np.ndarray:
    if algebra == "H":
        return wedge3(u, v)
    if algebra == "C":
        return wedge2(u, v)
    raise ValueError(f"no wedge structure for algebra {algebra!r}")


def identity_rotor(algebra: str) -> np.ndarray:
    m, _ = algebra_dims(algebra)
    out = np.zeros(m)
    out[0] = 1.0
    return out

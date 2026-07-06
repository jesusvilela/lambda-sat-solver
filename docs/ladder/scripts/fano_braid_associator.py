"""The Fano-braid / octonion substrate of the operator's "braid theta engine"
and "star of closure" (StarOfClosureBraid8), made correct and reproducible.

fano_braid(a,b) = Im(a*b) over the octonions O: octonion multiplication braids
the 7 imaginary units according to the Fano plane. The ASSOCIATOR
    [a,b,c] = (a*b)*c - a*(b*c)
is the local obstruction to a,b,c lying in a common associative (quaternionic
H) subalgebra -- it vanishes iff they fit in one classical frame, and is the
"curvature" of octonionic non-associativity. Aut(O) = G2 acts on the Fano
plane, so this substrate is the DYNAMICAL face of the same g2 = Der(O) object
whose STATIC face is the zero-divisor rank-deficiency of RUNG2_ALGEBRAIC and
whose SYMMETRY face is the Lie telos of RUNG2_LIE_TELOS.

Run: python -m docs.ladder.scripts.fano_braid_associator
"""
import numpy as np


def qmul(p, q):
    """Hamilton quaternion product; q = [w,x,y,z]."""
    w1, x1, y1, z1 = p
    w2, x2, y2, z2 = q
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def qconj(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])


def omul(o1, o2):
    """Octonion product via Cayley-Dickson doubling of H:
    (a,b)(c,d) = (a c - d* b,  d a + b c*)."""
    a, b = o1[:4], o1[4:]
    c, d = o2[:4], o2[4:]
    return np.concatenate([
        qmul(a, c) - qmul(qconj(d), b),
        qmul(d, a) + qmul(b, qconj(c)),
    ])


def fano_braid(a, b):
    """Im(a*b) in R^7 -- the operator's fano_braid."""
    return omul(a, b)[1:]


def associator(a, b, c):
    """[a,b,c] = (ab)c - a(bc); zero iff a,b,c share an associative H frame."""
    return omul(omul(a, b), c) - omul(a, omul(b, c))


def e(k):
    v = np.zeros(8)
    v[k] = 1.0
    return v


def main():
    rng = np.random.default_rng(0)
    o1, o2 = rng.standard_normal(8), rng.standard_normal(8)
    lhs = np.linalg.norm(omul(o1, o2))
    rhs = np.linalg.norm(o1) * np.linalg.norm(o2)
    print(f"composition |ab| = |a||b|:  {lhs:.6f} vs {rhs:.6f}  "
          f"(diff {abs(lhs - rhs):.2e}) -- O is a composition algebra")

    print(f"assoc(e1,e2,e3) quaternionic (expect 0):   "
          f"|.|={np.linalg.norm(associator(e(1), e(2), e(3))):.3f}")
    print(f"assoc(e1,e2,e4) octonionic  (expect !=0):  "
          f"|.|={np.linalg.norm(associator(e(1), e(2), e(4))):.3f}")
    print(f"assoc(e1,e4,e6) octonionic:                "
          f"|.|={np.linalg.norm(associator(e(1), e(4), e(6))):.3f}")
    print("=> associator = local obstruction to a common associative (H) frame; "
          "this is the Braid8 non-associativity core.")


if __name__ == "__main__":
    main()

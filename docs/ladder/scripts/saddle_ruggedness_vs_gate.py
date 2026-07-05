"""Reproduces & verifies the operator's SaddleInterspace.lean insight:
XOR-SAT has a MORE rugged energy landscape than 3-SAT, yet is in P via
Gaussian elimination. Therefore landscape ruggedness / saddle structure
is NOT the hardness separator - the algebraic gate (Schaefer 1978) is.

This is the honest boundary of the saddle-point view: it tracks LOCAL
(within-family) search hardness (see energy_landscape_saddle), but across
problem types a rugged-yet-easy family (XOR) breaks it. The live-research
name for the landscape obstruction that DOES imply hardness - for a
restricted algorithm class - is the Overlap Gap Property (Gamarnik).
"""
import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
import numpy as np


def _barriers(n, E):
    N = 1 << n; g = int(E.min()); ground = np.flatnonzero(E == g)
    p2 = list(range(N))
    def f2(a):
        while p2[a] != a: p2[a] = p2[p2[a]]; a = p2[a]
        return a
    for x in ground:
        for v in range(n):
            nb = int(x) ^ (1 << v)
            if E[nb] == g:
                ra, rb = f2(int(x)), f2(nb)
                if ra != rb: p2[ra] = rb
    basins = len({f2(int(x)) for x in ground})
    order = np.argsort(E, kind="stable"); added = bytearray(N)
    parent = list(range(N)); gs = set(int(x) for x in ground); barrier = g
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for x in order:
        x = int(x); added[x] = 1
        for v in range(n):
            nb = x ^ (1 << v)
            if added[nb]:
                ra, rb = find(x), find(nb)
                if ra != rb: parent[ra] = rb
        if len({find(s) for s in gs}) == 1:
            barrier = int(E[x]); break
    return g, basins, barrier


def _sat_energy(n, clauses):
    N = 1 << n; E = np.zeros(N, np.int32); cb = []
    for cl in clauses:
        pos = neg = 0
        for l in cl:
            v = abs(l) - 1
            (pos, neg) = (pos | (1 << v), neg) if l > 0 else (pos, neg | (1 << v))
        cb.append((pos, neg))
    for x in range(N):
        E[x] = sum(1 for pos, neg in cb if (x & pos) == 0 and (~x & neg) == 0)
    return E


def _xor_energy(n, cons):
    N = 1 << n; E = np.zeros(N, np.int32)
    for x in range(N):
        e = 0
        for vs, b in cons:
            p = 0
            for v in vs: p ^= (x >> v) & 1
            e += (p != b)
        E[x] = e
    return E


def _xor_in_P(n, cons):
    """Decide XOR-SAT by Gaussian elimination over GF(2) - polynomial."""
    piv = {}
    for vs, b in cons:
        r = 0
        for v in vs: r |= (1 << v)
        cr, cb = r, b
        for col in list(piv):
            if (cr >> col) & 1:
                pr, pb = piv[col]; cr ^= pr; cb ^= pb
        if cr == 0:
            if cb == 1: return False
            continue
        piv[(cr & -cr).bit_length() - 1] = (cr, cb)
    return True


if __name__ == "__main__":
    n = 16; m = int(round(4.25 * n)); rng = random.Random(0)
    print(f"n={n} alpha=4.25 : SAT-vs-XOR ruggedness (SaddleInterspace verification)")
    for _ in range(4):
        cls = [[(v + 1) if rng.random() < .5 else -(v + 1)
                for v in rng.sample(range(n), 3)] for _ in range(m)]
        print("  3SAT ", _barriers(n, _sat_energy(n, cls)), " NP-complete")
        cons = [(tuple(rng.sample(range(n), 3)), rng.randint(0, 1)) for _ in range(m)]
        print("  3XOR ", _barriers(n, _xor_energy(n, cons)),
              f" in P (GaussElim decides SAT={_xor_in_P(n, cons)})")

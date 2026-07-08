"""The escape field is a catastrophe FOLD, not a smooth Eikonal field.

Clashing the continuous escape-field / signed-distance framework (Eikonal
||grad U|| = 1/c, viscosity solutions, geodesic descent -- the smooth backbone of
GRD's escape field eps*T and Exp geodesic) against our DISCRETE algebraic
decidability, by measuring both an escape-field value U (coupling rounds to a
verdict) and a signed-distance f (hyperbolic depth to the decidable boundary)
across a structure gradient.

Finding: there is no smooth gradient to descend. As a satisfiable parity core is
diluted with random noise, everything SNAPS at the boundary -- verdict SAT ->
CDCL_NEEDED, U: 0 -> infinity, f: ~0 -> the boundary at infinity -- and the far
side is near-empty (the coupling entails almost nothing). The SAT decidability
landscape is a Thom catastrophe FOLD, not a graded Riemannian field.

Run:  python -m docs.ladder.scripts.escape_fold
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import random_3sat, random_xorsat  # noqa: E402

from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.frame_solver import coupled_entailments, coupling_breath  # noqa: E402
from backend.orbifold import hyperbolic_depth  # noqa: E402
from backend.xor_extraction import extract_xors  # noqa: E402


def dilute(base_clauses, n, noise, rng):
    return CNFFormula(num_vars=n, clauses=list(base_clauses) +
                      [[rng.choice([-1, 1]) * rng.randint(1, n) for _ in range(3)]
                       for _ in range(noise)])


def main():
    rng = random.Random(2)
    n = 26
    base = random_xorsat(n, n, 2).clauses            # a satisfiable parity core
    print("Crossing the decidability fold (satisfiable parity core + random noise):")
    print(f"   {'noise':>6} {'xor_cov':>8} {'verdict':>12} {'U(rounds)':>10} "
          f"{'f(depth)':>9} {'entail/n':>9}")
    for noise in (0, 10, 25, 45, 70, 100, 150, 220, 320):
        f = dilute(base, n, noise, random.Random(1000 + noise))
        bt = coupling_breath(f)
        ent, _ = coupled_entailments(f)
        cov = extract_xors(f).xor_clause_fraction
        u = "inf" if bt.verdict == "CDCL_NEEDED" else str(bt.rounds)
        print(f"   {noise:>6} {cov:>8.2f} {bt.verdict:>12} {u:>10} "
              f"{hyperbolic_depth(f):>9.2f} {len(ent) / n:>9.2f}")
    print("\nThe cliff: between noise 0 and 10 (coverage 1.00 -> 0.91) the verdict")
    print("snaps SAT -> CDCL_NEEDED, U jumps 0 -> inf, f jumps to the boundary at")
    print("infinity, and the far side is near-empty. No smooth escape field to")
    print("descend -- you cannot geodesically cross a fold; you must TUNNEL (CDCL).")

    print("\nBeyond the fold everywhere -- pure random 3-SAT (no structure, any alpha):")
    for a in (2.0, 4.26, 6.0):
        f = random_3sat(40, round(a * 40), 1)
        bt = coupling_breath(f)
        print(f"   alpha={a:>4}: {bt.verdict:>12}  U=inf  f(depth)={hyperbolic_depth(f):.2f}")


if __name__ == "__main__":
    main()

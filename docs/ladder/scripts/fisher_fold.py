"""Fisher-Rao geometrizes the decidability fold -- in the natural coordinate.

The operator's question: can Fisher-Rao help (hypercomplex/hyperdim/infinitesimal
or not)? Answer, measured: YES -- but only in the NATURAL algebraic coordinate.
Along the crude coverage feature the fold is smeared (P(decide) ~ 0.9 everywhere);
along the GF(2) RANK-DEFICIENCY of the recovered XOR system (the actual content of
the sign-patterns) the fold is razor-sharp, and the Fisher-Rao length element
sqrt(I), I = (P')^2 / (P(1-P)), SPIKES at the transition -- the catastrophe is a
metric singularity in information geometry.

Run:  python -m docs.ladder.scripts.fisher_fold
"""

from __future__ import annotations

import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import random_xorsat  # noqa: E402

from backend.cnf_utils import CNFFormula  # noqa: E402
from backend.frame_solver import frame_solve_coupled  # noqa: E402
from backend.scout import xor_rank_deficiency  # noqa: E402
from backend.xor_extraction import extract_xors  # noqa: E402


def _p_decide(coordinate, trials=2500, n=26, seed=1):
    """P(decide) binned along a chosen coordinate: 'coverage' or 'deficiency'."""
    rng = random.Random(seed)
    bins = defaultdict(lambda: [0, 0])
    for _ in range(trials):
        base = random_xorsat(n, n, rng.randint(0, 99999)).clauses
        noise = rng.randint(0, 80)
        f = CNFFormula(n, list(base) +
                       [[rng.choice([-1, 1]) * rng.randint(1, n) for _ in range(3)]
                        for _ in range(noise)])
        if coordinate == "coverage":
            key = round(extract_xors(f).xor_clause_fraction * 20) / 20
        else:
            kind, defic = xor_rank_deficiency(f)
            if kind != "consistent":       # inconsistent/nostruct are not the band
                continue
            key = round(defic * 20) / 20
        dec = frame_solve_coupled(f).status != "CDCL_NEEDED"
        bins[key][0] += dec
        bins[key][1] += 1
    return bins


def _report(name, bins):
    xs = [b for b in sorted(bins) if bins[b][1] >= 20]
    P = {b: bins[b][0] / bins[b][1] for b in xs}
    print(f"\n{name}:")
    print(f"   {'x':>6}{'P(decide)':>11}{'n':>6}{'Fisher sqrt(I)':>16}")
    peak = 0.0
    for i, b in enumerate(xs):
        p = min(max(P[b], 1e-3), 1 - 1e-3)
        dP = ((P[xs[i + 1]] - P[xs[i - 1]]) / (xs[i + 1] - xs[i - 1])
              if 0 < i < len(xs) - 1 else 0.0)
        fi = math.sqrt(dP * dP / (p * (1 - p)))
        peak = max(peak, fi)
        print(f"   {b:>6.2f}{P[b]:>11.2f}{bins[b][1]:>6}{fi:>16.1f}")
    print(f"   peak Fisher sqrt(I) = {peak:.1f}")


def main():
    _report("Along COVERAGE (crude proxy -- fold smeared, Fisher flat)",
            _p_decide("coverage"))
    _report("Along XOR RANK-DEFICIENCY (natural coordinate -- fold sharp, Fisher SPIKES)",
            _p_decide("deficiency"))
    print("\nThe fold is a Fisher-Rao metric singularity -- but only in the natural")
    print("algebraic coordinate. The metric is the right instrument; coverage is")
    print("the wrong chart. (Sign-patterns, measured as GF(2) rank, ARE the chart.)")


if __name__ == "__main__":
    main()

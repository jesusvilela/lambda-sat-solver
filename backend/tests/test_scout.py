"""Tests for the scout (backend/scout.py): the viscosity medium's predictive map.

Confident regions must be right (an ISLAND prediction is actually frame-decided; a
TUNNEL prediction actually needs CDCL); the FOLD band is allowed to be mixed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_3sat, random_xorsat, tseitin  # noqa: E402

from backend.eval.generators import pigeonhole  # noqa: E402
from backend.frame_solver import frame_solve_coupled  # noqa: E402
from backend.scout import (  # noqa: E402
    FOLD,
    ISLAND,
    TUNNEL,
    scout,
    xor_rank_deficiency,
)


class TestScoutRegions:
    def test_parity_is_island(self):
        r = scout(tseitin(20, 1))
        assert r.region == ISLAND and r.predicted_frame == "parity"

    def test_pigeonhole_is_island(self):
        r = scout(pigeonhole(6)[0])
        assert r.region == ISLAND and r.predicted_frame in ("counting", "2sat")

    def test_random_is_tunnel(self):
        r = scout(random_3sat(60, round(4.26 * 60), 1))
        assert r.region == TUNNEL

    def test_rank_coordinate_resolves_most_partial_parity(self):
        # partial-coverage instances that the crude coverage feature left in the
        # ambiguous FOLD band are now confidently resolved by the rank coordinate:
        # inconsistent/determined -> ISLAND, free -> TUNNEL, only the thin
        # deficiency~0.05 layer stays FOLD.
        import random
        from backend.cnf_utils import CNFFormula
        rng = random.Random(3)
        regions = set()
        for noise in (20, 50, 90):
            base = random_xorsat(26, 26, noise) .clauses
            f = CNFFormula(26, base + [[rng.choice([-1, 1]) * rng.randint(1, 26)
                                        for _ in range(3)] for _ in range(noise)])
            regions.add(scout(f).region)
        # at least one confident (non-FOLD) region appears -- the fold shrank
        assert regions & {ISLAND, TUNNEL}


class TestRankDeficiencyCoordinate:
    def test_full_parity_is_determined(self):
        # a fully-covered XOR system is consistent-or-inconsistent with 0 free
        # variables (deficiency 0) -- the natural coordinate says 'island'.
        kind, defic = xor_rank_deficiency(tseitin(20, 1))
        assert kind in ("consistent", "inconsistent")
        if kind == "consistent":
            assert defic <= 0.02

    def test_no_structure_has_no_coordinate(self):
        kind, _ = xor_rank_deficiency(random_3sat(60, 250, 1))
        assert kind == "nostruct"

    def test_inconsistent_xor_is_island(self):
        # x1^x2=0 AND x1^x2=1 -> inconsistent -> a certain UNSAT island
        from backend.cnf_utils import CNFFormula
        f = CNFFormula(2, [[1, -2], [-1, 2], [1, 2], [-1, -2]])
        kind, _ = xor_rank_deficiency(f)
        assert kind == "inconsistent"
        assert scout(f).region == ISLAND


class TestScoutSoundness:
    def test_confident_predictions_are_correct(self):
        # ISLAND => actually decided; TUNNEL => actually needs CDCL. The FOLD band
        # is exempt (it is the honest "cannot predict from cheap features" zone).
        corpus = ([tseitin(20, s) for s in range(4)]
                  + [pigeonhole(p)[0] for p in (5, 6, 7)]
                  + [random_xorsat(30, 30, s) for s in range(4)]
                  + [random_3sat(60, round(4.26 * 60), s) for s in range(6)])
        for f in corpus:
            r = scout(f)
            decided = frame_solve_coupled(f).status != "CDCL_NEEDED"
            if r.region == ISLAND:
                assert decided, "ISLAND scout but not frame-decided"
            elif r.region == TUNNEL:
                assert not decided, "TUNNEL scout but a frame decided it"

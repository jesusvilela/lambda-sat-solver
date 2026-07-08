"""Tests for the fabric (backend/fabric.py): the initial state as a woven tapestry.

Each family occupies a distinct region of the fabric-manifold; the threads read
the qualities that place it there.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/ladder/scripts"))

from frame_benchmark import random_3sat, random_xorsat, tseitin  # noqa: E402

from backend.eval.generators import pigeonhole  # noqa: E402
from backend.fabric import fabric  # noqa: E402


class TestFabricThreads:
    def test_parity_family_on_the_parity_thread(self):
        fb = fabric(random_xorsat(30, 30, 1))
        assert fb.rank_deficiency <= 0.02 or fb.parity_kind == "inconsistent"
        assert fb.region == "island" and fb.predicted_frame == "parity"

    def test_pigeonhole_on_the_orbit_thread(self):
        fb = fabric(pigeonhole(7)[0])
        assert fb.orbit_coarseness > 0.8            # highly symmetric
        assert fb.counting_signal > 0.5             # at-most-one heavy
        assert fb.region == "island"

    def test_random_at_the_gyration_boundary(self):
        fb = fabric(random_3sat(60, round(4.26 * 60), 1))
        assert fb.gyration > 5.0                    # out toward the boundary ∂∞
        assert fb.region == "tunnel"

    def test_families_occupy_distinct_regions(self):
        # the tapestry separates the families: their thread-vectors are not equal
        vecs = {name: tuple(round(v, 2) for v in fabric(f).as_dict().values())
                for name, f in [("tseitin", tseitin(20, 1)),
                                ("php", pigeonhole(7)[0]),
                                ("random", random_3sat(60, 250, 1))]}
        assert len(set(vecs.values())) == 3          # all distinct

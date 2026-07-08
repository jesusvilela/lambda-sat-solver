"""The distributional ledger: instance families as regions of the cosmo manifold.

Reads each instance's FABRIC (backend.fabric) -- the woven tapestry of qualities
(parity rank-deficiency, orbit coarseness, gyration/hyperbolic depth, counting and
implication signals, shape) -- and tabulates where the families sit. The families
occupy distinct regions of the fabric-manifold; the scout region and predicted
frame are the ledger's verdict column. This is the holistic view of the initial
state: not one number, a tapestry.

Run:  python -m docs.ladder.scripts.fabric_ledger
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import mixed, random_3sat, random_xorsat, tseitin  # noqa: E402

from backend.eval.generators import pigeonhole  # noqa: E402
from backend.fabric import fabric  # noqa: E402


def main():
    families = [
        ("Tseitin", lambda: tseitin(20, 1)),
        ("XORSAT", lambda: random_xorsat(30, 30, 1)),
        ("PHP", lambda: pigeonhole(7)[0]),
        ("mixed", lambda: mixed(30, 20, 20, 1)),
        ("random3", lambda: random_3sat(60, round(4.26 * 60), 1)),
    ]
    print("Distributional ledger -- families over the cosmo-manifold fabric:\n")
    print(f"{'family':9}{'parity':>7}{'rank_def':>9}{'orbit':>7}{'gyration':>9}"
          f"{'count':>7}{'impl':>6}{'ratio':>7}  {'region':>7} {'frame':>9}")
    for name, gen in families:
        fb = fabric(gen())
        print(f"{name:9}{fb.parity_signal:>7.2f}{fb.rank_deficiency:>9.2f}"
              f"{fb.orbit_coarseness:>7.2f}"
              f"{fb.gyration:>9.2f}{fb.counting_signal:>7.2f}"
              f"{fb.implication_signal:>6.2f}{fb.ratio:>7.1f}"
              f"  {fb.region:>7} {fb.predicted_frame:>9}")
    print("\nEach family is a distinct region of the fabric: Tseitin/XORSAT on the")
    print("parity thread (rank_def ~0), PHP on the orbit thread (orbit ~1, count")
    print("high), random3 at the gyration boundary (gyration -> the depth of ∂∞),")
    print("mixed strung between them. The tapestry, read as one initial state.")


if __name__ == "__main__":
    main()

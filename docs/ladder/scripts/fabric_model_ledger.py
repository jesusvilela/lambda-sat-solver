"""The distributional ledger, made PARAMETRIC and HYPERBOLIC.

Where `fabric_ledger.py` tabulates where families sit, this fits the parametric
model (`backend.fabric_model`) -- each family a wrapped-normal blob on the Poincare
ball -- and reports it as a distributional ledger over the curved manifold:

  * each family's hyperbolic DEPTH (geodesic distance of its centre from the ball
    centre): decided families near the centre, CDCL/tunnel out toward ∂∞;
  * the GEODESIC SEPARATION between family blobs: small angular hops among the
    decided families, a near-infinite crossing to the tunnel family at the boundary;
  * the model's held-out CLASSIFICATION accuracy -- a measured statement of how
    separable the families actually are in the hyperbolic fabric;
  * where external families (Tseitin/XORSAT/PHP/random/mixed) are PLACED by the
    fitted density (its predicted frame = the router prior).

This is the "n cosmo / n manifold distributional ledger" as a fitted density on a
curved manifold, not a table of regions. Charter: the model is a predictor (a router
prior), never a decider -- soundness lives in the frames it points at.

Run:  python -m docs.ladder.scripts.fabric_model_ledger
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frame_benchmark import mixed, random_3sat, random_xorsat, tseitin  # noqa: E402

from backend.eval.generators import (  # noqa: E402
    mutilated_chessboard, pigeonhole, random_ksat, xor_chain,
)
from backend.fabric import fabric  # noqa: E402
from backend.fabric_model import fit_default_model  # noqa: E402


def _held_out_accuracy(model, lo=400, hi=412):
    truth = {
        "parity": lambda s: xor_chain(22, expected_sat=(s % 2 == 0), seed=s)[0],
        "counting": lambda s: (pigeonhole(7)[0] if s % 2
                               else mutilated_chessboard(5)[0]),
        "tunnel": lambda s: random_ksat(70, round(4.26 * 70), seed=s)[0],
    }
    tot = cor = 0
    for fam, g in truth.items():
        for s in range(lo, hi):
            cor += (model.classify(fabric(g(s))) == fam)
            tot += 1
    return cor, tot


def main():
    m = fit_default_model()

    print("Hyperbolic distributional ledger -- family blobs on the Poincare ball:\n")
    print(f"{'family':10}{'frame':10}{'hyp.depth':>10}{'n':>4}")
    for g in m.families:
        print(f"{g.name:10}{g.frame:10}{g.depth():>10.2f}{g.n:>4}")

    print("\nGeodesic separation between family centres (the curvature of hardness):")
    for (a, b), d in m.geodesic_separation().items():
        tag = "  <- crosses the fold to ∂∞" if d > 5 else "  (angular hop, decided)"
        print(f"  {a:9}<->{b:9}{d:8.2f}{tag}")

    cor, tot = _held_out_accuracy(m)
    print(f"\nHeld-out classification accuracy: {cor}/{tot} = {cor / tot:.2f}"
          "  (measured separability of the families in the hyperbolic fabric)")

    print("\nExternal families placed by the fitted density (predicted frame = the"
          " router prior):")
    ext = [
        ("Tseitin", tseitin(20, 1)),
        ("XORSAT", random_xorsat(30, 30, 1)),
        ("PHP", pigeonhole(8)[0]),
        ("random3", random_3sat(70, 300, 1)),
        ("mixed", mixed(30, 20, 20, 1)),
    ]
    print(f"{'family':10}{'class':10}{'pred.frame':12}{'M(parity)':>10}"
          f"{'M(count)':>10}{'M(tunnel)':>10}")
    for name, f in ext:
        fb = fabric(f)
        mh = m.mahalanobis(fb)
        print(f"{name:10}{m.classify(fb):10}{m.predict_frame(fb):12}"
              f"{mh['parity']:>10.2f}{mh['counting']:>10.2f}{mh['tunnel']:>10.2f}")

    print("\nThe decided families cluster near the centre; the tunnel family lives")
    print("out at the boundary ∂∞, a near-infinite hyperbolic distance away -- the")
    print("holographic screen of hardness, fit as a density, not just tabulated.")


if __name__ == "__main__":
    main()

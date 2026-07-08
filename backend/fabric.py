"""fabric -- the instance's initial state as a woven tapestry, not a medium.

Where `scout` reads the viscosity medium as a field to move through, `fabric`
reads the instance as a FABRIC: a tapestry of qualities threaded together, giving a
holistic view of the initial state before any solving. Each thread is a chart of
instance-space with its own natural coordinate and its own decidability fold
(measured to be a Fisher-Rao metric singularity in that coordinate):

  parity thread    -- GF(2) rank-deficiency of the recovered XORs (fold ~0.05)
  orbit thread     -- symmetry coarseness / isotropy (fold ~0.9; sharper)
  gyration thread  -- hyperbolic depth in the Poincare mesh (distance to ∂∞)
  counting thread  -- at-most-one / cardinality signal
  implication thread -- binary-clause fraction
  shape thread     -- clause/variable ratio

The fabric is the coordinate of an instance in the "cosmo manifold"; the families
occupy distinct regions of it (a distributional ledger, `scripts/fabric_ledger.py`),
and the two Fisher folds (`scripts/fisher_fold.py`) are where the metric of the
predictive field diverges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .cnf_utils import CNFFormula
from .orbifold import hyperbolic_depth, symmetry_partition
from .scout import scout, xor_rank_deficiency


@dataclass
class Fabric:
    parity_kind: str          # 'consistent'|'inconsistent'|'nostruct'
    rank_deficiency: float    # parity thread: 0 determined ... 1 free (fold ~0.05)
    orbit_coarseness: float   # orbit thread: 0 rigid ... 1 highly symmetric (fold ~0.9)
    gyration: float           # hyperbolic depth (distance to the boundary ∂∞)
    counting_signal: float    # at-most-one fraction (cardinality thread)
    implication_signal: float # binary-clause fraction
    ratio: float              # clauses / variables
    region: str               # scout's verdict: island | tunnel | fold
    predicted_frame: str

    def as_dict(self) -> Dict[str, float]:
        return {"rank_def": self.rank_deficiency, "orbit": self.orbit_coarseness,
                "gyration": self.gyration, "counting": self.counting_signal,
                "implication": self.implication_signal, "ratio": self.ratio}


def fabric(formula: CNFFormula) -> Fabric:
    """Weave the instance's initial-state tapestry -- the holistic multi-quality
    coordinate of `formula` in the cosmo manifold."""
    n = max(formula.num_vars, 1)
    m = max(len(formula.clauses), 1)
    kind, defic = xor_rank_deficiency(formula)
    orbit = 1.0 - len(symmetry_partition(formula)) / n
    amo = sum(1 for c in formula.clauses
              if len(c) == 2 and all(l < 0 for l in c)) / m
    binf = sum(1 for c in formula.clauses if len(c) == 2) / m
    r = scout(formula)
    return Fabric(
        parity_kind=kind,
        rank_deficiency=defic,
        orbit_coarseness=orbit,
        gyration=hyperbolic_depth(formula),
        counting_signal=amo,
        implication_signal=binf,
        ratio=m / n,
        region=r.region,
        predicted_frame=r.predicted_frame,
    )

"""dynamics -- the view from outside: the laws, relations and motions of an
instance's solve, collected as one dynamical description.

Floating outside the model, we do not solve first -- we DESCRIBE. An instance,
before any CDCL search, already exhibits a dynamical signature under the coupled
frame router, and this module reads it into three registers:

  LAWS      the invariants -- what is conserved / cannot change under the solve:
            which algebraic conserved quantities are present (a GF(2) parity
            invariant, a ℤ counting bound, a 2-SAT implication closure), and whether
            the verdict is sound-by-construction.
  RELATIONS the couplings -- how the frames talk: the literals one frame ENTAILS and
            hands to the others (the Nelson-Oppen exchange), and how many cross.
  MOTIONS   the trajectory -- how the state moves: the breath (entailed-literal count
            per coupling round), its amplitude, whether it resonates to rest, and the
            instance's position in the hyperbolic mesh (gyration/depth toward ∂∞) and
            relative to the decidability fold (island / fold / tunnel).

This description is the bridge the operator asked for: collect the laws/relations/
motions dynamically, then REVERT them into an operational dispatch (backend/
metasolver.py) -- use the descriptive power precisely where the concrete frames and
geometry do not suffice. The description is sound to read (every entailed literal is
genuinely implied); it is a *predictor/driver*, never itself a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .cnf_utils import CNFFormula
from .fabric import fabric
from .frame_solver import coupling_breath


@dataclass
class Dynamics:
    # --- LAWS: the invariants (what is conserved under the solve) ---
    conserved: List[str]              # present algebraic invariants: parity|counting|implication
    verdict: str                      # 'SAT' | 'UNSAT' | 'CDCL_NEEDED' (frame/coupling)
    certified: bool                   # verdict sound by construction (not CDCL_NEEDED)

    # --- RELATIONS: the couplings (how the frames exchange entailed facts) ---
    entailed: Dict[int, bool]         # literals the coupling entails (the exchange)
    coupling_rank: int                # |entailed| -- strength of the cross-frame relation

    # --- MOTIONS: the trajectory (how the state moves) ---
    breath: List[int]                 # |fixed| after each coupling round (the inhale)
    amplitude: int                    # deepest single-round intake
    settled: bool                     # resonated to a fixpoint/conflict (rest)
    gyration: float                   # hyperbolic depth (distance toward the boundary ∂∞)
    region: str                       # 'island' | 'fold' | 'tunnel'
    predicted_frame: str              # the fabric's shallowest-frame guess

    # a compact, hashable signature of the whole dynamical state
    signature: tuple = field(default=())

    def sufficient(self) -> bool:
        """True when frame + geometry already suffice -- a certified verdict with no
        CDCL needed. When False, the description is the lever the metasolver reverts
        into a dispatch (this is 'where frame and geometry do not suffice')."""
        return self.certified

    def as_record(self) -> Dict[str, object]:
        return {
            "conserved": self.conserved, "verdict": self.verdict,
            "certified": self.certified, "coupling_rank": self.coupling_rank,
            "amplitude": self.amplitude, "settled": self.settled,
            "gyration": round(self.gyration, 3), "region": self.region,
            "predicted_frame": self.predicted_frame,
        }


def _conserved_invariants(formula: CNFFormula, fb) -> List[str]:
    """Which algebraic conserved quantities the instance carries (its 'laws')."""
    laws: List[str] = []
    if fb.parity_signal > 0.0:
        laws.append("parity")           # a GF(2) invariant lives here
    if fb.counting_signal > 0.0 or fb.orbit_coarseness >= 0.6:
        laws.append("counting")         # a ℤ magnitude bound / symmetry to count on
    if fb.implication_signal > 0.0:
        laws.append("implication")      # a 2-SAT closure
    return laws


def describe(formula: CNFFormula) -> Dynamics:
    """Read the instance's full dynamical description -- the view from outside. Runs
    the coupled router as a dynamical instrument (coupling_breath) and the fabric as
    the geometric read; collects both into the laws/relations/motions registers."""
    fb = fabric(formula)
    bt = coupling_breath(formula)
    entailed = dict(bt.entailed or {})
    conserved = _conserved_invariants(formula, fb)
    dyn = Dynamics(
        conserved=conserved,
        verdict=bt.verdict,
        certified=(bt.verdict != "CDCL_NEEDED"),
        entailed=entailed,
        coupling_rank=len(entailed),
        breath=list(bt.breath),
        amplitude=bt.amplitude,
        settled=bt.settled,
        gyration=fb.gyration,
        region=fb.region,
        predicted_frame=fb.predicted_frame,
    )
    dyn.signature = (tuple(conserved), dyn.verdict, dyn.region,
                     round(dyn.gyration, 2), dyn.coupling_rank)
    return dyn
